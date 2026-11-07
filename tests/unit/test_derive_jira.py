"""Jira kind and outcome derivation in core (story 14; test design R2, closed R-002)."""

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from tests.factories import SNAPSHOT_RESOLVED as RESOLVED
from tests.factories import snapshot_issue
from ticketscope.core.derive import (
    DEFAULT_KIND_THRESHOLD,
    UNKNOWN,
    Outcome,
    derivation_version,
    derive_kind,
    derive_outcome,
    duplicate_target,
    jira_to_fences,
    kind_score,
)
from ticketscope.core.snapshot import DuplicateLink, JiraComment, SnapshotIssueV2

STORY_4_VERSION = "kind1-t3.outcome2"


def at(day: int) -> datetime:
    return datetime(2025, 1, day, tzinfo=UTC)


def comment(day: int, *, from_reporter: bool) -> JiraComment:
    return JiraComment(body="a comment", created_at=at(day), from_reporter=from_reporter)


def link(number: int, direction: str = "duplicates") -> DuplicateLink:
    return DuplicateLink(
        target_number=number,
        target_key=f"MCL-{number}",
        direction=direction,  # type: ignore[arg-type]
        link_type="Duplicate",
    )


def open_issue(**overrides: Any) -> SnapshotIssueV2:
    return snapshot_issue(state="open", resolution=None, resolved_at=None, **overrides)


# --- outcome per resolution class -----------------------------------------------------------


def test_duplicate_points_at_target() -> None:
    issue = snapshot_issue(resolution="Duplicate", duplicate_links=[link(7)])
    assert derive_outcome(issue) == Outcome(
        "duplicate", "Duplicate of MCL-7", "label", "https://bugs.mojang.com/browse/MCL-7"
    )


def test_duplicate_without_link_has_no_ref() -> None:
    issue = snapshot_issue(resolution="Duplicate")
    assert derive_outcome(issue) == Outcome("duplicate", "Resolved as duplicate", "label", None)


def test_fixed() -> None:
    outcome = derive_outcome(snapshot_issue(resolution="Fixed"))
    assert outcome == Outcome("fixed", "Resolved as Fixed", None, None)


def test_not_planned() -> None:
    outcome = derive_outcome(snapshot_issue(resolution="Won't Fix"))
    assert outcome == Outcome("not_planned", "Resolved as Won't Fix", None, None)


def test_stale() -> None:
    outcome = derive_outcome(snapshot_issue(resolution="Timed out"))
    assert outcome == Outcome("stale", "Resolved as Timed out", None, None)


def test_answered_by_resolution() -> None:
    outcome = derive_outcome(snapshot_issue(resolution="Answered"))
    assert outcome == Outcome("answered", "Resolved as Answered", "closing_comment", None)


def test_unresolved_is_unknown() -> None:
    assert derive_outcome(open_issue()) == Outcome("unknown", None, None, None)


def test_unmapped_resolution_is_unknown() -> None:
    assert derive_outcome(snapshot_issue(resolution="Triaged")) == UNKNOWN


def test_resolution_matched_trimmed_and_case_insensitive() -> None:
    outcome = derive_outcome(snapshot_issue(resolution=" fixed "))
    assert outcome.status == "fixed"
    assert outcome.summary == "Resolved as fixed"


# --- answered rule --------------------------------------------------------------------------


def test_question_answered_by_non_reporter_comment() -> None:
    issue = snapshot_issue(
        issue_type="Question",
        resolution="Done",
        comments=[comment(2, from_reporter=True), comment(5, from_reporter=False)],
    )
    assert derive_outcome(issue) == Outcome(
        "answered", "Answered before resolution (Done)", "closing_comment", None
    )


def test_question_comment_at_resolution_time_counts() -> None:
    issue = snapshot_issue(
        issue_type="question",
        resolution="Done",
        comments=[JiraComment(body="x", created_at=RESOLVED, from_reporter=False)],
    )
    assert derive_outcome(issue).status == "answered"


def test_question_only_reporter_comments_is_fixed() -> None:
    issue = snapshot_issue(
        issue_type="Question", resolution="Done", comments=[comment(5, from_reporter=True)]
    )
    assert derive_outcome(issue).status == "fixed"


def test_question_non_reporter_comment_after_resolution_is_fixed() -> None:
    issue = snapshot_issue(
        issue_type="Question", resolution="Done", comments=[comment(20, from_reporter=False)]
    )
    assert derive_outcome(issue).status == "fixed"


def test_question_unmapped_resolution_answered() -> None:
    issue = snapshot_issue(
        issue_type="Question", resolution="Triaged", comments=[comment(5, from_reporter=False)]
    )
    assert derive_outcome(issue) == Outcome(
        "answered", "Answered before resolution (Triaged)", "closing_comment", None
    )


def test_bug_type_with_non_reporter_comment_stays_fixed() -> None:
    issue = snapshot_issue(
        issue_type="Bug", resolution="Done", comments=[comment(5, from_reporter=False)]
    )
    assert derive_outcome(issue).status == "fixed"


def test_support_duplicate_stays_duplicate() -> None:
    issue = snapshot_issue(
        issue_type="Support",
        resolution="Duplicate",
        comments=[comment(5, from_reporter=False)],
        duplicate_links=[link(7)],
    )
    assert derive_outcome(issue).status == "duplicate"


@pytest.mark.parametrize(
    ("resolution", "status"),
    [("Won't Fix", "not_planned"), ("Timed out", "stale"), ("Answered", "answered")],
)
def test_support_other_classes_keep_their_class(resolution: str, status: str) -> None:
    issue = snapshot_issue(
        issue_type="Support Request",
        resolution=resolution,
        comments=[comment(5, from_reporter=False)],
    )
    outcome = derive_outcome(issue)
    assert outcome.status == status
    assert outcome.summary == f"Resolved as {resolution}"


def test_answered_rule_independent_of_comment_order() -> None:
    comments = [
        comment(20, from_reporter=False),
        comment(3, from_reporter=True),
        comment(5, from_reporter=False),
    ]
    a = snapshot_issue(issue_type="Question", resolution="Done", comments=comments)
    b = snapshot_issue(issue_type="Question", resolution="Done", comments=comments[::-1])
    assert derive_outcome(a) == derive_outcome(b)
    assert derive_outcome(a).status == "answered"


# --- duplicate target (AD-26) ---------------------------------------------------------------


def test_duplicate_target_prefers_duplicates_direction() -> None:
    issue = snapshot_issue(
        resolution="Duplicate", duplicate_links=[link(3, "duplicated_by"), link(9)]
    )
    target = duplicate_target(issue)
    assert target is not None
    assert target.target_key == "MCL-9"


def test_duplicate_target_falls_back_to_lowest_any_direction() -> None:
    issue = snapshot_issue(
        resolution="Duplicate",
        duplicate_links=[link(12, "duplicated_by"), link(4, "duplicated_by")],
    )
    target = duplicate_target(issue)
    assert target is not None
    assert target.target_number == 4


def test_duplicate_target_independent_of_link_order() -> None:
    links = [link(30), link(8, "duplicated_by"), link(11)]
    a = snapshot_issue(resolution="Duplicate", duplicate_links=links)
    b = snapshot_issue(resolution="Duplicate", duplicate_links=links[::-1])
    assert duplicate_target(a) == duplicate_target(b)
    assert derive_outcome(a) == derive_outcome(b)
    assert derive_outcome(a).ref == "https://bugs.mojang.com/browse/MCL-11"


def test_duplicate_target_none_for_other_resolutions() -> None:
    assert duplicate_target(snapshot_issue(resolution="Fixed", duplicate_links=[link(7)])) is None
    assert duplicate_target(open_issue(duplicate_links=[link(7)])) is None


# --- derivation version ---------------------------------------------------------------------


def test_derivation_version_differs_from_story_4() -> None:
    assert derivation_version() == "kind2-t3.outcome3"
    assert derivation_version() != STORY_4_VERSION


# --- kind -----------------------------------------------------------------------------------

# Two {code}/{noformat} blocks score 2; one log line outside them adds 1.
TWO_BLOCKS = "Steps:\n{code}\nfoo()\n{code}\nand\n{noformat}\nbar\n{noformat}"


def jira_kind(body: str, threshold: int = DEFAULT_KIND_THRESHOLD) -> str:
    return derive_kind(snapshot_issue(body=body), threshold)


def test_kind_just_below_threshold_is_short() -> None:
    assert DEFAULT_KIND_THRESHOLD == 3
    assert kind_score(jira_to_fences(TWO_BLOCKS)) == 2
    assert jira_kind(TWO_BLOCKS) == "short"


def test_kind_at_threshold_is_log_heavy() -> None:
    body = TWO_BLOCKS + "\nERROR something broke"
    assert kind_score(jira_to_fences(body)) == 3
    assert jira_kind(body) == "log_heavy"


def test_kind_inline_toggles_count() -> None:
    body = "see {code}a{code} and {noformat}b{noformat} and {code}c{code}"
    assert jira_kind(body) == "log_heavy"


def test_parameterised_toggle_scores_like_plain() -> None:
    plain = "{code}\nx\n{code}"
    param = "{code:java|title=Foo.java}\nx\n{code}"
    noformat = "{NOFORMAT}\nx\n{noformat}"
    score = kind_score(jira_to_fences(plain))
    assert score == 1
    assert kind_score(jira_to_fences(param)) == score
    assert kind_score(jira_to_fences(noformat)) == score


def test_unclosed_toggle_counts_once() -> None:
    # The sources do not say; like an unclosed ``` fence, the opening counts once.
    assert kind_score(jira_to_fences("{code}\nfoo()\nbar()")) == 1


def test_kind_log_lines_inside_block_count_like_fenced_logs() -> None:
    body = "{noformat}\nERROR a\nERROR b\n{noformat}"
    assert kind_score(jira_to_fences(body)) == kind_score("```\nERROR a\nERROR b\n```") == 3
    assert jira_kind(body) == "log_heavy"


def test_kind_threshold_below_one_raises() -> None:
    with pytest.raises(ValueError):
        jira_kind(TWO_BLOCKS, 0)


def test_kind_none_body_is_short() -> None:
    assert derive_kind(snapshot_issue(body=None)) == "short"


# --- model ----------------------------------------------------------------------------------


def test_closed_without_resolution_is_invalid() -> None:
    with pytest.raises(ValidationError):
        snapshot_issue(state="closed", resolution=None)


def test_open_with_resolution_is_invalid() -> None:
    with pytest.raises(ValidationError):
        snapshot_issue(state="open", resolution="Fixed")


def test_naive_datetimes_are_invalid() -> None:
    naive = datetime(2025, 1, 10)
    with pytest.raises(ValidationError):
        snapshot_issue(resolved_at=naive)
    with pytest.raises(ValidationError):
        JiraComment(body="x", created_at=naive, from_reporter=False)


def test_number_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        snapshot_issue(number=0)
    with pytest.raises(ValidationError):
        link(0)


def test_model_has_no_identity_fields() -> None:
    names = set(SnapshotIssueV2.model_fields) | set(JiraComment.model_fields)
    assert not names & {"reporter", "author", "assignee", "creator"}
