"""`load`'s exit status: non-zero when the write fails, zero with every issue written."""

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
