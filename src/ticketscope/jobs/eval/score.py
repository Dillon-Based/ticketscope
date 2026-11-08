"""Score every available retrieval mode on the labelled pairs (AD-19, AD-26).

Story 2.1's relevance is the linked target only: Recall@10 is the share of pairs whose
target is in the mode's top 10, and MRR@10 is the mean of 1/rank of that target, 0 past
rank 10. Each query is the query issue's title and description (no comments), searched
with `k=10` and the query issue excluded. The registry is read when `score` is called,
so a newly registered mode is scored with no change here.
"""

from collections.abc import Iterable, Mapping
from fractions import Fraction
from typing import TypedDict

from ticketscope.core import modes
from ticketscope.core.pairs import Pair, as_pair
from ticketscope.core.ports import CorpusStore, Retriever

K = 10
RELEVANCE = "target"

ModeScores = TypedDict(
    "ModeScores",
    {"recall@10": float, "mrr@10": float, "pairs_scored": int},
)


class Results(TypedDict):
    k: int
    relevance: str
    modes: dict[str, ModeScores]


def query_text(store: CorpusStore, number: int) -> str:
    """The query issue's title, a blank line, then its description (as load indexes it)."""
    detail = store.get_issue(number)
    if detail is None:
        raise LookupError(f"query issue {number} is not in the loaded corpus")
    return f"{detail.issue.title}\n\n{detail.body or ''}"


class _Tally:
    def __init__(self) -> None:
        self.hits = 0
        self.reciprocal_ranks = Fraction(0)

    def add(self, target: int, ranked: list[int]) -> None:
        top = ranked[:K]
        if target in top:
            self.hits += 1
            self.reciprocal_ranks += Fraction(1, top.index(target) + 1)

    def scores(self, scored: int) -> ModeScores:
        if scored == 0:
            return {"recall@10": 0.0, "mrr@10": 0.0, "pairs_scored": 0}
        return {
            "recall@10": float(Fraction(self.hits, scored)),
            "mrr@10": float(self.reciprocal_ranks / scored),
            "pairs_scored": scored,
        }


def score(store: CorpusStore, pairs: Iterable[Pair | Mapping[str, object]]) -> Results:
    """Target-only Recall@10 and MRR@10 for every mode whose `available(store)` holds."""
    parsed = [as_pair(line) for line in pairs]
    retrievers: dict[str, Retriever] = {
        name: mode.build(store) for name, mode in modes.REGISTRY.items() if mode.available(store)
    }
    tallies = {name: _Tally() for name in retrievers}
    for pair in parsed:
        text = query_text(store, pair.query)
        exclude = frozenset({pair.query})
        for name, retriever in retrievers.items():
            hits = retriever.search(text, K, exclude=exclude)
            tallies[name].add(pair.target, [hit.issue.number for hit in hits])
    return {
        "k": K,
        "relevance": RELEVANCE,
        "modes": {name: tally.scores(len(parsed)) for name, tally in tallies.items()},
    }
