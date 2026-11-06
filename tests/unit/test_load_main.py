"""`load`'s exit status: non-zero when the write fails or a line is not schema v2, zero
with every issue written."""

import gzip
import json
from collections.abc import Iterable
from pathlib import Path

import pytest

from ticketscope.adapters.postgres import IssueRow
from ticketscope.jobs.load import main as load


@pytest.fixture(autouse=True)
def _no_database(snapshot_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_DIR", str(snapshot_dir))

    def no_wait(conninfo: str, *, role: str | None, timeout_s: float) -> None:
        return None

    monkeypatch.setattr(load, "wait_for_database", no_wait)


def test_load_exits_non_zero_when_the_write_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_replace(conninfo: str, version: str, rows: Iterable[IssueRow]) -> int:
        list(rows)
        raise RuntimeError("write failed")

    monkeypatch.setattr(load, "replace_corpus", failing_replace)
    assert load.main() == 1


def test_load_exits_zero_with_every_fixture_issue(monkeypatch: pytest.MonkeyPatch) -> None:
    written: list[IssueRow] = []
    versions: list[str] = []

    def fake_replace(conninfo: str, version: str, rows: Iterable[IssueRow]) -> int:
        versions.append(version)
        written.extend(rows)
        return len(written)

    monkeypatch.setattr(load, "replace_corpus", fake_replace)
    assert load.main() == 0
    assert versions == ["fixture"]
    assert len({row.number for row in written}) == len(written) == 8


def test_load_exits_non_zero_on_a_v1_snapshot(
    snapshot_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    v1 = {
        "number": 900001,
        "url": "https://github.com/kubernetes/kubernetes/issues/900001",
        "title": "v1",
        "body": None,
        "state": "closed",
        "state_reason": "completed",
        "created_at": "2025-01-01T00:00:00Z",
        "closed_at": "2025-01-02T00:00:00Z",
        "labels": [],
        "comments": [],
        "timeline": [],
    }
    with gzip.open(snapshot_dir / "fixture.jsonl.gz", "wt", encoding="utf-8") as f:
        f.write(json.dumps(v1) + "\n")
    written: list[IssueRow] = []

    def fake_replace(conninfo: str, version: str, rows: Iterable[IssueRow]) -> int:
        written.extend(rows)
        return len(written)

    monkeypatch.setattr(load, "replace_corpus", fake_replace)
    assert load.main() == 1
    assert written == []
