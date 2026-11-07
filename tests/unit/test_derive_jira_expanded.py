"""Expanded coverage for story 14's Jira outcome and kind rules (test design R2).

Beside `test_derive_jira.py`, which holds the ticket's matrix: the full resolution
table against spike 12, the per-class `/v1` source, kind on a Jira body, the answered
rule's edges, AD-26 tie-breaks, the toggle regex's edges and the v2 model's contract.
Priority tags follow the epic test design: [P1] for R2 rules, [P2] for edges.
"""

import ast
import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from ticketscope.core.derive import (
    MOJANG_BROWSE_URL,
    RESOLUTION_OUTCOME,
    UNKNOWN,
    derivation_version,
    derive_kind,
    derive_outcome,
    duplicate_target,
    jira_to_fences,
    kind_score,
)
from ticketscope.core.snapshot import (
    DuplicateLink,
    JiraComment,
    SnapshotIssueV2,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SPIKE_MEASURE = (
    REPO_ROOT
    / "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets"
    / "spike-choose-the-jira-corpus-findings/measure.py"
)

CREATED = datetime(2025, 1, 1, tzinfo=UTC)
RESOLVED = datetime(2025, 1, 10, tzinfo=UTC)

# outcome-mapping.md: values left `unknown` because they say nothing about the outcome.
UNMAPPED_IN_DUMP = [
    "REMIND",
    "Accepted",
    "Triaged",
    "Errata",
    "Known Error",
    "Stop Dots",
    "BugzillaOrphan",
    "Roadmap Candidate",
    "Unresolved",
]

EXPECTED_SOURCE = {
    "duplicate": "label",
    "fixed": None,
    "not_planned": None,
    "stale": None,
    "answered": "closing_comment",
}


# --- factories ------------------------------------------------------------------------------


def make_jira_issue(**overrides: Any) -> SnapshotIssueV2:
    fields: dict[str, Any] = {
        "schema_version": 2,
        "number": 200,
        "key": "MCL-200",
        "url": "https://bugs.mojang.com/browse/MCL-200",
        "title": "synthetic",
        "body": "A plain line.",
        "issue_type": "Bug",
        "state": "closed",
        "resolution": "Fixed",
        "created_at": CREATED,
        "resolved_at": RESOLVED,
        "comments": [],
        "duplicate_links": [],
    }
    fields.update(overrides)
    return SnapshotIssueV2(**fields)


def jira_comment(when: datetime, *, from_reporter: bool, body: str = "a comment") -> JiraComment:
    return JiraComment(body=body, created_at=when, from_reporter=from_reporter)


def dup_link(
    number: int,
    direction: str = "duplicates",
    *,
    key: str | None = None,
    link_type: str = "Duplicate",
) -> DuplicateLink:
    return DuplicateLink(
        target_number=number,
        target_key=key if key is not None else f"MCL-{number}",
        direction=direction,  # type: ignore[arg-type]
        link_type=link_type,
    )


def answered_question(**overrides: Any) -> SnapshotIssueV2:
    fields: dict[str, Any] = {
        "issue_type": "Question",
        "resolution": "Done",
        "comments": [jira_comment(datetime(2025, 1, 5, tzinfo=UTC), from_reporter=False)],
    }
    fields.update(overrides)
    return make_jira_issue(**fields)


def spike_resolution_table() -> dict[str, str]:
    """`RESOLUTION_OUTCOME` read from the spike's measure.py as a literal, never executed."""
    tree = ast.parse(SPIKE_MEASURE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "RESOLUTION_OUTCOME"
            and node.value is not None
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("RESOLUTION_OUTCOME not found in the spike's measure.py")


# --- the resolution table -------------------------------------------------------------------


def test_resolution_table_matches_spike_12_verbatim() -> None:
    """[P1] Core's mapping is the spike's `RESOLUTION_OUTCOME`, entry for entry."""
    if not SPIKE_MEASURE.exists():
        pytest.fail(f"spike 12's measure.py is missing at {SPIKE_MEASURE}")
    assert spike_resolution_table() == RESOLUTION_OUTCOME


def test_resolution_table_keys_are_normalised() -> None:
    """[P1] Every key is already trimmed and lower-cased, so the lookup can reach it."""
    for key in RESOLUTION_OUTCOME:
        assert key == key.strip().lower(), key


@pytest.mark.parametrize(("resolution", "status"), sorted(RESOLUTION_OUTCOME.items()))
def test_every_mapped_resolution_yields_its_class_and_source(resolution: str, status: str) -> None:
    """[P1] Each table entry, title-cased as Jira writes it, on a Bug with no links."""
    jira_value = resolution.title()
    outcome = derive_outcome(make_jira_issue(resolution=jira_value))
    assert outcome.status == status
    assert outcome.source == EXPECTED_SOURCE[status]
    assert outcome.ref is None
    if status == "duplicate":
        assert outcome.summary == "Resolved as duplicate"
    else:
        assert outcome.summary == f"Resolved as {jira_value}"


@pytest.mark.parametrize("resolution", UNMAPPED_IN_DUMP)
def test_unmapped_values_from_the_dump_are_unknown(resolution: str) -> None:
    """[P1] outcome-mapping.md's deliberately unmapped values read `unknown`, no summary."""
    assert derive_outcome(make_jira_issue(resolution=resolution)) == UNKNOWN


@pytest.mark.parametrize("resolution", ["Duplicate Issue", "  DUPLICATE  ", "duplicate"])
def test_duplicate_spellings_point_at_target(resolution: str) -> None:
    """[P1] Both duplicate spellings, trimmed and case-folded, get the AD-26 ref."""
    outcome = derive_outcome(make_jira_issue(resolution=resolution, duplicate_links=[dup_link(7)]))
    assert outcome.status == "duplicate"
    assert outcome.source == "label"
    assert outcome.summary == "Duplicate of MCL-7"
    assert outcome.ref == f"{MOJANG_BROWSE_URL}MCL-7"


def test_duplicate_ref_uses_target_key_not_number() -> None:
    """[P2] The browse URL is built from the readable key (another project's, here)."""
    issue = make_jira_issue(resolution="Duplicate", duplicate_links=[dup_link(5, key="REALMS-5")])
    assert derive_outcome(issue).ref == "https://bugs.mojang.com/browse/REALMS-5"


def test_summary_keeps_resolution_as_written_but_trimmed() -> None:
    """[P2] The summary shows the resolution's own spelling, without surrounding spaces."""
    outcome = derive_outcome(make_jira_issue(resolution="  Won't Fix\t"))
    assert outcome.status == "not_planned"
    assert outcome.summary == "Resolved as Won't Fix"


def test_inner_whitespace_is_not_normalised() -> None:
    """[P2] Only the ends are trimmed: `Won't  Fix` (two spaces) is unmapped."""
    assert derive_outcome(make_jira_issue(resolution="Won't  Fix")) == UNKNOWN


# --- kind on a Jira body ---------------------------------------------------------------------


def test_v2_body_jira_toggles_are_fences() -> None:
    """[P1] `derive_kind` turns `{code}` / `{noformat}` toggles in a body into fences."""
    body = "{code}\nfoo\n{code}\n{noformat}\nbar\n{noformat}\n{code}\nbaz\n{code}"
    assert derive_kind(make_jira_issue(body=body)) == "log_heavy"


def test_v2_body_backtick_fences_still_count() -> None:
    """[P2] A Markdown fence in a Jira body counts as on GitHub."""
    body = "```\nfoo\n```\n```\nbar\n```\n```\nbaz\n```"
    assert derive_kind(make_jira_issue(body=body)) == "log_heavy"


# --- answered rule edges --------------------------------------------------------------------


@pytest.mark.parametrize(
    "issue_type", ["Question", "QUESTION", "Support", "support request", "Questions & Feedback"]
)
def test_question_or_support_type_names_match(issue_type: str) -> None:
    """[P1] The type name contains "question" or "support", in any case."""
    assert derive_outcome(answered_question(issue_type=issue_type)).status == "answered"


@pytest.mark.parametrize("issue_type", ["Bug", "Task", "Improvement", "Feature Request"])
def test_other_types_never_answered_by_rule(issue_type: str) -> None:
    """[P1] Other types with a non-reporter comment keep the resolution's class."""
    assert derive_outcome(answered_question(issue_type=issue_type)).status == "fixed"


@pytest.mark.parametrize("resolution", ["Fixed", "Resolved", "Implemented", "Next Release"])
def test_answered_rule_overrides_every_fixed_class_value(resolution: str) -> None:
    """[P1] Any fixed-class resolution on an answered Question reads `answered`."""
    outcome = derive_outcome(answered_question(resolution=resolution))
    assert outcome.status == "answered"
    assert outcome.summary == f"Answered before resolution ({resolution})"
    assert outcome.source == "closing_comment"
    assert outcome.ref is None


def test_question_without_comments_is_fixed() -> None:
    """[P1] No comment at all: the answered rule fails, `Done` reads fixed."""
    assert derive_outcome(answered_question(comments=[])).status == "fixed"


def test_question_unmapped_without_non_reporter_comment_is_unknown() -> None:
    """[P1] Unmapped resolution and no answer: plain `unknown`, no summary."""
    issue = answered_question(
        resolution="Triaged",
        comments=[jira_comment(datetime(2025, 1, 5, tzinfo=UTC), from_reporter=True)],
    )
    assert derive_outcome(issue) == UNKNOWN


def test_open_question_with_comments_is_unknown() -> None:
    """[P1] An unresolved Question is `unknown` whatever its comments."""
    issue = answered_question(state="open", resolution=None, resolved_at=None)
    assert derive_outcome(issue) == UNKNOWN


def test_closed_question_without_resolved_at_is_not_answered() -> None:
    """[P2] No resolution time means no comment can precede it (the spike's rule)."""
    assert derive_outcome(answered_question(resolved_at=None)).status == "fixed"


def test_comment_one_second_after_resolution_does_not_count() -> None:
    """[P2] The cut is inclusive at `resolved_at` and exclusive one second later."""
    late = jira_comment(RESOLVED + timedelta(seconds=1), from_reporter=False)
    assert derive_outcome(answered_question(comments=[late])).status == "fixed"


def test_comment_compared_across_time_zones() -> None:
    """[P2] An aware comment in +02:00 at the resolution instant counts as at it."""
    plus_two = timezone(timedelta(hours=2))
    same_instant = jira_comment(RESOLVED.astimezone(plus_two), from_reporter=False)
    later_wall_clock = jira_comment(
        datetime(2025, 1, 10, 1, 0, tzinfo=plus_two), from_reporter=False
    )
    assert derive_outcome(answered_question(comments=[same_instant])).status == "answered"
    # 01:00 at +02:00 is 23:00 UTC the day before, so before the resolution.
    assert derive_outcome(answered_question(comments=[later_wall_clock])).status == "answered"


@pytest.mark.parametrize("resolution", ["Support Request", "Workaround", "Explained"])
def test_answered_class_resolution_on_question_keeps_resolution_summary(resolution: str) -> None:
    """[P2] An answered-class resolution reads as the resolution, not the rule."""
    outcome = derive_outcome(answered_question(resolution=resolution))
    assert outcome.status == "answered"
    assert outcome.summary == f"Resolved as {resolution}"
    assert outcome.source == "closing_comment"


# --- duplicate target (AD-26) edges ---------------------------------------------------------


def test_duplicate_target_none_without_links() -> None:
    """[P1] A duplicate with no links has no target."""
    assert duplicate_target(make_jira_issue(resolution="Duplicate")) is None


def test_duplicate_target_none_for_unmapped_resolution() -> None:
    """[P2] Only a duplicate-class resolution has a target."""
    issue = make_jira_issue(resolution="Triaged", duplicate_links=[dup_link(7)])
    assert duplicate_target(issue) is None


def test_duplicate_target_prefers_forward_even_when_higher_number() -> None:
    """[P1] Direction precedence beats number: a `duplicates` link 900 wins over 1."""
    issue = make_jira_issue(
        resolution="Duplicate",
        duplicate_links=[dup_link(1, "duplicated_by"), dup_link(900)],
    )
    target = duplicate_target(issue)
    assert target is not None
    assert target.target_number == 900


def test_duplicate_target_tie_breaks_on_key() -> None:
    """[P2] Equal numbers in different projects resolve by key, whatever the order."""
    links = [dup_link(5, key="REALMS-5"), dup_link(5, key="MCD-5")]
    a = make_jira_issue(resolution="Duplicate", duplicate_links=links)
    b = make_jira_issue(resolution="Duplicate", duplicate_links=links[::-1])
    target_a, target_b = duplicate_target(a), duplicate_target(b)
    assert target_a == target_b
    assert target_a is not None
    assert target_a.target_key == "MCD-5"


def test_duplicate_target_resolution_trimmed_and_case_folded() -> None:
    """[P2] ` duplicate issue ` still has a target."""
    issue = make_jira_issue(resolution=" duplicate issue ", duplicate_links=[dup_link(3)])
    target = duplicate_target(issue)
    assert target is not None
    assert target.target_key == "MCL-3"


# --- derivation version ---------------------------------------------------------------------


def test_derivation_version_carries_threshold() -> None:
    """[P1] Changing the threshold changes the version, so a load reloads."""
    assert derivation_version(5) == "kind2-t5.outcome3"
    assert derivation_version(5) != derivation_version()


def test_derivation_version_rejects_threshold_below_one() -> None:
    """[P2] The version refuses the same thresholds kind does."""
    with pytest.raises(ValueError):
        derivation_version(0)


# --- Jira toggle conversion -----------------------------------------------------------------


def test_jira_to_fences_none_is_none() -> None:
    """[P2] No body stays no body."""
    assert jira_to_fences(None) is None


def test_jira_to_fences_leaves_plain_text_alone() -> None:
    """[P2] A body without toggles is returned unchanged."""
    body = "Steps:\n1. open the world\n2. {not a toggle}"
    assert jira_to_fences(body) == body


@pytest.mark.parametrize(
    "lookalike", ["{codex}", "{code-block}", "{noformatting}", "{ code }", "{code:\nx}"]
)
def test_lookalike_braces_are_not_toggles(lookalike: str) -> None:
    """[P2] Only `{code}`, `{code:…}`, `{noformat}` and `{noformat:…}` are toggles."""
    assert kind_score(jira_to_fences(f"{lookalike}\nfoo\n{lookalike}")) == 0


@pytest.mark.parametrize(
    "toggle", ["{Code}", "{CODE:java}", "{noformat:title=log.txt}", "{NoFormat}"]
)
def test_toggles_any_case_and_parameters(toggle: str) -> None:
    """[P2] Case and parameters do not change what a toggle scores."""
    assert kind_score(jira_to_fences(f"{toggle}\nfoo\n{toggle}")) == 1


def test_mixed_toggle_types_close_each_other() -> None:
    """[P2] Both toggles become ``` fences, so `{code}` … `{noformat}` is one block.

    The sources do not say how Jira pairs them; this pins core's current choice.
    """
    assert kind_score(jira_to_fences("{code}\nfoo\n{noformat}")) == 1


def test_toggle_mid_line_splits_onto_own_line() -> None:
    """[P2] Text before and after an inline toggle is kept on its own lines."""
    converted = jira_to_fences("before {code}inside{code} after")
    assert converted is not None
    lines = [line for line in converted.splitlines() if line]
    assert lines == ["before ", "```", "inside", "```", " after"]


# --- the v2 model contract ------------------------------------------------------------------


def test_v2_parses_json_shaped_record() -> None:
    """[P1] A schema v2 record as JSON (RFC 3339 strings) parses into the model."""
    record = {
        "schema_version": 2,
        "number": 7,
        "key": "MCL-7",
        "url": "https://bugs.mojang.com/browse/MCL-7",
        "title": "t",
        "body": None,
        "issue_type": "Bug",
        "state": "closed",
        "resolution": "Duplicate",
        "created_at": "2025-01-01T00:00:00Z",
        "resolved_at": "2025-01-10T00:00:00Z",
        "comments": [{"body": "x", "created_at": "2025-01-02T00:00:00Z", "from_reporter": True}],
        "duplicate_links": [
            {
                "target_number": 3,
                "target_key": "MCL-3",
                "direction": "duplicates",
                "link_type": "Duplicate",
            }
        ],
    }
    issue = SnapshotIssueV2.model_validate_json(json.dumps(record))
    assert issue.resolved_at == RESOLVED
    assert derive_outcome(issue).ref == f"{MOJANG_BROWSE_URL}MCL-3"


def test_v2_rejects_other_schema_versions() -> None:
    """[P1] `schema_version` must be 2."""
    for version in (1, 3):
        with pytest.raises(ValidationError):
            make_jira_issue(schema_version=version)


def test_v2_rejects_unknown_fields() -> None:
    """[P1] Extra fields, such as a reporter id, are refused (no identity, AD-6)."""
    with pytest.raises(ValidationError):
        make_jira_issue(reporter="someone")
    with pytest.raises(ValidationError):
        JiraComment(body="x", created_at=RESOLVED, from_reporter=False, author="someone")  # type: ignore[call-arg]


def test_v2_rejects_unknown_link_direction() -> None:
    """[P2] `direction` is `duplicates` or `duplicated_by`."""
    with pytest.raises(ValidationError):
        dup_link(3, "relates_to")


def test_v2_naive_created_at_is_invalid() -> None:
    """[P2] The issue's own `created_at` must be timezone-aware too."""
    with pytest.raises(ValidationError):
        make_jira_issue(created_at=datetime(2025, 1, 1))


def test_v2_is_frozen() -> None:
    """[P2] Snapshot issues are immutable."""
    issue = make_jira_issue()
    with pytest.raises(ValidationError):
        issue.resolution = "Duplicate"  # type: ignore[misc]


def test_derivation_does_not_mutate_issue() -> None:
    """[P2] Deriving outcome and kind leaves the issue as it was."""
    issue = answered_question(duplicate_links=[dup_link(3)])
    before = issue.model_dump()
    derive_outcome(issue)
    derive_kind(issue)
    duplicate_target(issue)
    assert issue.model_dump() == before
