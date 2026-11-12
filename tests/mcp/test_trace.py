"""One MCP tool call is one trace in Tempo, from the tool call to the database (story 4.5, R5).

Needs `TICKETSCOPE_GATEWAY_URL` / `TICKETSCOPE_GATEWAY_HOST` and `kubectl` on the cluster. Calls
run one at a time, so the TraceQL search over a call's time window finds exactly that call's
trace (C-2). Run with `uv run pytest -m kind tests/mcp`.
"""

import asyncio
import json
import secrets
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any, NamedTuple

import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from tests import tempo
from tests.kind import gateway
from tests.waiting import eventually
from ticketscope.mcp import spans as tool_spans

pytestmark = [
    pytest.mark.kind,
    pytest.mark.criterion(
        "ticketscope--e4-s5--AC-1",
        "ticketscope--e4-s5--AC-2",
        "ticketscope--e4-s5--AC-3",
        "ticketscope--e4-s5--AC-4",
    ),
]

QUERY = "game crashes when I open the launcher"
SEARCH = "search_similar_issues"
GET_ISSUE = "get_issue"
TRACE_TIMEOUT_SECONDS = 60


@asynccontextmanager
async def _client(extra_headers: dict[str, str] | None = None) -> AsyncIterator[Client]:
    url, host = gateway()
    headers = {"Host": host, **(extra_headers or {})}
    async with (
        httpx2.AsyncClient(headers=headers, timeout=30) as http,
        Client(streamable_http_client(f"{url}/mcp", http_client=http)) as client,
    ):
        yield client


class Window(NamedTuple):
    """When a call ran: whole seconds around it for Tempo, and its start in nanoseconds."""

    start: int
    end: int
    since_ns: int


def _call(
    tool: str,
    arguments: dict[str, Any],
    *,
    meta: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[Any, Window]:
    """One call on a connection of its own: the result and the window it ran in."""

    async def run() -> Any:
        async with _client(headers) as client:
            return await client.call_tool(tool, arguments, meta=meta)  # pyright: ignore[reportArgumentType]

    since_ns = time.time_ns()
    result = asyncio.run(run())
    return result, Window(int(since_ns / 1e9) - 1, int(time.time()) + 2, since_ns)


def _tool_span_name(tool: str) -> str:
    return f"tools/call {tool}"


def _find_trace(
    tool: str, window: Window, complete: Callable[[list[dict[str, Any]]], None]
) -> list[dict[str, Any]]:
    """The spans of the one trace whose `ticketscope-mcp` tool span fell in `window`, once
    `complete` (which asserts) is satisfied."""
    traceql = f'{{resource.service.name="ticketscope-mcp" && name="{_tool_span_name(tool)}"' + "}"

    def check() -> list[dict[str, Any]]:
        ids = tempo.search(traceql, window.start, window.end, window.since_ns)
        assert len(ids) == 1, f"expected one trace in the window, found {ids}"
        status, body = tempo.trace_by_id(ids[0])
        assert status == 200, f"trace {ids[0]} not readable: {status}: {body[:1000]}"
        found = tempo.spans(json.loads(body))
        complete(found)
        return found

    return eventually(check, timeout=TRACE_TIMEOUT_SECONDS, interval=3)


def _named(found: list[dict[str, Any]], name: str, service: str | None = None) -> dict[str, Any]:
    matches = [
        s for s in found if s.get("name") == name and (service is None or s["service"] == service)
    ]
    assert len(matches) == 1, (name, [s.get("name") for s in found])
    return matches[0]


def _descends(found: list[dict[str, Any]], span: dict[str, Any], ancestor: dict[str, Any]) -> bool:
    by_id = {s["id"]: s for s in found}
    current = span
    while current["parent"] in by_id:
        current = by_id[current["parent"]]
        if current["id"] == ancestor["id"]:
            return True
    return False


def _assert_search_tree(found: list[dict[str, Any]]) -> None:
    tool = _named(found, _tool_span_name(SEARCH), "ticketscope-mcp")
    assert tempo.kind(tool) == "SERVER"
    assert tool["parent"] == "", "the tool span is the root"
    client = _named(found, "POST", "ticketscope-mcp")
    assert tempo.kind(client) == "CLIENT"
    assert client["parent"] == tool["id"]
    api = _named(found, "POST /v1/search", "ticketscope-api")
    assert tempo.kind(api) == "SERVER"
    assert api["parent"] == client["id"]
    retrieval = _named(found, "retrieval hybrid", "ticketscope-api")
    assert retrieval["parent"] == api["id"]
    embeddings = [s for s in found if str(s.get("name")).startswith("embeddings ")]
    assert len(embeddings) == 1
    assert embeddings[0]["parent"] == retrieval["id"]
    db = [
        s
        for s in found
        if tempo.kind(s) == "CLIENT"
        and s["attrs"].get("db.system.name") == "postgresql"
        and _descends(found, s, retrieval)
    ]
    assert db, [s.get("name") for s in found]


def _assert_no_query_text(found: list[dict[str, Any]]) -> None:
    needle = QUERY.lower()
    for span in found:
        assert not any(needle in str(v).lower() for v in span["attrs"].values()), span


def test_a_search_is_one_trace_under_the_tool_span() -> None:
    result, window = _call(SEARCH, {"query": QUERY, "mode": "hybrid"})
    assert not result.is_error, result
    found = _find_trace(SEARCH, window, _assert_search_tree)
    _assert_no_query_text(found)
    assert len({s["trace"] for s in found}) == 1
    tool_spans_found = [
        s for s in found if s["service"] == "ticketscope-mcp" and tempo.kind(s) == "SERVER"
    ]
    assert len(tool_spans_found) == 1
    assert set(tool_spans_found[0]["attrs"]) == tool_spans.TOOL_SPAN_KEYS


def test_meta_traceparent_lands_in_that_trace() -> None:
    trace_id, parent_id = secrets.token_hex(16), secrets.token_hex(8)
    meta = {"traceparent": f"00-{trace_id}-{parent_id}-01"}
    result, _ = _call(SEARCH, {"query": QUERY, "mode": "keyword"}, meta=meta)
    assert not result.is_error, result
    _assert_meta_trace(trace_id, parent_id)


def _assert_meta_trace(trace_id: str, parent_id: str) -> None:
    def check() -> None:
        status, body = tempo.trace_by_id(trace_id)
        assert status == 200, f"trace not readable: {status}: {body[:1000]}"
        found = tempo.spans(json.loads(body))
        tool = _named(found, _tool_span_name(SEARCH), "ticketscope-mcp")
        assert tool["trace"] == trace_id
        assert tool["parent"] == parent_id
        _named(found, "POST /v1/search", "ticketscope-api")

    eventually(check, timeout=TRACE_TIMEOUT_SECONDS, interval=3)


def test_meta_wins_over_a_different_http_traceparent_header() -> None:
    meta_trace, header_trace = secrets.token_hex(16), secrets.token_hex(16)
    meta_parent = secrets.token_hex(8)
    result, _ = _call(
        SEARCH,
        {"query": QUERY, "mode": "keyword"},
        meta={"traceparent": f"00-{meta_trace}-{meta_parent}-01"},
        headers={"traceparent": f"00-{header_trace}-{secrets.token_hex(8)}-01"},
    )
    assert not result.is_error, result
    _assert_meta_trace(meta_trace, meta_parent)
    status, body = tempo.trace_by_id(header_trace)
    # Tempo's v2 answer for an unknown trace id is 200 with an empty trace.
    assert status == 200 and not tempo.spans(json.loads(body)), (
        "the HTTP header's trace id must not be used"
    )


def test_an_unknown_mode_gives_an_error_tool_span() -> None:
    result, window = _call(SEARCH, {"query": QUERY, "mode": "bogus"})
    assert result.is_error

    def complete(found: list[dict[str, Any]]) -> None:
        tool = _named(found, _tool_span_name(SEARCH), "ticketscope-mcp")
        assert tool["status"].get("code") in ("STATUS_CODE_ERROR", 2), tool["status"]
        assert tool["attrs"]["gen_ai.tool.name"] == SEARCH

    found = _find_trace(SEARCH, window, complete)
    _assert_no_query_text(found)


def test_get_issue_is_its_own_trace() -> None:
    async def first_key() -> str:
        async with _client() as client:
            result = await client.call_tool(SEARCH, {"query": QUERY, "mode": "keyword", "k": 1})
        assert result.structured_content is not None
        return str(result.structured_content["results"][0]["issue"]["key"])

    key = asyncio.run(first_key())
    result, window = _call(GET_ISSUE, {"key": key})
    assert not result.is_error, result

    def complete(found: list[dict[str, Any]]) -> None:
        tool = _named(found, _tool_span_name(GET_ISSUE), "ticketscope-mcp")
        assert tool["parent"] == ""
        client = _named(found, "GET", "ticketscope-mcp")
        assert tempo.kind(client) == "CLIENT"
        assert client["parent"] == tool["id"]
        api = _named(found, "GET /v1/issues/by-key/{key}", "ticketscope-api")
        assert api["parent"] == client["id"]

    _find_trace(GET_ISSUE, window, complete)
