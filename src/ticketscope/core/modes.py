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

    def search(self, query: str, k: int) -> list[Scored]:
        return self._store.keyword_search(query, k)


@dataclass(frozen=True, slots=True)
class Mode:
    name: str
    score_kind: ScoreKind
    build: Callable[[CorpusStore], Retriever]


REGISTRY: Mapping[str, Mode] = MappingProxyType(
    {
        "keyword": Mode(name="keyword", score_kind="bm25", build=KeywordRetriever),
    }
)
