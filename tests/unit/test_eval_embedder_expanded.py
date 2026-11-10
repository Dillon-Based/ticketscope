"""Expanded coverage for story 3.5: the eval Job's embedder wiring and its time budget.

`build_embedder` is exercised with a fake `FastEmbedEmbedder` (no model download), the
failure paths of `run` are pinned, and the Job's deadline is checked against the Helm and
workflow timeouts that must outlast it.
"""

import logging
import re
import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest

from tests.unit.test_chart_embeddings import _NO_PIN, _doc, _render
from tests.unit.test_eval_main import META, PAIR, _embedded_store, _patch, _settings
from ticketscope.adapters import embedder as embedder_module
from ticketscope.core.fakes import HashEmbedder
from ticketscope.core.pairs import pairs_jsonl
from ticketscope.jobs.eval import main as eval_main
from ticketscope.jobs.eval import score
from ticketscope.settings import Settings

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


def test_each_pair_embeds_its_query_once_for_dense_and_once_for_hybrid() -> None:
    embedded: list[int] = []

    class Counting(HashEmbedder):
        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            embedded.append(len(texts))
            return super().embed(texts)

    results = score(_embedded_store(), [PAIR, PAIR], Counting())

    assert results["modes"]["dense"]["overall"]["pairs_scored"] == 2
    assert embedded == [1, 1, 1, 1]  # 2 pairs x (dense + hybrid); keyword never embeds


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
