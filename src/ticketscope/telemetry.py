"""Traces and JSON logs for every process (AD-10, AD-11, Logging convention).

Cross-cutting like `settings`: it imports no `ticketscope` layer. `core` and `contract`
never import OpenTelemetry; the retrieval span is opened around `core` by its callers.

Export is OTLP/HTTP to the in-cluster collector only. With an empty endpoint no exporter
is created, so local runs and unit tests never reach the network.
"""

import json
import logging
import os
import sys
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, SpanKind, StatusCode, Tracer

if TYPE_CHECKING:
    from fastapi import FastAPI

SERVICE_API = "ticketscope-api"
SERVICE_JOBS = "ticketscope-jobs"

# AD-10: every process opts in before any instrumentor reads it.
SEMCONV_OPT_IN_VAR = "OTEL_SEMCONV_STABILITY_OPT_IN"
SEMCONV_OPT_IN = "gen_ai_latest_experimental,database,http"

# AD-10: renamed in the same PR as a change of corpus source.
DATA_SOURCE_ID = "ticketscope-mojang-jira"

# The SERVER span's `url.query` when query text is not opted in (`GET /?q=...`).
REDACTED = "REDACTED"

# Never traced: probes (matched against scheme://host/path, without the query).
EXCLUDED_URLS = "/healthz$,/readyz$"

TRACER_NAME = "ticketscope"


def set_semconv_opt_in() -> None:
    """Set the semconv opt-in in this process's environment, for the instrumentors."""
    os.environ[SEMCONV_OPT_IN_VAR] = SEMCONV_OPT_IN


def tracer_provider(service_name: str, otlp_endpoint: str) -> TracerProvider:
    """A provider for `service_name`; it exports to `otlp_endpoint` only when it is set."""
    provider = TracerProvider(resource=Resource({SERVICE_NAME: service_name}))
    endpoint = otlp_endpoint.strip().rstrip("/")
    if endpoint:
        # Imported here: no exporter code is loaded where nothing is exported.
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces"))
        )
    return provider


def instrument_psycopg(provider: TracerProvider) -> None:
    """CLIENT spans for every psycopg query, once per process, never with parameters."""
    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

    instrumentor = PsycopgInstrumentor()
    if not instrumentor.is_instrumented_by_opentelemetry:
        instrumentor.instrument(
            tracer_provider=provider, capture_parameters=False, enable_commenter=False
        )


def setup(service_name: str, otlp_endpoint: str) -> TracerProvider:
    """Opt in, install JSON logging, build and register the provider, instrument psycopg."""
    set_semconv_opt_in()
    configure_logging()
    provider = tracer_provider(service_name, otlp_endpoint)
    trace.set_tracer_provider(provider)
    instrument_psycopg(provider)
    return provider


# --- logs ----------------------------------------------------------------------------------


class JsonFormatter(logging.Formatter):
    """One JSON object per line: `ts`, `level`, `logger`, `message`, `trace_id`, `span_id`,
    and `exception` when present. Ids are those of the span current at emit time."""

    def format(self, record: logging.LogRecord) -> str:
        context = trace.get_current_span().get_span_context()
        valid = context.is_valid
        line: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": format(context.trace_id, "032x") if valid else None,
            "span_id": format(context.span_id, "016x") if valid else None,
        }
        if record.exc_info:
            line["exception"] = self.formatException(record.exc_info)
        elif record.exc_text:
            line["exception"] = record.exc_text
        return json.dumps(line, ensure_ascii=False, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """JSON lines on stdout from the root logger, only when root has no handler yet
    (the `basicConfig` rule, so pytest's capture keeps working)."""
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)


# --- spans ---------------------------------------------------------------------------------


def server_request_hook(record_query_text: bool) -> Callable[[Span, dict[str, Any]], None]:
    """Redact the SERVER span's `url.query` unless query text is opted in."""

    def hook(span: Span, scope: dict[str, Any]) -> None:
        if not record_query_text and span.is_recording() and scope.get("query_string"):
            span.set_attribute("url.query", REDACTED)

    return hook


def instrument_app(
    app: FastAPI, tracer_provider: TracerProvider | None, record_query_text: bool
) -> None:
    """A SERVER span per request; probes and ASGI `receive`/`send` sub-spans excluded."""
    set_semconv_opt_in()
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(
        app,
        server_request_hook=server_request_hook(record_query_text),
        tracer_provider=tracer_provider,
        excluded_urls=EXCLUDED_URLS,
        exclude_spans=["receive", "send"],
    )


@contextmanager
def untraced() -> Generator[None]:
    """No instrumentation spans (e.g. psycopg) inside: for probe work."""
    from opentelemetry.instrumentation.utils import suppress_instrumentation

    with suppress_instrumentation():
        yield


def get_tracer(provider: TracerProvider | None = None) -> Tracer:
    """Our tracer, from `provider` or the global one."""
    return trace.get_tracer(TRACER_NAME, tracer_provider=provider)


class RetrievalSpan:
    """The open `retrieval {mode}` span; the caller reports the result count."""

    def __init__(self, span: Span) -> None:
        self._span = span

    def result_count(self, count: int) -> None:
        self._span.set_attribute("ticketscope.result.count", count)


@contextmanager
def retrieval_span(
    tracer: Tracer,
    *,
    mode: str,
    k: int,
    corpus_version: str,
    query: str,
    record_query_text: bool,
) -> Generator[RetrievalSpan]:
    """The AD-10 INTERNAL `retrieval {mode}` span. An exception sets status ERROR and
    is recorded on the span, then propagates."""
    attributes: dict[str, str | int] = {
        "gen_ai.operation.name": "retrieval",
        "gen_ai.data_source.id": DATA_SOURCE_ID,
        "ticketscope.retrieval.mode": mode,
        "ticketscope.retrieval.k": k,
        "ticketscope.corpus.version": corpus_version,
    }
    if record_query_text:
        attributes["ticketscope.query.text"] = query
    with tracer.start_as_current_span(
        f"retrieval {mode}", kind=SpanKind.INTERNAL, attributes=attributes
    ) as span:
        yield RetrievalSpan(span)


@contextmanager
def job_span(provider: TracerProvider, name: str) -> Generator[Callable[[], None]]:
    """One INTERNAL span around a job's body. Yields `failed()`, which sets status ERROR
    for a job that handles its own error and returns non-zero."""
    with get_tracer(provider).start_as_current_span(name, kind=SpanKind.INTERNAL) as span:

        def failed() -> None:
            span.set_status(StatusCode.ERROR)

        yield failed
