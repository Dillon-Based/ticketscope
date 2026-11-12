"""The MCP server in process against a fake `/v1` (story 4.1): no cluster, no database."""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

import httpx2
import pytest

from ticketscope.apiclient import ApiClient
from ticketscope.contract.search import SearchResponse
from ticketscope.mcp.server import build_app
from ticketscope.settings import Settings

HOST = "ticketscope.test"
HEADERS = {
    "content-type": "application/json",
    "accept": "application/json, text/event-stream",
}
API_BODY: dict[str, Any] = {
    "mode": "hybrid",
    "score_kind": "rrf",
    "corpus_version": "v1",
    "results": [],
}


def _rpc(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}


def _call(arguments: dict[str, Any]) -> dict[str, Any]:
    return _rpc("tools/call", {"name": "search_similar_issues", "arguments": arguments})


def _result(response: httpx2.Response) -> dict[str, Any]:
    data = next(line for line in response.text.splitlines() if line.startswith("data: "))
    return json.loads(data.removeprefix("data: "))["result"]


def _run(
    scenario: Callable[[httpx2.AsyncClient], Any],
    seen: list[dict[str, Any]],
    api: Callable[[httpx2.Request], httpx2.Response] | None = None,
    hosts: str = HOST,
) -> Any:
    def fake_api(request: httpx2.Request) -> httpx2.Response:
        seen.append(json.loads(request.content))
        return httpx2.Response(200, json=API_BODY)

    client = ApiClient("http://api", 5, transport=httpx2.MockTransport(api or fake_api))
    app = build_app(Settings(mcp_allowed_hosts=hosts, api_base_url="http://api"), client)  # pyright: ignore[reportArgumentType]

    async def main() -> Any:
        async with app.router.lifespan_context(app):
            transport = httpx2.ASGITransport(app=app)
            async with httpx2.AsyncClient(transport=transport, base_url=f"http://{HOST}") as http:
                return await scenario(http)

    return asyncio.run(main())


def test_tools_list_has_the_search_tool_with_the_contract_output_schema() -> None:
    async def scenario(http: httpx2.AsyncClient) -> dict[str, Any]:
        return _result(await http.post("/mcp", headers=HEADERS, json=_rpc("tools/list")))

    result = _run(scenario, [])
    assert {t["name"] for t in result["tools"]} == {"search_similar_issues", "get_issue"}
    [tool] = [t for t in result["tools"] if t["name"] == "search_similar_issues"]
    assert tool["inputSchema"]["required"] == ["query"]
    assert set(tool["inputSchema"]["properties"]) == {"query", "mode", "k"}
    assert tool["outputSchema"] == SearchResponse.model_json_schema()


def test_a_call_without_mode_sends_none_and_returns_the_body_unchanged() -> None:
    seen: list[dict[str, Any]] = []

    async def scenario(http: httpx2.AsyncClient) -> dict[str, Any]:
        # No `initialize` first: the transport is stateless.
        return _result(await http.post("/mcp", headers=HEADERS, json=_call({"query": "crash"})))

    result = _run(scenario, seen)
    assert seen == [{"query": "crash"}]
    assert result["isError"] is False
    assert result["structuredContent"] == API_BODY


@pytest.mark.parametrize("mode", ["bogus", ""])
def test_an_unknown_or_empty_mode_is_sent_unchanged(mode: str) -> None:
    seen: list[dict[str, Any]] = []

    async def scenario(http: httpx2.AsyncClient) -> None:
        await http.post("/mcp", headers=HEADERS, json=_call({"query": "q", "mode": mode, "k": 5}))

    _run(scenario, seen)
    assert seen == [{"query": "q", "mode": mode, "k": 5}]


def test_an_extra_api_field_passes_through() -> None:
    def api(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json={**API_BODY, "future_field": [1, 2]})

    async def scenario(http: httpx2.AsyncClient) -> dict[str, Any]:
        return _result(await http.post("/mcp", headers=HEADERS, json=_call({"query": "q"})))

    result = _run(scenario, [], api)
    assert result["structuredContent"]["future_field"] == [1, 2]


def _problem_422() -> httpx2.Response:
    problem = {"type": "t", "title": "x", "status": 422, "detail": "bad mode"}
    return httpx2.Response(422, json=problem, headers={"content-type": "application/problem+json"})


def test_an_api_422_reaches_the_client_as_a_tool_error() -> None:
    def api(request: httpx2.Request) -> httpx2.Response:
        return _problem_422()

    async def scenario(http: httpx2.AsyncClient) -> dict[str, Any]:
        call = _call({"query": "q", "mode": "bogus"})
        return _result(await http.post("/mcp", headers=HEADERS, json=call))

    result = _run(scenario, [], api)
    assert result["isError"] is True
    assert result["content"] == [{"type": "text", "text": "bad mode"}]


def _logged_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == "ticketscope.mcp"]


def test_an_api_422_logs_one_line_with_its_status(caplog: pytest.LogCaptureFixture) -> None:
    def api(request: httpx2.Request) -> httpx2.Response:
        return _problem_422()

    async def scenario(http: httpx2.AsyncClient) -> None:
        await http.post("/mcp", headers=HEADERS, json=_call({"query": "q", "mode": "bogus"}))

    with caplog.at_level(logging.INFO, logger="ticketscope.mcp"):
        _run(scenario, [], api)
    [line] = _logged_lines(caplog)
    assert "status=api_422" in line


@pytest.mark.parametrize("failure", [httpx2.ConnectError, httpx2.ReadTimeout])
def test_an_unreachable_api_logs_one_line_with_status_error(
    caplog: pytest.LogCaptureFixture,
    failure: type[httpx2.RequestError],
) -> None:
    def api(request: httpx2.Request) -> httpx2.Response:
        raise failure("api down")

    async def scenario(http: httpx2.AsyncClient) -> dict[str, Any]:
        return _result(await http.post("/mcp", headers=HEADERS, json=_call({"query": "q"})))

    with caplog.at_level(logging.INFO, logger="ticketscope.mcp"):
        result = _run(scenario, [], api)
    assert result["isError"] is True
    [line] = _logged_lines(caplog)
    assert "status=error" in line


def test_a_foreign_host_is_refused_without_a_stack_trace() -> None:
    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        return await http.post(
            "/mcp", headers={**HEADERS, "host": "evil.example"}, json=_call({"query": "q"})
        )

    seen: list[dict[str, Any]] = []
    response: httpx2.Response = _run(scenario, seen)
    assert response.status_code == 421
    assert "Traceback" not in response.text
    assert seen == []


def test_healthz_is_ok_for_any_host_and_never_calls_api() -> None:
    def api(request: httpx2.Request) -> httpx2.Response:
        raise AssertionError("healthz must not reach api")

    async def scenario(http: httpx2.AsyncClient) -> httpx2.Response:
        return await http.get("/healthz", headers={"host": "10.1.2.3:8080"})

    response: httpx2.Response = _run(scenario, [], api)
    assert response.status_code == 200


@pytest.mark.parametrize("hosts", ["", "*", "a.test,*"])
def test_empty_or_wildcard_allowed_hosts_are_refused_at_startup(hosts: str) -> None:
    client = ApiClient("http://api", 5)
    with pytest.raises(ValueError, match="TICKETSCOPE_MCP_ALLOWED_HOSTS"):
        build_app(Settings(mcp_allowed_hosts=hosts), client)  # pyright: ignore[reportArgumentType]


def test_a_tool_call_logs_one_line(caplog: pytest.LogCaptureFixture) -> None:
    async def scenario(http: httpx2.AsyncClient) -> None:
        await http.post("/mcp", headers=HEADERS, json=_call({"query": "secret text"}))

    with caplog.at_level(logging.INFO, logger="ticketscope.mcp"):
        _run(scenario, [])
    lines = [r.getMessage() for r in caplog.records if r.name == "ticketscope.mcp"]
    assert len(lines) == 1
    assert "search_similar_issues" in lines[0] and "status=ok" in lines[0]
    assert "secret text" not in lines[0]


def test_a_result_carries_a_text_block_of_the_serialised_json_beside_structured_content() -> None:
    async def scenario(http: httpx2.AsyncClient) -> dict[str, Any]:
        return _result(await http.post("/mcp", headers=HEADERS, json=_call({"query": "crash"})))

    result = _run(scenario, [])
    [block] = result["content"]
    assert block["type"] == "text"
    assert json.loads(block["text"]) == API_BODY == result["structuredContent"]
