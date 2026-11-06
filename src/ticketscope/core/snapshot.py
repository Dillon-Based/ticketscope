"""One issue of a corpus snapshot (AD-6), mirroring `snapshot/schema-v1.json`.

A snapshot is compressed JSONL: one `SnapshotIssue` per line.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

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
