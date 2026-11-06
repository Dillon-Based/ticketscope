"""In-repo fakes for the ports, so tests and the page run with no database (AD-1)."""

import re
from collections import Counter
from collections.abc import Iterable

from ticketscope.core.model import IssueRecord, Scored

_TOKEN = re.compile(r"\w+")


def _terms(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class InMemoryCorpusStore:
    """A `CorpusStore` with naive term-overlap scoring.

    The score of a document is the number of occurrences in it of the query's
    distinct terms. Ties break on issue number, so results are deterministic.
    """

    def __init__(
        self,
        documents: Iterable[tuple[IssueRecord, str]] = (),
        corpus_version: str | None = None,
    ) -> None:
        self._docs = [(issue, Counter(_terms(text))) for issue, text in documents]
        self._version = corpus_version

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
