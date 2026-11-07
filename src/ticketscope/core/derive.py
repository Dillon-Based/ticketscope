"""Derived fields of an issue: kind and outcome (AD-8, AD-26).

Pure functions over a snapshot issue, so the load, the ingest report and the eval agree.
A schema v1 `SnapshotIssue` (GitHub) uses the GitHub rules; a schema v2 `SnapshotIssueV2`
(Mojang Jira) uses the Jira resolution mapping, the answered rule and Jira block toggles.
Changing a rule or the default threshold changes `derivation_version`, which forces a reload.
`preprocessing_version` covers the derivations plus the search-text construction (AD-21).
"""

import re
from dataclasses import dataclass

from ticketscope.core.model import Kind, OutcomeSource, OutcomeStatus
from ticketscope.core.snapshot import (
    Comment,
    DuplicateLink,
    SnapshotIssue,
    SnapshotIssueV2,
    TimelineEvent,
)

DEFAULT_KIND_THRESHOLD = 3  # measured on snapshot 2026.11.1 (story 5): 309 log-heavy pairs
KIND_RULE_VERSION = "kind2"
OUTCOME_RULE_VERSION = "outcome3"
# How `search_text` builds an issue's indexed text. Bump it when that changes.
PREPROCESSING_RULE_VERSION = "pre1"

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
    """The version of every derivation rule, e.g. `kind2-t3.outcome3`."""
    _check_threshold(threshold)
    return f"{KIND_RULE_VERSION}-t{threshold}.{OUTCOME_RULE_VERSION}"


def preprocessing_version() -> str:
    """What `load` records in `corpus_meta`, e.g. `pre1.kind2-t3.outcome3` (AD-21).

    A change to the search text or to any derivation changes it, which forces a reload.
    """
    return f"{PREPROCESSING_RULE_VERSION}.{derivation_version()}"


def search_text(issue: SnapshotIssueV2) -> str:
    """The text that keyword search ranks: the title, a blank line, then the body."""
    return f"{issue.title}\n\n{issue.body or ''}"


# --- outcome -------------------------------------------------------------------------------


def derive_outcome(issue: SnapshotIssue | SnapshotIssueV2) -> Outcome:
    """The `/v1` outcome: Jira rules for a v2 issue, GitHub rules for a v1 issue."""
    if isinstance(issue, SnapshotIssueV2):
        return _jira_outcome(issue)
    return _github_outcome(issue)


def _github_outcome(issue: SnapshotIssue) -> Outcome:
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


# --- Jira outcome (schema v2) ----------------------------------------------------------------

MOJANG_BROWSE_URL = "https://bugs.mojang.com/browse/"

# `resolution` (trimmed, lower-cased) -> outcome, per spike 12's `outcome-mapping.md`.
# Anything else, and no resolution, is `unknown`.
RESOLUTION_OUTCOME: dict[str, OutcomeStatus] = {
    # duplicate
    "duplicate": "duplicate",
    "duplicate issue": "duplicate",
    # fixed: a change was made or the work was delivered
    "fixed": "fixed",
    "done": "fixed",
    "complete": "fixed",
    "implemented": "fixed",
    "resolved": "fixed",
    "fixed-verified": "fixed",
    "deployed": "fixed",
    "released": "fixed",
    "delivered": "fixed",
    "partially completed": "fixed",
    "staged": "fixed",
    "current release": "fixed",
    "next release": "fixed",
    # not_planned: closed without a change
    "won't fix": "not_planned",
    "won't do": "not_planned",
    "invalid": "not_planned",
    "incomplete": "not_planned",
    "incomplete description": "not_planned",
    "cannot reproduce": "not_planned",
    "works for me": "not_planned",
    "not a problem": "not_planned",
    "not a bug": "not_planned",
    "non-issue": "not_planned",
    "works as intended": "not_planned",
    "works as designed": "not_planned",
    "expected behavior": "not_planned",
    "rejected": "not_planned",
    "declined": "not_planned",
    "out of scope": "not_planned",
    "obsolete": "not_planned",
    "out of date": "not_planned",
    "gone away": "not_planned",
    "later": "not_planned",
    "deferred": "not_planned",
    "parked": "not_planned",
    "low priority": "not_planned",
    "deprioritized": "not_planned",
    "no resources": "not_planned",
    "won't finish": "not_planned",
    "will not implement": "not_planned",
    "canceled": "not_planned",
    "abandoned": "not_planned",
    "spam": "not_planned",
    "incorrectly filed": "not_planned",
    "invalid ticket": "not_planned",
    "not applicable": "not_planned",
    "unactionable": "not_planned",
    "unsolved mysteries": "not_planned",
    "eol": "not_planned",
    "incorporated": "not_planned",
    "tracked elsewhere": "not_planned",
    "moved": "not_planned",
    "migrated to another its": "not_planned",
    "resolved at apache": "not_planned",
    "upstream": "not_planned",
    "invalid: works as expected": "not_planned",
    "invalid: environment issue": "not_planned",
    "invalid: test error": "not_planned",
    "invalid: not supported": "not_planned",
    # stale: closed for want of a response
    "timed out": "stale",
    "awaiting response": "stale",
    "automatically closed": "stale",
    "auto closed": "stale",
    "low engagement": "stale",
    "pending closed": "stale",
    # answered: closed with an answer rather than a change
    "answered": "answered",
    "support request": "answered",
    "handled by support": "answered",
    "explained": "answered",
    "information provided": "answered",
    "community answered": "answered",
    "feedback received": "answered",
    "sent to forums": "answered",
    "sent to docs": "answered",
    "resolved locally": "answered",
    "workaround": "answered",
}

_QUESTION_TYPE = re.compile(r"question|support", re.IGNORECASE)


def _jira_outcome(issue: SnapshotIssueV2) -> Outcome:
    """The resolution's class, except that a Question/Support issue whose resolution reads
    as fixed or is unmapped is `answered` when the answered rule holds."""
    if issue.resolution is None:
        return UNKNOWN
    resolution = issue.resolution.strip()
    status = RESOLUTION_OUTCOME.get(resolution.lower(), "unknown")
    if status in ("fixed", "unknown") and _is_answered(issue):
        return Outcome(
            "answered", f"Answered before resolution ({resolution})", "closing_comment", None
        )
    if status == "unknown":
        return UNKNOWN
    if status == "duplicate":
        target = duplicate_target(issue)
        if target is None:
            return Outcome("duplicate", "Resolved as duplicate", "label", None)
        return Outcome(
            "duplicate",
            f"Duplicate of {target.target_key}",
            "label",
            f"{MOJANG_BROWSE_URL}{target.target_key}",
        )
    source: OutcomeSource | None = "closing_comment" if status == "answered" else None
    return Outcome(status, f"Resolved as {resolution}", source, None)


def _is_answered(issue: SnapshotIssueV2) -> bool:
    """A resolved Question/Support-type issue with a non-reporter comment at or before
    the resolution time."""
    if not _QUESTION_TYPE.search(issue.issue_type):
        return False
    resolved_at = issue.resolved_at
    if issue.resolution is None or resolved_at is None:
        return False
    return any(not c.from_reporter and c.created_at <= resolved_at for c in issue.comments)


def duplicate_target(issue: SnapshotIssueV2) -> DuplicateLink | None:
    """The issue a duplicate-class issue duplicates (AD-26): the lowest-numbered
    `duplicates` link; failing that, the lowest-numbered link either way. `None` for
    any other resolution or without links."""
    if issue.resolution is None:
        return None
    if RESOLUTION_OUTCOME.get(issue.resolution.strip().lower()) != "duplicate":
        return None
    forward = [link for link in issue.duplicate_links if link.direction == "duplicates"]
    candidates = forward or issue.duplicate_links
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda link: (link.target_number, link.target_key, link.direction, link.link_type),
    )


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


_JIRA_BLOCK = re.compile(r"\{(?:code|noformat)(?::[^}\n]*)?\}", re.IGNORECASE)


def jira_to_fences(body: str | None) -> str | None:
    """Put every `{code...}` / `{noformat}` toggle on its own line as a ``` fence."""
    if body is None:
        return None
    return _JIRA_BLOCK.sub("\n```\n", body)


def derive_kind(
    issue: SnapshotIssue | SnapshotIssueV2, threshold: int = DEFAULT_KIND_THRESHOLD
) -> Kind:
    """`log_heavy` when the body's kind score reaches `threshold`, else `short`.

    A v2 (Jira) body has its `{code}` / `{noformat}` toggles turned into fences first.
    """
    _check_threshold(threshold)
    body = jira_to_fences(issue.body) if isinstance(issue, SnapshotIssueV2) else issue.body
    return "log_heavy" if kind_score(body) >= threshold else "short"


def _check_threshold(threshold: int) -> None:
    if threshold < 1:
        raise ValueError(f"kind threshold must be >= 1, got {threshold}")
