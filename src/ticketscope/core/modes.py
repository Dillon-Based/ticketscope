"""Retrieval modes and the registry that `/v1` and eval read (AD-19)."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from ticketscope.core.derive import cut_for_embedding
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.ports import CorpusStore, Embedder, Retriever

ScoreKind = Literal["bm25", "cosine", "rrf"]


class KeywordRetriever:
    """BM25 keyword retrieval, ranked by the store."""

    def __init__(self, store: CorpusStore) -> None:
        self._store = store

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        # Over-fetch by |exclude| so an excluded issue never costs a slot (AD-19).
        hits = self._store.keyword_search(query, k + len(exclude))
        return [h for h in hits if h.issue.number not in exclude][: max(k, 0)]


class DenseRetriever:
    """Cosine retrieval over stored embeddings: the query is cut like a document, embedded,
    and the store returns the nearest issues."""

    def __init__(self, store: CorpusStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        if k <= 0:
            return []
        [vector] = self._embedder.embed([cut_for_embedding(query)])
        # Over-fetch by |exclude| so an excluded issue never costs a slot (AD-19).
        hits = self._store.dense_search(self._embedder.model_id, vector, k + len(exclude))
        return [h for h in hits if h.issue.number not in exclude][:k]


RRF_K = 60
"""The fixed reciprocal-rank-fusion constant (AD-19); not tuned per query."""


class HybridRetriever:
    """Keyword and dense fused by reciprocal rank fusion with equal weights.

    Each side supplies `k + |exclude|` candidates with the excluded issues already out, so an
    excluded issue neither scores nor costs a slot. An issue's score is the sum of
    `1 / (RRF_K + rank)` over the sides it appears in; ties break on issue number."""

    def __init__(self, keyword: Retriever, dense: Retriever) -> None:
        self._sides = (keyword, dense)

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        if k <= 0:
            return []
        wanted = k + len(exclude)
        fused: dict[int, float] = {}
        issues: dict[int, IssueRecord] = {}
        for side in self._sides:
            for rank, hit in enumerate(side.search(query, wanted, exclude), start=1):
                number = hit.issue.number
                issues.setdefault(number, hit.issue)
                fused[number] = fused.get(number, 0.0) + 1.0 / (RRF_K + rank)
        ranked = sorted(fused, key=lambda number: (-fused[number], number))
        return [Scored(issue=issues[n], score=fused[n]) for n in ranked[:k]]


def _build_keyword(store: CorpusStore, _embedder: Embedder | None) -> Retriever:
    return KeywordRetriever(store)


def _build_dense(store: CorpusStore, embedder: Embedder | None) -> Retriever:
    if embedder is None:
        raise ValueError("dense retrieval needs an embedder")
    return DenseRetriever(store, embedder)


def _build_hybrid(store: CorpusStore, embedder: Embedder | None) -> Retriever:
    if embedder is None:
        raise ValueError("hybrid retrieval needs an embedder")
    return HybridRetriever(KeywordRetriever(store), DenseRetriever(store, embedder))


def _always_available(_store: CorpusStore, _embedder: Embedder | None) -> bool:
    return True


def _dense_available(store: CorpusStore, embedder: Embedder | None) -> bool:
    return embedder is not None and store.has_embeddings(embedder.model_id)


@dataclass(frozen=True, slots=True)
class Mode:
    name: str
    score_kind: ScoreKind
    build: Callable[[CorpusStore, Embedder | None], Retriever]
    # Whether the mode can serve on `store` with `embedder` (e.g. its embeddings are loaded);
    # eval skips it if not.
    available: Callable[[CorpusStore, Embedder | None], bool]


REGISTRY: Mapping[str, Mode] = MappingProxyType(
    {
        "keyword": Mode(
            name="keyword",
            score_kind="bm25",
            build=_build_keyword,
            available=_always_available,
        ),
        "dense": Mode(
            name="dense",
            score_kind="cosine",
            build=_build_dense,
            available=_dense_available,
        ),
        "hybrid": Mode(
            name="hybrid",
            score_kind="rrf",
            build=_build_hybrid,
            # Keyword is always there, so hybrid is available exactly when dense is.
            available=_dense_available,
        ),
    }
)
