"""Story 2.1 (ticketscope--e2-s1), ATDD red phase: `jobs.eval` scores keyword on the oracle.

Remove the skip marker when story 2.1's build adds `ticketscope.jobs.eval`. The test must
fail first (no module), then pass. Expected values come from `tests/eval_oracle.py`, which
the build session does not edit (epic-eval-gate test design, R-005).

The seam this scaffold assumes, from the story description and spine AD-19:

- `ticketscope.jobs.eval.score(store, pairs)` scores every mode in `core.modes.REGISTRY`
  whose `available(store)` holds. It reads the registry when called, not at import.
- `pairs` are the parsed lines of `eval/pairs/<snapshot>.jsonl`: `query`, `target`, `kind`.
- Each query's text comes from the query issue's title and description, read through the
  store; each mode is searched with `k=10` and the query issue in `exclude`.
- It returns the results JSON as a dict, with `results["modes"][<mode name>]` holding
  `"recall@10"`, `"mrr@10"` and `"pairs_scored"`.

If the build names the call or the keys differently, it may adapt this file's call site and
key lookups, and must record that in its plan. The oracle values and what each assertion
means do not change.
"""

import importlib
from types import MappingProxyType

import pytest

from tests import eval_oracle as oracle
from ticketscope.core import modes
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.ports import CorpusStore, Retriever

ORACLE_ISSUES = sorted({n for link in oracle.DUPLICATE_LINKS for n in link} | set(oracle.FILLERS))
QUERY_KIND: dict[int, oracle.Kind] = {pair["query"]: pair["kind"] for pair in oracle.PAIRS}


def _title_token(number: int) -> str:
    return f"[oracle-{number}-title]"


def _description_token(number: int) -> str:
    return f"[oracle-{number}-description]"


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
        bodies={n: f"Oracle description {n} {_description_token(n)}" for n in ORACLE_ISSUES},
    )


class ScriptedRetriever:
    """Returns the oracle's ranking for the query issue whose title the query text carries,
    and records every call as (query issue, query text, k, exclude)."""

    def __init__(self, calls: list[tuple[int, str, int, frozenset[int]]]) -> None:
        self._calls = calls

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        # Text naming no single oracle query is recorded as -1 and gets no hits, so the metric
        # assertions fail first and the call-log assertion then shows which text was wrong.
        matched = [n for n in oracle.RANKINGS if _title_token(n) in query]
        number = matched[0] if len(matched) == 1 else -1
        self._calls.append((number, query, k, exclude))
        ranking = oracle.RANKINGS.get(number, ())[:k]
        return [Scored(issue=RECORDS[n], score=float(10 - i)) for i, n in enumerate(ranking)]


def _scripted_keyword(calls: list[tuple[int, str, int, frozenset[int]]]) -> modes.Mode:
    def build(_store: CorpusStore) -> Retriever:
        return ScriptedRetriever(calls)

    def available(_store: CorpusStore) -> bool:
        return True

    return modes.Mode(name="keyword", score_kind="bm25", build=build, available=available)


@pytest.mark.skip(
    reason=(
        "ATDD red phase, [P0] AC-1: keyword's Recall@10 and MRR@10 over every pair. "
        "Remove when story 2.1 adds ticketscope.jobs.eval."
    )
)
@pytest.mark.criterion("ticketscope--e2-s1--AC-1")
def test_p0_ac1_keyword_target_only_metrics_match_the_oracle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[P0] AC-1: keyword's Recall@10 and MRR@10, over every pair, equal the hand-computed
    target-only oracle; every query is searched with k=10 and its own issue excluded."""
    eval_job = importlib.import_module("ticketscope.jobs.eval")
    calls: list[tuple[int, str, int, frozenset[int]]] = []
    # Replaced after import, so a job that binds the registry at import fails (AD-19, R-002).
    monkeypatch.setattr(modes, "REGISTRY", MappingProxyType({"keyword": _scripted_keyword(calls)}))

    results = eval_job.score(_oracle_store(), [dict(pair) for pair in oracle.PAIRS])

    keyword = results["modes"]["keyword"]
    assert keyword["recall@10"] == pytest.approx(
        float(oracle.TARGET_ONLY_RECALL_AT_10), abs=oracle.TOLERANCE
    )
    assert keyword["mrr@10"] == pytest.approx(
        float(oracle.TARGET_ONLY_MRR_AT_10), abs=oracle.TOLERANCE
    )
    assert keyword["pairs_scored"] == len(oracle.PAIRS)
    assert sorted(number for number, _text, _k, _exclude in calls) == sorted(oracle.RANKINGS)
    for number, text, k, exclude in calls:
        assert k == 10
        assert exclude == frozenset({number})
        assert _description_token(number) in text
