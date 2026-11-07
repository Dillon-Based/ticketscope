"""`load` over its I/O matrix (story 5), with the database and the Release faked.

The fixture asset sits in `snapshot_dir`, so `fetch_snapshot` takes its local-file path;
the download rows wrap it with an `httpx2.MockTransport`.
"""

import gzip
import json
import logging
import re
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path

import httpx2
import pytest

from tests.target import fixture_kinds
from ticketscope.adapters import release
from ticketscope.adapters.postgres import CorpusMeta, IssueRow
from ticketscope.core import derive
from ticketscope.jobs.load import main as load

PRE = derive.preprocessing_version()


class FakeDb:
    """`corpus_meta` plus the issue rows, as `read_corpus_meta` / `replace_corpus` see them."""

    def __init__(self, meta: CorpusMeta | None = None, rows: list[IssueRow] | None = None):
        self.meta = meta
        self.rows = rows or []
        self.replace_calls = 0
        self.fail_write = False

    def read_corpus_meta(self, conninfo: str) -> CorpusMeta | None:
        return self.meta

    def replace_corpus(self, conninfo: str, meta: CorpusMeta, rows: Iterable[IssueRow]) -> int:
        self.replace_calls += 1
        new = list(rows)
        if self.fail_write:
            raise RuntimeError("write failed")
        self.meta, self.rows = meta, new
        return len(new)


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch) -> FakeDb:
    fake = FakeDb()
    monkeypatch.setattr(load, "read_corpus_meta", fake.read_corpus_meta)
    monkeypatch.setattr(load, "replace_corpus", fake.replace_corpus)
    return fake


@pytest.fixture(autouse=True)
def _env(snapshot_dir: Path, fixture_sha256: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_DIR", str(snapshot_dir))
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_VERSION", "fixture")
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", fixture_sha256)
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_BASE_URL", "https://releases.invalid/download")

    def no_wait(conninfo: str, *, role: str | None, timeout_s: float) -> None:
        return None

    monkeypatch.setattr(load, "wait_for_database", no_wait)


@pytest.fixture
def fetches(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Records each `fetch_snapshot` call's version, then fetches for real."""
    calls: list[str] = []
    real = load.fetch_snapshot

    def spy(base_url: str, version: str, dest_dir: Path, sha256: str, *, timeout: float) -> Path:
        calls.append(version)
        return real(base_url, version, dest_dir, sha256, timeout=timeout)

    monkeypatch.setattr(load, "fetch_snapshot", spy)
    return calls


def _old_corpus() -> FakeDb:
    old_row = IssueRow(
        number=1,
        title="old",
        body=None,
        url="https://bugs.mojang.com/browse/MCL-1",
        state="open",
        state_reason=None,
        created_at=datetime(2020, 1, 1, tzinfo=UTC),
        closed_at=None,
        kind="short",
        outcome_status="unknown",
        outcome_summary=None,
        outcome_source=None,
        outcome_ref=None,
        search_text="old",
    )
    return FakeDb(CorpusMeta("2026.10.1", None, "pre0.old"), [old_row])


def _use(db: FakeDb, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(load, "read_corpus_meta", db.read_corpus_meta)
    monkeypatch.setattr(load, "replace_corpus", db.replace_corpus)


# --- first load, kinds, report ---------------------------------------------------------------


def test_first_load_writes_every_issue_with_core_kind_and_outcome(
    db: FakeDb, fetches: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    assert fetches == ["fixture"]
    assert db.meta == CorpusMeta("fixture", None, PRE)
    assert PRE == "pre1.kind2-t3.outcome3"
    assert len({row.number for row in db.rows}) == len(db.rows) == 8
    assert all(row.outcome_status != "unknown" for row in db.rows)
    assert "reloading snapshot fixture: no corpus loaded" in caplog.text


def test_computed_fixture_kinds_equal_the_expected_kinds(db: FakeDb) -> None:
    assert load.main() == 0
    assert {row.number: row.kind for row in db.rows} == fixture_kinds()


def test_story_1_row_reloads_for_the_preprocessing_version(
    monkeypatch: pytest.MonkeyPatch, fetches: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    db = FakeDb(CorpusMeta("fixture", None, None))
    _use(db, monkeypatch)
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    assert fetches == ["fixture"]
    assert "reloading" in caplog.text
    assert "preprocessing_version None -> 'pre1.kind2-t3.outcome3'" in caplog.text
    assert db.meta == CorpusMeta("fixture", None, PRE)


def test_report_line_has_count_shares_time_and_budget(
    db: FakeDb, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    [record] = [r for r in caplog.records if r.getMessage().startswith("load report:")]
    line = record.getMessage()
    assert record.levelno == logging.INFO
    assert "issues=8" in line
    # 4 of 8 fixture issues are log-heavy.
    assert "kind.short=50.0%" in line and "kind.log_heavy=50.0%" in line
    outcomes = dict(re.findall(r"outcome\.(\w+)=([\d.]+)%", line))
    assert set(outcomes) == {"fixed", "duplicate", "not_planned", "stale", "answered", "unknown"}
    assert outcomes["stale"] == outcomes["unknown"] == "0.0"
    assert sum(float(v) for v in outcomes.values()) == pytest.approx(100.0, abs=0.2)
    assert re.search(r"load_seconds=\d+\.\d budget_seconds=600 within_budget=true$", line)


def test_report_over_budget_is_a_warning(
    db: FakeDb, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(load, "BUDGET_SECONDS", -1)
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    [record] = [r for r in caplog.records if r.getMessage().startswith("load report:")]
    assert record.levelno == logging.WARNING
    assert record.getMessage().endswith("within_budget=false")


# --- no-op and reload ------------------------------------------------------------------------


def test_same_pin_is_a_no_op(
    monkeypatch: pytest.MonkeyPatch, fetches: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    db = FakeDb(CorpusMeta("fixture", None, PRE))
    _use(db, monkeypatch)
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    assert "no-op" in caplog.text
    assert fetches == []
    assert db.replace_calls == 0


def test_changed_derivation_reloads(
    monkeypatch: pytest.MonkeyPatch, fetches: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    db = FakeDb(CorpusMeta("fixture", None, PRE))
    _use(db, monkeypatch)
    monkeypatch.setattr(derive, "derivation_version", lambda threshold=3: "kind9-t3.outcome9")
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    assert "reloading" in caplog.text and "preprocessing_version" in caplog.text
    assert fetches == ["fixture"]
    assert db.meta == CorpusMeta("fixture", None, "pre1.kind9-t3.outcome9")


def test_changed_snapshot_version_reloads(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    db = FakeDb(CorpusMeta("2026.10.1", None, PRE))
    _use(db, monkeypatch)
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    assert "snapshot_version '2026.10.1' -> 'fixture'" in caplog.text


# --- refusals: the old corpus stays ---------------------------------------------------------


def test_wrong_checksum_exits_1_and_keeps_the_corpus(
    monkeypatch: pytest.MonkeyPatch, fixture_sha256: str, caplog: pytest.LogCaptureFixture
) -> None:
    db = _old_corpus()
    before = (db.meta, list(db.rows))
    _use(db, monkeypatch)
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", "0" * 64)
    assert load.main() == 1
    assert db.replace_calls == 0
    assert (db.meta, db.rows) == before
    assert "0" * 64 in caplog.text and fixture_sha256 in caplog.text


def test_wrong_checksum_on_download_exits_1_and_keeps_the_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    db = _old_corpus()
    before = (db.meta, list(db.rows))
    _use(db, monkeypatch)
    empty = tmp_path / "download"
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_DIR", str(empty))
    _serve(monkeypatch, lambda request: httpx2.Response(200, content=b"tampered"))
    assert load.main() == 1
    assert db.replace_calls == 0
    assert (db.meta, db.rows) == before
    assert list(empty.iterdir()) == []
    assert "does not match the pinned" in caplog.text


def test_empty_pin_exits_1_before_anything(
    monkeypatch: pytest.MonkeyPatch, fetches: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    db = _old_corpus()
    _use(db, monkeypatch)
    monkeypatch.delenv("TICKETSCOPE_SNAPSHOT_SHA256")

    def must_not_wait(conninfo: str, *, role: str | None, timeout_s: float) -> None:
        raise AssertionError("waited for the database with no pin")

    monkeypatch.setattr(load, "wait_for_database", must_not_wait)
    assert load.main() == 1
    assert fetches == []
    assert db.replace_calls == 0
    assert "TICKETSCOPE_SNAPSHOT_SHA256" in caplog.text


def test_download_failure_exits_1_removes_the_partial_file_and_keeps_the_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    db = _old_corpus()
    before = (db.meta, list(db.rows))
    _use(db, monkeypatch)
    empty = tmp_path / "download"
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_DIR", str(empty))
    _serve(monkeypatch, lambda request: httpx2.Response(502, content=b"bad gateway"))
    assert load.main() == 1
    assert db.replace_calls == 0
    assert (db.meta, db.rows) == before
    assert list(empty.iterdir()) == []
    assert "load of snapshot fixture failed" in caplog.text


def test_write_failure_exits_1(db: FakeDb) -> None:
    db.fail_write = True
    assert load.main() == 1


def test_v1_line_exits_1(
    snapshot_dir: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
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
    asset = snapshot_dir / "fixture.jsonl.gz"
    with gzip.open(asset, "wt", encoding="utf-8") as f:
        f.write(json.dumps(v1) + "\n")
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", release.sha256_file(asset))
    db = _old_corpus()
    _use(db, monkeypatch)
    assert load.main() == 1
    assert db.meta == _old_corpus().meta
    assert "fixture.jsonl.gz:1: invalid snapshot issue" in caplog.text


def _serve(
    monkeypatch: pytest.MonkeyPatch, handler: Callable[[httpx2.Request], httpx2.Response]
) -> None:
    """Route `load`'s download through an `httpx2.MockTransport`."""
    real = release.fetch_snapshot
    transport = httpx2.MockTransport(handler)

    def fetch(base_url: str, version: str, dest_dir: Path, sha256: str, *, timeout: float) -> Path:
        return real(base_url, version, dest_dir, sha256, timeout=timeout, transport=transport)

    monkeypatch.setattr(load, "fetch_snapshot", fetch)
