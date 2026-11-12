"""Claude Desktop's captured requests, replayed against `/mcp` on kind (story 4.2, R4, R-003, C-9).

The fixtures in `captured/` are what Claude Desktop sent through the tunnel on 2026-11-11, with the
headers that matter and none that identify a person or carry a credential. They speak the stateless
2026-07-28 protocol: `server/discover` rather than `initialize`. Later stories do not edit them
(`tests/unit/test_mcp_captured_pin.py` pins their bytes); an edit is a review finding.

Needs `TICKETSCOPE_GATEWAY_URL` and `TICKETSCOPE_GATEWAY_HOST`, like the other tests here. Each
request is sent with the tunnel host (`TICKETSCOPE_TUNNEL_HOST`, default the stand-in), so the
replay also proves the tunnel's admission path.
"""

import json
import os
from pathlib import Path
from typing import Any

import httpx2
import pytest

pytestmark = pytest.mark.kind

CAPTURED = Path(__file__).parent / "captured"
# The stand-in in kind values; locally, the host kind-up.sh was given as TUNNEL_HOSTNAME.
TUNNEL_HOST = os.environ.get("TICKETSCOPE_TUNNEL_HOST", "tunnel.ticketscope.test")
REPLAYS = 6  # past the two replicas, so each one answers


def _fixtures() -> list[Path]:
    return sorted(CAPTURED.glob("*.json"))


def _send(fixture: Path) -> dict[str, Any]:
    url = os.environ.get("TICKETSCOPE_GATEWAY_URL")
    if not url:
        pytest.fail("TICKETSCOPE_GATEWAY_URL must be set")
    captured = json.loads(fixture.read_text())
    headers = {**captured["headers"], "Host": TUNNEL_HOST}
    response = httpx2.post(
        f"{url.rstrip('/')}/mcp", headers=headers, json=captured["body"], timeout=60
    )
    assert response.status_code == 200, (fixture.name, response.status_code, response.text)
    text = response.text
    if response.headers.get("content-type", "").startswith("text/event-stream"):
        text = next(line for line in text.splitlines() if line.startswith("data: "))[
            len("data: ") :
        ]
    message = json.loads(text)
    assert message["id"] == captured["body"]["id"], message
    assert "error" not in message, message
    return message["result"]


def test_the_captured_set_covers_the_handshake_and_both_tool_requests() -> None:
    names = {path.stem for path in _fixtures()}
    assert {"server-discover", "tools-list", "tools-call"} <= names


@pytest.mark.parametrize("fixture", _fixtures(), ids=lambda path: path.stem)
def test_every_captured_request_is_answered_on_every_replica(fixture: Path) -> None:
    for _ in range(REPLAYS):
        _send(fixture)


def test_the_discover_response_serves_the_protocol_version_claude_desktop_sends() -> None:
    captured = json.loads((CAPTURED / "server-discover.json").read_text())
    version = captured["headers"]["Mcp-Protocol-Version"]
    result = _send(CAPTURED / "server-discover.json")
    assert version in result["supportedVersions"]


def test_tools_list_returns_the_tool_with_its_schemas() -> None:
    result = _send(CAPTURED / "tools-list.json")
    assert {t["name"] for t in result["tools"]} == {"search_similar_issues", "get_issue"}
    [tool] = [t for t in result["tools"] if t["name"] == "search_similar_issues"]
    assert tool["inputSchema"]["required"] == ["query"]
    assert tool["outputSchema"]["required"] == ["mode", "score_kind", "corpus_version", "results"]


def test_tools_call_returns_structured_content_and_a_text_block_of_the_same_json() -> None:
    result = _send(CAPTURED / "tools-call.json")
    assert result.get("isError") is False
    structured = result["structuredContent"]
    assert structured["results"], "the corpus answers the captured question"
    [block] = result["content"]
    assert block["type"] == "text"
    assert json.loads(block["text"]) == structured
