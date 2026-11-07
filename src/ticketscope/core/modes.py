"""Retrieval modes and the registry that `/v1` and eval read (AD-19)."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

from ticketscope.core.model import Scored
from ticketscope.core.ports import CorpusStore, Retriever

ScoreKind = Literal["bm25", "cosine", "rrf"]


class KeywordRetriever:
    """BM25 keyword retrieval, ranked by the store."""

    def __init__(self, store: CorpusStore) -> None:
        self._store = store

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        # Over-fetch by |exclude| so an excluded issue never costs a slot (AD-19).
        hits = self._store.keyword_search(query, k + len(exclude))
        return [h for h in hits if h.issue.number not in exclude][: max(k, 0)]


def _always_available(_store: CorpusStore) -> bool:
    return True


@dataclass(frozen=True, slots=True)
class Mode:
    name: str
    score_kind: ScoreKind
    build: Callable[[CorpusStore], Retriever]
    # Whether the mode can serve on `store` (e.g. its embeddings are loaded); eval skips it if not.
    available: Callable[[CorpusStore], bool]


REGISTRY: Mapping[str, Mode] = MappingProxyType(
    {
        "keyword": Mode(
            name="keyword",
            score_kind="bm25",
            build=KeywordRetriever,
            available=_always_available,
        ),
    }
)
