"""Score every available retrieval mode on the labelled pairs (AD-19, AD-26).

Relevance is the query's duplicate cluster (`Pair.relevant`): a query is a hit at k when any
cluster member is in the mode's top k. Recall@1/5/10 are hit rates, MRR@10 uses the first
member's rank (0 past rank 10), and each is tallied per kind and over all queries (never as
the mean of the kind means). Each query is the query issue's title and description (no
comments), searched with `k=10` and the query issue excluded; each search is timed. The
registry is read when `score` is called, so a newly registered mode is scored with no change
here.

Each query is embedded once: dense and hybrid both ask for the same text's vector, so the
second asks a one-entry cache (`QueryVectorCache`) and gets the identical vector, and ranks
cannot change. The embedding time the second mode skipped is added to its measured latency,
so every embedding mode's p95 still includes the model.
"""

import math
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from fractions import Fraction
from typing import Any, TypedDict

from ticketscope.core import modes
from ticketscope.core.pairs import Pair, as_pair
from ticketscope.core.ports import CorpusStore, Embedder, Retriever

K = 10
RELEVANCE = "cluster"
KINDS = ("short", "log_heavy")
CUTOFFS = (1, 5, 10)

KindScores = TypedDict(
    "KindScores",
    {
        "recall@1": float,
        "recall@5": float,
        "recall@10": float,
        "mrr@10": float,
        "p95_latency_ms": float,
        "pairs_scored": int,
    },
)


class ModeResults(TypedDict):
    short: KindScores
    log_heavy: KindScores
    overall: KindScores
    first_member_ranks: list[list[int | None]]


class Results(TypedDict):
    k: int
    relevance: str
    modes: dict[str, ModeResults]
    skipped_modes: list[str]


def query_text(store: CorpusStore, number: int) -> str:
    """The query issue's title, a blank line, then its description (as load indexes it)."""
    detail = store.get_issue(number)
    if detail is None:
        raise LookupError(f"query issue {number} is not in the loaded corpus")
    return f"{detail.issue.title}\n\n{detail.body or ''}"


class QueryVectorCache:
    """An `Embedder` that remembers the last texts it embedded and their vectors.

    A repeat of the same texts returns copies of the stored vectors without calling the
    model, and books the time the model took for them, which `take_reused_ms` hands to the
    caller's latency. One entry only: the eval asks for one query at a time.
    """

    def __init__(self, inner: Embedder, clock: Callable[[], float] | None = None) -> None:
        self.model_id = inner.model_id
        self._inner = inner
        self._clock = clock or time.perf_counter
        self._texts: tuple[str, ...] | None = None
        self._vectors: list[list[float]] = []
        self._embed_ms = 0.0
        self._reused_ms = 0.0

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        key = tuple(texts)
        if key == self._texts:
            self._reused_ms += self._embed_ms
        else:
            started = self._clock()
            self._vectors = self._inner.embed(texts)
            self._embed_ms = (self._clock() - started) * 1000
            self._texts = key
        return [list(vector) for vector in self._vectors]

    def take_reused_ms(self) -> float:
        """The model time skipped by repeats since the last call; resets it to zero."""
        reused, self._reused_ms = self._reused_ms, 0.0
        return reused


def first_member_rank(relevant: Iterable[int], ranked: list[int]) -> int | None:
    """The 1-based rank of the first cluster member in the top `K` of `ranked`, else None."""
    members = set(relevant)
    for rank, number in enumerate(ranked[:K], start=1):
        if number in members:
            return rank
    return None


def p95(latencies_ms: list[float]) -> float:
    """Nearest-rank 95th percentile; 0.0 for no searches."""
    if not latencies_ms:
        return 0.0
    ordered = sorted(latencies_ms)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


class _Tally:
    def __init__(self) -> None:
        self.scored = 0
        self.hits = {cutoff: 0 for cutoff in CUTOFFS}
        self.reciprocal_ranks = Fraction(0)
        self.latencies_ms: list[float] = []

    def add(self, rank: int | None, latency_ms: float) -> None:
        self.scored += 1
        self.latencies_ms.append(latency_ms)
        if rank is None:
            return
        self.reciprocal_ranks += Fraction(1, rank)
        for cutoff in CUTOFFS:
            if rank <= cutoff:
                self.hits[cutoff] += 1

    def scores(self) -> KindScores:
        n = self.scored

        def rate(count: int | Fraction) -> float:
            return float(Fraction(count) / n) if n else 0.0

        return {
            "recall@1": rate(self.hits[1]),
            "recall@5": rate(self.hits[5]),
            "recall@10": rate(self.hits[10]),
            "mrr@10": rate(self.reciprocal_ranks),
            "p95_latency_ms": p95(self.latencies_ms),
            "pairs_scored": n,
        }


class _ModeTally:
    def __init__(self) -> None:
        self.kinds = {kind: _Tally() for kind in KINDS}
        self.overall = _Tally()
        self.ranks: dict[int, int | None] = {}

    def add(self, pair: Pair, rank: int | None, latency_ms: float) -> None:
        self.kinds[pair.kind].add(rank, latency_ms)
        self.overall.add(rank, latency_ms)
        self.ranks[pair.query] = rank

    def results(self) -> ModeResults:
        return {
            "short": self.kinds["short"].scores(),
            "log_heavy": self.kinds["log_heavy"].scores(),
            "overall": self.overall.scores(),
            "first_member_ranks": [[query, rank] for query, rank in sorted(self.ranks.items())],
        }


def score(
    store: CorpusStore,
    pairs: Iterable[Pair | Mapping[str, Any]],
    embedder: Embedder | None = None,
) -> Results:
    """Cluster Recall@1/5/10, MRR@10 and p95 latency, per kind and overall, for every mode
    whose `available(store, embedder)` holds; the other registry modes are named in
    `skipped_modes`. Dense and hybrid embed each query's text live through `embedder` inside
    the timed search, once per query (`QueryVectorCache`); the mode that reuses the vector
    has the model's time added back, so both p95s include the model."""
    parsed = [as_pair(line) for line in pairs]
    cache = QueryVectorCache(embedder) if embedder is not None else None
    embedder = cache
    registry = modes.REGISTRY
    retrievers: dict[str, Retriever] = {}
    skipped: list[str] = []
    for name, mode in registry.items():
        # Without an embedder (or its model's embeddings in the store) dense and hybrid are
        # skipped and named.
        if mode.available(store, embedder):
            retrievers[name] = mode.build(store, embedder)
        else:
            skipped.append(name)
    tallies = {name: _ModeTally() for name in retrievers}
    for pair in parsed:
        text = query_text(store, pair.query)
        exclude = frozenset({pair.query})
        for name, retriever in retrievers.items():
            started = time.perf_counter()
            hits = retriever.search(text, K, exclude=exclude)
            latency_ms = (time.perf_counter() - started) * 1000
            if cache is not None:
                latency_ms += cache.take_reused_ms()
            ranked = [hit.issue.number for hit in hits]
            tallies[name].add(pair, first_member_rank(pair.relevant, ranked), latency_ms)
    return {
        "k": K,
        "relevance": RELEVANCE,
        "modes": {name: tally.results() for name, tally in tallies.items()},
        "skipped_modes": sorted(skipped),
    }
