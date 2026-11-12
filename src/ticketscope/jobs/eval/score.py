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

Each query's keyword and dense searches also run once: hybrid fuses the same two candidate
lists that keyword and dense search for, so a per-query store (`SearchReuseStore`) fetches
each list once, with the most rows any mode asks for, and every mode reads its leading rows.
Both SQL queries order by score, then issue number, so the leading rows of a longer fetch are
exactly a shorter fetch's rows. The search time a mode skipped is added to its latency, as
for the vector.

The results carry a `timing` block, reported only: where the run's time went.
"""

import math
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from fractions import Fraction
from typing import Any, TypedDict

from ticketscope.core import modes
from ticketscope.core.model import IssueDetail, Scored
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


class Timing(TypedDict):
    """Where a run's time went, in seconds; reported, never gated."""

    query_text_seconds: float
    embed_seconds: float
    embed_calls: int
    keyword_fetches: int
    dense_fetches: int
    # Each mode's own search time, before any reused time is added to its latency.
    mode_search_seconds: dict[str, float]


class Results(TypedDict):
    k: int
    relevance: str
    modes: dict[str, ModeResults]
    skipped_modes: list[str]
    timing: Timing


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
        self.calls = 0
        self.total_ms = 0.0

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        key = tuple(texts)
        if key == self._texts:
            self._reused_ms += self._embed_ms
        else:
            started = self._clock()
            self._vectors = self._inner.embed(texts)
            self._embed_ms = (self._clock() - started) * 1000
            self._texts = key
            self.calls += 1
            self.total_ms += self._embed_ms
        return [list(vector) for vector in self._vectors]

    def take_reused_ms(self) -> float:
        """The model time skipped by repeats since the last call; resets it to zero."""
        reused, self._reused_ms = self._reused_ms, 0.0
        return reused


class SearchReuseStore:
    """A `CorpusStore` that fetches each keyword and dense candidate list once per query.

    `begin(rows)` starts a query: it forgets the last query's lists and sets how many rows a
    fetch takes (the most any mode will ask for). A search asking for no more rows than were
    fetched gets the leading rows of the stored list without a round trip, and books the
    fetch's time, which `take_reused_ms` hands to the caller's latency. Asking for more rows
    fetches again. Every other call goes straight to the inner store.
    """

    def __init__(self, inner: CorpusStore, clock: Callable[[], float] | None = None) -> None:
        self._inner = inner
        self._clock = clock or time.perf_counter
        self._rows = 0
        # key -> (hits, the fetch's time in ms, the rows it asked for)
        self._lists: dict[tuple[Any, ...], tuple[list[Scored], float, int]] = {}
        self._reused_ms = 0.0
        self.keyword_fetches = 0
        self.dense_fetches = 0

    def begin(self, rows: int) -> None:
        self._rows = rows
        self._lists.clear()
        self._reused_ms = 0.0

    def _cached(
        self, key: tuple[Any, ...], k: int, fetch: Callable[[int], list[Scored]]
    ) -> list[Scored]:
        stored = self._lists.get(key)
        if stored is not None:
            hits, fetch_ms, requested = stored
            # A fetch of n rows holds every row a smaller fetch returns; one that came back
            # with fewer than n rows holds every row there is.
            if k <= requested or len(hits) < requested:
                self._reused_ms += fetch_ms
                return hits[:k]
        requested = max(k, self._rows)
        started = self._clock()
        hits = fetch(requested)
        fetch_ms = (self._clock() - started) * 1000
        self._lists[key] = (hits, fetch_ms, requested)
        return hits[:k]

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        def fetch(rows: int) -> list[Scored]:
            self.keyword_fetches += 1
            return self._inner.keyword_search(query, rows)

        return self._cached(("keyword", query), k, fetch)

    def dense_search(self, model_id: str, vector: Sequence[float], k: int) -> list[Scored]:
        def fetch(rows: int) -> list[Scored]:
            self.dense_fetches += 1
            return self._inner.dense_search(model_id, vector, rows)

        return self._cached(("dense", model_id, tuple(vector)), k, fetch)

    def get_issue(self, number: int) -> IssueDetail | None:
        return self._inner.get_issue(number)

    def get_issue_by_key(self, key: str) -> IssueDetail | None:
        return self._inner.get_issue_by_key(key)

    def corpus_version(self) -> str | None:
        return self._inner.corpus_version()

    def has_embeddings(self, model_id: str) -> bool:
        return self._inner.has_embeddings(model_id)

    def embedding_model_id(self) -> str | None:
        return self._inner.embedding_model_id()

    def take_reused_ms(self) -> float:
        """The search time skipped by reuse since the last call; resets it to zero."""
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
    the timed search, once per query (`QueryVectorCache`), and each keyword and dense list is
    fetched once per query (`SearchReuseStore`); a mode that reuses a vector or a list has
    the skipped time added back, so every p95 includes the model and the database."""
    parsed = [as_pair(line) for line in pairs]
    cache = QueryVectorCache(embedder) if embedder is not None else None
    embedder = cache
    reuse = SearchReuseStore(store)
    registry = modes.REGISTRY
    retrievers: dict[str, Retriever] = {}
    skipped: list[str] = []
    for name, mode in registry.items():
        # Without an embedder (or its model's embeddings in the store) dense and hybrid are
        # skipped and named.
        if mode.available(store, embedder):
            retrievers[name] = mode.build(reuse, embedder)
        else:
            skipped.append(name)
    tallies = {name: _ModeTally() for name in retrievers}
    search_ms = dict.fromkeys(retrievers, 0.0)
    query_text_ms = 0.0
    for pair in parsed:
        started = time.perf_counter()
        text = query_text(store, pair.query)
        query_text_ms += (time.perf_counter() - started) * 1000
        exclude = frozenset({pair.query})
        # Hybrid asks each side for k + |exclude| hits, and a side asks the store for
        # |exclude| more: the most rows any registered mode asks for.
        reuse.begin(K + 2 * len(exclude))
        for name, retriever in retrievers.items():
            started = time.perf_counter()
            hits = retriever.search(text, K, exclude=exclude)
            latency_ms = (time.perf_counter() - started) * 1000
            search_ms[name] += latency_ms
            latency_ms += reuse.take_reused_ms()
            if cache is not None:
                latency_ms += cache.take_reused_ms()
            ranked = [hit.issue.number for hit in hits]
            tallies[name].add(pair, first_member_rank(pair.relevant, ranked), latency_ms)
    return {
        "k": K,
        "relevance": RELEVANCE,
        "modes": {name: tally.results() for name, tally in tallies.items()},
        "skipped_modes": sorted(skipped),
        "timing": {
            "query_text_seconds": round(query_text_ms / 1000, 3),
            "embed_seconds": round((cache.total_ms if cache else 0.0) / 1000, 3),
            "embed_calls": cache.calls if cache else 0,
            "keyword_fetches": reuse.keyword_fetches,
            "dense_fetches": reuse.dense_fetches,
            "mode_search_seconds": {name: round(ms / 1000, 3) for name, ms in search_ms.items()},
        },
    }
