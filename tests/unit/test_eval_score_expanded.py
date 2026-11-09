"""Expanded coverage for story 2.2: cutoff boundaries, MRR arithmetic, p95, pair derivation.

A scripted retriever returns fixed rankings, so every metric is hand-computable.
"""

import pytest

from tests.factories import snapshot_issue
from ticketscope.core import modes
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.pairs import (
    Pair,
    derive_pairs,
    duplicate_clusters,
    pairs_jsonl,
    read_pairs,
)
from ticketscope.core.ports import CorpusStore, Embedder
from ticketscope.core.snapshot import DuplicateLink
from ticketscope.jobs.eval import score
from ticketscope.jobs.eval.score import K, p95


def _store(count: int = 30) -> InMemoryCorpusStore:
    return InMemoryCorpusStore(
        [
            (IssueRecord(n, f"t{n}", f"u{n}", "short", "closed"), f"t{n}")
            for n in range(1, count + 1)
        ]
    )


def _scripted(monkeypatch: pytest.MonkeyPatch, ranking_for: dict[int, list[int]]) -> list[object]:
    """Register one mode whose ranking depends on the query's title; returns seen excludes."""
    seen: list[object] = []

    class Scripted:
        def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
            seen.append((k, exclude))
            number = int(query.split("\n")[0].removeprefix("t"))
            return [
                Scored(IssueRecord(n, f"t{n}", f"u{n}", "short", "closed"), 0.0)
                for n in ranking_for[number]
            ]

    def build(_store: CorpusStore, _embedder: Embedder | None) -> Scripted:
        return Scripted()

    mode = modes.Mode("scripted", "bm25", build, lambda _s, _e: True)
    monkeypatch.setattr(modes, "REGISTRY", {"scripted": mode})
    return seen


def _rank_at(position: int) -> list[int]:
    """A ranking whose first cluster member (number 99) sits at 1-based `position`."""
    filler = [100 + i for i in range(position - 1)]
    return [*filler, 99]


@pytest.mark.parametrize(
    ("position", "r1", "r5", "r10", "mrr"),
    [
        (1, 1.0, 1.0, 1.0, 1.0),
        (2, 0.0, 1.0, 1.0, 0.5),
        (5, 0.0, 1.0, 1.0, 0.2),
        (6, 0.0, 0.0, 1.0, 1 / 6),
        (10, 0.0, 0.0, 1.0, 0.1),
        (11, 0.0, 0.0, 0.0, 0.0),
    ],
)
def test_cutoff_boundaries_for_one_query(
    monkeypatch: pytest.MonkeyPatch, position: int, r1: float, r5: float, r10: float, mrr: float
) -> None:
    _scripted(monkeypatch, {1: _rank_at(position)})
    result = score(_store(), [Pair(1, 99, "short", (99,))])["modes"]["scripted"]
    overall = result["overall"]
    assert (overall["recall@1"], overall["recall@5"], overall["recall@10"]) == (r1, r5, r10)
    assert overall["mrr@10"] == pytest.approx(mrr)
    assert result["first_member_ranks"] == [[1, position if position <= K else None]]


def test_mrr_and_recall_average_over_queries_and_split_by_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _scripted(monkeypatch, {1: _rank_at(1), 2: _rank_at(4), 3: _rank_at(11), 4: _rank_at(2)})
    pairs = [
        Pair(1, 99, "short", (99,)),
        Pair(2, 99, "short", (99,)),
        Pair(3, 99, "log_heavy", (99,)),
        Pair(4, 99, "log_heavy", (99,)),
    ]
    result = score(_store(), pairs)["modes"]["scripted"]
    assert result["short"]["mrr@10"] == pytest.approx((1 + 0.25) / 2)
    assert result["log_heavy"]["mrr@10"] == pytest.approx(0.25)
    assert result["overall"]["mrr@10"] == pytest.approx((1 + 0.25 + 0 + 0.5) / 4)
    assert result["overall"]["recall@5"] == 0.75
    assert result["log_heavy"]["recall@5"] == 0.5
    assert [
        r["pairs_scored"] for r in (result["short"], result["log_heavy"], result["overall"])
    ] == [
        2,
        2,
        4,
    ]
    assert result["first_member_ranks"] == [[1, 1], [2, 4], [3, None], [4, 2]]


def test_any_cluster_member_counts_and_the_query_is_excluded_from_the_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _scripted(monkeypatch, {5: [200, 8, 7]})
    result = score(_store(), [Pair(5, 7, "short", (7, 8))])["modes"]["scripted"]
    assert result["first_member_ranks"] == [[5, 2]]
    assert seen == [(K, frozenset({5}))]


def test_the_results_report_the_relevance_and_cutoff() -> None:
    out = score(_store(3), [])
    assert (out["k"], out["relevance"], out["skipped_modes"]) == (10, "cluster", ["dense"])


def test_a_missing_query_issue_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _scripted(monkeypatch, {1: []})
    with pytest.raises(LookupError, match="500"):
        score(_store(3), [Pair(500, 1, "short", (1,))])


def test_skipped_modes_are_listed_sorted(monkeypatch: pytest.MonkeyPatch) -> None:
    def never(_s: CorpusStore, _e: Embedder | None) -> bool:
        return False

    extra = {
        n: modes.Mode(n, "cosine", lambda s, _e: modes.KeywordRetriever(s), never)
        for n in ("zeta", "alpha")
    }
    monkeypatch.setattr(modes, "REGISTRY", {**modes.REGISTRY, **extra})
    assert score(_store(3), [])["skipped_modes"] == ["alpha", "dense", "zeta"]


def test_p95_nearest_rank_at_the_ceiling_boundaries() -> None:
    twenty = [float(n) for n in range(1, 21)]
    assert p95(twenty) == 19.0  # ceil(0.95 * 20) = 19
    assert p95([*twenty, 21.0]) == 20.0  # ceil(0.95 * 21) = 20 -> 20th of 21 sorted
    assert p95(list(reversed(twenty))) == 19.0


def _link(target: int, direction: str = "duplicates") -> DuplicateLink:
    return DuplicateLink(
        target_number=target,
        target_key=f"MCL-{target}",
        direction=direction,  # pyright: ignore[reportArgumentType]
        link_type="Duplicate",
    )


def test_derived_relevant_is_sorted_excludes_the_query_and_holds_the_target() -> None:
    issues = [
        snapshot_issue(number=9, resolution="Duplicate", duplicate_links=[_link(3)]),
        snapshot_issue(number=3, duplicate_links=[]),
        snapshot_issue(number=5, resolution="Duplicate", duplicate_links=[_link(3)]),
        snapshot_issue(number=7, duplicate_links=[_link(5, "duplicated_by")]),
        snapshot_issue(number=40, duplicate_links=[]),
    ]
    pairs = {p.query: p for p in derive_pairs(issues)}
    assert pairs[9].relevant == (3, 5, 7)
    assert pairs[5].relevant == (3, 7, 9)
    assert all(p.query not in p.relevant and p.target in p.relevant for p in pairs.values())


def test_clusters_are_ordered_by_smallest_member_and_include_singletons() -> None:
    issues = [
        snapshot_issue(number=8, duplicate_links=[_link(2)]),
        snapshot_issue(number=2, duplicate_links=[]),
        snapshot_issue(number=1, duplicate_links=[]),
    ]
    assert duplicate_clusters(issues) == (frozenset({1}), frozenset({2, 8}))


def test_the_pairs_file_round_trips_relevant_and_regenerates_identically() -> None:
    pairs = [Pair(2, 1, "short", (1, 4)), Pair(4, 1, "log_heavy", (1, 2))]
    data = pairs_jsonl(pairs)
    assert read_pairs(data) == pairs
    assert pairs_jsonl(read_pairs(data)) == data
