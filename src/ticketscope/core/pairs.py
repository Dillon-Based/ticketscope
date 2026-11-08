"""Labelled duplicate pairs for eval (AD-26, epic-eval-gate R1).

A pair is one duplicate issue whose `duplicate_target` is in the snapshot, counted under
that issue's kind: the same rule as ingest's `report()`, which produced the Release notes'
counts. The pairs file holds query, target, kind and relevant members, sorted by query, one
JSON object per line with a fixed key order, so it regenerates byte-identical.

Each pair also carries `relevant`: the query's duplicate cluster minus the query. A cluster
is a connected component over every in-subset `duplicate_links` entry of every issue, in
both directions (epic-eval-gate Hit definition). The links live only in the snapshot, so
the pairs file is where eval gets them.
"""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import cast, get_args

from ticketscope.core.derive import DEFAULT_KIND_THRESHOLD, derive_kind, duplicate_target
from ticketscope.core.model import Kind
from ticketscope.core.snapshot import SnapshotIssueV2

PAIR_KEYS = ("query", "target", "kind", "relevant")


@dataclass(frozen=True, slots=True, order=True)
class Pair:
    """One labelled query: the duplicate issue, the issue it duplicates, its kind, and the
    other members of its duplicate cluster (sorted, never the query, always the target)."""

    query: int
    target: int
    kind: Kind
    relevant: tuple[int, ...]


def duplicate_clusters(issues: Iterable[SnapshotIssueV2]) -> tuple[frozenset[int], ...]:
    """Connected components of the in-subset duplicate links, singletons included, ordered by
    smallest member. A link to an issue outside `issues` adds no member."""
    snapshot = list(issues)
    parent = {issue.number: issue.number for issue in snapshot}

    def find(number: int) -> int:
        while parent[number] != number:
            parent[number] = parent[parent[number]]
            number = parent[number]
        return number

    for issue in snapshot:
        for link in issue.duplicate_links:
            if link.target_number in parent:
                low, high = sorted((find(issue.number), find(link.target_number)))
                parent[high] = low
    groups: dict[int, set[int]] = {}
    for number in parent:
        groups.setdefault(find(number), set()).add(number)
    return tuple(frozenset(members) for _root, members in sorted(groups.items()))


def derive_pairs(
    issues: Iterable[SnapshotIssueV2], threshold: int = DEFAULT_KIND_THRESHOLD
) -> list[Pair]:
    """One pair per duplicate issue whose `duplicate_target` is in `issues`, sorted by query."""
    snapshot = list(issues)
    numbers = {issue.number for issue in snapshot}
    cluster_of = {n: cluster for cluster in duplicate_clusters(snapshot) for n in cluster}
    pairs: list[Pair] = []
    for issue in snapshot:
        target = duplicate_target(issue)
        if target is not None and target.target_number in numbers:
            relevant = tuple(sorted(cluster_of[issue.number] - {issue.number}))
            pairs.append(
                Pair(issue.number, target.target_number, derive_kind(issue, threshold), relevant)
            )
    return sorted(pairs)


def pairs_jsonl(pairs: Iterable[Pair]) -> bytes:
    """The pairs file: one `{"query", "target", "kind", "relevant"}` object per line, each
    `\\n`-ended, in the order given."""
    lines = (
        json.dumps(
            {"query": p.query, "target": p.target, "kind": p.kind, "relevant": list(p.relevant)}
        )
        + "\n"
        for p in pairs
    )
    return "".join(lines).encode("utf-8")


def as_pair(line: Pair | Mapping[str, object]) -> Pair:
    """A `Pair` from a parsed pairs-file line; refuses other keys and wrong types."""
    if isinstance(line, Pair):
        return line
    if set(line) != set(PAIR_KEYS):
        raise ValueError(f"pair must have exactly the keys {PAIR_KEYS}, got {sorted(line)}")
    query, target, kind, relevant = line["query"], line["target"], line["kind"], line["relevant"]
    if type(query) is not int or type(target) is not int:
        raise ValueError(f"pair query and target must be integers: {dict(line)}")
    if kind not in get_args(Kind):
        raise ValueError(f"pair kind must be one of {get_args(Kind)}: {dict(line)}")
    if not isinstance(relevant, list) or any(
        type(n) is not int for n in cast(list[object], relevant)
    ):
        raise ValueError(f"pair relevant must be a list of integers: {dict(line)}")
    members = tuple(cast(list[int], relevant))
    if list(members) != sorted(set(members)):
        raise ValueError(f"pair relevant must be sorted and unique: {dict(line)}")
    if query in members or target not in members:
        raise ValueError(f"pair relevant must hold the target and not the query: {dict(line)}")
    return Pair(query, target, cast(Kind, kind), members)


def read_pairs(data: bytes) -> list[Pair]:
    """Parse a pairs file written by `pairs_jsonl`."""
    pairs: list[Pair] = []
    for lineno, line in enumerate(data.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed: object = json.loads(line)
            if not isinstance(parsed, dict):
                raise ValueError("not a JSON object")
            pairs.append(as_pair(cast(dict[str, object], parsed)))
        except ValueError as exc:
            raise ValueError(f"pairs line {lineno}: {exc}") from exc
    return pairs


def count_by_kind(pairs: Iterable[Pair]) -> dict[str, int]:
    """`total`, `short` and `log_heavy` pair counts, as the Release notes give them."""
    counts = {kind: 0 for kind in get_args(Kind)}
    for pair in pairs:
        counts[pair.kind] += 1
    return {"total": sum(counts.values()), **counts}
