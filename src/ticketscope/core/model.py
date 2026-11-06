"""The result model that every retrieval mode returns."""

from dataclasses import dataclass
from typing import Literal

Kind = Literal["short", "log_heavy"]
OutcomeStatus = Literal["fixed", "duplicate", "not_planned", "stale", "answered", "unknown"]
OutcomeSource = Literal["label", "linked_pr", "closing_comment"]


@dataclass(frozen=True, slots=True)
class IssueRecord:
    """A loaded issue with its persisted derived fields (AD-8)."""

    number: int
    title: str
    url: str
    kind: Kind
    state: str
    outcome_status: OutcomeStatus = "unknown"
    outcome_summary: str | None = None
    outcome_source: OutcomeSource | None = None
    outcome_ref: str | None = None


@dataclass(frozen=True, slots=True)
class Scored:
    """One hit. `score` is higher-is-better within one result list (AD-4)."""

    issue: IssueRecord
    score: float
