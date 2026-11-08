"""Labelled duplicate pairs for eval (AD-26, epic-eval-gate R1).

A pair is one duplicate issue whose `duplicate_target` is in the snapshot, counted under
that issue's kind: the same rule as ingest's `report()`, which produced the Release notes'
counts. The pairs file holds numbers and kind only, sorted by query, one JSON object per
line with a fixed key order, so it regenerates byte-identical.
"""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import cast, get_args

from ticketscope.core.derive import DEFAULT_KIND_THRESHOLD, derive_kind, duplicate_target
from ticketscope.core.model import Kind
from ticketscope.core.snapshot import SnapshotIssueV2

PAIR_KEYS = ("query", "target", "kind")


@dataclass(frozen=True, slots=True, order=True)
class Pair:
    """One labelled query: the duplicate issue, the issue it duplicates, and its kind."""

    query: int
    target: int
    kind: Kind


def derive_pairs(
    issues: Iterable[SnapshotIssueV2], threshold: int = DEFAULT_KIND_THRESHOLD
) -> list[Pair]:
    """One pair per duplicate issue whose `duplicate_target` is in `issues`, sorted by query."""
    snapshot = list(issues)
    numbers = {issue.number for issue in snapshot}
    pairs: list[Pair] = []
    for issue in snapshot:
        target = duplicate_target(issue)
        if target is not None and target.target_number in numbers:
            pairs.append(Pair(issue.number, target.target_number, derive_kind(issue, threshold)))
    return sorted(pairs)


def pairs_jsonl(pairs: Iterable[Pair]) -> bytes:
    """The pairs file: one `{"query", "target", "kind"}` object per line, each `\\n`-ended,
    in the order given."""
    lines = (
        json.dumps({"query": p.query, "target": p.target, "kind": p.kind}) + "\n" for p in pairs
    )
    return "".join(lines).encode("utf-8")


def as_pair(line: Pair | Mapping[str, object]) -> Pair:
    """A `Pair` from a parsed pairs-file line; refuses other keys and wrong types."""
    if isinstance(line, Pair):
        return line
    if set(line) != set(PAIR_KEYS):
        raise ValueError(f"pair must have exactly the keys {PAIR_KEYS}, got {sorted(line)}")
    query, target, kind = line["query"], line["target"], line["kind"]
    if type(query) is not int or type(target) is not int:
        raise ValueError(f"pair query and target must be integers: {dict(line)}")
    if kind in get_args(Kind):
        return Pair(query, target, cast(Kind, kind))
    raise ValueError(f"pair kind must be one of {get_args(Kind)}: {dict(line)}")


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
