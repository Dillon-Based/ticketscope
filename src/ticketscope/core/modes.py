"""Retrieval modes and the registry that `/v1` and eval read (AD-19)."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from ticketscope.core.derive import cut_for_embedding
from ticketscope.core.model import Scored
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


def _build_keyword(store: CorpusStore, _embedder: Embedder | None) -> Retriever:
    return KeywordRetriever(store)


def _build_dense(store: CorpusStore, embedder: Embedder | None) -> Retriever:
    if embedder is None:
        raise ValueError("dense retrieval needs an embedder")
    return DenseRetriever(store, embedder)


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
    }
)
