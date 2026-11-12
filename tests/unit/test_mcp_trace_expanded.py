"""Gap coverage for story 4.5: main()'s telemetry wiring and the remaining CLIENT-span failures."""

import asyncio
from typing import Any

import httpx2
import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import StatusCode

from ticketscope import telemetry
from ticketscope.apiclient import ApiClient, ApiUnreachable
from ticketscope.mcp import main as mcp_main

pytestmark = pytest.mark.criterion("ticketscope--e4-s5--AC-1", "ticketscope--e4-s5--AC-3")


def test_main_sets_up_telemetry_as_mcp_without_db_instrumentation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TICKETSCOPE_API_BASE_URL", "http://api")
    monkeypatch.setenv("TICKETSCOPE_MCP_ALLOWED_HOSTS", "a.test")
    monkeypatch.setenv("TICKETSCOPE_OTLP_ENDPOINT", "http://collector:4318")
    setups: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    monkeypatch.setattr(mcp_main.telemetry, "setup", lambda *a, **k: setups.append((a, k)))
    monkeypatch.setattr(mcp_main.uvicorn, "run", lambda *a, **k: None)
    mcp_main.main()
    assert setups == [((telemetry.SERVICE_MCP, "http://collector:4318"), {"instrument_db": False})]


def test_main_exits_before_telemetry_when_api_url_is_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TICKETSCOPE_API_BASE_URL", "  ")
    called: list[object] = []
    monkeypatch.setattr(mcp_main.telemetry, "setup", lambda *a, **k: called.append(a))
    with pytest.raises(SystemExit):
        mcp_main.main()
    assert called == []


@pytest.mark.parametrize(
    ("error", "message", "error_type"),
    [
        (httpx2.ReadTimeout, "timed out after 5s", "ReadTimeout"),
        (httpx2.ReadError, "connection lost", "ReadError"),
    ],
)
def test_timeout_and_transport_errors_mark_the_client_span(
    monkeypatch: pytest.MonkeyPatch, error: type[httpx2.RequestError], message: str, error_type: str
) -> None:
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    memory = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(memory))
    monkeypatch.setattr(telemetry, "get_tracer", lambda: provider.get_tracer("t"))

    def boom(request: httpx2.Request) -> httpx2.Response:
        raise error("x", request=request)

    client = ApiClient("http://api:8000", 5, transport=httpx2.MockTransport(boom))
    with pytest.raises(ApiUnreachable, match=message):
        asyncio.run(client.search("q", None, None))
    [span] = memory.get_finished_spans()
    assert span.status.status_code == StatusCode.ERROR
    assert (span.attributes or {})["error.type"] == error_type
    asyncio.run(client.aclose())
