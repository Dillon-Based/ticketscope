"""`jobs.eval`'s run over its I/O matrix (story 2.1), with the database faked.

`read_corpus_meta` and `PostgresCorpusStore` are replaced on the module, as the load tests
do, so `run` reads lineage from a fake row and scores a fake store.
"""

import json
import logging
from pathlib import Path

import pytest
from opentelemetry.instrumentation.utils import is_instrumentation_enabled

from tests.eval.conftest import results_from_log
from tests.factories import snapshot_issue
from ticketscope import telemetry
from ticketscope.adapters.postgres import CorpusMeta
from ticketscope.core import modes
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.pairs import Pair, pairs_jsonl
from ticketscope.core.ports import CorpusStore, Retriever
from ticketscope.core.snapshot import JiraComment
from ticketscope.jobs.eval import main as eval_main
from ticketscope.jobs.eval import score
from ticketscope.jobs.load.main import build_rows
from ticketscope.settings import Settings

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
    (tmp_path / f"{META.snapshot_version}.jsonl").write_bytes(pairs_jsonl([Pair(2, 1, "short")]))
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
    assert results["modes"] == {"keyword": {"recall@10": 1.0, "mrr@10": 1.0, "pairs_scored": 1}}


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

    def spy_score(store: CorpusStore, pairs: object) -> dict[str, object]:
        seen.append(is_instrumentation_enabled())
        return {"k": 10, "relevance": "target", "modes": {}}

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
    (tmp_path / "2026.99.1.jsonl").write_bytes(pairs_jsonl([Pair(42, 1, "short")]))
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

    def build(_store: CorpusStore) -> Retriever:
        return Spy()

    spy_mode = modes.Mode("spy", "bm25", build, lambda _store: True)
    monkeypatch.setattr(modes, "REGISTRY", {"spy": spy_mode})

    score(store, [Pair(2, 1, "short")])

    assert texts == ["Title token alpha\n\nDescription token bravo"]
    assert "charlie" not in texts[0]


def test_unavailable_modes_are_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    off = modes.Mode("off", "cosine", modes.KeywordRetriever, lambda _store: False)
    monkeypatch.setattr(modes, "REGISTRY", {**modes.REGISTRY, "off": off})
    results = score(_store(), [Pair(2, 1, "short")])
    assert list(results["modes"]) == ["keyword"]


def test_no_pairs_scores_zero_pairs() -> None:
    results = score(_store(), [])
    assert results["modes"]["keyword"] == {"recall@10": 0.0, "mrr@10": 0.0, "pairs_scored": 0}
