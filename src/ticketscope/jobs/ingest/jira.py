"""Dump documents to schema v2 records (AD-6, AD-26). Pure: no I/O but the package data.

- `to_issue`: one dump document as a masked, identity-free `SnapshotIssueV2`.
- `select`: the snapshot's issues from the documents of one instance, in `_id` order:
  every resolved issue of the in-scope projects, plus each unresolved in-scope issue that
  a resolved duplicate's `core.duplicate_target` points to. A repeated key keeps its
  first document; an excluded key is never written nor added as an open target.
- `report`: the counts the Release notes state, with core's kind and duplicate rules.
"""

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib import resources
from typing import Any, Literal, cast

from ticketscope.core.derive import (
    DEFAULT_KIND_THRESHOLD,
    MOJANG_BROWSE_URL,
    derive_kind,
    duplicate_target,
)
from ticketscope.core.snapshot import DuplicateLink, JiraComment, SnapshotIssueV2
from ticketscope.jobs.ingest.mask import mask_jira

INSTANCE = "Mojang"
PROJECTS: tuple[str, ...] = ("MCL", "REALMS", "MCD")
SUBSET_RULE = "every resolved issue, plus the unresolved issues their duplicates point to"

Document = Mapping[str, Any]


class BadTime(ValueError):
    """A time the dump holds that cannot be parsed."""


# --- link types ----------------------------------------------------------------------------

_LINKTYPE_PREFIX = re.compile(r"^\s*\d+\s*-\s*")  # Sakai: "3 - Duplicate"


def load_linktypes() -> dict[str, str]:
    """The dataset's link-type name -> category mapping (a copy of spike 12's file)."""
    text = (
        resources.files("ticketscope.jobs.ingest")
        .joinpath("linktypes.json")
        .read_text(encoding="utf-8")
    )
    raw = cast(dict[str, dict[str, str]], json.loads(text))
    return dict(raw["link types"])


def is_duplicate_linktype(name: str | None, linkmap: Mapping[str, str]) -> bool:
    if not name:
        return False
    return linkmap.get(_LINKTYPE_PREFIX.sub("", name).strip()) == "Duplicate"


# --- fields --------------------------------------------------------------------------------


def parse_time(value: object) -> datetime | None:
    """Jira `2021-12-28T20:34:52.000+0200` -> aware UTC. `None` when absent."""
    if value is None or value == "":
        return None
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                return datetime.strptime(value, fmt).astimezone(UTC)
            except ValueError:
                continue
    raise BadTime(f"unparseable Jira time {value!r}")


def _dict(value: object) -> dict[str, Any]:
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def _fields(doc: Document) -> dict[str, Any]:
    return _dict(doc.get("fields"))


def _user(person: object) -> str | None:
    """A person's masked id, used only to compare comment authors with the reporter."""
    data = _dict(person)
    value = data.get("key") or data.get("name") or data.get("accountId")
    return str(value) if value else None


def _comments(fields: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = fields.get("comments")
    if raw is None:
        raw = _dict(fields.get("comment")).get("comments")
    if not isinstance(raw, list):
        return []
    return [comment for c in cast(list[object], raw) if (comment := _dict(c))]


def project_of(doc: Document) -> str:
    project = _dict(_fields(doc).get("project")).get("key")
    if isinstance(project, str) and project:
        return project
    return str(doc.get("key") or "").split("-", 1)[0]


def resolution_of(doc: Document) -> str | None:
    resolution = _fields(doc).get("resolution")
    if resolution is None:
        return None
    name = _dict(resolution).get("name")
    return str(name) if name else ""


def browse_url(key: str) -> str:
    return f"{MOJANG_BROWSE_URL}{key}"


# --- one document --------------------------------------------------------------------------


@dataclass(slots=True)
class LinkCounts:
    dropped: int = 0  # Duplicate-mapped links whose target id could not be found


def duplicate_links(
    doc: Document,
    ids: Mapping[str, int],
    linkmap: Mapping[str, str],
    counts: LinkCounts,
) -> list[DuplicateLink]:
    """The document's Duplicate-mapped links, deduplicated and sorted; self-links dropped."""
    key = str(doc.get("key"))
    links: set[DuplicateLink] = set()
    raw = _fields(doc).get("issuelinks")
    for link in cast(list[object], raw) if isinstance(raw, list) else []:
        data = _dict(link)
        ltype = _dict(data.get("type"))
        name = ltype.get("name")
        if not is_duplicate_linktype(name if isinstance(name, str) else None, linkmap):
            continue
        for side, text_key in (("outwardIssue", "outward"), ("inwardIssue", "inward")):
            other = _dict(data.get(side))
            target_key = other.get("key")
            if not isinstance(target_key, str) or not target_key or target_key == key:
                continue
            target_number = _int(other.get("id"))
            if target_number is None:
                target_number = ids.get(target_key)
            if target_number is None:
                counts.dropped += 1
                continue
            text = str(ltype.get(text_key) or "").strip().lower()
            direction: Literal["duplicates", "duplicated_by"] = (
                "duplicates" if text == "duplicates" else "duplicated_by"
            )
            links.add(
                DuplicateLink(
                    target_number=target_number,
                    target_key=target_key,
                    direction=direction,
                    link_type=str(name),
                )
            )
    return sorted(links, key=lambda x: (x.target_number, x.target_key, x.direction, x.link_type))


def _int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 1 else None
    if isinstance(value, str) and value.isdigit() and int(value) >= 1:
        return int(value)
    return None


def to_issue(
    doc: Document,
    ids: Mapping[str, int],
    linkmap: Mapping[str, str],
    counts: LinkCounts | None = None,
) -> SnapshotIssueV2:
    """One dump document as a schema v2 record. Raises `BadTime` on an unparseable
    created or resolution time, and `ValueError` on a document without an id or key."""
    key = doc.get("key")
    number = _int(doc.get("id"))
    if not isinstance(key, str) or not key or number is None:
        raise ValueError(f"document without a usable id and key: {doc.get('_id')!r}")
    fields = _fields(doc)
    created_at = parse_time(fields.get("created"))
    if created_at is None:
        raise BadTime(f"{key}: no created time")
    resolution = resolution_of(doc)
    resolved_at = parse_time(fields.get("resolutiondate")) if resolution is not None else None
    reporter = _user(fields.get("reporter"))
    comments: list[JiraComment] = []
    for comment in _comments(fields):
        try:
            created = parse_time(comment.get("created"))
        except BadTime:
            created = None
        if created is None:
            continue
        author = _user(comment.get("author"))
        comments.append(
            JiraComment(
                body=mask_jira(str(comment.get("body") or "")),
                created_at=created,
                from_reporter=reporter is not None and author == reporter,
            )
        )
    description = fields.get("description")
    return SnapshotIssueV2(
        schema_version=2,
        number=number,
        key=key,
        url=browse_url(key),
        title=mask_jira(str(fields.get("summary") or "")),
        body=None if description is None else mask_jira(str(description)),
        issue_type=str(_dict(fields.get("issuetype")).get("name") or ""),
        state="open" if resolution is None else "closed",
        resolution=resolution,
        created_at=created_at,
        resolved_at=resolved_at,
        comments=comments,
        duplicate_links=duplicate_links(doc, ids, linkmap, counts or LinkCounts()),
    )


# --- selection -----------------------------------------------------------------------------


@dataclass(slots=True)
class Selection:
    issues: list[SnapshotIssueV2] = field(default_factory=lambda: list[SnapshotIssueV2]())
    open_targets: int = 0
    repeated_keys_dropped: int = 0
    excluded: int = 0
    bad_time: int = 0
    resolved_without_date: int = 0
    links_dropped: int = 0


def select(
    docs: Iterable[Document],
    *,
    exclusions: frozenset[str] = frozenset(),
    linkmap: Mapping[str, str] | None = None,
) -> Selection:
    """The snapshot's issues, sorted by number. `docs` come in `_id` order."""
    linkmap = load_linktypes() if linkmap is None else linkmap
    scope = frozenset(PROJECTS)
    selection = Selection()

    first: dict[str, Document] = {}
    for doc in docs:
        key = doc.get("key")
        if not isinstance(key, str) or project_of(doc) not in scope:
            continue
        if key in first:
            selection.repeated_keys_dropped += 1
            continue
        first[key] = doc
    ids = {key: number for key, doc in first.items() if (number := _int(doc.get("id")))}

    counts = LinkCounts()
    written: dict[str, SnapshotIssueV2] = {}
    excluded: set[str] = set()

    def add(key: str) -> SnapshotIssueV2 | None:
        if key in exclusions:
            excluded.add(key)
            return None
        try:
            issue = to_issue(first[key], ids, linkmap, counts)
        except BadTime:
            selection.bad_time += 1
            return None
        written[key] = issue
        return issue

    resolved = [key for key, doc in first.items() if resolution_of(doc) is not None]
    for key in resolved:
        issue = add(key)
        if issue is not None and issue.resolved_at is None:
            selection.resolved_without_date += 1

    targets: set[str] = set()
    for issue in list(written.values()):
        target = duplicate_target(issue)
        if target is None:
            continue
        doc = first.get(target.target_key)
        if doc is not None and resolution_of(doc) is None:
            targets.add(target.target_key)
    for key in sorted(targets):
        if add(key) is not None:
            selection.open_targets += 1

    numbers: dict[int, str] = {}
    for key, issue in written.items():
        if issue.number in numbers:
            raise ValueError(f"{key} and {numbers[issue.number]} share id {issue.number}")
        numbers[issue.number] = key
    selection.issues = sorted(written.values(), key=lambda i: i.number)
    selection.excluded = len(excluded)
    selection.links_dropped = counts.dropped
    return selection


# --- report --------------------------------------------------------------------------------


def report(selection: Selection, threshold: int = DEFAULT_KIND_THRESHOLD) -> dict[str, Any]:
    """Subset, counts, kind split and in-subset duplicate pairs by kind.

    A pair is one duplicate issue whose `duplicate_target` is in the snapshot, counted
    under that issue's kind.
    """
    numbers = {issue.number for issue in selection.issues}
    kinds = {"short": 0, "log_heavy": 0}
    pairs = {"short": 0, "log_heavy": 0}
    for issue in selection.issues:
        kind = derive_kind(issue, threshold)
        kinds[kind] += 1
        target = duplicate_target(issue)
        if target is not None and target.target_number in numbers:
            pairs[kind] += 1
    return {
        "subset": {"instance": INSTANCE, "projects": list(PROJECTS), "rule": SUBSET_RULE},
        "count": len(selection.issues),
        "open_targets": selection.open_targets,
        "repeated_keys_dropped": selection.repeated_keys_dropped,
        "excluded": selection.excluded,
        "bad_time_skipped": selection.bad_time,
        "resolved_without_date": selection.resolved_without_date,
        "links_dropped": selection.links_dropped,
        "kind_threshold": threshold,
        "kinds": kinds,
        "pairs": {"total": pairs["short"] + pairs["log_heavy"], **pairs},
    }
