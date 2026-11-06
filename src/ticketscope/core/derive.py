"""Derived fields of an issue: kind and outcome (AD-8).

Pure functions over `SnapshotIssue`, so the load, the ingest report and the eval agree.
Changing a rule or the default threshold changes `derivation_version`, which forces a reload.
"""

import re
from dataclasses import dataclass

from ticketscope.core.model import Kind, OutcomeSource, OutcomeStatus
from ticketscope.core.snapshot import Comment, SnapshotIssue, TimelineEvent

DEFAULT_KIND_THRESHOLD = 3  # provisional; story 5 sets the final threshold
KIND_RULE_VERSION = "kind1"
OUTCOME_RULE_VERSION = "outcome2"

DUPLICATE_LABEL = "triage/duplicate"
STALE_LABELS = frozenset({"lifecycle/stale", "lifecycle/rotten"})
SUPPORT_LABEL = "kind/support"
MAINTAINER_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
_PR_EVENTS = frozenset({"closed", "cross-referenced", "connected"})


@dataclass(frozen=True, slots=True)
class Outcome:
    """The `/v1` outcome of an issue."""

    status: OutcomeStatus
    summary: str | None = None
    source: OutcomeSource | None = None
    ref: str | None = None


UNKNOWN = Outcome(status="unknown")


def derivation_version(threshold: int = DEFAULT_KIND_THRESHOLD) -> str:
    """The version of every derivation rule, e.g. `kind1-t3.outcome1`."""
    _check_threshold(threshold)
    return f"{KIND_RULE_VERSION}-t{threshold}.{OUTCOME_RULE_VERSION}"


# --- outcome -------------------------------------------------------------------------------


def derive_outcome(issue: SnapshotIssue) -> Outcome:
    """Outcome by precedence, first match wins:
    duplicate, fixed, not_planned, stale, answered, unknown.
    """
    labels = {label.name for label in issue.labels}
    for rule in (_duplicate, _fixed, _not_planned, _stale, _answered):
        outcome = rule(issue, labels)
        if outcome is not None:
            return outcome
    return UNKNOWN


def _event_key(event: TimelineEvent) -> tuple[object, ...]:
    return (event.created_at, event.source_number or 0, event.source_url or "")


def _duplicate(issue: SnapshotIssue, labels: set[str]) -> Outcome | None:
    marks = [
        e for e in issue.timeline if e.event in ("marked_as_duplicate", "unmarked_as_duplicate")
    ]
    # A mark wins an otherwise indistinguishable tie, independent of input order.
    latest = (
        max(marks, key=lambda e: (*_event_key(e), e.event == "marked_as_duplicate"))
        if marks
        else None
    )
    if latest is not None and latest.event == "marked_as_duplicate":
        summary = (
            f"Duplicate of #{latest.source_number}"
            if latest.source_number is not None
            else "Marked as duplicate"
        )
        return Outcome("duplicate", summary, "label", latest.source_url)
    if DUPLICATE_LABEL in labels:
        return Outcome("duplicate", "Marked as duplicate", "label", None)
    return None


def _fixed(issue: SnapshotIssue, labels: set[str]) -> Outcome | None:
    merged = [
        e
        for e in issue.timeline
        if e.event in _PR_EVENTS and e.source_is_pull_request is True and e.source_merged is True
    ]
    if not merged:
        return None
    pr = max(merged, key=lambda e: (e.event == "closed", *_event_key(e)))
    summary = (
        f"Fixed by #{pr.source_number}"
        if pr.source_number is not None
        else ("Fixed by a merged PR")
    )
    return Outcome("fixed", summary, "linked_pr", pr.source_url)


def _not_planned(issue: SnapshotIssue, labels: set[str]) -> Outcome | None:
    if issue.state_reason != "not_planned":
        return None
    return Outcome("not_planned", "Closed as not planned")


def _stale(issue: SnapshotIssue, labels: set[str]) -> Outcome | None:
    found = sorted(labels & STALE_LABELS)
    if not found:
        return None
    return Outcome("stale", f"Closed as stale ({', '.join(found)})")


def _comment_key(comment: Comment) -> tuple[object, ...]:
    return (comment.created_at, comment.author_association, comment.body)


def _answered(issue: SnapshotIssue, labels: set[str]) -> Outcome | None:
    if SUPPORT_LABEL not in labels or issue.closed_at is None:
        return None
    closed_at = issue.closed_at
    maintainer = [
        c
        for c in issue.comments
        if c.author_association in MAINTAINER_ASSOCIATIONS and c.created_at <= closed_at
    ]
    if not maintainer:
        return None
    latest = max(maintainer, key=_comment_key)
    summary = f"Answered by a maintainer ({latest.author_association})"
    return Outcome("answered", summary, "closing_comment", None)


# --- kind ----------------------------------------------------------------------------------

_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_FENCE_CLOSE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")
_LOG_LINE = re.compile(
    "|".join(
        (
            r"^\s*[IWEF]\d{4} \d{2}:\d{2}:\d{2}",  # klog prefix
            r"^\s*\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}",  # ISO / RFC3339 timestamp
            r"\blevel=",
            r"\bpanic:",
            r"\bgoroutine \d+ \[",
            r"\bTraceback\b",
            r'\bFile ".*", line \d+',
            r"\.go:\d+",
            r"^\s+at [\w$.<>]+\(",  # Java stack frame
            r"\b(?:ERROR|FATAL|WARN(?:ING)?)\b",
            # kubectl-style `Error from server (Forbidden):`, `error:`
            r"^\s*(?:[Ee]rror|Warning)(?: from server)?(?: \([^)]*\))?:",
        )
    )
)


def kind_score(body: str | None) -> int:
    """Fence openings plus log-like lines; a line counts at most once as log-like."""
    if not body:
        return 0
    score = 0
    open_fence: str | None = None  # the opening run, e.g. "```"
    for line in body.splitlines():
        if open_fence is None:
            fence = _FENCE.match(line)
            if fence:
                open_fence = fence.group(1)
                score += 1
                continue
        else:
            close = _FENCE_CLOSE.match(line)
            if close:
                run = close.group(1)
                if run[0] == open_fence[0] and len(run) >= len(open_fence):
                    open_fence = None
                continue
            if _FENCE.match(line):
                continue
        if _LOG_LINE.search(line):
            score += 1
    return score


def derive_kind(issue: SnapshotIssue, threshold: int = DEFAULT_KIND_THRESHOLD) -> Kind:
    """`log_heavy` when `kind_score(body) >= threshold`, else `short`."""
    _check_threshold(threshold)
    return "log_heavy" if kind_score(issue.body) >= threshold else "short"


def _check_threshold(threshold: int) -> None:
    if threshold < 1:
        raise ValueError(f"kind threshold must be >= 1, got {threshold}")
