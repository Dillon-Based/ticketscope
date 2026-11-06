"""Release notes and attribution (story 13; test design P2 "Release notes report" case 2,
"no identities" case 5)."""

import json
from pathlib import Path
from typing import Any

import pytest

from tests.target import REPO
from ticketscope.jobs.ingest import jira
from ticketscope.jobs.ingest import main as ingest
from ticketscope.jobs.ingest.notes import ATTRIBUTION, main, render_notes

SLICE = Path(__file__).parent / "ingest" / "slice.json"
TERMS = (
    REPO
    / "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets"
    / "spike-choose-the-jira-corpus-findings/terms.md"
)
COMMIT = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def report(tmp_path: Path) -> dict[str, Any]:
    docs = json.loads(SLICE.read_text(encoding="utf-8"))
    selection = jira.select(docs, exclusions=frozenset({"MCL-40", "REALMS-10"}))
    return ingest.write_outputs(tmp_path, "2026.11.1", selection)


def test_notes_state_subset_counts_pairs_kinds_and_load_time(report: dict[str, Any]) -> None:
    notes = render_notes(report, 3.9, COMMIT, "owner/name")
    assert "Corpus snapshot 2026.11.1 (schema v2): Mojang projects MCL, REALMS, MCD" in notes
    assert "- Issues: 12 (1 unresolved duplicate targets; 2 excluded" in notes
    assert "- In-subset duplicate pairs: 2 (1 short, 1 log-heavy)" in notes
    assert "- Kind split at threshold 3: 10 short, 2 log-heavy" in notes
    assert "- Timed load into the in-repo Postgres image: 3.9 s (budget 600 s)" in notes
    assert f"`{COMMIT}`" in notes
    assert report["sha256"] in notes
    assert "https://github.com/owner/name/issues" in notes


def test_notes_carry_the_attribution_line(report: dict[str, Any]) -> None:
    assert ATTRIBUTION in render_notes(report, 1.0, COMMIT)


def test_readme_carries_the_attribution_line() -> None:
    assert ATTRIBUTION in (REPO / "README.md").read_text(encoding="utf-8")


def test_attribution_is_spike_12s_line() -> None:
    terms = TERMS.read_text(encoding="utf-8")
    quoted = next(line for line in terms.splitlines() if line.startswith("> Issue text from"))
    assert quoted.removeprefix("> ") == ATTRIBUTION


@pytest.mark.parametrize("seconds", [600.5, 1200.0, float("nan"), -1.0])
def test_notes_refuse_a_load_over_budget_or_invalid(report: dict[str, Any], seconds: float) -> None:
    with pytest.raises(ValueError):
        render_notes(report, seconds, COMMIT)


def test_notes_accept_the_budget_exactly(report: dict[str, Any]) -> None:
    assert "600 s (budget 600 s)" in render_notes(report, 600.0, COMMIT)


def test_cli_exits_non_zero_over_budget(
    tmp_path: Path, report: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "report.json"
    assert main(["--report", str(path), "--load-seconds", "601", "--commit", COMMIT]) == 1
    assert capsys.readouterr().out == ""
    assert main(["--report", str(path), "--load-seconds", "4.2", "--commit", COMMIT]) == 0
    assert ATTRIBUTION in capsys.readouterr().out
