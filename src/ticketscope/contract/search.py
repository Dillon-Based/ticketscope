"""The `/v1` request and response models, exactly as AD-4 gives them.

Every model allows unknown fields and passes them through (AD-20), so additive
changes within /v1 never break a consumer.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ModeName = Literal["keyword", "dense", "hybrid"]
ScoreKind = Literal["bm25", "cosine", "rrf"]
IssueKind = Literal["short", "log_heavy"]
OutcomeStatus = Literal["fixed", "duplicate", "not_planned", "stale", "answered", "unknown"]
OutcomeSource = Literal["label", "linked_pr", "closing_comment"]

K_MIN = 1
K_MAX = 50


class _Wire(BaseModel):
    model_config = ConfigDict(extra="allow")


class SearchRequest(_Wire):
    query: str
    # Omitted means the server default (AD-25); there is deliberately no default here.
    mode: ModeName | None = None
    k: int = Field(default=10, ge=K_MIN, le=K_MAX)


class Issue(_Wire):
    number: int
    title: str
    url: str
    kind: IssueKind
    state: str
    # The Jira key (`MCL-6629`) read from `url`; null for a url that is not a browse url (C-8).
    key: str | None = None


class Outcome(_Wire):
    status: OutcomeStatus
    summary: str | None
    source: OutcomeSource | None
    ref: str | None


class SearchResult(_Wire):
    rank: int
    score: float
    issue: Issue
    outcome: Outcome


class SearchResponse(_Wire):
    mode: ModeName
    score_kind: ScoreKind
    corpus_version: str
    results: list[SearchResult]


class IssueDetail(Issue):
    body: str | None


class IssueResponse(_Wire):
    """`GET /v1/issues/{number}`."""

    issue: IssueDetail
    outcome: Outcome


class ProblemError(_Wire):
    loc: list[str | int]
    msg: str


class Problem(_Wire):
    """An RFC 9457 problem body, as every `/v1` error returns it."""

    type: str
    title: str
    status: int
    detail: str
    errors: list[ProblemError] | None = None
