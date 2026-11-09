from itertools import pairwise

from tests.target import NO_MATCH_QUERY, TARGET_NUMBER, TARGET_QUERY
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord
from ticketscope.core.modes import REGISTRY, KeywordRetriever


def _issue(number: int) -> IssueRecord:
    return IssueRecord(number=number, title=f"t{number}", url="u", kind="short", state="closed")


def test_registry_holds_keyword_and_dense() -> None:
    assert set(REGISTRY) == {"keyword", "dense"}
    mode = REGISTRY["keyword"]
    assert mode.name == "keyword"
    assert mode.score_kind == "bm25"


def test_registry_builds_a_keyword_retriever() -> None:
    store = InMemoryCorpusStore([(_issue(7), "alpha beta"), (_issue(9), "unrelated")])
    retriever = REGISTRY["keyword"].build(store, None)
    assert isinstance(retriever, KeywordRetriever)
    hits = retriever.search("alpha beta", k=10)
    assert [(hit.issue.number, hit.score) for hit in hits] == [(7, 2.0)]


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


def test_exclude_drops_the_top_hit_and_still_fills_k() -> None:
    store = InMemoryCorpusStore([(_issue(n), "alpha " * (10 - n)) for n in range(1, 6)])
    retriever = KeywordRetriever(store)
    top = retriever.search("alpha", k=3)
    assert [h.issue.number for h in top] == [1, 2, 3]
    hits = retriever.search("alpha", k=3, exclude=frozenset({1}))
    assert [h.issue.number for h in hits] == [2, 3, 4]


def test_exclude_of_an_absent_number_changes_nothing() -> None:
    store = InMemoryCorpusStore([(_issue(n), "alpha " * (10 - n)) for n in range(1, 6)])
    retriever = KeywordRetriever(store)
    assert retriever.search("alpha", k=3, exclude=frozenset({99})) == retriever.search("alpha", k=3)


def test_exclude_on_the_fixture_drops_the_target(fixture_store: InMemoryCorpusStore) -> None:
    retriever = KeywordRetriever(fixture_store)
    full = retriever.search(TARGET_QUERY, k=2)
    hits = retriever.search(TARGET_QUERY, k=2, exclude=frozenset({TARGET_NUMBER}))
    assert TARGET_NUMBER not in {h.issue.number for h in hits}
    assert len(full) == len(hits) == 2


def test_keyword_is_always_available() -> None:
    assert REGISTRY["keyword"].available(InMemoryCorpusStore(), None) is True
