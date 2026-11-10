"""Story 3.1 expand coverage: embedder adapters, retriever guards, startup wiring, kind-up flag."""

import os
import stat
import subprocess
import sys
import types
from collections.abc import Sequence
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from tests.factories import search_payload
from ticketscope import telemetry
from ticketscope.adapters import embedder as embedder_mod
from ticketscope.adapters.embedder import FastEmbedEmbedder, TracedEmbedder
from ticketscope.core.fakes import HashEmbedder, InMemoryCorpusStore
from ticketscope.core.model import IssueRecord
from ticketscope.core.modes import REGISTRY, DenseRetriever
from ticketscope.http.app import create_app
from ticketscope.jobs.load import main as load
from ticketscope.settings import Settings

REPO = Path(__file__).resolve().parents[2]
MODEL = "hash-fake"


class _Vec:
    def __init__(self, values: list[float]) -> None:
        self._values = values

    def tolist(self) -> list[float]:
        return self._values


def _store() -> InMemoryCorpusStore:
    issue = IssueRecord(number=1, title="t", url="u", kind="short", state="closed")
    vector = HashEmbedder(MODEL).embed(["crash"])[0]
    return InMemoryCorpusStore(
        [(issue, "crash")],
        corpus_version="v",
        embeddings={MODEL: {1: vector}},
        embedding_model=MODEL,
    )


# --- FastEmbedEmbedder, with fastembed stubbed (no model, no onnxruntime) -------------------


def test_fastembed_embedder_loads_from_the_cache_and_converts_vectors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: dict[str, object] = {}

    class FakeTextEmbedding:
        def __init__(self, **kwargs: object) -> None:
            seen.update(kwargs)

        def embed(self, documents: Sequence[str]) -> list[_Vec]:
            seen["documents"] = list(documents)
            return [_Vec([1.0, 0.0]) for _ in documents]

    monkeypatch.setitem(
        sys.modules, "fastembed", types.SimpleNamespace(TextEmbedding=FakeTextEmbedding)
    )
    adapter = FastEmbedEmbedder("some/model", tmp_path)
    assert adapter.model_id == "some/model"
    assert seen["model_name"] == "some/model"
    assert seen["cache_dir"] == str(tmp_path)
    assert adapter.embed(["a", "b"]) == [[1.0, 0.0], [1.0, 0.0]]
    assert seen["documents"] == ["a", "b"]


def test_embedder_module_does_not_import_fastembed_at_import_time() -> None:
    code = "import sys; import ticketscope.adapters.embedder; print('fastembed' in sys.modules)"
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, cwd=REPO
    )
    assert out.stdout.strip() == "False"


# --- TracedEmbedder --------------------------------------------------------------------------


def test_traced_embedder_passes_through_model_id_and_vectors() -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    inner = HashEmbedder("m1")
    traced = TracedEmbedder(inner, telemetry.get_tracer(provider))
    assert traced.model_id == "m1"
    assert traced.embed(["x y"]) == inner.embed(["x y"])
    spans = [s for s in exporter.get_finished_spans() if s.name == "embeddings m1"]
    assert len(spans) == 1
    assert spans[0].attributes is not None
    assert spans[0].attributes["gen_ai.request.model"] == "m1"
    assert spans[0].attributes["gen_ai.operation.name"] == "embeddings"


# --- DenseRetriever / registry guards -------------------------------------------------------


@pytest.mark.parametrize("k", [0, -3])
def test_dense_retriever_with_nonpositive_k_returns_nothing_and_does_not_embed(k: int) -> None:
    embedder = HashEmbedder(MODEL)
    assert DenseRetriever(_store(), embedder).search("crash", k) == []
    assert embedder.calls == []


def test_building_dense_without_an_embedder_is_refused() -> None:
    with pytest.raises(ValueError, match="needs an embedder"):
        REGISTRY["dense"].build(_store(), None)


def test_dense_is_unavailable_without_an_embedder() -> None:
    assert REGISTRY["dense"].available(_store(), None) is False
    assert REGISTRY["keyword"].available(_store(), None) is True


def test_dense_is_unavailable_when_the_store_holds_another_models_rows() -> None:
    assert REGISTRY["dense"].available(_store(), HashEmbedder("other")) is False


# --- load guards -----------------------------------------------------------------------------


def test_embedding_rows_rejects_a_short_embedder_reply(snapshot_dir: Path) -> None:
    class Short:
        model_id = MODEL

        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            return [[1.0]] * (len(texts) - 1)

    issues = load.read_snapshot(snapshot_dir / "fixture.jsonl.gz")
    with pytest.raises(ValueError, match="vectors for"):
        list(load.embedding_rows(issues, Short(), load.EmbeddingStats()))


def test_report_line_mentions_embeddings_only_when_computed() -> None:
    from collections import Counter

    plain = load.report_line("v", 0, Counter(), 1.0, 600)
    assert "embeddings=" not in plain
    stats = load.EmbeddingStats(count=5, seconds=2.0)
    assert " embeddings=5 embedding_seconds=2.0" in load.report_line(
        "v", 0, Counter(), 1.0, 600, stats
    )


# --- app startup wiring ---------------------------------------------------------------------


def test_startup_loads_the_baked_model_when_a_model_id_is_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    built: list[tuple[str, Path, int | None]] = []

    class Spy(HashEmbedder):
        def __init__(self, model_id: str, cache_dir: Path, threads: int | None = None) -> None:
            super().__init__(model_id)
            built.append((model_id, cache_dir, threads))

    monkeypatch.setattr("ticketscope.http.app.FastEmbedEmbedder", Spy)
    settings = Settings(embedding_model_id=MODEL, embedding_cache_dir=tmp_path)
    client = TestClient(create_app(store=_store(), settings=settings))
    assert built == [(MODEL, tmp_path, None)]  # no thread setting: the runtime's default
    assert (
        client.post("/v1/search", json=search_payload(query="crash", mode="dense")).status_code
        == 200
    )


def test_startup_fails_fast_when_the_model_cannot_load(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(model_id: str, cache_dir: Path, threads: int | None = None) -> None:
        raise RuntimeError("model missing")

    monkeypatch.setattr("ticketscope.http.app.FastEmbedEmbedder", boom)
    with pytest.raises(RuntimeError, match="model missing"):
        create_app(store=_store(), settings=Settings(embedding_model_id=MODEL))


def test_no_model_id_never_touches_fastembed(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a: object, **_k: object) -> None:
        raise AssertionError("must not load a model")

    monkeypatch.setattr("ticketscope.http.app.FastEmbedEmbedder", boom)
    client = TestClient(create_app(store=_store(), settings=Settings()))
    res = client.post("/v1/search", json=search_payload(query="crash", mode="dense"))
    assert res.status_code == 503


# --- kind-up.sh flag -------------------------------------------------------------------------


def _run_kind_up(tmp_path: Path, extra: dict[str, str]) -> list[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    log = tmp_path / "calls.log"
    log.write_text("", "utf-8")
    bodies = {
        "docker": 'case "$1" in image) exit 0;; inspect) echo true;; esac; exit 0',
        "kind": '[[ "$1" == get ]] && echo ticketscope; exit 0',
        "kubectl": '[[ "$*" == *"get gateway/"* ]] && printf 10.0.0.1; exit 0',
        "helm": "exit 0",
        "git": "echo unused-sha",
        "uname": "echo Linux",
    }
    for name, body in bodies.items():
        stub = bin_dir / name
        stub.write_text(f'#!/usr/bin/env bash\necho "{name} $*" >> "$STUB_LOG"\n{body}\n', "utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    env = {
        "PATH": f"{bin_dir}{os.pathsep}/usr/bin:/bin",
        "HOME": str(tmp_path),
        "TAG": "t",
        "STUB_LOG": str(log),
        **extra,
    }
    proc = subprocess.run(
        ["bash", str(REPO / "scripts" / "kind-up.sh")],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return log.read_text("utf-8").splitlines()


def test_kind_up_sets_compute_on_kind_only_when_asked(tmp_path: Path) -> None:
    off = _run_kind_up(tmp_path / "off", {})
    assert not any("embeddings.computeOnKind" in c for c in off)
    on = _run_kind_up(tmp_path / "on", {"EMBEDDINGS_COMPUTE": "1"})
    upgrade = [c for c in on if c.startswith("helm ") and "upgrade --install ticketscope " in c]
    assert len(upgrade) == 1
    assert "--set embeddings.computeOnKind=true" in upgrade[0]
    assert "--timeout 50m" in upgrade[0]


def test_settings_defaults_keep_embeddings_off() -> None:
    s = Settings()
    assert s.embedding_model_id == ""
    assert s.embeddings_compute is False
    assert embedder_mod is not None
