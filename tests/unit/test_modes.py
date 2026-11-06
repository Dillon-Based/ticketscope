from itertools import pairwise

from tests.target import NO_MATCH_QUERY, TARGET_NUMBER, TARGET_QUERY
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord
from ticketscope.core.modes import REGISTRY, KeywordRetriever


def _issue(number: int) -> IssueRecord:
    return IssueRecord(number=number, title=f"t{number}", url="u", kind="short", state="closed")


def test_registry_holds_keyword_only() -> None:
    assert set(REGISTRY) == {"keyword"}
    mode = REGISTRY["keyword"]
    assert mode.name == "keyword"
    assert mode.score_kind == "bm25"


def test_registry_builds_a_keyword_retriever() -> None:
    assert isinstance(REGISTRY["keyword"].build(InMemoryCorpusStore()), KeywordRetriever)


def test_keyword_ranks_by_overlap_then_number() -> None:
    store = InMemoryCorpusStore(
        [
            (_issue(3), "alpha"),
            (_issue(1), "alpha beta beta"),
            (_issue(2), "alpha"),
            (_issue(4), "gamma"),
        ]
    )
    hits = KeywordRetriever(store).search("Alpha BETA", k=10)
    assert [h.issue.number for h in hits] == [1, 2, 3]
    assert [h.score for h in hits] == [3.0, 1.0, 1.0]


def test_keyword_honours_k() -> None:
    store = InMemoryCorpusStore([(_issue(n), "alpha") for n in range(5)])
    assert len(KeywordRetriever(store).search("alpha", k=2)) == 2
    assert KeywordRetriever(store).search("alpha", k=0) == []


def test_fixture_target_ranks_first(fixture_store: InMemoryCorpusStore) -> None:
    hits = KeywordRetriever(fixture_store).search(TARGET_QUERY, k=10)
    assert hits[0].issue.number == TARGET_NUMBER
    assert len(hits) > 1
    assert all(a.score >= b.score for a, b in pairwise(hits))


def test_fixture_no_match_is_empty(fixture_store: InMemoryCorpusStore) -> None:
    assert KeywordRetriever(fixture_store).search(NO_MATCH_QUERY, k=10) == []
