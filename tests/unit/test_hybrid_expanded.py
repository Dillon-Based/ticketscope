"""Expanded coverage for story 3.2: hybrid retrieval over the real fake-backed retrievers."""

import pytest

from ticketscope.core.fakes import HashEmbedder, InMemoryCorpusStore
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.modes import (
    REGISTRY,
    RRF_K,
    DenseRetriever,
    HybridRetriever,
    KeywordRetriever,
)

MODEL = "hash-fake"
TEXTS = {
    1: "kernel panic on boot",
    2: "texture glitch near spawn",
    3: "boot loop after update",
    4: "crash when loading world",
    5: "boot screen freezes",
}


def _issue(number: int, title: str | None = None) -> IssueRecord:
    return IssueRecord(
        number=number, title=title or f"t{number}", url="u", kind="short", state="closed"
    )


def _store() -> InMemoryCorpusStore:
    embedder = HashEmbedder(MODEL)
    vectors = dict(zip(TEXTS, embedder.embed(list(TEXTS.values())), strict=True))
    return InMemoryCorpusStore(
        [(_issue(n), t) for n, t in TEXTS.items()],
        corpus_version="v1",
        embeddings={MODEL: vectors},
        embedding_model=MODEL,
    )


def _hybrid() -> HybridRetriever:
    store = _store()
    return HybridRetriever(KeywordRetriever(store), DenseRetriever(store, HashEmbedder(MODEL)))


def _numbers(hits: list[Scored]) -> list[int]:
    return [h.issue.number for h in hits]


class Fixed:
    def __init__(self, hits: list[Scored]) -> None:
        self._hits = hits

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        return list(self._hits)


def test_negative_k_is_empty() -> None:
    assert _hybrid().search("boot", k=-3) == []


@pytest.mark.parametrize("k", [1, 2, 3])
def test_real_retrievers_respect_k_and_exclude(k: int) -> None:
    excluded = frozenset({1, 3})
    hits = _hybrid().search("boot", k=k, exclude=excluded)
    assert len(hits) == k
    assert not excluded & set(_numbers(hits))


def test_excluding_everything_returns_nothing() -> None:
    assert _hybrid().search("boot", k=5, exclude=frozenset(TEXTS)) == []


def test_results_are_unique_and_scores_non_increasing() -> None:
    hits = _hybrid().search("boot loop", k=5)
    numbers = _numbers(hits)
    assert len(numbers) == len(set(numbers))
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)
    assert all(0 < s <= 2 / (RRF_K + 1) for s in scores)


def test_search_is_deterministic_over_real_retrievers() -> None:
    assert _hybrid().search("boot", k=5) == _hybrid().search("boot", k=5)


def test_issue_record_comes_from_the_first_side_that_returned_it() -> None:
    keyword = Fixed([Scored(issue=_issue(7, "from keyword"), score=1.0)])
    dense = Fixed([Scored(issue=_issue(7, "from dense"), score=0.9)])
    [hit] = HybridRetriever(keyword, dense).search("q", k=1)
    assert hit.issue.title == "from keyword"
    assert hit.score == pytest.approx(2 / (RRF_K + 1))


def test_a_side_that_over_returns_still_yields_at_most_k() -> None:
    many = Fixed([Scored(issue=_issue(n), score=0.0) for n in range(1, 10)])
    hits = HybridRetriever(many, Fixed([])).search("q", k=3)
    assert _numbers(hits) == [1, 2, 3]


def test_hybrid_unavailable_for_a_store_without_the_embedding_model() -> None:
    bare = InMemoryCorpusStore([(_issue(1), "x")], corpus_version="v1")
    assert REGISTRY["hybrid"].available(bare, HashEmbedder(MODEL)) is False
    assert REGISTRY["keyword"].available(bare, None) is True
