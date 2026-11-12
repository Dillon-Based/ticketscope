"""Derived fields of an issue: kind and outcome (AD-8, AD-26).

Pure functions over a schema v2 `SnapshotIssueV2` (Mojang Jira), so the load, the ingest
report and the eval agree: the Jira resolution mapping, the answered rule and Jira block
toggles.
Changing a rule or the default threshold changes `derivation_version`, which forces a reload.
`preprocessing_version` covers the derivations plus the search-text construction (AD-21).
"""

import re
from dataclasses import dataclass

from ticketscope.core.model import Kind, OutcomeSource, OutcomeStatus
from ticketscope.core.snapshot import DuplicateLink, SnapshotIssueV2

DEFAULT_KIND_THRESHOLD = 3  # measured on snapshot 2026.11.1 (story 5): 309 log-heavy pairs
KIND_RULE_VERSION = "kind2"
OUTCOME_RULE_VERSION = "outcome3"
# How `search_text` builds an issue's indexed text. Bump it when that changes.
PREPROCESSING_RULE_VERSION = "pre1"
# How `embedding_text` builds the text a model embeds. Bump it when that changes.
EMBEDDING_RULE_VERSION = "emb1"
# Embedding text is cut at this many characters; the model's token limit is the backstop.
EMBEDDING_MAX_CHARS = 2000


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


def preprocessing_version(embeddings: bool = False) -> str:
    """What `load` records in `corpus_meta`, e.g. `pre1.kind2-t3.outcome3` (AD-21).

    A change to the search text or to any derivation changes it, which forces a reload.
    With `embeddings`, the embedding rule version is appended (`...outcome3.emb1`); without,
    the string is the one keyword-only loads have always written.
    """
    base = f"{PREPROCESSING_RULE_VERSION}.{derivation_version()}"
    return f"{base}.{EMBEDDING_RULE_VERSION}" if embeddings else base


def search_text(issue: SnapshotIssueV2) -> str:
    """The text that keyword search ranks: the title, a blank line, then the body."""
    return f"{issue.title}\n\n{issue.body or ''}"


def cut_for_embedding(text: str) -> str:
    """The one cut documents and queries share: at most `EMBEDDING_MAX_CHARS` characters."""
    return text[:EMBEDDING_MAX_CHARS]


def embedding_text(title: str, body: str | None) -> str:
    """The text a model embeds for an issue: the title, a blank line, then the body, cut.

    A query goes through `cut_for_embedding` alone, so the same text embeds the same way
    whether it is stored or searched.
    """
    return cut_for_embedding(f"{title}\n\n{body or ''}")


# --- outcome -------------------------------------------------------------------------------


def derive_outcome(issue: SnapshotIssueV2) -> Outcome:
    """The `/v1` outcome of a Jira issue."""
    return _jira_outcome(issue)


MOJANG_BROWSE_URL = "https://bugs.mojang.com/browse/"

# The one shape of an issue key (C-4): matched exactly, with no case or whitespace handling.
KEY_PATTERN = r"^[A-Z][A-Z0-9]*-[1-9][0-9]*$"
_KEY_RE = re.compile(KEY_PATTERN)


def is_issue_key(key: str) -> bool:
    """Whether `key` is exactly an issue key. `$` would admit a trailing newline: no."""
    return _KEY_RE.fullmatch(key) is not None


def key_from_url(url: str) -> str | None:
    """The issue key of a browse url, or None when `url` is anything else."""
    if not url.startswith(MOJANG_BROWSE_URL):
        return None
    key = url[len(MOJANG_BROWSE_URL) :]
    return key if is_issue_key(key) else None


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


def derive_kind(issue: SnapshotIssueV2, threshold: int = DEFAULT_KIND_THRESHOLD) -> Kind:
    """`log_heavy` when the body's kind score reaches `threshold`, else `short`.

    The body's `{code}` / `{noformat}` toggles are turned into fences first.
    """
    _check_threshold(threshold)
    body = jira_to_fences(issue.body)
    return "log_heavy" if kind_score(body) >= threshold else "short"


def _check_threshold(threshold: int) -> None:
    if threshold < 1:
        raise ValueError(f"kind threshold must be >= 1, got {threshold}")
