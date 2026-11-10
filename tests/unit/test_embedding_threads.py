"""api caps onnxruntime's threads at its CPU limit.

onnxruntime sizes its intra-op pool from the host's cores, not the cgroup quota. On a CI
runner that is four threads under api's one-core limit, which are throttled in bursts; 16
queued dense requests then ran past Envoy's 15 s route timeout (story 3.7's integrated
check). The chart sets `api.embeddingThreads` beside the limit; api passes it to fastembed.
"""

import shutil
import sys
import types
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from tests.unit.test_chart_embeddings import _NO_PIN, _doc, _render
from ticketscope.adapters.embedder import FastEmbedEmbedder
from ticketscope.core.fakes import HashEmbedder, InMemoryCorpusStore
from ticketscope.http.app import create_app
from ticketscope.settings import Settings

needs_helm = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")
MODEL = "BAAI/bge-small-en-v1.5"


def _fake_fastembed(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    seen: dict[str, object] = {}

    class FakeTextEmbedding:
        def __init__(self, **kwargs: object) -> None:
            seen.update(kwargs)

    monkeypatch.setitem(
        sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=FakeTextEmbedding)
    )
    return seen


def test_the_adapter_passes_the_thread_cap_to_fastembed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen = _fake_fastembed(monkeypatch)
    FastEmbedEmbedder("some/model", tmp_path, threads=1)
    assert seen["threads"] == 1


def test_the_adapter_keeps_the_runtime_default_without_a_cap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen = _fake_fastembed(monkeypatch)
    FastEmbedEmbedder("some/model", tmp_path)
    assert seen["threads"] is None


def test_the_setting_reads_the_env_and_defaults_to_the_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert Settings().embedding_threads == 0
    monkeypatch.setenv("TICKETSCOPE_EMBEDDING_THREADS", "1")
    assert Settings().embedding_threads == 1
    monkeypatch.setenv("TICKETSCOPE_EMBEDDING_THREADS", "-1")
    with pytest.raises(ValidationError):
        Settings()


def test_api_builds_its_embedder_with_the_configured_threads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    built: list[int | None] = []

    class Spy(HashEmbedder):
        def __init__(self, model_id: str, cache_dir: Path, threads: int | None = None) -> None:
            super().__init__(model_id)
            built.append(threads)

    monkeypatch.setattr("ticketscope.http.app.FastEmbedEmbedder", Spy)
    settings = Settings(embedding_model_id=MODEL, embedding_cache_dir=tmp_path, embedding_threads=1)
    create_app(store=InMemoryCorpusStore(), settings=settings)
    assert built == [1]


@needs_helm
def test_the_chart_sets_api_threads_equal_to_its_cpu_limit() -> None:
    [api] = [
        d
        for d in yaml.safe_load_all(_render(*_NO_PIN))
        if d and d.get("kind") == "Deployment" and d["metadata"]["name"] == "ticketscope-api"
    ]
    container = api["spec"]["template"]["spec"]["containers"][0]
    env = {e["name"]: e.get("value") for e in container["env"]}
    limit = str(container["resources"]["limits"]["cpu"])
    assert env["TICKETSCOPE_EMBEDDING_THREADS"] == "1"
    assert env["TICKETSCOPE_EMBEDDING_THREADS"] == limit  # one value, kept in step


@needs_helm
def test_only_api_is_capped() -> None:
    rendered = _render(*_NO_PIN, "--set", "eval.enabled=true")
    assert "TICKETSCOPE_EMBEDDING_THREADS" in _doc(rendered, "ticketscope-api")
    assert "TICKETSCOPE_EMBEDDING_THREADS" not in _doc(rendered, "ticketscope-eval")
