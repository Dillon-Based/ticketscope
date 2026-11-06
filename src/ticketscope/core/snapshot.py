"""One issue of a corpus snapshot (AD-6).

A snapshot is compressed JSONL: one issue per line. `SnapshotIssue` mirrors
`snapshot/schema-v1.json` (GitHub). `SnapshotIssueV2` is the Mojang Jira shape that
schema v2 mirrors; it carries no reporter or author identity, only each comment's
`from_reporter` flag.
"""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = 1


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Label(_Frozen):
    name: str


class Comment(_Frozen):
    author_association: str
    body: str
    created_at: datetime


class TimelineEvent(_Frozen):
    """A timeline event. `marked_as_duplicate`, `cross-referenced` and `closed` matter.

    `source_*` fields carry the duplicate target or the cross-referencing / closing PR.
    """

    event: str
    created_at: datetime
    source_number: int | None = None
    source_url: str | None = None
    source_is_pull_request: bool | None = None
    source_merged: bool | None = None


class SnapshotIssue(_Frozen):
    number: int
    url: str
    title: str
    body: str | None
    state: Literal["open", "closed"]
    state_reason: Literal["completed", "not_planned", "duplicate", "reopened"] | None
    created_at: datetime
    closed_at: datetime | None
    labels: list[Label]
    comments: list[Comment]
    timeline: list[TimelineEvent]


# --- schema v2 (Mojang Jira) ---------------------------------------------------------------


class JiraComment(_Frozen):
    body: str
    created_at: AwareDatetime
    from_reporter: bool


class DuplicateLink(_Frozen):
    """A Duplicate-type issue link; `direction` reads from this issue toward the target."""

    target_number: Annotated[int, Field(ge=1)]
    target_key: str
    direction: Literal["duplicates", "duplicated_by"]
    link_type: str


class SnapshotIssueV2(_Frozen):
    schema_version: Literal[2]
    number: Annotated[int, Field(ge=1)]
    key: str
    url: str
    title: str
    body: str | None
    issue_type: str
    state: Literal["open", "closed"]
    resolution: str | None
    created_at: AwareDatetime
    resolved_at: AwareDatetime | None
    comments: list[JiraComment]
    duplicate_links: list[DuplicateLink]

    @model_validator(mode="after")
    def _closed_iff_resolved(self) -> Self:
        if (self.state == "closed") != (self.resolution is not None):
            raise ValueError("state must be 'closed' exactly when a resolution is set")
        return self
