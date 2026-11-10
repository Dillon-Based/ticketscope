"""`jobs.eval`'s run over its I/O matrix (story 2.1), with the database faked.

`read_corpus_meta` and `PostgresCorpusStore` are replaced on the module, as the load tests
do, so `run` reads lineage from a fake row and scores a fake store.
"""

import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest
from opentelemetry.instrumentation.utils import is_instrumentation_enabled

from tests.eval.conftest import results_from_log, write_job_summary
from tests.factories import snapshot_issue
from ticketscope import telemetry
from ticketscope.adapters.postgres import CorpusMeta
from ticketscope.core import modes
from ticketscope.core.fakes import HashEmbedder, InMemoryCorpusStore
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.pairs import Pair, pairs_jsonl
from ticketscope.core.ports import CorpusStore, Embedder, Retriever
from ticketscope.core.snapshot import JiraComment
from ticketscope.jobs.eval import main as eval_main
from ticketscope.jobs.eval import score
from ticketscope.jobs.eval.score import first_member_rank, p95
from ticketscope.jobs.load.main import build_rows
from ticketscope.settings import Settings

PAIR = Pair(2, 1, "short", (1,))
META = CorpusMeta(
    snapshot_version="2026.99.1",
    embedding_model_id=None,
    preprocessing_version="pre1.kind2-t3.outcome3",
)


def _store() -> InMemoryCorpusStore:
    records = [
        (IssueRecord(number=1, title="launcher crash", url="u1", kind="short", state="closed"), ""),
        (IssueRecord(number=2, title="launcher crash", url="u2", kind="short", state="closed"), ""),
    ]
    return InMemoryCorpusStore(
        [(r, f"{r.title}\n\n{b}") for r, b in records], corpus_version="2026.99.1"
    )


@pytest.fixture
def pairs_dir(tmp_path: Path) -> Path:
    (tmp_path / f"{META.snapshot_version}.jsonl").write_bytes(pairs_jsonl([PAIR]))
    return tmp_path


def _settings(pairs_dir: Path) -> Settings:
    return Settings(eval_pairs_dir=pairs_dir)


def _patch(monkeypatch: pytest.MonkeyPatch, meta: CorpusMeta | None) -> None:
    monkeypatch.setattr(eval_main, "read_corpus_meta", lambda conninfo: meta)
    monkeypatch.setattr(eval_main, "PostgresCorpusStore", lambda conninfo: _store())


def _results_line(caplog: pytest.LogCaptureFixture) -> dict[str, object]:
    lines = [
        r.getMessage().removeprefix(eval_main.RESULTS_PREFIX)
        for r in caplog.records
        if r.getMessage().startswith(eval_main.RESULTS_PREFIX)
    ]
    assert len(lines) == 1, caplog.text
    return json.loads(lines[0])


def test_results_line_carries_scores_lineage_pairs_file_and_wall_seconds(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, pairs_dir: Path
) -> None:
    _patch(monkeypatch, META)
    caplog.set_level(logging.INFO, logger="ticketscope.eval")

    assert eval_main.run(_settings(pairs_dir)) == 0

    results = _results_line(caplog)
    assert results["lineage"] == {
        "snapshot_version": "2026.99.1",
        "embedding_model_id": None,
        "preprocessing_version": "pre1.kind2-t3.outcome3",
    }
    assert results["pairs_file"] == str(pairs_dir / "2026.99.1.jsonl")
    assert isinstance(results["wall_seconds"], float)
    assert results["relevance"] == "cluster"
    assert results["skipped_modes"] == ["dense", "hybrid"]  # eval has no embedder
    keyword = results["modes"]["keyword"]  # pyright: ignore[reportIndexIssue]
    assert keyword["overall"]["recall@1"] == 1.0
    assert keyword["overall"]["mrr@10"] == 1.0
    assert keyword["short"]["pairs_scored"] == 1
    assert keyword["log_heavy"]["pairs_scored"] == 0
    assert keyword["first_member_ranks"] == [[2, 1]]


def test_the_kind_check_reads_the_results_line_back_from_the_json_log(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, pairs_dir: Path
) -> None:
    _patch(monkeypatch, META)
    caplog.set_level(logging.INFO, logger="ticketscope.eval")
    assert eval_main.run(_settings(pairs_dir)) == 0
    formatter = telemetry.JsonFormatter()
    log = "\n".join(formatter.format(r) for r in caplog.records)

    assert results_from_log(log) == _results_line(caplog)


def test_scoring_runs_with_instrumentation_suppressed(
    monkeypatch: pytest.MonkeyPatch, pairs_dir: Path
) -> None:
    seen: list[bool] = []

    def spy_score(store: CorpusStore, pairs: object, embedder: object = None) -> dict[str, object]:
        seen.append(is_instrumentation_enabled())
        return {"k": 10, "relevance": "cluster", "modes": {}}

    _patch(monkeypatch, META)
    monkeypatch.setattr(eval_main, "score", spy_score)
    assert eval_main.run(_settings(pairs_dir)) == 0
    assert seen == [False]
    assert is_instrumentation_enabled()


def test_missing_pairs_file_exits_1_and_logs_the_path(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    _patch(monkeypatch, META)
    assert eval_main.run(_settings(tmp_path)) == 1
    assert str(tmp_path / "2026.99.1.jsonl") in caplog.text
    assert eval_main.RESULTS_PREFIX not in caplog.text


def test_no_corpus_loaded_exits_1(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, pairs_dir: Path
) -> None:
    _patch(monkeypatch, None)
    assert eval_main.run(_settings(pairs_dir)) == 1
    assert "no corpus loaded" in caplog.text
    assert eval_main.RESULTS_PREFIX not in caplog.text


def test_a_store_failure_exits_1(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, pairs_dir: Path
) -> None:
    def broken(conninfo: str) -> CorpusMeta:
        raise OSError("connection refused")

    monkeypatch.setattr(eval_main, "read_corpus_meta", broken)
    assert eval_main.run(_settings(pairs_dir)) == 1
    assert "eval failed" in caplog.text


def test_a_query_issue_missing_from_the_corpus_fails_rather_than_scoring_zero(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    (tmp_path / "2026.99.1.jsonl").write_bytes(pairs_jsonl([Pair(42, 1, "short", (1,))]))
    _patch(monkeypatch, META)
    assert eval_main.run(_settings(tmp_path)) == 1
    assert "query issue 42" in caplog.text


def test_query_text_is_title_and_description_without_comments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    query = snapshot_issue(
        number=2,
        title="Title token alpha",
        body="Description token bravo",
        resolution="Duplicate",
        comments=[
            JiraComment(
                body="Comment token charlie",
                created_at=snapshot_issue().created_at,
                from_reporter=False,
            )
        ],
    )
    target = snapshot_issue(number=1)
    rows = list(build_rows([target, query]))
    store = InMemoryCorpusStore(
        [(IssueRecord(r.number, r.title, r.url, r.kind, r.state), r.search_text) for r in rows],
        bodies={r.number: r.body for r in rows},
    )
    texts: list[str] = []

    class Spy:
        def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
            texts.append(query)
            return []

    def build(_store: CorpusStore, _embedder: Embedder | None) -> Retriever:
        return Spy()

    spy_mode = modes.Mode("spy", "bm25", build, lambda _store, _embedder: True)
    monkeypatch.setattr(modes, "REGISTRY", {"spy": spy_mode})

    score(store, [PAIR])

    assert texts == ["Title token alpha\n\nDescription token bravo"]
    assert "charlie" not in texts[0]


def test_unavailable_modes_are_skipped_and_named(monkeypatch: pytest.MonkeyPatch) -> None:
    off = modes.Mode(
        "off", "cosine", lambda s, _e: modes.KeywordRetriever(s), lambda _store, _embedder: False
    )
    monkeypatch.setattr(modes, "REGISTRY", {**modes.REGISTRY, "off": off})
    results = score(_store(), [PAIR])
    assert list(results["modes"]) == ["keyword"]
    assert results["skipped_modes"] == ["dense", "hybrid", "off"]


def test_a_mode_registered_after_import_is_scored_with_no_job_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    second = modes.Mode(
        "second", "cosine", lambda s, _e: modes.KeywordRetriever(s), lambda _store, _embedder: True
    )
    monkeypatch.setattr(modes, "REGISTRY", {**modes.REGISTRY, "second": second})
    results = score(_store(), [PAIR])
    assert sorted(results["modes"]) == ["keyword", "second"]
    assert results["modes"]["second"]["overall"]["recall@10"] == 1.0


def test_no_pairs_scores_zero_pairs_with_zero_metrics() -> None:
    empty = {
        "recall@1": 0.0,
        "recall@5": 0.0,
        "recall@10": 0.0,
        "mrr@10": 0.0,
        "p95_latency_ms": 0.0,
        "pairs_scored": 0,
    }
    keyword = score(_store(), [])["modes"]["keyword"]
    assert keyword["short"] == keyword["log_heavy"] == keyword["overall"] == empty
    assert keyword["first_member_ranks"] == []


def test_a_kind_with_no_pairs_has_zero_metrics_while_overall_counts_the_rest() -> None:
    keyword = score(_store(), [PAIR])["modes"]["keyword"]
    assert keyword["log_heavy"]["pairs_scored"] == 0
    assert keyword["log_heavy"]["recall@10"] == 0.0
    assert keyword["log_heavy"]["p95_latency_ms"] == 0.0
    assert keyword["overall"]["pairs_scored"] == 1


def test_scoring_the_same_corpus_twice_gives_identical_metrics_and_ranks() -> None:
    def metrics() -> object:
        keyword = score(_store(), [PAIR])["modes"]["keyword"]
        return {
            kind: {m: v for m, v in keyword[kind].items() if m != "p95_latency_ms"}  # pyright: ignore[reportIndexIssue, reportAttributeAccessIssue]
            for kind in ("short", "log_heavy", "overall")
        } | {"ranks": keyword["first_member_ranks"]}

    assert metrics() == metrics()


def test_a_latency_is_measured_per_search(monkeypatch: pytest.MonkeyPatch) -> None:
    ticks = iter([0.0, 0.004, 1.0, 1.010, 2.0, 2.002])
    monkeypatch.setattr(
        sys.modules["ticketscope.jobs.eval.score"].time, "perf_counter", lambda: next(ticks)
    )
    pairs = [PAIR, Pair(1, 2, "log_heavy", (2,)), Pair(3, 1, "short", (1,))]
    store = InMemoryCorpusStore(
        [
            (IssueRecord(n, "launcher crash", f"u{n}", "short", "closed"), "launcher crash")
            for n in (1, 2, 3)
        ]
    )
    keyword = score(store, pairs)["modes"]["keyword"]
    # three searches of 4, 10 and 2 ms; nearest-rank p95 of three is the largest
    assert keyword["overall"]["p95_latency_ms"] == pytest.approx(10.0)
    assert keyword["short"]["pairs_scored"] == 2
    assert keyword["log_heavy"]["pairs_scored"] == 1
    assert keyword["short"]["p95_latency_ms"] == pytest.approx(4.0)
    assert keyword["log_heavy"]["p95_latency_ms"] == pytest.approx(10.0)


def test_p95_is_the_nearest_rank_value() -> None:
    values = [float(n) for n in range(1, 101)]
    assert p95(values) == 95.0
    assert p95([5.0]) == 5.0
    assert p95([]) == 0.0
    assert p95([10.0, 1.0]) == 10.0


def test_first_member_rank_boundaries() -> None:
    assert first_member_rank({1, 3}, [100, 3, 1]) == 2
    assert first_member_rank({6}, [*range(100, 109), 6]) == 10
    assert first_member_rank({6}, [*range(100, 110), 6]) is None
    assert first_member_rank({6}, []) is None


def test_the_job_summary_shows_cost_pair_counts_and_metrics(tmp_path: Path) -> None:
    results = {"wall_seconds": 12.3, "skipped_modes": [], "modes": score(_store(), [PAIR])["modes"]}
    summary = tmp_path / "summary.md"
    write_job_summary(results, summary)
    write_job_summary(results, summary)  # appends
    text = summary.read_text()
    assert text.count("Wall seconds: 12.3") == 2
    assert "short 1, log_heavy 0, overall 1" in text
    assert "| overall | 1.0000 | 1.0000 | 1.0000 | 1.0000 |" in text


def test_the_job_summary_is_skipped_without_the_env_var(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.chdir(tmp_path)
    write_job_summary({"wall_seconds": 1.0, "skipped_modes": [], "modes": {}})
    assert list(tmp_path.iterdir()) == []


def test_the_job_summary_goes_to_github_step_summary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "s.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(path))
    write_job_summary({"wall_seconds": 1.0, "skipped_modes": ["dense"], "modes": {}})
    assert "Skipped modes: dense" in path.read_text()


def test_a_malformed_pairs_line_exits_1_and_names_the_line(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    good = pairs_jsonl([PAIR])
    (tmp_path / "2026.99.1.jsonl").write_bytes(
        good + b'{"query": 3, "target": 1, "kind": "short"}\n'
    )
    _patch(monkeypatch, META)
    assert eval_main.run(_settings(tmp_path)) == 1
    assert "pairs line 2" in caplog.text


def test_modes_keep_separate_ranks_and_latency_samples(monkeypatch: pytest.MonkeyPatch) -> None:
    class Miss:
        def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
            return []

    second = modes.Mode(
        "miss", "cosine", lambda _store, _embedder: Miss(), lambda _store, _embedder: True
    )
    monkeypatch.setattr(modes, "REGISTRY", {**modes.REGISTRY, "miss": second})
    ticks = iter([0.0, 0.004, 1.0, 1.020])
    monkeypatch.setattr(
        sys.modules["ticketscope.jobs.eval.score"].time, "perf_counter", lambda: next(ticks)
    )
    results = score(_store(), [PAIR])["modes"]
    assert results["keyword"]["first_member_ranks"] == [[2, 1]]
    assert results["miss"]["first_member_ranks"] == [[2, None]]
    assert results["keyword"]["overall"]["recall@10"] == 1.0
    assert results["miss"]["overall"]["recall@10"] == 0.0
    assert results["keyword"]["overall"]["p95_latency_ms"] == pytest.approx(4.0)
    assert results["miss"]["overall"]["p95_latency_ms"] == pytest.approx(20.0)


# --- dense and hybrid beside keyword (story 3.5) -------------------------------------------


def _embedded_store() -> InMemoryCorpusStore:
    embedder = HashEmbedder()
    records = [
        IssueRecord(number=1, title="launcher crash", url="u1", kind="short", state="closed"),
        IssueRecord(number=2, title="launcher crash", url="u2", kind="short", state="closed"),
        IssueRecord(number=3, title="unrelated sound bug", url="u3", kind="short", state="open"),
    ]
    documents = [(r, f"{r.title}\n\n") for r in records]
    vectors = embedder.embed([text for _, text in documents])
    return InMemoryCorpusStore(
        documents,
        corpus_version="2026.99.1",
        embeddings={
            embedder.model_id: {r.number: v for (r, _), v in zip(documents, vectors, strict=True)}
        },
        embedding_model=embedder.model_id,
    )


def test_an_embedder_scores_dense_and_hybrid_beside_keyword_on_every_pair() -> None:
    results = score(_embedded_store(), [PAIR], HashEmbedder())

    assert sorted(results["modes"]) == ["dense", "hybrid", "keyword"]
    assert results["skipped_modes"] == []
    for name in ("keyword", "dense", "hybrid"):
        mode = results["modes"][name]
        assert mode["overall"]["pairs_scored"] == 1, name
        assert mode["short"]["pairs_scored"] == 1, name
        assert mode["log_heavy"]["pairs_scored"] == 0, name
        assert mode["first_member_ranks"] == [[2, 1]], name


def test_query_embedding_is_inside_the_timed_search_so_dense_p95_is_honest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]
    monkeypatch.setattr(
        sys.modules["ticketscope.jobs.eval.score"].time, "perf_counter", lambda: clock[0]
    )

    class Slow(HashEmbedder):
        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            clock[0] += 0.02  # the model takes 20 ms of the fake clock
            return super().embed(texts)

    results = score(_embedded_store(), [PAIR], Slow())

    assert results["modes"]["keyword"]["overall"]["p95_latency_ms"] == 0.0
    assert results["modes"]["dense"]["overall"]["p95_latency_ms"] == pytest.approx(20.0)
    assert results["modes"]["hybrid"]["overall"]["p95_latency_ms"] == pytest.approx(20.0)


def test_an_embedder_for_another_model_leaves_dense_and_hybrid_skipped() -> None:
    results = score(_embedded_store(), [PAIR], HashEmbedder(model_id="other-model"))

    assert list(results["modes"]) == ["keyword"]
    assert results["skipped_modes"] == ["dense", "hybrid"]


def test_build_embedder_is_none_without_a_model_id() -> None:
    assert eval_main.build_embedder(Settings(embedding_model_id="")) is None


def test_run_hands_the_built_embedder_to_score(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, pairs_dir: Path
) -> None:
    embedder = HashEmbedder()
    seen: list[object] = []
    real = eval_main.score

    def spy(store: CorpusStore, pairs: object, given: Embedder | None = None) -> object:
        seen.append(given)
        return real(store, pairs, given)  # pyright: ignore[reportArgumentType]

    _patch(monkeypatch, META)
    monkeypatch.setattr(eval_main, "build_embedder", lambda settings: embedder)
    monkeypatch.setattr(eval_main, "score", spy)
    caplog.set_level(logging.INFO, logger="ticketscope.eval")

    assert eval_main.run(_settings(pairs_dir)) == 0
    assert seen == [embedder]
