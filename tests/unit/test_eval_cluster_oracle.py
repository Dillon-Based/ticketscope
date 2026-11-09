"""Story 2.2 (ticketscope--e2-s2), ATDD red phase: cluster metrics equal the oracle.

Remove the skip marker when story 2.2's build replaces target-only relevance with the
duplicate cluster. The test must fail first, then pass. Expected values come from
`tests/eval_oracle.py`, which the build session does not edit (epic-eval-gate test design,
R-005).

The seam this scaffold assumes, extending story 2.1's `score(store, pairs)`:

- Each pairs line carries `relevant`: the query's cluster minus the query, sorted. Cluster
  links live only in the snapshot, so the pairs file is where eval can get them.
- `results["relevance"] == "cluster"`, and `results["modes"][<mode>]` holds `"short"`,
  `"log_heavy"` and `"overall"`, each with `"recall@1"`, `"recall@5"`, `"recall@10"`,
  `"mrr@10"` and `"pairs_scored"`, plus `"first_member_ranks"`: `[query, rank or None]`
  pairs sorted by query.

If the build carries the cluster or names the keys differently, it may adapt this file's
setup and key lookups, and must record that in its plan. The oracle values and what each
assertion means do not change. Story 2.1's `test_p0_ac1_keyword_target_only_metrics_match_
the_oracle` is retired by this story: its target-only values no longer hold, and its `k`,
`exclude` and `pairs_scored` checks are carried here.
"""

import importlib
from collections.abc import Mapping
from types import MappingProxyType

import pytest

from tests import eval_oracle as oracle
from ticketscope.core import modes
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.ports import CorpusStore, Embedder, Retriever

KINDS = ("short", "log_heavy", "overall")
METRICS = ("recall@1", "recall@5", "recall@10", "mrr@10")
ORACLE_ISSUES = sorted({n for link in oracle.DUPLICATE_LINKS for n in link} | set(oracle.FILLERS))
QUERY_KIND: dict[int, oracle.Kind] = {pair["query"]: pair["kind"] for pair in oracle.PAIRS}

type Call = tuple[int, str, int, frozenset[int]]


def _title_token(number: int) -> str:
    return f"[oracle-{number}-title]"


def _record(number: int) -> IssueRecord:
    return IssueRecord(
        number=number,
        title=f"Oracle issue {number} {_title_token(number)}",
        url=f"https://bugs.mojang.com/browse/MC-{number}",
        kind=QUERY_KIND.get(number, "short"),
        state="closed",
    )


RECORDS = {number: _record(number) for number in ORACLE_ISSUES}


def _oracle_store() -> InMemoryCorpusStore:
    return InMemoryCorpusStore(
        [(record, record.title) for record in RECORDS.values()],
        corpus_version="oracle",
        bodies={n: f"Oracle description {n}" for n in ORACLE_ISSUES},
    )


def _cluster_pairs(queries: Mapping[int, object] | None = None) -> list[dict[str, object]]:
    return [
        {**pair, "relevant": sorted(oracle.CLUSTER_RELEVANT[pair["query"]])}
        for pair in oracle.PAIRS
        if queries is None or pair["query"] in queries
    ]


class ScriptedRetriever:
    """Returns the scripted ranking for the query issue whose title the query text carries,
    and records every call as (query issue, query text, k, exclude)."""

    def __init__(self, rankings: Mapping[int, tuple[int, ...]], calls: list[Call]) -> None:
        self._rankings = rankings
        self._calls = calls

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        # Text naming no single scripted query is recorded as -1 and gets no hits, so the
        # metric assertions fail first and the call-log assertion then shows which text.
        matched = [n for n in self._rankings if _title_token(n) in query]
        number = matched[0] if len(matched) == 1 else -1
        self._calls.append((number, query, k, exclude))
        ranking = self._rankings.get(number, ())[:k]
        return [Scored(issue=RECORDS[n], score=float(10 - i)) for i, n in enumerate(ranking)]


def _scripted_keyword(rankings: Mapping[int, tuple[int, ...]], calls: list[Call]) -> modes.Mode:
    def build(_store: CorpusStore, _embedder: Embedder | None) -> Retriever:
        return ScriptedRetriever(rankings, calls)

    def available(_store: CorpusStore, _embedder: Embedder | None) -> bool:
        return True

    return modes.Mode(name="keyword", score_kind="bm25", build=build, available=available)


@pytest.mark.criterion("ticketscope--e2-s2--AC-1")
def test_p0_ac1_cluster_metrics_match_the_oracle(monkeypatch: pytest.MonkeyPatch) -> None:
    """[P0] AC-1: every cluster metric, short, log-heavy and overall, equals the oracle; a
    sibling counts as a hit; overall is over all queries; the query never scores itself."""
    eval_job = importlib.import_module("ticketscope.jobs.eval")
    calls: list[Call] = []
    # Replaced after import, so a job that binds the registry at import fails (AD-19, R-002).
    monkeypatch.setattr(
        modes, "REGISTRY", MappingProxyType({"keyword": _scripted_keyword(oracle.RANKINGS, calls)})
    )

    results = eval_job.score(_oracle_store(), _cluster_pairs())

    keyword = results["modes"]["keyword"]
    # Query 3's sibling at rank 4 is a hit: 4/5, where target-only relevance gives 3/5.
    assert keyword["overall"]["recall@10"] == pytest.approx(
        float(oracle.CLUSTER_EXPECTED["overall"]["recall@10"]), abs=oracle.TOLERANCE
    )
    actual = {(kind, metric): keyword[kind][metric] for kind in KINDS for metric in METRICS}
    expected = {
        (kind, metric): float(oracle.CLUSTER_EXPECTED[kind][metric])
        for kind in KINDS
        for metric in METRICS
    }
    assert actual == pytest.approx(expected, abs=oracle.TOLERANCE)
    assert {kind: keyword[kind]["pairs_scored"] for kind in KINDS} == oracle.CLUSTER_PAIRS_BY_KIND
    assert results["relevance"] == "cluster"
    assert keyword["first_member_ranks"] == [
        [query, rank] for query, rank in sorted(oracle.FIRST_MEMBER_RANKS.items())
    ]
    assert sorted(number for number, _text, _k, _exclude in calls) == sorted(oracle.RANKINGS)
    for number, _text, k, exclude in calls:
        assert k == 10
        assert exclude == frozenset({number})

    # The query never scores itself, even when a retriever returns it.
    self_calls: list[Call] = []
    monkeypatch.setattr(
        modes,
        "REGISTRY",
        MappingProxyType({"keyword": _scripted_keyword(oracle.SELF_RANKING, self_calls)}),
    )
    alone = eval_job.score(_oracle_store(), _cluster_pairs(oracle.SELF_RANKING))
    assert alone["modes"]["keyword"]["overall"]["recall@10"] == 0.0
    assert alone["modes"]["keyword"]["overall"]["mrr@10"] == 0.0
