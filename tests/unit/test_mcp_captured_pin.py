"""Claude Desktop's captured requests are frozen (story 4.2, test design: Independent Oracles).

They are the oracle for what Claude Desktop really sends. Changing one to make a test pass would
defeat that, so their bytes are pinned. A later story that needs a new shape adds a fixture; editing
or deleting one of these is a review finding.
"""

import hashlib
import json

from tests.target import REPO

CAPTURED = REPO / "tests" / "mcp" / "captured"

PINNED = {
    "prompts-list.json": "166bcdf3daa82369d445f34c66703ccb0ed7e677d57908c9bc39dfcc491d0552",
    "resources-list.json": "6b4684524f1902f5ad47c0bd228ac88695c1bb5d7563029e6cdcb8937b7575f9",
    "server-discover.json": "30f637f98e8c666ddf5d1a923862af371d8d4aa03344a502a251acc2f94acfee",
    "tools-call.json": "063f4f98ecfb8c56dd920288d813b44477ea5c771763e60e836d01ffe249b4ee",
    "tools-list.json": "9fe6e64cf6997ca3d027b5b2cdb54a30768192f23e8105c6b178a28701005f5d",
}

# Headers a person or a credential could ride on; none may be captured.
FORBIDDEN_HEADERS = {"authorization", "cookie", "x-forwarded-for", "host", "proxy-authorization"}


def test_the_captured_requests_are_unchanged() -> None:
    found = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in CAPTURED.glob("*.json")
    }
    for name, digest in PINNED.items():
        assert found.get(name) == digest, f"{name} changed or is missing: a review finding"


def test_no_captured_request_carries_a_credential() -> None:
    for path in CAPTURED.glob("*.json"):
        headers = {name.lower() for name in json.loads(path.read_text())["headers"]}
        assert not headers & FORBIDDEN_HEADERS, path.name
        assert "bearer " not in path.read_text().lower(), path.name


def test_each_captured_request_names_the_protocol_version_claude_desktop_sent() -> None:
    for path in CAPTURED.glob("*.json"):
        captured = json.loads(path.read_text())
        assert captured["headers"]["Mcp-Protocol-Version"] == "2026-07-28", path.name
