"""In-repo fakes for the ports, so tests and the page run with no database (AD-1)."""

import hashlib
import math
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence

from ticketscope.core.derive import MOJANG_BROWSE_URL
from ticketscope.core.model import IssueDetail, IssueRecord, Scored

_TOKEN = re.compile(r"\w+")


def _terms(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity; 0.0 when either vector is all zeros."""
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    if norm == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True)) / norm


class HashEmbedder:
    """A deterministic `Embedder` with no model: each term hashes into one of `dim` buckets,
    and the counts are L2-normalised. Texts sharing terms get a high cosine."""

    def __init__(self, model_id: str = "hash-fake", dim: int = 16) -> None:
        self.model_id = model_id
        self._dim = dim
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self._dim
        for term in _terms(text):
            bucket = int.from_bytes(hashlib.sha256(term.encode()).digest()[:4], "big")
            vector[bucket % self._dim] += 1.0
        norm = math.sqrt(sum(x * x for x in vector))
        return [x / norm for x in vector] if norm else vector


class InMemoryCorpusStore:
    """A `CorpusStore` with naive term-overlap scoring.

    The score of a document is the number of occurrences in it of the query's
    distinct terms. Ties break on issue number, so results are deterministic.

    `embeddings` maps a model id to issue number -> vector and gives dense search an exact
    cosine scan; `embedding_model` is what `corpus_meta` would hold.
    """

    def __init__(
        self,
        documents: Iterable[tuple[IssueRecord, str]] = (),
        corpus_version: str | None = None,
        *,
        bodies: Mapping[int, str | None] | None = None,
        embeddings: Mapping[str, Mapping[int, Sequence[float]]] | None = None,
        embedding_model: str | None = None,
    ) -> None:
        self._docs = [(issue, Counter(_terms(text))) for issue, text in documents]
        self._version = corpus_version
        self._bodies = dict(bodies or {})
        self._embeddings = {model: dict(rows) for model, rows in (embeddings or {}).items()}
        self._embedding_model = embedding_model

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        wanted = set(_terms(query))
        hits: list[Scored] = []
        for issue, counts in self._docs:
            score = float(sum(counts[t] for t in wanted))
            if score > 0:
                hits.append(Scored(issue=issue, score=score))
        hits.sort(key=lambda s: (-s.score, s.issue.number))
        return hits[: max(k, 0)]

    def corpus_version(self) -> str | None:
        return self._version

    def get_issue(self, number: int) -> IssueDetail | None:
        for issue, _counts in self._docs:
            if issue.number == number:
                return IssueDetail(issue=issue, body=self._bodies.get(number))
        return None

    def get_issue_by_key(self, key: str) -> IssueDetail | None:
        url = MOJANG_BROWSE_URL + key
        for issue, _counts in self._docs:
            if issue.url == url:
                return IssueDetail(issue=issue, body=self._bodies.get(issue.number))
        return None

    def dense_search(self, model_id: str, vector: Sequence[float], k: int) -> list[Scored]:
        rows = self._embeddings.get(model_id, {})
        hits = [
            Scored(issue=issue, score=cosine(vector, rows[issue.number]))
            for issue, _counts in self._docs
            if issue.number in rows
        ]
        hits.sort(key=lambda s: (-s.score, s.issue.number))
        return hits[: max(k, 0)]

    def has_embeddings(self, model_id: str) -> bool:
        return bool(self._embeddings.get(model_id))

    def embedding_model_id(self) -> str | None:
        return self._embedding_model
