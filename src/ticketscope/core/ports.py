"""The ports `core` reaches the outside through (AD-1, AD-19)."""

from collections.abc import Sequence
from typing import Protocol

from ticketscope.core.model import IssueDetail, Scored


class CorpusStore(Protocol):
    """Read access to the loaded corpus."""

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        """Return up to `k` BM25 hits, best first, with higher-is-better scores."""
        ...

    def get_issue(self, number: int) -> IssueDetail | None:
        """Return the issue with its body, or None when `number` is not loaded."""
        ...

    def get_issue_by_key(self, key: str) -> IssueDetail | None:
        """Return the issue whose url is the browse url of `key`, or None."""
        ...

    def corpus_version(self) -> str | None:
        """Return the loaded snapshot version, or None when no corpus is loaded."""
        ...

    def dense_search(self, model_id: str, vector: Sequence[float], k: int) -> list[Scored]:
        """Return up to `k` nearest issues of `model_id` by cosine, best first.

        `score` is cosine similarity (1 - cosine distance), higher is better; ties
        break on issue number.
        """
        ...

    def has_embeddings(self, model_id: str) -> bool:
        """Whether any issue has an embedding from `model_id`."""
        ...

    def embedding_model_id(self) -> str | None:
        """The `corpus_meta` embedding model id, or None when none was computed."""
        ...


class Embedder(Protocol):
    """Turns text into vectors of one model (AD-1: the model stays behind this port)."""

    model_id: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one vector per text, in order."""
        ...


class Retriever(Protocol):
    """One retrieval mode."""

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        """Return up to `k` hits, best first, none of whose numbers is in `exclude`."""
        ...
