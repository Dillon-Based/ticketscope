"""`POST /v1/search` request and response models, exactly as AD-4 gives them.

Every model allows unknown fields and passes them through (AD-20), so additive
changes within /v1 never break a consumer.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

ModeName = Literal["keyword", "dense", "hybrid"]
ScoreKind = Literal["bm25", "cosine", "rrf"]
IssueKind = Literal["short", "log_heavy"]
OutcomeStatus = Literal["fixed", "duplicate", "not_planned", "stale", "answered", "unknown"]
OutcomeSource = Literal["label", "linked_pr", "closing_comment"]


class _Wire(BaseModel):
    model_config = ConfigDict(extra="allow")


class SearchRequest(_Wire):
    query: str
    # Omitted means the server default (AD-25); there is deliberately no default here.
    mode: ModeName | None = None
    k: int = 10


class Issue(_Wire):
    number: int
    title: str
    url: str
    kind: IssueKind
    state: str


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
