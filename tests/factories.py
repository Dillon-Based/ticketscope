"""Raw test inputs; response expectations stay independent of these builders."""

from datetime import UTC, datetime
from typing import Any

from ticketscope.core.model import IssueRecord
from ticketscope.core.snapshot import SnapshotIssueV2

SNAPSHOT_CREATED = datetime(2025, 1, 1, tzinfo=UTC)
SNAPSHOT_RESOLVED = datetime(2025, 1, 10, tzinfo=UTC)


def issue_record(number: int, title: str | None = None) -> IssueRecord:
    """A neutral closed short-kind `IssueRecord` titled `t<number>`."""
    return IssueRecord(
        number=number, title=title or f"t{number}", url="u", kind="short", state="closed"
    )


def search_payload(query: str, **overrides: object) -> dict[str, object]:
    """Leave optional fields absent unless the scenario explicitly supplies them."""
    return {"query": query, **overrides}


def form_payload(query: str) -> dict[str, str]:
    return {"q": query}


def outcome_payload(**overrides: object) -> dict[str, object]:
    return {"status": "unknown", "summary": None, "source": None, "ref": None, **overrides}


def issue_outcome_payload(number: int, **outcome: object) -> dict[str, object]:
    return {"issue": {"number": number}, "outcome": outcome_payload(**outcome)}


def issue_payload(number: int = 1, **overrides: object) -> dict[str, object]:
    """A `/v1` issue object with neutral required fields; scenarios override what they test."""
    return {
        "number": number,
        "title": "t",
        "url": "u",
        "kind": "short",
        "state": "closed",
        **overrides,
    }


def snapshot_issue(**overrides: Any) -> SnapshotIssueV2:
    """A closed, fixed v2 snapshot issue with a plain body; scenarios override what they test."""
    number = overrides.get("number", 1)
    fields: dict[str, Any] = {
        "schema_version": 2,
        "number": number,
        "key": f"MCL-{number}",
        "url": f"https://bugs.mojang.com/browse/MCL-{number}",
        "title": "synthetic",
        "body": "A plain line.",
        "issue_type": "Bug",
        "state": "closed",
        "resolution": "Fixed",
        "created_at": SNAPSHOT_CREATED,
        "resolved_at": SNAPSHOT_RESOLVED,
        "comments": [],
        "duplicate_links": [],
    }
    fields.update(overrides)
    return SnapshotIssueV2(**fields)
