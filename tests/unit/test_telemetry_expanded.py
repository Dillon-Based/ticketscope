"""Story 9 expanded coverage: edges of the span contract (AD-10), JSON logs inside a request,
trace-context propagation, the jobs' flush/error paths, and the layer rule for `telemetry`."""

import ast
import json
import logging
import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from opentelemetry.instrumentation.utils import is_instrumentation_enabled
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode

from tests.target import TARGET_QUERY
from ticketscope import telemetry
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueDetail, Scored
from ticketscope.http import app as app_module
from ticketscope.http.app import create_app
from ticketscope.jobs.load import main as load
from ticketscope.jobs.migrate import main as migrate
from ticketscope.settings import Settings

SECRET = "secretword"
TELEMETRY_PY = Path(telemetry.__file__)
SRC = TELEMETRY_PY.parent.parent


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


def _server(spans: tuple[ReadableSpan, ...]) -> ReadableSpan:
    [span] = [s for s in spans if s.kind == SpanKind.SERVER]
    return span


def _retrievals(spans: tuple[ReadableSpan, ...]) -> list[ReadableSpan]:
    return [s for s in spans if s.name.startswith("retrieval ")]


class _SearchBrokenStore:
    """Loaded, but the search itself fails."""

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        raise ConnectionError("database down")

    def get_issue(self, number: int) -> IssueDetail | None:
        raise ConnectionError("database down")

    def corpus_version(self) -> str | None:
        return "fixture"


# --- trace context -------------------------------------------------------------------------


def test_incoming_traceparent_is_continued_by_the_server_span(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    # The smoke test (8) relies on this: a caller-chosen trace id is the one Tempo stores.
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    parent_id = "00f067aa0ba902b7"
    response = _client(fixture_store, provider).post(
        "/v1/search",
        json={"query": TARGET_QUERY, "mode": "keyword"},
        headers={"traceparent": f"00-{trace_id}-{parent_id}-01"},
    )
    assert response.status_code == 200
    spans = exporter.get_finished_spans()
    server = _server(spans)
    assert server.context is not None
    assert format(server.context.trace_id, "032x") == trace_id
    assert server.parent is not None
    assert format(server.parent.span_id, "016x") == parent_id
    assert server.parent.is_remote
    [retrieval] = _retrievals(spans)
    assert retrieval.context is not None
    assert format(retrieval.context.trace_id, "032x") == trace_id


def test_each_request_without_traceparent_is_its_own_trace(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(fixture_store, provider)
    for _ in range(2):
        assert client.post("/v1/search", json={"query": TARGET_QUERY}).status_code == 200
    servers = [s for s in exporter.get_finished_spans() if s.kind == SpanKind.SERVER]
    assert len(servers) == 2
    assert all(s.parent is None for s in servers)
    assert len({s.context.trace_id for s in servers if s.context}) == 2


# --- retrieval span edges ------------------------------------------------------------------


def test_zero_results_reports_a_count_of_zero(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    response = _client(fixture_store, provider).post(
        "/v1/search", json={"query": "zzqxjvnomatchtoken", "mode": "keyword"}
    )
    assert response.status_code == 200
    assert response.json()["results"] == []
    [retrieval] = _retrievals(exporter.get_finished_spans())
    assert (retrieval.attributes or {})["ticketscope.result.count"] == 0
    assert retrieval.status.status_code != StatusCode.ERROR


def test_no_retrieval_span_when_the_corpus_is_not_loaded(
    provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    empty = InMemoryCorpusStore([], corpus_version=None)
    client = _client(empty, provider)
    assert client.post("/v1/search", json={"query": TARGET_QUERY}).status_code == 503
    assert client.get("/", params={"q": TARGET_QUERY}).status_code == 503
    spans = exporter.get_finished_spans()
    assert len([s for s in spans if s.kind == SpanKind.SERVER]) == 2
    assert _retrievals(spans) == []


def test_no_retrieval_span_for_a_blank_page_query_or_an_invalid_request(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(fixture_store, provider)
    assert client.get("/", params={"q": "   "}).status_code == 200
    assert client.post("/v1/search", json={"query": TARGET_QUERY, "k": 0}).status_code == 422
    assert client.post("/v1/search", json={"query": TARGET_QUERY, "mode": "x"}).status_code == 422
    assert _retrievals(exporter.get_finished_spans()) == []


def test_issue_detail_is_traced_without_a_retrieval_span(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    response = _client(fixture_store, provider).post(
        "/v1/search", json={"query": TARGET_QUERY, "k": 1}
    )
    number = response.json()["results"][0]["issue"]["number"]
    exporter.clear()
    client = _client(fixture_store, provider)
    assert client.get(f"/v1/issues/{number}").status_code == 200
    spans = exporter.get_finished_spans()
    assert _server(spans).name == "GET /v1/issues/{number}"
    assert _retrievals(spans) == []


def test_retrieval_span_error_recording_and_propagation(
    provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    tracer = telemetry.get_tracer(provider)
    with (
        pytest.raises(ConnectionError, match="database down"),
        telemetry.retrieval_span(
            tracer, mode="keyword", k=3, corpus_version="v1", query=SECRET, record_query_text=False
        ),
    ):
        raise ConnectionError("database down")
    [span] = exporter.get_finished_spans()
    assert span.name == "retrieval keyword"
    assert span.kind == SpanKind.INTERNAL
    assert span.status.status_code == StatusCode.ERROR
    [event] = span.events
    assert event.name == "exception"
    assert (event.attributes or {})["exception.type"] == "ConnectionError"
    attributes = dict(span.attributes or {})
    # No count was reported, and the query stays off the span.
    assert "ticketscope.result.count" not in attributes
    assert SECRET not in json.dumps({k: str(v) for k, v in attributes.items()})


def test_only_ticketscope_and_gen_ai_attributes_on_the_retrieval_span(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(fixture_store, provider, trace_query_text=True)
    assert client.post("/v1/search", json={"query": TARGET_QUERY}).status_code == 200
    [retrieval] = _retrievals(exporter.get_finished_spans())
    for key in retrieval.attributes or {}:
        assert key.startswith(("ticketscope.", "gen_ai.")), key


def test_opt_in_query_text_is_also_on_the_page_retrieval_span(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    response = _client(fixture_store, provider, trace_query_text=True).post(
        "/",
        content=urlencode({"q": SECRET}),
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    [retrieval] = _retrievals(exporter.get_finished_spans())
    assert (retrieval.attributes or {})["ticketscope.query.text"] == SECRET


# --- SERVER span url.query -----------------------------------------------------------------


def test_url_query_is_kept_when_query_text_is_opted_in(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(fixture_store, provider, trace_query_text=True)
    assert client.get("/", params={"q": SECRET}).status_code == 200
    server = _server(exporter.get_finished_spans())
    assert (server.attributes or {}).get("url.query") == f"q={SECRET}"


def test_no_url_query_attribute_without_a_query_string(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    assert _client(fixture_store, provider).get("/").status_code == 200
    server = _server(exporter.get_finished_spans())
    assert "url.query" not in (server.attributes or {})


def test_url_query_redacted_on_v1_search_too(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(fixture_store, provider)
    response = client.post(f"/v1/search?debug={SECRET}", json={"query": TARGET_QUERY})
    assert response.status_code == 200
    server = _server(exporter.get_finished_spans())
    assert (server.attributes or {})["url.query"] == telemetry.REDACTED


def test_server_span_uses_stable_http_semconv(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    assert (
        _client(fixture_store, provider)
        .post("/v1/search", json={"query": TARGET_QUERY})
        .status_code
        == 200
    )
    attributes = dict(_server(exporter.get_finished_spans()).attributes or {})
    assert attributes["http.request.method"] == "POST"
    assert attributes["http.response.status_code"] == 200
    assert attributes["http.route"] == "/v1/search"
    # Old (pre-stable) names are not duplicated: the opt-in is `http`, not `http/dup`.
    assert "http.method" not in attributes and "http.status_code" not in attributes


# --- probes --------------------------------------------------------------------------------


def test_probes_with_a_query_string_are_not_traced(
    fixture_store: InMemoryCorpusStore, provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(fixture_store, provider)
    assert client.get("/healthz", params={"x": "1"}).status_code == 200
    assert client.get("/readyz", params={"x": "1"}).status_code == 200
    assert exporter.get_finished_spans() == ()


def test_readyz_when_not_ready_is_still_untraced(
    provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(InMemoryCorpusStore([], corpus_version=None), provider)
    assert client.get("/readyz").status_code == 503
    assert exporter.get_finished_spans() == ()


def test_untraced_disables_instrumentation_and_restores_it() -> None:
    assert is_instrumentation_enabled()
    with telemetry.untraced():
        assert not is_instrumentation_enabled()
    assert is_instrumentation_enabled()
    with pytest.raises(RuntimeError), telemetry.untraced():
        raise RuntimeError("probe failed")
    assert is_instrumentation_enabled()


# --- logs ----------------------------------------------------------------------------------


class _JsonLines(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.setFormatter(telemetry.JsonFormatter())
        self.lines: list[dict[str, Any]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(json.loads(self.format(record)))


@pytest.fixture
def json_lines() -> Iterator[_JsonLines]:
    handler = _JsonLines()
    root = logging.getLogger()
    root.addHandler(handler)
    yield handler
    root.removeHandler(handler)


def test_a_log_line_during_a_request_carries_the_request_trace(
    provider: TracerProvider, exporter: InMemorySpanExporter, json_lines: _JsonLines
) -> None:
    response = _client(_SearchBrokenStore(), provider).get("/", params={"q": TARGET_QUERY})
    assert response.status_code == 500
    [line] = [x for x in json_lines.lines if x["message"] == "search page failed"]
    server = _server(exporter.get_finished_spans())
    assert server.context is not None
    assert line["trace_id"] == format(server.context.trace_id, "032x")
    assert line["span_id"] == format(server.context.span_id, "016x")
    assert line["level"] == "ERROR"
    assert line["logger"] == "ticketscope.http.app"
    assert "ConnectionError: database down" in line["exception"]
    # Logs may name the failure; the query text stays out of the log line.
    assert TARGET_QUERY not in json.dumps(line)


def test_json_formatter_formats_args_and_keeps_non_ascii() -> None:
    record = logging.LogRecord(
        "ticketscope.load",
        logging.WARNING,
        __file__,
        1,
        "load report: %s rows, %d%%",
        ("é→✓", 5),
        None,
    )
    raw = telemetry.JsonFormatter().format(record)
    assert "\n" not in raw
    assert "é→✓" in raw  # not \u-escaped
    line = json.loads(raw)
    assert line["message"] == "load report: é→✓ rows, 5%"
    assert line["level"] == "WARNING"
    assert set(line) == {"ts", "level", "logger", "message", "trace_id", "span_id"}


def test_json_formatter_uses_exc_text_when_no_exc_info() -> None:
    record = logging.LogRecord("x", logging.ERROR, __file__, 1, "failed", (), None)
    record.exc_text = "Traceback: precomputed"
    line = json.loads(telemetry.JsonFormatter().format(record))
    assert line["exception"] == "Traceback: precomputed"


def test_json_formatter_multiline_exception_is_still_one_line() -> None:
    try:
        raise ValueError("line one\nline two")
    except ValueError:
        exc_info = sys.exc_info()
    record = logging.LogRecord("x", logging.ERROR, __file__, 1, "multi\nline", (), exc_info)
    raw = telemetry.JsonFormatter().format(record)
    assert "\n" not in raw
    line = json.loads(raw)
    assert line["message"] == "multi\nline"
    assert "line two" in line["exception"]


# --- providers and instrumentation ---------------------------------------------------------


@pytest.mark.parametrize("endpoint", ["", "   ", "/", " / "])
def test_blank_endpoints_create_no_exporter(endpoint: str) -> None:
    provider = telemetry.tracer_provider(telemetry.SERVICE_API, endpoint)
    try:
        assert provider._active_span_processor._span_processors == ()  # pyright: ignore[reportPrivateUsage]
    finally:
        provider.shutdown()


def test_endpoint_is_stripped_before_v1_traces_is_appended() -> None:
    provider = telemetry.tracer_provider(telemetry.SERVICE_JOBS, "  http://collector:4318//  ")
    try:
        [processor] = provider._active_span_processor._span_processors  # pyright: ignore[reportPrivateUsage]
        span_exporter = processor._batch_processor._exporter  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        assert span_exporter._endpoint == "http://collector:4318/v1/traces"  # pyright: ignore[reportUnknownMemberType]
    finally:
        provider.shutdown()


class _FakePsycopgInstrumentor:
    instrumented = False
    calls: ClassVar[list[dict[str, Any]]] = []

    @property
    def is_instrumented_by_opentelemetry(self) -> bool:
        return type(self).instrumented

    def instrument(self, **kwargs: Any) -> None:
        type(self).calls.append(kwargs)
        type(self).instrumented = True


def test_psycopg_is_instrumented_once_without_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    import opentelemetry.instrumentation.psycopg as psycopg_instrumentation

    _FakePsycopgInstrumentor.instrumented = False
    _FakePsycopgInstrumentor.calls = []
    monkeypatch.setattr(psycopg_instrumentation, "PsycopgInstrumentor", _FakePsycopgInstrumentor)
    provider = TracerProvider()
    telemetry.instrument_psycopg(provider)
    telemetry.instrument_psycopg(provider)
    [kwargs] = _FakePsycopgInstrumentor.calls
    assert kwargs["tracer_provider"] is provider
    assert kwargs["capture_parameters"] is False
    assert kwargs["enable_commenter"] is False


def test_create_app_sets_the_semconv_opt_in(
    monkeypatch: pytest.MonkeyPatch, fixture_store: InMemoryCorpusStore, provider: TracerProvider
) -> None:
    monkeypatch.delenv(telemetry.SEMCONV_OPT_IN_VAR, raising=False)
    _client(fixture_store, provider)
    assert os.environ[telemetry.SEMCONV_OPT_IN_VAR] == "gen_ai_latest_experimental,database,http"


def test_api_main_sets_up_api_telemetry_before_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, Any]] = []
    monkeypatch.setenv("TICKETSCOPE_OTLP_ENDPOINT", "http://otel-collector.platform.svc:4318")
    monkeypatch.setattr(
        app_module.telemetry,
        "setup",
        lambda name, endpoint: calls.append(("setup", (name, endpoint))),
    )
    monkeypatch.setattr(
        app_module.uvicorn, "run", lambda *args, **kwargs: calls.append(("run", kwargs))
    )
    app_module.main()
    assert [c[0] for c in calls] == ["setup", "run"]
    assert calls[0][1] == ("ticketscope-api", "http://otel-collector.platform.svc:4318")
    run_kwargs = calls[1][1]
    assert run_kwargs["log_config"] is None
    assert run_kwargs["factory"] is True


def test_settings_read_the_telemetry_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TICKETSCOPE_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("TICKETSCOPE_TRACE_QUERY_TEXT", raising=False)
    defaults = Settings()
    assert (defaults.otlp_endpoint, defaults.trace_query_text) == ("", False)
    monkeypatch.setenv("TICKETSCOPE_OTLP_ENDPOINT", "http://c:4318")
    monkeypatch.setenv("TICKETSCOPE_TRACE_QUERY_TEXT", "true")
    configured = Settings()
    assert (configured.otlp_endpoint, configured.trace_query_text) == ("http://c:4318", True)


# --- jobs ----------------------------------------------------------------------------------


@pytest.fixture
def jobs(monkeypatch: pytest.MonkeyPatch) -> tuple[InMemorySpanExporter, list[str]]:
    """Spans of a job `main` on an in-memory exporter, and a log of provider shutdowns."""
    exporter = InMemorySpanExporter()
    shutdowns: list[str] = []
    real = telemetry.tracer_provider

    def with_memory(service_name: str, otlp_endpoint: str) -> TracerProvider:
        provider = real(service_name, otlp_endpoint)
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        original = provider.shutdown

        def shutdown() -> None:
            shutdowns.append(service_name)
            original()

        provider.shutdown = shutdown  # type: ignore[method-assign]
        return provider

    monkeypatch.setattr(telemetry, "tracer_provider", with_memory)
    monkeypatch.setattr(telemetry, "instrument_psycopg", lambda provider: None)
    return exporter, shutdowns


def test_failed_load_sets_error_and_still_flushes(
    jobs: tuple[InMemorySpanExporter, list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    exporter, shutdowns = jobs
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", "")
    assert load.main() == 1
    [span] = exporter.get_finished_spans()
    assert (span.name, span.status.status_code) == ("load", StatusCode.ERROR)
    assert shutdowns == ["ticketscope-jobs"]


def test_a_crashing_load_records_the_exception_and_still_flushes(
    jobs: tuple[InMemorySpanExporter, list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    exporter, shutdowns = jobs

    def crash(settings: Settings) -> int:
        raise RuntimeError("unexpected")

    monkeypatch.setattr(load, "run", crash)
    with pytest.raises(RuntimeError, match="unexpected"):
        load.main()
    [span] = exporter.get_finished_spans()
    assert span.status.status_code == StatusCode.ERROR
    assert [e.name for e in span.events] == ["exception"]
    assert shutdowns == ["ticketscope-jobs"]


def test_successful_migrate_emits_one_ok_jobs_span(
    jobs: tuple[InMemorySpanExporter, list[str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    exporter, shutdowns = jobs
    monkeypatch.setattr(migrate, "run", lambda settings: 0)
    assert migrate.main() == 0
    [span] = exporter.get_finished_spans()
    assert (span.name, span.kind) == ("migrate", SpanKind.INTERNAL)
    assert span.resource.attributes["service.name"] == "ticketscope-jobs"
    assert span.status.status_code != StatusCode.ERROR
    assert shutdowns == ["ticketscope-jobs"]


def test_job_logs_inside_the_job_span_carry_its_ids(
    jobs: tuple[InMemorySpanExporter, list[str]],
    monkeypatch: pytest.MonkeyPatch,
    json_lines: _JsonLines,
    caplog: pytest.LogCaptureFixture,
) -> None:
    exporter, _ = jobs
    caplog.set_level(logging.INFO)  # pytest leaves root at WARNING; the job logs at INFO

    def run(settings: Settings) -> int:
        logging.getLogger("ticketscope.migrate").info("migrations applied")
        return 0

    monkeypatch.setattr(migrate, "run", run)
    assert migrate.main() == 0
    [span] = exporter.get_finished_spans()
    [line] = [x for x in json_lines.lines if x["message"] == "migrations applied"]
    assert span.context is not None
    assert line["trace_id"] == format(span.context.trace_id, "032x")
    assert line["span_id"] == format(span.context.span_id, "016x")


# --- layer rule ----------------------------------------------------------------------------


def _imports(path: Path) -> list[tuple[str, bool]]:
    """(module, under TYPE_CHECKING) for every import in `path`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and ast.unparse(node.test) == "TYPE_CHECKING":
            for child in ast.walk(node):
                guarded.add(id(child))
    found: list[tuple[str, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((a.name, id(node) in guarded) for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.module, id(node) in guarded))
    return found


def test_telemetry_imports_no_ticketscope_layer_and_fastapi_only_for_typing() -> None:
    imports = _imports(TELEMETRY_PY)
    assert not [m for m, _ in imports if m.split(".")[0] == "ticketscope"]
    assert all(guarded for m, guarded in imports if m.split(".")[0] in {"fastapi", "starlette"})


def test_core_and_contract_never_import_opentelemetry() -> None:
    for layer in ("core", "contract"):
        for path in (SRC / "ticketscope" / layer).rglob("*.py"):
            assert not [m for m, _ in _imports(path) if m.startswith("opentelemetry")], path


def test_jobs_never_load_fastapi_or_the_otlp_exporter_at_import() -> None:
    code = (
        "import sys, ticketscope.telemetry, ticketscope.jobs.load.main, "
        "ticketscope.jobs.migrate.main; "
        "print([m for m in ('fastapi', 'starlette', "
        "'opentelemetry.exporter.otlp.proto.http.trace_exporter', "
        "'opentelemetry.instrumentation.fastapi') if m in sys.modules])"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]"
