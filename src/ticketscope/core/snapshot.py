"""One issue of a corpus snapshot (AD-6).

A snapshot is compressed JSONL: one issue per line. `SnapshotIssueV2` is the Mojang Jira
shape that `snapshot/schema-v2.json` is generated from; it carries no reporter or author
identity, only each comment's `from_reporter` flag.
"""

from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


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
