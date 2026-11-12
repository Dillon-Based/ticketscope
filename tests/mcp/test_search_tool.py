"""An MCP client calls `search_similar_issues` through the Gateway on kind (story 4.1, R1).

Needs `TICKETSCOPE_GATEWAY_URL` (e.g. `http://172.18.0.5`) and `TICKETSCOPE_GATEWAY_HOST`
(the route hostname), plus `kubectl` on the cluster. Run with `uv run pytest -m kind tests/mcp`.
"""

import asyncio
import json
import os
import re
import subprocess
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx2
import jsonschema
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from tests.target import CHART_VALUES
from tests.waiting import eventually
from ticketscope.contract.search import SearchResponse

pytestmark = pytest.mark.kind

NAMESPACE = os.environ.get("TICKETSCOPE_NAMESPACE", "ticketscope")
QUERY = "game crashes when I open the launcher"
TOOL = "search_similar_issues"
FRESH_CONNECTIONS = 20


def _gateway() -> tuple[str, str]:
    url = os.environ.get("TICKETSCOPE_GATEWAY_URL")
    host = os.environ.get("TICKETSCOPE_GATEWAY_HOST")
    if not url or not host:
        pytest.fail("TICKETSCOPE_GATEWAY_URL and TICKETSCOPE_GATEWAY_HOST must be set")
    return url.rstrip("/"), host


def _default_mode() -> str:
    match = re.search(r"^\s*defaultMode:\s*(\w+)", CHART_VALUES.read_text(), re.MULTILINE)
    assert match, "values.yaml has no retrieval.defaultMode"
    return match.group(1)


@asynccontextmanager
async def _client() -> AsyncIterator[Client]:
    url, host = _gateway()
    async with (
        httpx2.AsyncClient(headers={"Host": host}, timeout=30) as http,
        Client(streamable_http_client(f"{url}/mcp", http_client=http)) as client,
    ):
        yield client


async def _search(arguments: dict[str, Any]) -> dict[str, Any]:
    """One call on a connection of its own; the result as structured content."""
    async with _client() as client:
        result = await client.call_tool(TOOL, arguments)
    assert not result.is_error, result
    assert result.structured_content is not None
    return result.structured_content


def _output_schema() -> dict[str, Any]:
    async def fetch() -> dict[str, Any]:
        async with _client() as client:
            [tool] = (await client.list_tools()).tools
        assert tool.name == TOOL
        assert tool.output_schema is not None
        return tool.output_schema

    return asyncio.run(fetch())


def _direct_search(payload: dict[str, Any]) -> dict[str, Any]:
    url, host = _gateway()
    response = httpx2.post(f"{url}/v1/search", json=payload, headers={"Host": host}, timeout=30)
    assert response.status_code == 200, response.text
    return response.json()


def test_tools_list_advertises_search_similar_issues() -> None:
    async def fetch() -> list[Any]:
        async with _client() as client:
            return (await client.list_tools()).tools

    [tool] = asyncio.run(fetch())
    assert tool.name == TOOL
    assert tool.output_schema == SearchResponse.model_json_schema()


def test_a_call_without_mode_uses_the_server_default_and_matches_the_schema() -> None:
    body = asyncio.run(_search({"query": QUERY}))
    assert body["mode"] == _default_mode()
    jsonschema.validate(body, _output_schema())


def test_a_keyword_call_equals_the_direct_v1_body() -> None:
    body = asyncio.run(_search({"query": QUERY, "mode": "keyword"}))
    jsonschema.validate(body, _output_schema())
    assert body == _direct_search({"query": QUERY, "mode": "keyword"})


def test_tools_call_works_without_initialize() -> None:
    url, host = _gateway()
    response = httpx2.post(
        f"{url}/mcp",
        headers={
            "Host": host,
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": TOOL, "arguments": {"query": QUERY, "mode": "keyword"}},
        },
        timeout=30,
    )
    assert response.status_code == 200, response.text
    data = next(line for line in response.text.splitlines() if line.startswith("data: "))
    result = json.loads(data.removeprefix("data: "))["result"]
    assert result["isError"] is False
    assert result["structuredContent"]["mode"] == "keyword"


def _mcp_pods() -> list[str]:
    out = subprocess.run(
        [
            "kubectl",
            "-n",
            NAMESPACE,
            "get",
            "pods",
            "-l",
            "app.kubernetes.io/component=mcp",
            "-o",
            "jsonpath={.items[*].metadata.name}",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return out.split()


def _pod_log(pod: str) -> str:
    return subprocess.run(
        ["kubectl", "-n", NAMESPACE, "logs", pod],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_fresh_connections_are_served_by_both_replicas() -> None:
    pods = _mcp_pods()
    assert len(pods) == 2, pods
    marker = f"tool call {TOOL}"
    before = {pod: _pod_log(pod).count(marker) for pod in pods}

    async def many() -> None:
        for _ in range(FRESH_CONNECTIONS):
            body = await _search({"query": QUERY, "mode": "keyword"})
            assert body["mode"] == "keyword"

    asyncio.run(many())

    def both_logged() -> None:
        for pod in pods:
            assert _pod_log(pod).count(marker) > before[pod], f"no new tool call logged by {pod}"

    eventually(both_logged, timeout=60, interval=2)


# The stand-in in kind values; locally, the host kind-up.sh was given as TUNNEL_HOSTNAME.
STAND_IN_HOST = os.environ.get("TICKETSCOPE_TUNNEL_HOST", "tunnel.ticketscope.test")
MCP_HEADERS = {"content-type": "application/json", "accept": "application/json, text/event-stream"}


def _post(path: str, host: str, body: dict[str, Any]) -> httpx2.Response:
    url, _ = _gateway()
    return httpx2.post(f"{url}{path}", headers={"Host": host, **MCP_HEADERS}, json=body, timeout=30)


def _tools_list(host: str) -> httpx2.Response:
    return _post("/mcp", host, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})


def test_the_stand_in_tunnel_host_reaches_mcp() -> None:
    response = _tools_list(STAND_IN_HOST)
    assert response.status_code == 200, response.text
    assert TOOL in response.text


def test_the_kind_host_still_reaches_mcp() -> None:
    _, host = _gateway()
    assert _tools_list(host).status_code == 200


@pytest.mark.parametrize("path", ["/v1/search", "/"])
def test_the_tunnel_host_reaches_nothing_but_mcp(path: str) -> None:
    response = _post(path, STAND_IN_HOST, {"query": QUERY})
    assert response.status_code == 404, (path, response.status_code)


def test_a_foreign_host_is_refused() -> None:
    url, _ = _gateway()
    response = httpx2.post(
        f"{url}/mcp",
        headers={
            "Host": "evil.example",
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
        },
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        timeout=30,
    )
    assert 400 <= response.status_code < 500, response.status_code
    assert "Traceback" not in response.text
