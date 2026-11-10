"""The eval Job stays untraced (story 3.1 AC-4; epic 3 retro, G1).

AC-4: "`/readyz` and eval stay untraced". `test_scoring_runs_with_instrumentation_suppressed`
shows suppression inside `run`; this runs the Job's whole entry point, scoring keyword, dense
and hybrid with an embedder, and reads what the process actually exports: the one `eval` jobs
span, and no retrieval, embeddings or database span from the ~10,000 searches inside it.
"""

from pathlib import Path

import pytest
from opentelemetry.instrumentation.utils import is_instrumentation_enabled
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind

from tests.unit.test_eval_main import META, PAIR, _embedded_store
from ticketscope import telemetry
from ticketscope.core.fakes import HashEmbedder
from ticketscope.core.pairs import Pair, pairs_jsonl
from ticketscope.jobs.eval import main as eval_main


@pytest.mark.criterion("ticketscope--e3-s1--AC-4")
def test_the_eval_job_exports_only_its_jobs_span(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    exporter = InMemorySpanExporter()
    real = telemetry.tracer_provider
    # The Job's provider: telemetry.setup instruments psycopg against it, so the fake
    # instrumentation below reports to it too (the unit conftest keeps the global unset).
    providers: list[TracerProvider] = []

    def with_memory(service_name: str, otlp_endpoint: str) -> TracerProvider:
        provider = real(service_name, otlp_endpoint)
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        providers.append(provider)
        return provider

    inner = _embedded_store()
    model = inner.embedding_model_id()
    assert model is not None

    class InstrumentedStore:
        """Emits a CLIENT `db query` span per call, as psycopg's instrumentation does, and
        honours suppression the same way: this is what an untraced eval must silence."""

        def __getattr__(self, name: str) -> object:
            method = getattr(inner, name)

            def call(*args: object, **kwargs: object) -> object:
                if not is_instrumentation_enabled():
                    return method(*args, **kwargs)
                [provider] = providers
                tracer = provider.get_tracer("psycopg-like")
                with tracer.start_as_current_span("db query", kind=SpanKind.CLIENT):
                    return method(*args, **kwargs)

            return call

    store = InstrumentedStore()
    meta = META.__class__(META.snapshot_version, model, META.preprocessing_version)
    (tmp_path / f"{meta.snapshot_version}.jsonl").write_bytes(
        pairs_jsonl([PAIR, Pair(3, 1, "short", (1,))])
    )
    monkeypatch.setattr(telemetry, "tracer_provider", with_memory)
    monkeypatch.setattr(telemetry, "instrument_psycopg", lambda provider: None)
    monkeypatch.setattr(eval_main, "read_corpus_meta", lambda conninfo: meta)
    monkeypatch.setattr(eval_main, "PostgresCorpusStore", lambda conninfo: store)
    monkeypatch.setattr(eval_main, "build_embedder", lambda settings: HashEmbedder(model))
    monkeypatch.setenv("TICKETSCOPE_EVAL_PAIRS_DIR", str(tmp_path))

    assert eval_main.main() == 0

    spans = exporter.get_finished_spans()
    assert [(s.name, s.kind) for s in spans] == [("eval", SpanKind.INTERNAL)], [
        s.name for s in spans
    ]
    assert spans[0].resource.attributes["service.name"] == "ticketscope-jobs"
