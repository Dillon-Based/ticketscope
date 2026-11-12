"""The `ticketscope-mcp` trace on an in-memory exporter (story 4.5, R5).

The tool span is the MCP SDK's own (it uses the global provider); `apiclient` opens the CLIENT
span and injects `traceparent`. A fake `/v1` records the headers it receives.
"""

import asyncio
import json
import os
from collections.abc import Callable, Iterator
from typing import Any

import httpx2
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanContext, SpanKind, StatusCode

from tests.factories import issue_response_payload
from ticketscope import telemetry
from ticketscope.apiclient import ApiClient
from ticketscope.mcp import spans
from ticketscope.mcp.server import build_app
from ticketscope.settings import Settings

pytestmark = pytest.mark.criterion(
    "ticketscope--e4-s5--AC-2",
    "ticketscope--e4-s5--AC-3",
    "ticketscope--e4-s5--AC-4",
    "ticketscope--e4-s5--AC-5",
)

HOST = "ticketscope.test"
HEADERS = {
    "content-type": "application/json",
    "accept": "application/json, text/event-stream",
}
SEARCH_BODY: dict[str, Any] = {
    "mode": "hybrid",
    "score_kind": "rrf",
    "corpus_version": "v1",
    "results": [],
}
ISSUE_BODY = issue_response_payload(6629, "MCL-6629")
QUERY = "secretquery"
TRACE_A = "0af7651916cd43dd8448eb211c80319c"
TRACE_B = "4bf92f3577b34da6a3ce929d0e0e4736"


@pytest.fixture(scope="module")
def exporter() -> Iterator[InMemorySpanExporter]:
    """The SDK's tracer follows the global provider, which is write-once: register ours
    (or attach to the one already there) once for this module."""
    memory = InMemorySpanExporter()
    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        provider = telemetry.tracer_provider(telemetry.SERVICE_MCP, "")
        trace.set_tracer_provider(provider)
    processor = SimpleSpanProcessor(memory)
    provider.add_span_processor(processor)  # pyright: ignore[reportAttributeAccessIssue]
    yield memory
    processor.shutdown()


@pytest.fixture(autouse=True)
def _clear(exporter: InMemorySpanExporter) -> None:
    exporter.clear()


def _rpc(
    name: str, arguments: dict[str, Any], meta: dict[str, Any] | None = None
) -> dict[str, Any]:
    params: dict[str, Any] = {"name": name, "arguments": arguments}
    if meta:
        params["_meta"] = meta
    return {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params}


def _search(arguments: dict[str, Any] | None = None, **kw: Any) -> dict[str, Any]:
    return _rpc("search_similar_issues", arguments or {"query": QUERY}, **kw)


def _run(
    body: dict[str, Any],
    *,
    api: Callable[[httpx2.Request], httpx2.Response] | None = None,
    headers: dict[str, str] | None = None,
    trace_query_text: bool = False,
    seen: list[httpx2.Request] | None = None,
) -> None:
    def fake_api(request: httpx2.Request) -> httpx2.Response:
        if seen is not None:
            seen.append(request)
        if api is not None:
            return api(request)
        if request.method == "GET":
            return httpx2.Response(200, json=ISSUE_BODY)
        return httpx2.Response(200, json=SEARCH_BODY)

    client = ApiClient("http://api:8000", 5, transport=httpx2.MockTransport(fake_api))
    settings = Settings(  # pyright: ignore[reportCallIssue]
        mcp_allowed_hosts=HOST,  # pyright: ignore[reportArgumentType]
        api_base_url="http://api:8000",
        trace_query_text=trace_query_text,
    )
    app = build_app(settings, client)

    async def main() -> None:
        async with app.router.lifespan_context(app):
            transport = httpx2.ASGITransport(app=app)
            async with httpx2.AsyncClient(transport=transport, base_url=f"http://{HOST}") as http:
                response = await http.post(
                    "/mcp", headers={**HEADERS, **(headers or {})}, json=body
                )
                assert response.status_code == 200, response.text

    asyncio.run(main())


def _finished(exporter: InMemorySpanExporter) -> list[ReadableSpan]:
    return list(exporter.get_finished_spans())


def _one(spans_: list[ReadableSpan], kind: SpanKind) -> ReadableSpan:
    [span] = [s for s in spans_ if s.kind == kind]
    return span


def _ctx(span: ReadableSpan) -> SpanContext:
    assert span.context is not None
    return span.context


def _hex(value: int, width: int) -> str:
    return format(value, f"0{width}x")


def test_plain_call_is_one_trace_with_tool_span_root_and_client_child(
    exporter: InMemorySpanExporter,
) -> None:
    seen: list[httpx2.Request] = []
    _run(_search(), seen=seen)
    finished = _finished(exporter)
    tool = _one(finished, SpanKind.SERVER)
    client = _one(finished, SpanKind.CLIENT)
    assert tool.name == "tools/call search_similar_issues"
    assert tool.parent is None
    assert client.name == "POST"
    assert client.parent is not None
    assert client.parent.span_id == _ctx(tool).span_id
    assert _ctx(client).trace_id == _ctx(tool).trace_id
    # The tool span is created through the SDK's tracer, so the service is the provider's.
    assert tool.attributes is not None
    assert tool.attributes["gen_ai.operation.name"] == "execute_tool"
    assert tool.attributes["gen_ai.tool.name"] == "search_similar_issues"
    assert tool.attributes["mcp.method.name"] == "tools/call"
    assert tool.status.status_code == StatusCode.UNSET
    [request] = seen
    version, trace_id, span_id, _ = request.headers["traceparent"].split("-")
    assert version == "00"
    assert trace_id == _hex(_ctx(tool).trace_id, 32)
    assert span_id == _hex(_ctx(client).span_id, 16)


def test_client_span_has_http_semconv_attributes(exporter: InMemorySpanExporter) -> None:
    _run(_search({"query": QUERY, "mode": "hybrid"}))
    client = _one(_finished(exporter), SpanKind.CLIENT)
    assert dict(client.attributes or {}) == {
        "http.request.method": "POST",
        "url.full": "http://api:8000/v1/search",
        "server.address": "api",
        "server.port": 8000,
        "http.response.status_code": 200,
    }
    assert client.status.status_code == StatusCode.UNSET


def test_tool_span_keys_equal_the_constants_list(exporter: InMemorySpanExporter) -> None:
    _run(_search())
    tool = _one(_finished(exporter), SpanKind.SERVER)
    assert set(tool.attributes or {}) == spans.TOOL_SPAN_KEYS


def test_meta_traceparent_is_continued(exporter: InMemorySpanExporter) -> None:
    meta = {"traceparent": f"00-{TRACE_A}-00f067aa0ba902b7-01"}
    seen: list[httpx2.Request] = []
    _run(_search(meta=meta), seen=seen)
    tool = _one(_finished(exporter), SpanKind.SERVER)
    assert _hex(_ctx(tool).trace_id, 32) == TRACE_A
    assert tool.parent is not None
    assert _hex(tool.parent.span_id, 16) == "00f067aa0ba902b7"
    assert seen[0].headers["traceparent"].split("-")[1] == TRACE_A


def test_malformed_meta_traceparent_starts_a_new_trace(exporter: InMemorySpanExporter) -> None:
    _run(_search(meta={"traceparent": "garbage"}))
    tool = _one(_finished(exporter), SpanKind.SERVER)
    assert tool.parent is None
    assert _ctx(tool).trace_id != 0


def test_meta_wins_over_the_http_traceparent_header(exporter: InMemorySpanExporter) -> None:
    meta = {"traceparent": f"00-{TRACE_A}-00f067aa0ba902b7-01"}
    header = {"traceparent": f"00-{TRACE_B}-b7ad6b7169203331-01"}
    _run(_search(meta=meta), headers=header)
    tool = _one(_finished(exporter), SpanKind.SERVER)
    assert _hex(_ctx(tool).trace_id, 32) == TRACE_A


def test_http_header_alone_is_ignored(exporter: InMemorySpanExporter) -> None:
    _run(_search(), headers={"traceparent": f"00-{TRACE_B}-b7ad6b7169203331-01"})
    tool = _one(_finished(exporter), SpanKind.SERVER)
    assert _hex(_ctx(tool).trace_id, 32) != TRACE_B


def test_an_api_422_sets_error_status_on_the_tool_span(exporter: InMemorySpanExporter) -> None:
    problem = {"type": "t", "title": "x", "status": 422, "detail": "bad mode"}

    def api(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            422, json=problem, headers={"content-type": "application/problem+json"}
        )

    _run(_search({"query": QUERY, "mode": "bogus"}), api=api)
    finished = _finished(exporter)
    tool = _one(finished, SpanKind.SERVER)
    assert tool.status.status_code == StatusCode.ERROR
    assert tool.attributes is not None
    assert tool.attributes["gen_ai.tool.name"] == "search_similar_issues"
    assert set(tool.attributes) == spans.TOOL_SPAN_ERROR_KEYS


def test_an_unreachable_api_sets_error_on_the_client_and_tool_spans(
    exporter: InMemorySpanExporter,
) -> None:
    def api(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("refused", request=request)

    _run(_search(), api=api)
    finished = _finished(exporter)
    client = _one(finished, SpanKind.CLIENT)
    assert client.status.status_code == StatusCode.ERROR
    assert (client.attributes or {})["error.type"] == "ConnectError"
    assert _one(finished, SpanKind.SERVER).status.status_code == StatusCode.ERROR


def test_a_5xx_sets_error_on_the_client_span(exporter: InMemorySpanExporter) -> None:
    _run(_search(), api=lambda request: httpx2.Response(503, text="down"))
    client = _one(_finished(exporter), SpanKind.CLIENT)
    assert client.status.status_code == StatusCode.ERROR
    attrs = client.attributes or {}
    assert attrs["error.type"] == "503"
    assert attrs["http.response.status_code"] == 503


def test_get_issue_is_its_own_trace_with_a_get_client_span(exporter: InMemorySpanExporter) -> None:
    seen: list[httpx2.Request] = []
    _run(_rpc("get_issue", {"key": "MCL-6629"}), seen=seen)
    finished = _finished(exporter)
    tool = _one(finished, SpanKind.SERVER)
    client = _one(finished, SpanKind.CLIENT)
    assert tool.name == "tools/call get_issue"
    assert tool.parent is None
    assert client.name == "GET"
    assert (client.attributes or {})["url.full"] == "http://api:8000/v1/issues/by-key/MCL-6629"
    assert client.parent is not None
    assert client.parent.span_id == _ctx(tool).span_id
    assert seen[0].headers["traceparent"].split("-")[1] == _hex(_ctx(tool).trace_id, 32)


def test_an_api_404_for_an_unknown_key_sets_error_status_on_the_tool_span(
    exporter: InMemorySpanExporter,
) -> None:
    problem = {"type": "t", "title": "x", "status": 404, "detail": "no such issue"}
    _run(
        _rpc("get_issue", {"key": "MCL-1"}),
        api=lambda r: httpx2.Response(
            404, json=problem, headers={"content-type": "application/problem+json"}
        ),
    )
    tool = _one(_finished(exporter), SpanKind.SERVER)
    assert tool.status.status_code == StatusCode.ERROR
    assert (tool.attributes or {})["gen_ai.tool.name"] == "get_issue"


def test_the_url_on_the_client_span_never_carries_a_query(exporter: InMemorySpanExporter) -> None:
    _run(_rpc("get_issue", {"key": "MCL-6629?x=1"}), api=lambda r: httpx2.Response(404, text=""))
    client = _one(_finished(exporter), SpanKind.CLIENT)
    assert "?" not in str((client.attributes or {})["url.full"])


def test_no_span_carries_the_query_by_default(exporter: InMemorySpanExporter) -> None:
    _run(_search())
    for span in _finished(exporter):
        assert QUERY not in json.dumps(dict(span.attributes or {}), default=str)
        assert spans.QUERY_TEXT not in (span.attributes or {})


def test_query_text_is_on_the_tool_span_only_when_opted_in(exporter: InMemorySpanExporter) -> None:
    _run(_search(), trace_query_text=True)
    finished = _finished(exporter)
    tool = _one(finished, SpanKind.SERVER)
    assert (tool.attributes or {})[spans.QUERY_TEXT] == QUERY
    assert set(tool.attributes or {}) == spans.TOOL_SPAN_QUERY_KEYS
    client = _one(finished, SpanKind.CLIENT)
    assert spans.QUERY_TEXT not in (client.attributes or {})


def test_an_empty_endpoint_creates_no_exporter() -> None:
    provider = telemetry.tracer_provider(telemetry.SERVICE_MCP, "")
    assert not provider._active_span_processor._span_processors  # pyright: ignore[reportPrivateUsage]


@pytest.fixture
def psycopg_calls(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    called: list[object] = []
    monkeypatch.setattr(telemetry, "instrument_psycopg", called.append)
    return called


def test_setup_without_db_does_not_instrument_psycopg(psycopg_calls: list[object]) -> None:
    telemetry.setup(telemetry.SERVICE_MCP, "", instrument_db=False)
    assert psycopg_calls == []


def test_setup_with_db_instruments_psycopg_once(psycopg_calls: list[object]) -> None:
    telemetry.setup(telemetry.SERVICE_API, "")
    assert len(psycopg_calls) == 1


def test_setup_names_the_provider_after_the_service(psycopg_calls: list[object]) -> None:
    provider = telemetry.setup(telemetry.SERVICE_MCP, "", instrument_db=False)
    assert provider.resource.attributes["service.name"] == "ticketscope-mcp"


def test_setup_sets_the_semconv_opt_in(psycopg_calls: list[object]) -> None:
    telemetry.setup(telemetry.SERVICE_MCP, "", instrument_db=False)
    assert os.environ[telemetry.SEMCONV_OPT_IN_VAR] == telemetry.SEMCONV_OPT_IN
