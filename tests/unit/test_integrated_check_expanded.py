"""Expanded coverage for the integrated check (story 11), without a cluster.

Guards the parts a kind run would only catch late: the md5 digest matching Postgres'
`string_agg(... ORDER BY number)`, the five-check module shape, the CI job wiring, the
golden report, and helper edge cases.
"""

import ast
import hashlib
from pathlib import Path

import pytest

import tests.integrated.test_done_when as done_when
from tests.integrated.golden import GoldenRow, Verdict, page_rank, summary_table, twin_verdict
from tests.target import REPO

MODULE = REPO / "tests" / "integrated" / "test_done_when.py"
CI = REPO / ".github" / "workflows" / "ci.yml"


# P1: check (1) digest equals Postgres md5(string_agg(number::text, ',' ORDER BY number))
def test_numbers_digest_sorts_numerically_like_postgres() -> None:
    expected = hashlib.md5(b"9,10,100", usedforsecurity=False).hexdigest()
    assert done_when._numbers_digest([100, 9, 10]) == expected


def test_numbers_digest_is_order_independent_and_sensitive_to_members() -> None:
    assert done_when._numbers_digest([3, 1, 2]) == done_when._numbers_digest([1, 2, 3])
    assert done_when._numbers_digest([1, 2, 3]) != done_when._numbers_digest([1, 2, 4])


def test_sql_list_quotes_each_value() -> None:
    assert done_when._sql_list(("short", "log_heavy")) == "'short', 'log_heavy'"


def test_kinds_come_from_the_contract() -> None:
    assert set(done_when.KINDS) == {"short", "log_heavy"}


# P1: exactly five kind checks, in Done-when order, none imported from smoke
def test_module_has_exactly_five_checks_in_order() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    names = [
        n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")
    ]
    assert names == [
        "test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2",
        "test_every_loaded_issue_has_a_valid_kind_and_outcome",
        "test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page",
        "test_one_search_reaches_tempo_as_the_ad10_tree",
        "test_an_on_demand_backup_completes_to_seaweedfs",
    ]
    imported = [alias.name for n in tree.body if isinstance(n, ast.ImportFrom) for alias in n.names]
    assert not [i for i in imported if i.startswith("test_")]


def test_module_is_marked_kind() -> None:
    marks = done_when.pytestmark
    marks = marks if isinstance(marks, list) else [marks]
    assert any(m.name == "kind" for m in marks)


# P1: CI wiring — one kind job named integrated-check, integrated before smoke
def test_ci_runs_integrated_then_smoke_in_one_kind_job() -> None:
    text = CI.read_text(encoding="utf-8")
    assert "\n  integrated-check:\n" in text
    assert "\n  kind-deploy:\n" not in text
    assert text.count("uses: ./.github/workflows/_kind-deploy.yml") == 1
    assert "check: uv run pytest -m kind tests/integrated tests/smoke" in text


# P2: the golden report goes to the job summary only when CI sets it
def test_report_appends_table_to_github_step_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    summary = tmp_path / "summary.md"
    summary.write_text("before\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    done_when._report("TABLE\n", capsys)
    done_when._report("TABLE\n", capsys)
    text = summary.read_text(encoding="utf-8")
    assert text.startswith("before\n")
    assert text.count("### Integrated check: TABLE") == 2


def test_report_without_step_summary_writes_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.chdir(tmp_path)
    done_when._report("TABLE\n", capsys)
    assert list(tmp_path.iterdir()) == []


# P2: helper edge cases
def test_twin_verdict_reports_the_first_rank_on_duplicates() -> None:
    assert twin_verdict(False, 7, [7, 7]).rank == 1
    assert twin_verdict(False, 7, [1, 2, 3, 4, 5, 6, 8, 9, 10, 7]).rank == 10


def test_page_rank_ignores_a_trailing_slash() -> None:
    assert page_rank(["https://x/browse/MCL-602/"], "MCL-602") == 1


def test_summary_table_with_no_rows_has_only_the_header() -> None:
    lines = summary_table([], k=10, mode="keyword").splitlines()
    assert len(lines) == 4


def test_summary_table_row_count_matches_rows() -> None:
    rows = [GoldenRow(str(i), "short", f"MCD-{i}", Verdict("pass", i)) for i in range(1, 4)]
    assert len(summary_table(rows, k=10, mode="keyword").splitlines()) == 7
