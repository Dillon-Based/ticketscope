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
from ticketscope.core.fakes import HashEmbedder
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
