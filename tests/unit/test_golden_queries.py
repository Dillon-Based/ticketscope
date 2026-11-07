"""The R-004 golden-query file (story 5): its shape, its pin, and that every source and
expected issue exists in the pinned asset.

Story 11 gates on the twins through `/v1/search`; this is only the file check. The asset is
downloaded once per session through `fetch_snapshot` (network, checksum-verified).
"""

import gzip
import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests.target import REPO, snapshot_pin
from ticketscope.adapters.release import fetch_snapshot

GOLDEN = REPO / "eval" / "golden-queries.json"
ENTRY_FIELDS = {
    "id",
    "kind",
    "query",
    "chosen_by",
    "source_issue",
    "expected_issue",
    "known_keyword_miss",
}
# `C:\Users\<name>`, `/Users/<name>`, `/home/<name>`: OS user-name paths.
_USER_PATH = re.compile(r"[A-Za-z]:\\\\?Users\\|/Users/|/home/", re.IGNORECASE)


def _golden() -> dict[str, Any]:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def pinned_keys(tmp_path_factory: pytest.TempPathFactory) -> dict[int, str]:
    """Issue number -> key of every issue in the pinned asset."""
    pin = snapshot_pin()
    path = fetch_snapshot(
        pin["baseUrl"],
        pin["version"],
        tmp_path_factory.mktemp("pinned"),
        pin["sha256"],
        timeout=120,
    )
    keys: dict[int, str] = {}
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        for line in lines:
            record = json.loads(line)
            keys[record["number"]] = record["key"]
    return keys


def test_file_is_pinned_to_the_chart_snapshot() -> None:
    golden = _golden()
    assert golden["snapshot_version"] == snapshot_pin()["version"]
    assert golden["mode"] == "keyword"
    assert golden["k"] == 10


def test_entries_have_every_field_and_both_kinds() -> None:
    entries = _golden()["queries"]
    for entry in entries:
        assert set(entry) == ENTRY_FIELDS, entry["id"]
        assert entry["query"].strip()
        assert entry["chosen_by"].strip()
        assert isinstance(entry["known_keyword_miss"], bool)
        for side in ("source_issue", "expected_issue"):
            assert set(entry[side]) == {"number", "key"}
    assert len({e["id"] for e in entries}) == len(entries)
    assert {e["kind"] for e in entries} == {"short", "log_heavy"}


def test_expected_issue_differs_from_its_source() -> None:
    for entry in _golden()["queries"]:
        source, expected = entry["source_issue"], entry["expected_issue"]
        assert source["number"] != expected["number"], entry["id"]
        assert source["key"] != expected["key"], entry["id"]


def test_file_holds_no_os_user_name_path() -> None:
    assert not _USER_PATH.search(GOLDEN.read_text(encoding="utf-8"))


def test_source_and_expected_issues_exist_in_the_pinned_asset(
    pinned_keys: dict[int, str],
) -> None:
    for entry in _golden()["queries"]:
        for side in ("source_issue", "expected_issue"):
            issue = entry[side]
            assert pinned_keys.get(issue["number"]) == issue["key"], (entry["id"], side)


def test_user_path_pattern_catches_the_shapes_it_names(tmp_path: Path) -> None:
    for text in (r"C:\Users\someone\AppData", "/Users/someone/Library", "/home/someone/.x"):
        assert _USER_PATH.search(json.dumps(text)), text
