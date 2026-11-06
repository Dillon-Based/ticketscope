"""The ports `core` reaches the outside through (AD-1, AD-19)."""

from typing import Protocol

from ticketscope.core.model import Scored


class CorpusStore(Protocol):
    """Read access to the loaded corpus."""

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        """Return up to `k` BM25 hits, best first, with higher-is-better scores."""
        ...

    def corpus_version(self) -> str | None:
        """Return the loaded snapshot version, or None when no corpus is loaded."""
        ...


class Retriever(Protocol):
    """One retrieval mode."""

    def search(self, query: str, k: int) -> list[Scored]: ...
