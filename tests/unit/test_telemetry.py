"""The span contract (AD-10) and JSON logs, on an in-memory exporter (story 9's I/O matrix)."""

import json
import logging
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanContext, SpanKind, StatusCode

from tests.target import TARGET_QUERY
from ticketscope import telemetry
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueDetail, Scored
from ticketscope.http.app import PAGE_K, create_app
from ticketscope.jobs.load import main as load
from ticketscope.jobs.migrate import main as migrate
from ticketscope.settings import Settings

SECRET = "secretword"
AD10_ATTRIBUTES = {
    "gen_ai.operation.name",
    "gen_ai.data_source.id",
    "ticketscope.retrieval.mode",
    "ticketscope.retrieval.k",
    "ticketscope.corpus.version",
    "ticketscope.result.count",
}


@pytest.fixture
def exporter() -> InMemorySpanExporter:
    return InMemorySpanExporter()


@pytest.fixture
def provider(exporter: InMemorySpanExporter) -> Iterator[TracerProvider]:
    provider = telemetry.tracer_provider(telemetry.SERVICE_API, "")
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    yield provider
    provider.shutdown()


def _client(
    store: object, provider: TracerProvider, *, trace_query_text: bool = False
) -> TestClient:
    settings = Settings(default_mode="keyword", trace_query_text=trace_query_text)
    app = create_app(store=store, settings=settings, tracer_provider=provider)  # pyright: ignore[reportArgumentType]
    return TestClient(app, raise_server_exceptions=False)


def _named(spans: tuple[ReadableSpan, ...], name: str) -> ReadableSpan:
    [span] = [s for s in spans if s.name == name]
    return span


def _ctx(span: ReadableSpan) -> SpanContext:
    assert span.context is not None
    return span.context


def _server(spans: tuple[ReadableSpan, ...]) -> ReadableSpan:
    [span] = [s for s in spans if s.kind == SpanKind.SERVER]
    return span


def _all_attribute_values(spans: tuple[ReadableSpan, ...]) -> list[str]:
    values: list[str] = [s.name for s in spans]
    for span in spans:
        values.extend(str(v) for v in (span.attributes or {}).values())
        for event in span.events:
            values.extend(str(v) for v in (event.attributes or {}).values())
    return values


# --- search and page -----------------------------------------------------------------------


def test_search_is_a_server_span_over_a_retrieval_span(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    response = _client(fixture_store, provider).post(
        "/v1/search", json={"query": TARGET_QUERY, "mode": "keyword", "k": 5}
    )
    assert response.status_code == 200
    results = response.json()["results"]
    spans = exporter.get_finished_spans()
    server = _server(spans)
    assert server.name == "POST /v1/search"
    retrieval = _named(spans, "retrieval keyword")
    assert retrieval.kind == SpanKind.INTERNAL
    assert retrieval.parent is not None
    assert retrieval.parent.span_id == _ctx(server).span_id
    assert _ctx(retrieval).trace_id == _ctx(server).trace_id
    attributes = dict(retrieval.attributes or {})
    assert set(attributes) >= AD10_ATTRIBUTES
    assert attributes["gen_ai.operation.name"] == "retrieval"
    assert attributes["gen_ai.data_source.id"] == "ticketscope-mojang-jira"
    assert attributes["ticketscope.retrieval.mode"] == "keyword"
    assert attributes["ticketscope.retrieval.k"] == 5
    assert attributes["ticketscope.corpus.version"] == "fixture"
    assert attributes["ticketscope.result.count"] == len(results)
    assert "ticketscope.query.text" not in attributes
    assert retrieval.resource.attributes["service.name"] == "ticketscope-api"
    # Only the SERVER and retrieval spans: ASGI receive/send sub-spans are excluded.
    assert {s.name for s in spans} == {"POST /v1/search", "retrieval keyword"}


def test_page_post_is_traced_with_k_10(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    response = _client(fixture_store, provider).post(
        "/",
        content=urlencode({"q": TARGET_QUERY}),
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    spans = exporter.get_finished_spans()
    server = _server(spans)
    retrieval = _named(spans, "retrieval keyword")
    assert retrieval.parent is not None
    assert retrieval.parent.span_id == _ctx(server).span_id
    assert (retrieval.attributes or {})["ticketscope.retrieval.k"] == PAGE_K == 10


def test_no_query_text_on_any_span_by_default(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(fixture_store, provider)
    assert client.post("/v1/search", json={"query": SECRET}).status_code == 200
    assert client.get("/", params={"q": SECRET}).status_code == 200
    spans = exporter.get_finished_spans()
    assert len([s for s in spans if s.kind == SpanKind.SERVER]) == 2
    assert not [v for v in _all_attribute_values(spans) if SECRET in v]
    get_server = _named(spans, "GET /")
    assert (get_server.attributes or {})["url.query"] == telemetry.REDACTED


def test_query_text_is_recorded_when_opted_in(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(fixture_store, provider, trace_query_text=True)
    assert client.post("/v1/search", json={"query": SECRET}).status_code == 200
    retrieval = _named(exporter.get_finished_spans(), "retrieval keyword")
    assert (retrieval.attributes or {})["ticketscope.query.text"] == SECRET


class _SearchBrokenStore:
    """Loaded, but the search itself fails (the `_BrokenStore` row past the version check)."""

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        raise ConnectionError("database down")

    def get_issue(self, number: int) -> IssueDetail | None:
        raise ConnectionError("database down")

    def corpus_version(self) -> str | None:
        return "fixture"


def _assert_error_retrieval(exporter: InMemorySpanExporter) -> None:
    retrieval = _named(exporter.get_finished_spans(), "retrieval keyword")
    assert retrieval.status.status_code == StatusCode.ERROR
    assert [e.name for e in retrieval.events] == ["exception"]


def test_store_failure_sets_error_and_keeps_the_problem_response(
    provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    response = _client(_SearchBrokenStore(), provider).post(
        "/v1/search", json={"query": TARGET_QUERY}
    )
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "database down" not in response.json()["detail"]
    _assert_error_retrieval(exporter)


def test_store_failure_on_the_page_sets_error_and_keeps_the_html_500(
    provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    response = _client(_SearchBrokenStore(), provider).get("/", params={"q": TARGET_QUERY})
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("text/html")
    _assert_error_retrieval(exporter)


def test_probes_are_not_traced(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(fixture_store, provider)
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 200
    assert exporter.get_finished_spans() == ()
    # A search for the probe's name is still traced: exclusion matches the path only.
    assert client.get("/", params={"q": "healthz"}).status_code == 200
    assert exporter.get_finished_spans()


class _RecordingStore(InMemoryCorpusStore):
    """Records whether instrumentation was enabled during each `corpus_version()`."""

    def __init__(self) -> None:
        super().__init__([], corpus_version="fixture")
        self.enabled: list[bool] = []

    def corpus_version(self) -> str | None:
        from opentelemetry.instrumentation.utils import is_instrumentation_enabled

        self.enabled.append(is_instrumentation_enabled())
        return super().corpus_version()


def test_readyz_db_work_is_untraced(provider: TracerProvider) -> None:
    store = _RecordingStore()
    assert _client(store, provider).get("/readyz").status_code == 200
    assert store.enabled == [False]


# --- logs ----------------------------------------------------------------------------------


def _record(message: str, exc: bool = False) -> logging.LogRecord:
    exc_info = None
    if exc:
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()
    return logging.LogRecord("ticketscope.test", logging.INFO, __file__, 1, message, (), exc_info)


def test_log_line_inside_a_span_carries_its_ids(provider: TracerProvider) -> None:
    formatter = telemetry.JsonFormatter()
    with telemetry.get_tracer(provider).start_as_current_span("work") as span:
        line = json.loads(formatter.format(_record("load report: snapshot=x")))
    context = span.get_span_context()
    assert line["trace_id"] == format(context.trace_id, "032x")
    assert line["span_id"] == format(context.span_id, "016x")
    assert len(line["trace_id"]) == 32 and len(line["span_id"]) == 16
    assert line["message"] == "load report: snapshot=x"
    assert line["level"] == "INFO"
    assert line["logger"] == "ticketscope.test"
    assert line["ts"].endswith("+00:00")
    assert "exception" not in line


def test_log_line_outside_a_span_has_null_ids_and_the_exception() -> None:
    line = json.loads(telemetry.JsonFormatter().format(_record("failed", exc=True)))
    assert line["trace_id"] is None and line["span_id"] is None
    assert "ValueError: boom" in line["exception"]


def test_configure_logging_leaves_an_existing_root_handler_alone() -> None:
    root = logging.getLogger()
    before = list(root.handlers)
    assert before  # pytest's capture handler
    telemetry.configure_logging()
    assert root.handlers == before


def test_configure_logging_installs_json_on_a_bare_root(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = logging.getLogger()
    monkeypatch.setattr(root, "handlers", [])
    monkeypatch.setattr(root, "level", logging.WARNING)
    telemetry.configure_logging()
    [handler] = root.handlers
    assert isinstance(handler.formatter, telemetry.JsonFormatter)
    logging.getLogger("ticketscope.test").info("no-op: hello")
    assert json.loads(capsys.readouterr().out.strip())["message"] == "no-op: hello"


# --- setup and jobs ------------------------------------------------------------------------


def test_setup_sets_the_opt_in_and_creates_no_exporter_without_an_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(telemetry.SEMCONV_OPT_IN_VAR, raising=False)
    monkeypatch.setattr(telemetry, "instrument_psycopg", lambda provider: None)
    provider = telemetry.setup(telemetry.SERVICE_JOBS, "")
    try:
        assert os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] == (
            "gen_ai_latest_experimental,database,http"
        )
        assert provider.resource.attributes["service.name"] == "ticketscope-jobs"
        assert provider._active_span_processor._span_processors == ()  # pyright: ignore[reportPrivateUsage]
    finally:
        provider.shutdown()


def test_an_endpoint_adds_one_batch_exporter_to_the_collector() -> None:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = telemetry.tracer_provider(
        telemetry.SERVICE_API, "http://otel-collector.platform.svc:4318/"
    )
    try:
        [processor] = provider._active_span_processor._span_processors  # pyright: ignore[reportPrivateUsage]
        assert isinstance(processor, BatchSpanProcessor)
        span_exporter = processor._batch_processor._exporter  # pyright: ignore[reportPrivateUsage, reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        assert isinstance(span_exporter, OTLPSpanExporter)
        assert span_exporter._endpoint == "http://otel-collector.platform.svc:4318/v1/traces"  # pyright: ignore[reportPrivateUsage]
    finally:
        provider.shutdown()


@pytest.fixture
def jobs_exporter(monkeypatch: pytest.MonkeyPatch) -> InMemorySpanExporter:
    """Spans of a job `main`, on its own provider (built by the real `tracer_provider`)."""
    exporter = InMemorySpanExporter()
    real = telemetry.tracer_provider

    def with_memory(service_name: str, otlp_endpoint: str) -> TracerProvider:
        provider = real(service_name, otlp_endpoint)
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        return provider

    monkeypatch.setattr(telemetry, "tracer_provider", with_memory)
    monkeypatch.setattr(telemetry, "instrument_psycopg", lambda provider: None)
    return exporter


def test_load_main_emits_one_jobs_span(
    jobs_exporter: InMemorySpanExporter,
    monkeypatch: pytest.MonkeyPatch,
    snapshot_dir: Path,
    fixture_sha256: str,
) -> None:
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_DIR", str(snapshot_dir))
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_VERSION", "fixture")
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", fixture_sha256)
    monkeypatch.setattr(load, "wait_for_database", lambda conninfo, *, role, timeout_s: None)
    monkeypatch.setattr(load, "read_corpus_meta", lambda conninfo: None)
    monkeypatch.setattr(load, "replace_corpus", lambda conninfo, meta, rows: len(list(rows)))
    assert load.main() == 0
    [span] = jobs_exporter.get_finished_spans()
    assert (span.name, span.kind) == ("load", SpanKind.INTERNAL)
    assert span.resource.attributes["service.name"] == "ticketscope-jobs"
    assert span.status.status_code != StatusCode.ERROR


def test_failed_migrate_main_sets_error_on_its_jobs_span(
    jobs_exporter: InMemorySpanExporter, monkeypatch: pytest.MonkeyPatch
) -> None:
    def down(conninfo: str, *, role: str | None, timeout_s: float) -> None:
        raise ConnectionError("database down")

    monkeypatch.setattr(migrate, "wait_for_database", down)
    assert migrate.main() == 1
    [span] = jobs_exporter.get_finished_spans()
    assert span.name == "migrate"
    assert span.resource.attributes["service.name"] == "ticketscope-jobs"
    assert span.status.status_code == StatusCode.ERROR
