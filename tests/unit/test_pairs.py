"""The AD-26 pair rule and the pairs-file format (story 2.1, R1, risk R-001)."""

import json
from typing import Any

import pytest

from tests.factories import snapshot_issue
from ticketscope.core.derive import duplicate_target
from ticketscope.core.pairs import (
    Pair,
    as_pair,
    count_by_kind,
    derive_pairs,
    pairs_jsonl,
    read_pairs,
)
from ticketscope.core.snapshot import DuplicateLink, SnapshotIssueV2

LOG_BODY = "```\npanic: boom\ngoroutine 1 [running]:\n```"  # kind score 3: log_heavy


def _link(target: int, direction: str = "duplicates") -> DuplicateLink:
    return DuplicateLink(
        target_number=target,
        target_key=f"MCL-{target}",
        direction=direction,  # pyright: ignore[reportArgumentType]
        link_type="Duplicate",
    )


def _duplicate(number: int, *links: DuplicateLink, **overrides: Any) -> SnapshotIssueV2:
    return snapshot_issue(
        number=number, resolution="Duplicate", duplicate_links=list(links), **overrides
    )


def test_one_pair_per_duplicate_issue_to_its_duplicate_target() -> None:
    issues = [snapshot_issue(number=1), _duplicate(2, _link(1))]
    pairs = derive_pairs(issues)
    assert pairs == [Pair(query=2, target=1, kind="short")]
    target = duplicate_target(issues[1])
    assert target is not None and pairs[0].target == target.target_number


def test_a_target_outside_the_snapshot_gives_no_pair() -> None:
    assert derive_pairs([_duplicate(2, _link(99))]) == []


def test_a_fixed_issue_with_duplicate_links_gives_no_pair() -> None:
    issues = [snapshot_issue(number=1), snapshot_issue(number=2, duplicate_links=[_link(1)])]
    assert derive_pairs(issues) == []


def test_a_duplicate_linked_both_ways_pairs_to_its_duplicates_target() -> None:
    issues = [
        snapshot_issue(number=1),
        snapshot_issue(number=5),
        _duplicate(3, _link(1, "duplicated_by"), _link(5, "duplicates")),
    ]
    assert derive_pairs(issues) == [Pair(query=3, target=5, kind="short")]


def test_two_duplicates_links_give_one_pair_to_the_lowest_number() -> None:
    issues = [snapshot_issue(number=7), snapshot_issue(number=4), _duplicate(9, _link(7), _link(4))]
    assert derive_pairs(issues) == [Pair(query=9, target=4, kind="short")]


def test_the_chosen_target_outside_the_snapshot_gives_no_pair_even_if_another_link_is_in() -> None:
    # report() counts only duplicate_target's link; the in-snapshot 7 is not a fallback.
    issues = [snapshot_issue(number=7), _duplicate(9, _link(7), _link(4))]
    assert derive_pairs(issues) == []


def test_a_pair_carries_the_query_issues_kind() -> None:
    issues = [snapshot_issue(number=1), _duplicate(2, _link(1), body=LOG_BODY)]
    assert derive_pairs(issues) == [Pair(query=2, target=1, kind="log_heavy")]


def test_pairs_are_sorted_by_query_whatever_the_input_order() -> None:
    issues = [
        _duplicate(30, _link(1)),
        snapshot_issue(number=1),
        _duplicate(4, _link(1)),
        _duplicate(12, _link(30)),
    ]
    assert [p.query for p in derive_pairs(issues)] == [4, 12, 30]


def test_pairs_jsonl_has_fixed_key_order_one_line_each_and_a_trailing_newline() -> None:
    data = pairs_jsonl([Pair(2, 1, "short"), Pair(7, 6, "log_heavy")])
    assert data == (
        b'{"query": 2, "target": 1, "kind": "short"}\n'
        b'{"query": 7, "target": 6, "kind": "log_heavy"}\n'
    )
    assert pairs_jsonl([]) == b""


def test_every_line_holds_only_numbers_and_kind() -> None:
    data = pairs_jsonl([Pair(2, 1, "short")])
    [line] = data.decode().splitlines()
    assert list(json.loads(line)) == ["query", "target", "kind"]


def test_read_pairs_round_trips() -> None:
    pairs = [Pair(2, 1, "short"), Pair(7, 6, "log_heavy")]
    assert read_pairs(pairs_jsonl(pairs)) == pairs


@pytest.mark.parametrize(
    "line",
    [
        b'{"query": 2, "target": 1}\n',
        b'{"query": 2, "target": 1, "kind": "short", "title": "x"}\n',
        b'{"query": "2", "target": 1, "kind": "short"}\n',
        b'{"query": 2, "target": 1, "kind": "medium"}\n',
        b"[2, 1]\n",
    ],
)
def test_read_pairs_refuses_a_malformed_line(line: bytes) -> None:
    with pytest.raises(ValueError, match="pairs line 1"):
        read_pairs(line)


def test_as_pair_accepts_a_parsed_mapping() -> None:
    assert as_pair({"query": 2, "target": 1, "kind": "short"}) == Pair(2, 1, "short")


def test_count_by_kind() -> None:
    pairs = [Pair(2, 1, "short"), Pair(3, 1, "short"), Pair(7, 6, "log_heavy")]
    assert count_by_kind(pairs) == {"total": 3, "short": 2, "log_heavy": 1}
