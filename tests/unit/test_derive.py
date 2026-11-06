"""Kind and outcome derivation in core (story 4; test design R2, closed R-002)."""

from datetime import UTC, datetime
from typing import Any

import pytest

from ticketscope.core.derive import (
    DEFAULT_KIND_THRESHOLD,
    KIND_RULE_VERSION,
    OUTCOME_RULE_VERSION,
    Outcome,
    derivation_version,
    derive_kind,
    derive_outcome,
    kind_score,
)
from ticketscope.core.snapshot import Comment, Label, SnapshotIssue, TimelineEvent

CREATED = datetime(2025, 1, 1, tzinfo=UTC)
CLOSED = datetime(2025, 1, 10, tzinfo=UTC)
PR_URL = "https://github.com/kubernetes/kubernetes/pull/42"
DUP_URL = "https://github.com/kubernetes/kubernetes/issues/7"


def make_issue(**overrides: Any) -> SnapshotIssue:
    fields: dict[str, Any] = {
        "number": 1,
        "url": "https://github.com/kubernetes/kubernetes/issues/1",
        "title": "synthetic",
        "body": "A plain line.",
        "state": "closed",
        "state_reason": "completed",
        "created_at": CREATED,
        "closed_at": CLOSED,
        "labels": [],
        "comments": [],
        "timeline": [],
    }
    fields.update(overrides)
    return SnapshotIssue(**fields)


def labels(*names: str) -> list[Label]:
    return [Label(name=n) for n in names]


def at(day: int) -> datetime:
    return datetime(2025, 1, day, tzinfo=UTC)


def merged_pr(event: str = "cross-referenced", number: int = 42, day: int = 9) -> TimelineEvent:
    return TimelineEvent(
        event=event,
        created_at=at(day),
        source_number=number,
        source_url=f"https://github.com/kubernetes/kubernetes/pull/{number}",
        source_is_pull_request=True,
        source_merged=True,
    )


def dup_event() -> TimelineEvent:
    return TimelineEvent(
        event="marked_as_duplicate", created_at=at(5), source_number=7, source_url=DUP_URL
    )


# --- outcome: one case per branch -------------------------------------------------------------


def test_duplicate_by_event_uses_its_url() -> None:
    outcome = derive_outcome(make_issue(timeline=[dup_event()]))
    assert outcome == Outcome("duplicate", "Duplicate of #7", "label", DUP_URL)


def test_duplicate_by_label_has_no_ref() -> None:
    outcome = derive_outcome(make_issue(labels=labels("triage/duplicate")))
    assert outcome == Outcome("duplicate", "Marked as duplicate", "label", None)


def test_duplicate_also_fixed_by_merged_pr_is_duplicate() -> None:
    issue = make_issue(timeline=[merged_pr(event="closed"), dup_event()])
    assert derive_outcome(issue).status == "duplicate"


def test_marked_then_unmarked_duplicate_falls_through() -> None:
    unmark = TimelineEvent(event="unmarked_as_duplicate", created_at=at(6))
    issue = make_issue(timeline=[dup_event(), unmark, merged_pr()])
    assert derive_outcome(issue).status == "fixed"


def test_unmarked_then_remarked_is_duplicate() -> None:
    unmark = TimelineEvent(event="unmarked_as_duplicate", created_at=at(4))
    outcome = derive_outcome(make_issue(timeline=[unmark, dup_event()]))
    assert outcome == Outcome("duplicate", "Duplicate of #7", "label", DUP_URL)


def test_duplicate_mark_unmark_tie_is_independent_of_order() -> None:
    mark = dup_event()
    unmark = mark.model_copy(update={"event": "unmarked_as_duplicate"})
    expected = Outcome("duplicate", "Duplicate of #7", "label", DUP_URL)
    assert derive_outcome(make_issue(timeline=[mark, unmark])) == expected
    assert derive_outcome(make_issue(timeline=[unmark, mark])) == expected


def test_unmarked_duplicate_with_label_is_duplicate() -> None:
    unmark = TimelineEvent(event="unmarked_as_duplicate", created_at=at(6))
    issue = make_issue(labels=labels("triage/duplicate"), timeline=[dup_event(), unmark])
    assert derive_outcome(issue).status == "duplicate"


def test_duplicate_event_with_number_only() -> None:
    event = TimelineEvent(event="marked_as_duplicate", created_at=at(5), source_number=7)
    outcome = derive_outcome(make_issue(timeline=[event]))
    assert outcome == Outcome("duplicate", "Duplicate of #7", "label", None)


def test_duplicate_uses_latest_event_even_without_url() -> None:
    newer = TimelineEvent(event="marked_as_duplicate", created_at=at(8), source_number=9)
    outcome = derive_outcome(make_issue(timeline=[dup_event(), newer]))
    assert outcome == Outcome("duplicate", "Duplicate of #9", "label", None)


def test_state_reason_duplicate_alone_is_not_duplicate() -> None:
    assert derive_outcome(make_issue(state_reason="duplicate")).status == "unknown"


@pytest.mark.parametrize("event", ["closed", "cross-referenced", "connected"])
def test_fixed_by_merged_pr(event: str) -> None:
    outcome = derive_outcome(make_issue(timeline=[merged_pr(event=event)]))
    assert outcome == Outcome("fixed", "Fixed by #42", "linked_pr", PR_URL)


def test_fixed_prefers_the_closing_pr() -> None:
    issue = make_issue(
        timeline=[merged_pr(event="closed", number=42, day=3), merged_pr(number=43, day=9)]
    )
    assert derive_outcome(issue).ref == PR_URL


def test_fixed_without_number() -> None:
    event = TimelineEvent(
        event="closed", created_at=at(9), source_is_pull_request=True, source_merged=True
    )
    outcome = derive_outcome(make_issue(timeline=[event]))
    assert outcome == Outcome("fixed", "Fixed by a merged PR", "linked_pr", None)


@pytest.mark.parametrize("merged", [False, None])
def test_unmerged_cross_referenced_pr_is_not_fixed(merged: bool | None) -> None:
    event = TimelineEvent(
        event="cross-referenced",
        created_at=at(9),
        source_number=42,
        source_url=PR_URL,
        source_is_pull_request=True,
        source_merged=merged,
    )
    assert derive_outcome(make_issue(timeline=[event])).status == "unknown"


def test_merged_cross_reference_from_an_issue_is_not_fixed() -> None:
    event = merged_pr().model_copy(update={"source_is_pull_request": False})
    assert derive_outcome(make_issue(timeline=[event])).status == "unknown"


def test_not_planned_has_no_source() -> None:
    outcome = derive_outcome(make_issue(state_reason="not_planned"))
    assert outcome.status == "not_planned"
    assert outcome.source is None
    assert outcome.ref is None


def test_not_planned_beats_stale() -> None:
    issue = make_issue(state_reason="not_planned", labels=labels("lifecycle/stale"))
    assert derive_outcome(issue).status == "not_planned"


@pytest.mark.parametrize("label", ["lifecycle/stale", "lifecycle/rotten"])
def test_stale_has_no_source(label: str) -> None:
    outcome = derive_outcome(make_issue(labels=labels(label)))
    assert outcome.status == "stale"
    assert outcome.source is None
    assert outcome.ref is None


@pytest.mark.parametrize("association", ["OWNER", "MEMBER", "COLLABORATOR"])
def test_answered_support_issue(association: str) -> None:
    issue = make_issue(
        labels=labels("kind/support"),
        comments=[Comment(author_association=association, body="try X", created_at=CLOSED)],
    )
    outcome = derive_outcome(issue)
    assert outcome.status == "answered"
    assert outcome.source == "closing_comment"
    assert outcome.ref is None
    assert association in (outcome.summary or "")


def test_support_issue_with_only_contributor_comment_after_close_is_not_answered() -> None:
    issue = make_issue(
        labels=labels("kind/support"),
        comments=[Comment(author_association="CONTRIBUTOR", body="same", created_at=at(12))],
    )
    assert derive_outcome(issue) == Outcome("unknown")


def test_maintainer_comment_after_close_is_not_answered() -> None:
    issue = make_issue(
        labels=labels("kind/support"),
        comments=[Comment(author_association="MEMBER", body="late", created_at=at(12))],
    )
    assert derive_outcome(issue).status == "unknown"


def test_open_support_issue_is_not_answered() -> None:
    issue = make_issue(
        state="open",
        state_reason=None,
        closed_at=None,
        labels=labels("kind/support"),
        comments=[Comment(author_association="MEMBER", body="x", created_at=at(2))],
    )
    assert derive_outcome(issue).status == "unknown"


def test_maintainer_comment_without_support_label_is_not_answered() -> None:
    issue = make_issue(
        comments=[Comment(author_association="MEMBER", body="x", created_at=at(2))],
    )
    assert derive_outcome(issue).status == "unknown"


def test_unknown_has_no_summary_source_or_ref() -> None:
    assert derive_outcome(make_issue()) == Outcome("unknown", None, None, None)


# --- determinism ----------------------------------------------------------------------------


def test_outcome_is_independent_of_order() -> None:
    comments = [
        Comment(author_association="MEMBER", body="a", created_at=at(3)),
        Comment(author_association="OWNER", body="b", created_at=at(8)),
        Comment(author_association="CONTRIBUTOR", body="c", created_at=at(9)),
    ]
    timeline = [merged_pr(number=40, day=4), merged_pr(number=41, day=8), dup_event()]
    names = labels("kind/support", "lifecycle/stale", "sig/node")
    forward = make_issue(labels=names, comments=comments, timeline=timeline)
    backward = make_issue(labels=names[::-1], comments=comments[::-1], timeline=timeline[::-1])
    assert derive_outcome(forward) == derive_outcome(backward)
    no_dup = [forward.timeline[0], forward.timeline[1]]
    assert derive_outcome(forward.model_copy(update={"timeline": no_dup})) == derive_outcome(
        forward.model_copy(update={"timeline": no_dup[::-1]})
    )
    assert derive_outcome(forward.model_copy(update={"timeline": no_dup})).summary == (
        "Fixed by #41"
    )
    answered = forward.model_copy(update={"timeline": [], "labels": labels("kind/support")})
    reordered = answered.model_copy(update={"comments": comments[::-1]})
    assert derive_outcome(answered) == derive_outcome(reordered)
    assert derive_outcome(answered).summary == "Answered by a maintainer (OWNER)"


# --- kind -----------------------------------------------------------------------------------


def body_with_score(score: int) -> str:
    """A fenced block plus `score - 1` klog lines: score exactly `score` (>= 1)."""
    lines = [f"E1105 10:00:{i:02d}.000001 1 x.go:{i}] boom" for i in range(score - 1)]
    return "Intro.\n\n```\n" + "\n".join(lines) + "\n```\n"


@pytest.mark.parametrize("threshold", [2, 5, 10])
def test_kind_just_below_threshold_is_short(threshold: int) -> None:
    body = body_with_score(threshold - 1)
    assert kind_score(body) == threshold - 1
    assert derive_kind(make_issue(body=body), threshold) == "short"


@pytest.mark.parametrize("threshold", [1, 5, 10])
def test_kind_at_threshold_is_log_heavy(threshold: int) -> None:
    body = body_with_score(threshold)
    assert kind_score(body) == threshold
    assert derive_kind(make_issue(body=body), threshold) == "log_heavy"


@pytest.mark.parametrize("body", [None, ""])
def test_empty_body_is_short(body: str | None) -> None:
    assert derive_kind(make_issue(body=body)) == "short"


@pytest.mark.parametrize("threshold", [0, -1])
def test_threshold_below_one_raises(threshold: int) -> None:
    with pytest.raises(ValueError):
        derive_kind(make_issue(), threshold)
    with pytest.raises(ValueError):
        derivation_version(threshold)


def test_plain_body_scores_zero() -> None:
    assert kind_score("The controller ignores the annotation.\nExpected a default.") == 0


@pytest.mark.parametrize(
    "line",
    [
        "I1201 12:00:00.000001 1 drain.go:101] evicting",
        "2025-01-10T09:00:00Z something happened",
        'time="x" level=error msg="boom"',
        "panic: runtime error: nil pointer",
        "goroutine 1 [running]:",
        "Traceback (most recent call last):",
        '  File "app.py", line 3, in <module>',
        "\t/src/cache.go:88 +0x1c",
        "    at com.example.Main.run(Main.java:10)",
        "the pod reported ERROR on start",
        "WARNING: deprecated flag",
        'Error from server (Forbidden): admission webhook "x" denied the request',
        "error: unable to recognize manifest.yaml",
    ],
)
def test_log_like_line_scores_one(line: str) -> None:
    assert kind_score(line) == 1


@pytest.mark.parametrize(
    "line",
    [
        "Error handling in the controller is wrong: it retries forever",
        "  at the moment the pod restarts, the cache is empty",
    ],
)
def test_prose_line_scores_zero(line: str) -> None:
    assert kind_score(line) == 0


def test_fence_with_info_string_does_not_close() -> None:
    # Were "```yaml" a close, the last line would open a second fence (score 2).
    assert kind_score("```\nx\n```yaml\n```\n") == 1


def test_shorter_fence_run_does_not_close() -> None:
    # Were "```" a close, the last line would open a second fence (score 2).
    assert kind_score("````\n```\n````\n") == 1


def test_line_matching_several_patterns_counts_once() -> None:
    assert kind_score("E1105 10:00:01.000001 1 x.go:42] panic: ERROR level=fatal") == 1


def test_fences_count_openings_including_unclosed() -> None:
    assert kind_score("```\nplain\n```\n~~~\nplain\n~~~\n  ```yaml\nkind: Pod\n") == 3


# --- derivation version ---------------------------------------------------------------------


def test_derivation_version_names_every_rule() -> None:
    version = derivation_version()
    assert version == f"{KIND_RULE_VERSION}-t{DEFAULT_KIND_THRESHOLD}.{OUTCOME_RULE_VERSION}"


def test_derivation_version_changes_with_threshold() -> None:
    assert derivation_version(3) != derivation_version(4)
