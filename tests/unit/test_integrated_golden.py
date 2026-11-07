"""The integrated check's golden verdict and report (story 11), without a cluster."""

from tests.factories import issue_outcome_payload
from tests.integrated.golden import (
    KNOWN_MISS_FOUND,
    GoldenRow,
    Verdict,
    page_rank,
    results_without_outcome,
    summary_table,
    twin_verdict,
)

OUTCOMES = ("fixed", "duplicate", "not_planned", "stale", "answered", "unknown")


def test_twin_found_passes_with_its_rank() -> None:
    assert twin_verdict(False, 7, [3, 5, 7, 9]) == Verdict("pass", 3, "")


def test_twin_absent_on_a_gated_entry_fails() -> None:
    assert twin_verdict(False, 7, [3, 5, 9]) == Verdict("fail", None)


def test_twin_absent_from_an_empty_result_fails() -> None:
    assert twin_verdict(False, 7, []).status == "fail"


def test_known_miss_still_absent_is_reported_not_gated() -> None:
    verdict = twin_verdict(True, 7, [3, 5, 9])
    assert (verdict.status, verdict.rank) == ("known-miss", None)
    assert verdict.note


def test_known_miss_now_found_passes_with_a_note() -> None:
    assert twin_verdict(True, 7, [7, 3]) == Verdict("pass", 1, KNOWN_MISS_FOUND)


def test_results_without_outcome_are_named() -> None:
    results: list[dict[str, object]] = [
        issue_outcome_payload(1, status="fixed"),
        issue_outcome_payload(2, status=""),
        issue_outcome_payload(3, status="wontfix"),
        {"issue": {"number": 4}, "outcome": None},
        {"issue": {"number": 5}},
    ]
    assert results_without_outcome(results, OUTCOMES) == [2, 3, 4, 5]


def test_page_rank_matches_the_key_at_the_end_of_the_href() -> None:
    hrefs = [
        "https://bugs.mojang.com/browse/MCD-64670",
        "https://bugs.mojang.com/browse/XMCD-6467",
        "https://bugs.mojang.com/browse/MCD-6467",
    ]
    assert page_rank(hrefs, "MCD-6467") == 3


def test_page_lacking_the_twin_has_no_rank() -> None:
    assert page_rank(["https://bugs.mojang.com/browse/MCD-1"], "MCD-6467") is None
    assert page_rank([], "MCD-6467") is None


def test_summary_table_reports_rank_or_absent() -> None:
    rows = [
        GoldenRow("vague", "short", "MCD-6467", Verdict("pass", 5)),
        GoldenRow("gone", "short", "MCD-1", Verdict("fail", None)),
        GoldenRow("miss", "log_heavy", "MCL-2", Verdict("known-miss", None, "not gated")),
    ]
    table = summary_table(rows, k=10, mode="keyword")
    lines = table.splitlines()
    assert lines[0] == "Golden queries (keyword, top-10)"
    assert lines[2] == "| entry | kind | expected | verdict | rank | note |"
    assert lines[4] == "| vague | short | MCD-6467 | pass | 5 |  |"
    assert lines[5] == "| gone | short | MCD-1 | fail | absent |  |"
    assert lines[6] == "| miss | log_heavy | MCL-2 | known-miss | absent | not gated |"
    assert table.endswith("\n")
