"""Listing filter and record mapping: GitHub REST JSON to `SnapshotIssue`.

The GitHub shapes below declare only the fields a snapshot carries. No user object or
login is declared, so none can be mapped. Text is masked here, before a record leaves
this module.
"""

import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from ticketscope.core.snapshot import Comment, Label, SnapshotIssue, TimelineEvent
from ticketscope.jobs.ingest.mask import mask, mask_optional

log = logging.getLogger(__name__)

# Timeline items kept as events; `commented` items become comments; the rest are dropped.
KEPT_EVENTS = frozenset(
    {"marked_as_duplicate", "unmarked_as_duplicate", "closed", "connected", "cross-referenced"}
)


class _GitHub(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class _Label(_GitHub):
    name: str


class _ListedIssue(_GitHub):
    number: int
    title: str
    body: str | None = None
    state: Literal["open", "closed"]
    state_reason: Literal["completed", "not_planned", "duplicate", "reopened"] | None = None
    created_at: datetime
    closed_at: datetime | None = None
    labels: list[_Label] = []
    pull_request: dict[str, Any] | None = None


class _PullRequestRef(_GitHub):
    merged_at: datetime | None = None


class _SourceIssue(_GitHub):
    number: int | None = None
    html_url: str | None = None
    pull_request: _PullRequestRef | None = None


class _Source(_GitHub):
    issue: _SourceIssue | None = None


class _TimelineItem(_GitHub):
    event: str | None = None
    created_at: datetime | None = None
    author_association: str | None = None
    body: str | None = None
    source: _Source | None = None


def issue_url(repo: str, number: int) -> str:
    return f"https://github.com/{repo}/issues/{number}"


def select_issues(
    items: Iterable[dict[str, Any]],
    *,
    repo: str,
    window_start: datetime,
    cap: int,
    exclusions: frozenset[int],
) -> tuple[list[SnapshotIssue], int]:
    """Closed issues (not PRs) closed in the window, most recently closed first, capped.

    Returns the masked base records (no comments or timeline yet) and how many listed
    issues the exclusion list removed.
    """
    chosen: dict[int, SnapshotIssue] = {}
    excluded: set[int] = set()
    for raw in items:
        if "pull_request" in raw:
            continue
        listed = _ListedIssue.model_validate(raw)
        if listed.state != "closed" or listed.closed_at is None:
            continue
        if listed.closed_at < window_start:
            continue
        if listed.number in exclusions:
            excluded.add(listed.number)
            continue
        chosen[listed.number] = _base_record(listed, repo)
    ordered = sorted(
        chosen.values(),
        key=lambda issue: (issue.closed_at, issue.number),
        reverse=True,
    )
    return ordered[:cap], len(excluded)


def _base_record(listed: _ListedIssue, repo: str) -> SnapshotIssue:
    return SnapshotIssue(
        number=listed.number,
        url=issue_url(repo, listed.number),
        title=mask(listed.title),
        body=mask_optional(listed.body),
        state=listed.state,
        state_reason=listed.state_reason,
        created_at=listed.created_at,
        closed_at=listed.closed_at,
        labels=[Label(name=label.name) for label in listed.labels],
        comments=[],
        timeline=[],
    )


def enrich(base: SnapshotIssue, timeline: Iterable[dict[str, Any]]) -> SnapshotIssue:
    """The base record with comments and kept events from the issue's timeline."""
    comments: list[Comment] = []
    events: list[TimelineEvent] = []
    for raw in timeline:
        try:
            item = _TimelineItem.model_validate(raw)
        except ValidationError as exc:
            log.warning("issue %d: unreadable timeline item dropped: %s", base.number, exc)
            continue
        if item.event == "commented":
            if item.created_at is None or item.author_association is None:
                log.warning("issue %d: comment without created_at dropped", base.number)
                continue
            comments.append(
                Comment(
                    author_association=item.author_association,
                    body=mask(item.body or ""),
                    created_at=item.created_at,
                )
            )
        elif item.event in KEPT_EVENTS:
            if item.created_at is None:
                log.warning("issue %d: %s without created_at dropped", base.number, item.event)
                continue
            events.append(_event(item.event, item.created_at, item.source))
    return base.model_copy(update={"comments": comments, "timeline": events})


def _event(event: str, created_at: datetime, source: _Source | None) -> TimelineEvent:
    issue = source.issue if source is not None else None
    if issue is None:
        return TimelineEvent(event=event, created_at=created_at)
    is_pr = issue.pull_request is not None
    return TimelineEvent(
        event=event,
        created_at=created_at,
        source_number=issue.number,
        source_url=issue.html_url,
        source_is_pull_request=is_pr,
        source_merged=(issue.pull_request.merged_at is not None) if issue.pull_request else None,
    )
