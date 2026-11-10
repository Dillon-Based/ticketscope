"""Expanded coverage for story 3.5: the eval Job's embedder wiring and its time budget.

`build_embedder` is exercised with a fake `FastEmbedEmbedder` (no model download), the
failure paths of `run` are pinned, and the Job's deadline is checked against the Helm and
workflow timeouts that must outlast it.
"""

import importlib
import logging
import re
import shutil
from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.unit.test_chart_embeddings import _NO_PIN, _doc, _render
from tests.unit.test_eval_main import META, PAIR, _embedded_store, _patch, _settings
from ticketscope.adapters import embedder as embedder_module
from ticketscope.core import modes
from ticketscope.core.fakes import HashEmbedder, InMemoryCorpusStore
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.pairs import Pair, pairs_jsonl
from ticketscope.jobs.eval import main as eval_main
from ticketscope.jobs.eval import score
from ticketscope.settings import Settings

# The module, not the `score` function the package re-exports under the same name.
score_module = importlib.import_module("ticketscope.jobs.eval.score")

# A second query with a different text from PAIR's (issue 3 against issue 2's cluster).
OTHER_PAIR = Pair(3, 1, "short", (1,))

ROOT = Path(__file__).resolve().parents[2]
needs_helm = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")


def test_build_embedder_loads_the_named_model_from_the_cache_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[str, Path]] = []

    class Fake(HashEmbedder):
        def __init__(self, model_id: str, cache_dir: Path) -> None:
            super().__init__(model_id=model_id)
            calls.append((model_id, cache_dir))

    monkeypatch.setattr(embedder_module, "FastEmbedEmbedder", Fake)
    built = eval_main.build_embedder(
        Settings(embedding_model_id="BAAI/bge-small-en-v1.5", embedding_cache_dir=tmp_path)
    )

    assert built is not None and built.model_id == "BAAI/bge-small-en-v1.5"
    assert calls == [("BAAI/bge-small-en-v1.5", tmp_path)]


def test_a_model_that_fails_to_load_fails_the_job_without_a_results_line(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    (tmp_path / f"{META.snapshot_version}.jsonl").write_bytes(pairs_jsonl([PAIR]))
    _patch(monkeypatch, META)

    def boom(settings: Settings) -> None:
        raise RuntimeError("model missing from /models")

    monkeypatch.setattr(eval_main, "build_embedder", boom)
    caplog.set_level(logging.INFO, logger="ticketscope.eval")

    assert eval_main.run(_settings(tmp_path)) == 1
    assert eval_main.RESULTS_PREFIX not in caplog.text
    assert "eval failed" in caplog.text


def test_each_pair_embeds_its_query_once_for_dense_and_hybrid_together() -> None:
    embedded: list[int] = []

    class Counting(HashEmbedder):
        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            embedded.append(len(texts))
            return super().embed(texts)

    results = score(_embedded_store(), [PAIR, OTHER_PAIR], Counting())

    assert results["modes"]["dense"]["overall"]["pairs_scored"] == 2
    assert results["modes"]["hybrid"]["overall"]["pairs_scored"] == 2
    assert embedded == [1, 1]  # one per query: hybrid reuses dense's vector; keyword never embeds


def test_reusing_the_query_vector_leaves_every_rank_unchanged() -> None:
    # Oracle: each mode's retriever, built and searched directly with its own fresh embedder,
    # as score did before the cache.
    store = _embedded_store()
    pairs = [PAIR, OTHER_PAIR]
    results = score(store, pairs, HashEmbedder())

    for name in ("dense", "hybrid"):
        expected: list[list[int | None]] = []
        for pair in sorted(pairs, key=lambda p: p.query):
            retriever = modes.REGISTRY[name].build(store, HashEmbedder())
            hits = retriever.search(
                score_module.query_text(store, pair.query),
                score_module.K,
                exclude=frozenset({pair.query}),
            )
            ranked = [hit.issue.number for hit in hits]
            expected.append([pair.query, score_module.first_member_rank(pair.relevant, ranked)])
        assert results["modes"][name]["first_member_ranks"] == expected, name


def test_the_mode_that_reuses_the_vector_has_the_model_time_added_to_its_latency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A fake clock: every reading moves 1 ms, and each model call costs another 500 ms.
    now = [0.0]

    def clock() -> float:
        now[0] += 0.001
        return now[0]

    class Slow(HashEmbedder):
        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            now[0] += 0.5
            return super().embed(texts)

    # Only score's own `time` name: the real time module stays untouched.
    monkeypatch.setattr(score_module, "time", SimpleNamespace(perf_counter=clock))
    results = score(_embedded_store(), [PAIR], Slow())

    dense = results["modes"]["dense"]["overall"]["p95_latency_ms"]
    hybrid = results["modes"]["hybrid"]["overall"]["p95_latency_ms"]
    keyword = results["modes"]["keyword"]["overall"]["p95_latency_ms"]
    assert dense >= 500 and hybrid >= 500  # both include the one model call
    assert keyword < 500  # keyword never embeds, so nothing is added to it


def test_query_vector_cache_reuses_only_the_same_texts_and_returns_copies() -> None:
    calls: list[list[str]] = []
    ticks = iter([0.0, 0.25, 1.0, 1.5])  # first call: 250 ms; second, other text: 500 ms

    class Recording(HashEmbedder):
        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            calls.append(list(texts))
            return super().embed(texts)

    cache = score_module.QueryVectorCache(Recording("m"), clock=lambda: next(ticks))
    assert cache.model_id == "m"

    first = cache.embed(["launcher crash"])
    first[0][0] = 99.0  # a caller mutating its copy must not leak into the next answer
    again = cache.embed(["launcher crash"])
    assert again == HashEmbedder("m").embed(["launcher crash"])
    assert calls == [["launcher crash"]]
    assert cache.take_reused_ms() == pytest.approx(250.0)
    assert cache.take_reused_ms() == 0.0  # taking resets it

    cache.embed(["unrelated sound bug"])
    assert calls == [["launcher crash"], ["unrelated sound bug"]]
    assert cache.take_reused_ms() == 0.0  # a new text is a model call, not a reuse


def test_an_embedder_over_a_store_without_embeddings_skips_dense_and_hybrid() -> None:
    from tests.unit.test_eval_main import _store

    results = score(_store(), [PAIR], HashEmbedder())

    assert list(results["modes"]) == ["keyword"]
    assert results["skipped_modes"] == ["dense", "hybrid"]


# --- search reuse: each keyword and dense list fetched once per query ------------------------


class _Counting:
    """Wraps a store and counts the keyword and dense searches that reach it, with k."""

    def __init__(self, inner: InMemoryCorpusStore) -> None:
        self._inner = inner
        self.keyword: list[int] = []
        self.dense: list[int] = []

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        self.keyword.append(k)
        return self._inner.keyword_search(query, k)

    def dense_search(self, model_id: str, vector: Sequence[float], k: int) -> list[Scored]:
        self.dense.append(k)
        return self._inner.dense_search(model_id, vector, k)

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)


def _tied_store() -> InMemoryCorpusStore:
    """30 issues in three tie groups of ten, by keyword score and by vector, so the 11th and
    12th rows of every list sit inside a tie broken only by issue number."""
    embedder = HashEmbedder()
    texts = {
        **{n: "launcher crash launcher crash" for n in range(1, 11)},
        **{n: "launcher crash" for n in range(11, 21)},
        **{n: "launcher crash on startup" for n in range(21, 31)},
    }
    records = [IssueRecord(n, text, f"u{n}", "short", "closed") for n, text in texts.items()]
    documents = [(r, f"{r.title}\n\n") for r in records]
    vectors = embedder.embed([text for _, text in documents])
    return InMemoryCorpusStore(
        documents,
        embeddings={
            embedder.model_id: {r.number: v for (r, _), v in zip(documents, vectors, strict=True)}
        },
        embedding_model=embedder.model_id,
    )


TIED_PAIRS = [Pair(q, 1, "short", (5,)) for q in (2, 12, 22, 7)]


def test_each_query_fetches_its_keyword_and_dense_lists_once() -> None:
    counting = _Counting(_embedded_store())
    results = score(counting, [PAIR, OTHER_PAIR], HashEmbedder())  # type: ignore[arg-type]

    # Without reuse: keyword and hybrid each search keyword, dense and hybrid each search dense.
    assert len(counting.keyword) == 2 and len(counting.dense) == 2  # one of each per pair
    assert set(counting.keyword) == set(counting.dense) == {score_module.K + 2}
    timing = results["timing"]
    assert (timing["keyword_fetches"], timing["dense_fetches"], timing["embed_calls"]) == (2, 2, 2)
    assert set(timing["mode_search_seconds"]) == {"keyword", "dense", "hybrid"}


def test_reusing_searches_leaves_every_rank_unchanged_across_ties() -> None:
    # Oracle: each mode built over the raw store, with its own embedder, searched directly.
    store = _tied_store()
    results = score(store, TIED_PAIRS, HashEmbedder())
    for name in ("keyword", "dense", "hybrid"):
        expected: list[list[int | None]] = []
        for pair in sorted(TIED_PAIRS, key=lambda p: p.query):
            retriever = modes.REGISTRY[name].build(store, HashEmbedder())
            text = score_module.query_text(store, pair.query)
            hits = retriever.search(text, score_module.K, exclude=frozenset({pair.query}))
            ranked = [hit.issue.number for hit in hits]
            expected.append([pair.query, score_module.first_member_rank(pair.relevant, ranked)])
        assert results["modes"][name]["first_member_ranks"] == expected, name


def test_hybrid_gets_the_search_time_it_reused_added_to_its_latency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Every clock read moves 1 ms; each keyword or dense fetch costs another 300 ms.
    now = [0.0]

    def clock() -> float:
        now[0] += 0.001
        return now[0]

    class Slow(InMemoryCorpusStore):
        def keyword_search(self, query: str, k: int) -> list[Scored]:
            now[0] += 0.3
            return super().keyword_search(query, k)

        def dense_search(self, model_id: str, vector: Sequence[float], k: int) -> list[Scored]:
            now[0] += 0.3
            return super().dense_search(model_id, vector, k)

    base = _embedded_store()
    slow = Slow([], embeddings={}, embedding_model=None)
    slow.__dict__.update(base.__dict__)
    monkeypatch.setattr(score_module, "time", SimpleNamespace(perf_counter=clock))
    results = score(slow, [PAIR], HashEmbedder())

    overall = {m: results["modes"][m]["overall"]["p95_latency_ms"] for m in results["modes"]}
    assert overall["keyword"] >= 300 and overall["dense"] >= 300
    assert overall["hybrid"] >= 600  # both lists it fused, though neither was fetched again
    raw = results["timing"]["mode_search_seconds"]
    assert raw["hybrid"] < 0.3  # its own search touched neither store call


def test_search_reuse_store_serves_heads_refetches_longer_and_starts_clean() -> None:
    counting = _Counting(_tied_store())
    ticks = iter([0.0, 0.2, 1.0, 1.5, 2.0, 2.1])  # fetches of 200 ms, 500 ms, 100 ms
    reuse = score_module.SearchReuseStore(counting, clock=lambda: next(ticks))  # type: ignore[arg-type]

    reuse.begin(12)
    first = [h.issue.number for h in reuse.keyword_search("launcher crash", 11)]
    assert counting.keyword == [12]  # fetched the most any mode asks for
    assert len(first) == 11
    again = [h.issue.number for h in reuse.keyword_search("launcher crash", 12)]
    assert counting.keyword == [12] and again[:11] == first
    assert reuse.take_reused_ms() == pytest.approx(200.0)

    longer = reuse.keyword_search("launcher crash", 20)  # more rows than were fetched
    assert counting.keyword == [12, 20] and len(longer) == 20
    assert reuse.take_reused_ms() == 0.0

    reuse.begin(12)  # a new query forgets the last one's lists
    reuse.keyword_search("launcher crash", 5)
    assert counting.keyword == [12, 20, 12]


def test_a_short_list_answers_any_longer_request_without_a_refetch() -> None:
    counting = _Counting(_tied_store())
    reuse = score_module.SearchReuseStore(counting)  # type: ignore[arg-type]
    reuse.begin(12)
    # "startup" matches only issues 21-30: the fetch of 12 comes back with 10, all there is.
    assert len(reuse.keyword_search("startup", 11)) == 10
    assert len(reuse.keyword_search("startup", 40)) == 10
    assert counting.keyword == [12]


# --- time budget ---------------------------------------------------------------------------


def _eval_deadline_seconds() -> int:
    text = (ROOT / "deploy/charts/ticketscope/values.yaml").read_text(encoding="utf-8")
    match = re.search(r"^eval:\n(?:[ #].*\n)*?  activeDeadlineSeconds: (\d+)", text, re.MULTILINE)
    assert match
    return int(match.group(1))


def test_the_workflow_timeout_outlasts_the_eval_deadline_plus_setup() -> None:
    text = (ROOT / ".github/workflows/_kind-deploy.yml").read_text(encoding="utf-8")
    minutes = int(re.search(r"timeout-minutes: (\d+)", text.split("  deploy:")[1]).group(1))  # type: ignore[union-attr]
    assert minutes * 60 >= _eval_deadline_seconds() + 15 * 60


def test_the_eval_helm_timeout_outlasts_the_eval_deadline() -> None:
    text = (ROOT / "scripts/kind-up.sh").read_text(encoding="utf-8")
    branch = text[text.index('if [[ "${EVAL_ENABLED:-0}" == 1 ]]; then') :]
    minutes = int(re.search(r"HELM_TIMEOUT=(\d+)m", branch).group(1))  # type: ignore[union-attr]
    assert minutes * 60 > _eval_deadline_seconds()


@pytest.mark.xfail(
    strict=True,
    reason="PRODUCT DEFECT: EMBEDDINGS_COMPUTE=1 resets HELM_TIMEOUT to 50m after eval set 60m",
)
def test_embeddings_compute_does_not_shrink_the_eval_helm_timeout() -> None:
    text = (ROOT / "scripts/kind-up.sh").read_text(encoding="utf-8")
    compute = text[text.index('if [[ "${EMBEDDINGS_COMPUTE:-0}" == 1 ]]; then') :]
    compute = compute[: compute.index("\nfi\n")]
    match = re.search(r"HELM_TIMEOUT=(\d+)m", compute)
    assert match is None or int(match.group(1)) * 60 > _eval_deadline_seconds() + 15 * 60


@needs_helm
def test_eval_resources_can_be_overridden_and_default_to_a_1gi_limit() -> None:
    default = _doc(_render(*_NO_PIN, "--set", "eval.enabled=true"), "ticketscope-eval")
    assert "memory: 1Gi" in default and "memory: 256Mi" in default
    bigger = _doc(
        _render(
            *_NO_PIN, "--set", "eval.enabled=true", "--set", "eval.resources.limits.memory=2Gi"
        ),
        "ticketscope-eval",
    )
    assert "memory: 2Gi" in bigger and "memory: 1Gi" not in bigger
