"""R3's unreachable-API case on kind (story 4.7, R-009).

Scales `api` to zero, so it runs as its own pytest invocation after the main `tests/mcp`
suite (see `.github/workflows/mcp-e2e.yml`), never by test order. The fixture's finalizer
scales `api` back and waits for it to be Ready, so a rerun on the same cluster still works.
"""

import asyncio
import os
import subprocess
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

import httpx2
import pytest
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from tests.kind import gateway

pytestmark = [
    pytest.mark.kind,
    pytest.mark.criterion("ticketscope--e4-s7--AC-1"),
]

NAMESPACE = os.environ.get("TICKETSCOPE_NAMESPACE", "ticketscope")
API = "deployment/ticketscope-api"
MCP = "deployment/ticketscope-mcp"
API_TIMEOUT_SECONDS = 10  # chart default for mcp.apiTimeoutSeconds
MARGIN_SECONDS = 10
RESTORE_TIMEOUT = "300s"


def _kubectl(*args: str) -> str:
    return subprocess.run(
        ["kubectl", "-n", NAMESPACE, *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _replicas(target: str, field: str) -> int:
    return int(_kubectl("get", target, "-o", f"jsonpath={{{field}}}") or 0)


@pytest.fixture(scope="module")
def api_at_zero() -> Iterator[None]:
    original = _replicas(API, ".spec.replicas")
    assert original > 0, "api must be running before the unreachable case"
    try:
        _kubectl("scale", API, "--replicas=0")
        _kubectl("rollout", "status", API, "--timeout=120s")
        yield
    finally:
        _kubectl("scale", API, f"--replicas={original}")
        _kubectl("rollout", "status", API, f"--timeout={RESTORE_TIMEOUT}")
        _kubectl("wait", "--for=condition=Available", API, f"--timeout={RESTORE_TIMEOUT}")


@asynccontextmanager
async def _client() -> AsyncIterator[Client]:
    url, host = gateway()
    async with (
        httpx2.AsyncClient(headers={"Host": host}, timeout=60) as http,
        Client(streamable_http_client(f"{url}/mcp", http_client=http)) as client,
    ):
        yield client


def test_mcp_stays_ready_and_both_tools_return_the_unreachable_detail(api_at_zero: None) -> None:
    assert _replicas(MCP, ".status.readyReplicas") == _replicas(MCP, ".spec.replicas")

    async def call(tool: str, arguments: dict[str, Any]) -> Any:
        async with _client() as client:
            return await client.call_tool(tool, arguments)

    for tool, arguments in (
        ("search_similar_issues", {"query": "game crashes", "mode": "keyword"}),
        ("get_issue", {"key": "MCL-1"}),
    ):
        started = time.monotonic()
        result = asyncio.run(call(tool, arguments))
        elapsed = time.monotonic() - started
        # A tool error, not a Gateway 503 (which would raise on the transport).
        assert result.is_error, result
        [block] = result.content
        assert block.text.startswith("ticketscope API unreachable:"), block.text
        assert elapsed < API_TIMEOUT_SECONDS + MARGIN_SECONDS, elapsed
