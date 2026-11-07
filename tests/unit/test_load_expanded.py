"""Expanded coverage for `load` (story 5): the reload decision, the report line, row
building and the preprocessing version, beyond the I/O matrix in `test_load_main.py`."""

import gzip
import logging
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import pytest

from tests.target import SNAPSHOT_DIR
from ticketscope.adapters.postgres import CorpusMeta, IssueRow
from ticketscope.core import derive
from ticketscope.core.snapshot import SnapshotIssueV2
from ticketscope.jobs.load import main as load

PRE = derive.preprocessing_version()


def _fixture_issues() -> list[SnapshotIssueV2]:
    lines = (SNAPSHOT_DIR / "fixture.jsonl").read_text(encoding="utf-8").splitlines()
    return [SnapshotIssueV2.model_validate_json(line) for line in lines if line.strip()]


# --- reload_reason ---------------------------------------------------------------------------


def test_reload_reason_is_none_when_all_three_fields_match() -> None:
    assert load.reload_reason(CorpusMeta("v", None, PRE), CorpusMeta("v", None, PRE)) is None


def test_reload_reason_with_no_row_says_nothing_is_loaded() -> None:
    assert load.reload_reason(None, CorpusMeta("v", None, PRE)) == "no corpus loaded"


def test_reload_reason_names_a_changed_embedding_model() -> None:
    reason = load.reload_reason(CorpusMeta("v", "model-a", PRE), CorpusMeta("v", None, PRE))
    assert reason == "embedding_model_id 'model-a' -> None"


def test_reload_reason_lists_every_changed_field_in_order() -> None:
    reason = load.reload_reason(
        CorpusMeta("2026.10.1", "model-a", "pre0.old"), CorpusMeta("2026.11.1", None, PRE)
    )
    assert reason == (
        "snapshot_version '2026.10.1' -> '2026.11.1'; "
        "embedding_model_id 'model-a' -> None; "
        f"preprocessing_version 'pre0.old' -> '{PRE}'"
    )


def test_pinned_meta_carries_the_pin_no_model_and_core_preprocessing() -> None:
    assert load.pinned_meta("2026.11.1") == CorpusMeta("2026.11.1", None, PRE)


# --- report_line -----------------------------------------------------------------------------


def test_report_line_for_an_empty_corpus_has_zero_shares_not_a_division_error() -> None:
    line = load.report_line("v", 0, Counter(), 1.0, 600)
    assert "issues=0" in line
    shares = re.findall(r"(?:kind|outcome)\.\w+=([\d.]+)%", line)
    assert len(shares) == 2 + 6
    assert set(shares) == {"0.0"}


def test_report_line_at_exactly_the_budget_is_within_budget() -> None:
    line = load.report_line("v", 1, Counter({"kind:short": 1, "outcome:fixed": 1}), 600.0, 600)
    assert line.endswith("load_seconds=600.0 budget_seconds=600 within_budget=true")


def test_report_line_just_over_the_budget_is_not_within_budget() -> None:
    line = load.report_line("v", 1, Counter(), 600.04, 600)
    assert line.endswith("within_budget=false")


def test_report_line_names_the_snapshot_and_rounds_shares_to_one_decimal() -> None:
    counts = Counter({"kind:short": 1, "kind:log_heavy": 2, "outcome:fixed": 3})
    line = load.report_line("2026.11.1", 3, counts, 2.25, 600)
    assert line.startswith("load report: snapshot=2026.11.1 issues=3 ")
    assert "kind.short=33.3%" in line and "kind.log_heavy=66.7%" in line
    assert "outcome.fixed=100.0%" in line


# --- read_snapshot and build_rows ------------------------------------------------------------


def test_read_snapshot_skips_blank_lines(tmp_path: Path) -> None:
    lines = (SNAPSHOT_DIR / "fixture.jsonl").read_text(encoding="utf-8").splitlines()
    asset = tmp_path / "blank.jsonl.gz"
    with gzip.open(asset, "wt", encoding="utf-8") as f:
        f.write("\n" + "\n   \n".join(lines) + "\n\n")
    assert [i.number for i in load.read_snapshot(asset)] == [i.number for i in _fixture_issues()]


def test_build_rows_maps_snapshot_fields_and_derives_with_core() -> None:
    issues = _fixture_issues()
    rows = list(load.build_rows(issues))
    assert len(rows) == len(issues)
    for issue, row in zip(issues, rows, strict=True):
        outcome = derive.derive_outcome(issue)
        assert row.number == issue.number
        assert row.title == issue.title and row.body == issue.body and row.url == issue.url
        assert row.state == issue.state
        assert row.state_reason is None
        assert row.created_at == issue.created_at
        assert row.closed_at == issue.resolved_at
        assert row.kind == derive.derive_kind(issue)
        assert (row.outcome_status, row.outcome_summary, row.outcome_source, row.outcome_ref) == (
            outcome.status,
            outcome.summary,
            outcome.source,
            outcome.ref,
        )
        assert row.search_text == derive.search_text(issue)


def test_build_rows_counts_one_kind_and_one_outcome_per_issue() -> None:
    issues = _fixture_issues()
    counts: Counter[str] = Counter()
    rows = list(load.build_rows(issues, counts))
    kinds = sum(v for k, v in counts.items() if k.startswith("kind:"))
    outcomes = sum(v for k, v in counts.items() if k.startswith("outcome:"))
    assert kinds == outcomes == len(rows)
    assert counts == Counter(
        [f"kind:{r.kind}" for r in rows] + [f"outcome:{r.outcome_status}" for r in rows]
    )


# --- preprocessing version and search text (core) --------------------------------------------


def test_preprocessing_version_changes_with_the_search_text_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(derive, "PREPROCESSING_RULE_VERSION", "pre2")
    assert derive.preprocessing_version() == f"pre2.{derive.derivation_version()}"
    assert derive.preprocessing_version() != PRE


def test_search_text_of_an_issue_without_a_body_is_the_title_and_a_blank_line() -> None:
    issue = _fixture_issues()[0].model_copy(update={"body": None})
    assert derive.search_text(issue) == f"{issue.title}\n\n"


# --- main: the embedding model is part of the no-op key --------------------------------------


class _Db:
    def __init__(self, meta: CorpusMeta | None) -> None:
        self.meta = meta
        self.replace_calls = 0

    def read(self, conninfo: str) -> CorpusMeta | None:
        return self.meta

    def replace(self, conninfo: str, meta: CorpusMeta, rows: Iterable[IssueRow]) -> int:
        self.replace_calls += 1
        n = len(list(rows))
        self.meta = meta
        return n


@pytest.fixture
def env(snapshot_dir: Path, fixture_sha256: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_DIR", str(snapshot_dir))
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_VERSION", "fixture")
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", fixture_sha256)
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_BASE_URL", "https://releases.invalid/download")
    monkeypatch.setattr(load, "wait_for_database", lambda conninfo, *, role, timeout_s: None)


def _use(db: _Db, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(load, "read_corpus_meta", db.read)
    monkeypatch.setattr(load, "replace_corpus", db.replace)


@pytest.mark.usefixtures("env")
def test_a_corpus_with_an_embedding_model_reloads_to_none(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    db = _Db(CorpusMeta("fixture", "some-model", PRE))
    _use(db, monkeypatch)
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    assert "reloading snapshot fixture: embedding_model_id 'some-model' -> None" in caplog.text
    assert db.replace_calls == 1
    assert db.meta == CorpusMeta("fixture", None, PRE)


@pytest.mark.usefixtures("env")
def test_no_op_runs_before_the_pin_is_checked_against_the_asset(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A matching row short-circuits before any fetch, so a mismatched local asset is never
    read on an unchanged upgrade."""
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", "f" * 64)
    db = _Db(CorpusMeta("fixture", None, PRE))
    _use(db, monkeypatch)

    def no_fetch(*args: object, **kwargs: object) -> Path:
        raise AssertionError("fetched on a no-op")

    monkeypatch.setattr(load, "fetch_snapshot", no_fetch)
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    assert "no-op" in caplog.text
    assert db.replace_calls == 0


@pytest.mark.usefixtures("env")
def test_db_unreachable_exits_1_without_fetching(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def down(conninfo: str, *, role: str | None, timeout_s: float) -> None:
        raise TimeoutError("database not ready")

    def no_fetch(*args: object, **kwargs: object) -> Path:
        raise AssertionError("fetched with no database")

    monkeypatch.setattr(load, "wait_for_database", down)
    monkeypatch.setattr(load, "fetch_snapshot", no_fetch)
    assert load.main() == 1
    assert "load of snapshot fixture failed; previous corpus kept" in caplog.text


@pytest.mark.usefixtures("env")
def test_whitespace_only_pin_exits_1(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", "   ")
    db = _Db(None)
    _use(db, monkeypatch)
    assert load.main() == 1
    assert db.replace_calls == 0
    assert "TICKETSCOPE_SNAPSHOT_SHA256 is empty" in caplog.text


@pytest.mark.usefixtures("env")
def test_main_silences_httpx2_request_logging() -> None:
    db = _Db(CorpusMeta("fixture", None, PRE))
    logging.getLogger("httpx2").setLevel(logging.INFO)
    with pytest.MonkeyPatch.context() as mp:
        _use(db, mp)
        assert load.main() == 0
    assert logging.getLogger("httpx2").level == logging.WARNING
