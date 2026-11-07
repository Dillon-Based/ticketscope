"""Expanded `/v1` contract coverage for story 1.6 (AD-4, AD-19, AD-20).

These add the edges the story's own tests leave open: problem+json on every error
path (405, 500 on search, multi-error 422s), the additive-only request (an unknown
field, including `exclude`, is ignored on the HTTP surface), a null issue body, the
readiness 503 staying a plain body, and the keyword over-fetch arithmetic.
"""

from http import HTTPStatus
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient

from tests.target import TARGET_NUMBER, TARGET_QUERY
from ticketscope.contract.search import IssueResponse, Problem, SearchRequest, SearchResponse
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueDetail, IssueRecord, Scored
from ticketscope.core.modes import REGISTRY, KeywordRetriever
from ticketscope.core.ports import Retriever
from ticketscope.http.app import create_app
from ticketscope.settings import Settings


def _issue(number: int) -> IssueRecord:
    return IssueRecord(number=number, title=f"t{number}", url="u", kind="short", state="closed")


@pytest.fixture
def client(fixture_store: InMemoryCorpusStore) -> TestClient:
    return TestClient(create_app(store=fixture_store, settings=Settings(default_mode="keyword")))


def _problem(response: httpx2.Response, status: int) -> Problem:
    assert response.status_code == status, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = Problem.model_validate(response.json())
    assert problem.type == "about:blank"
    assert problem.status == status
    assert problem.title == HTTPStatus(status).phrase
    assert isinstance(response.json()["detail"], str)
    return problem


# --- problem+json on every error path -------------------------------------------------


def test_wrong_method_is_a_405_problem_keeping_allow(client: TestClient) -> None:
    response = client.get("/v1/search")
    _problem(response, 405)
    assert "POST" in response.headers["allow"]


def test_wrong_method_on_the_issue_route_is_a_405_problem(client: TestClient) -> None:
    response = client.post(f"/v1/issues/{TARGET_NUMBER}", json={})
    _problem(response, 405)
    assert "GET" in response.headers["allow"]


class _BrokenStore:
    def keyword_search(self, query: str, k: int) -> list[Scored]:
        raise ConnectionError("database down at 10.0.0.5")

    def get_issue(self, number: int) -> IssueDetail | None:
        raise ConnectionError("database down at 10.0.0.5")

    def corpus_version(self) -> str | None:
        raise ConnectionError("database down at 10.0.0.5")


def test_search_store_failure_is_a_500_problem_without_the_error_text() -> None:
    client = TestClient(
        create_app(store=_BrokenStore(), settings=Settings()), raise_server_exceptions=False
    )
    response = client.post("/v1/search", json={"query": "x", "mode": "keyword"})
    problem = _problem(response, 500)
    assert problem.detail == "internal server error"
    assert "10.0.0.5" not in response.text
    assert problem.errors is None


class _SearchFailsStore(InMemoryCorpusStore):
    def keyword_search(self, query: str, k: int) -> list[Scored]:
        raise RuntimeError("bm25 index missing")


def test_failure_after_the_version_check_is_a_500_problem() -> None:
    store = _SearchFailsStore([(_issue(1), "alpha")], corpus_version="v")
    client = TestClient(create_app(store=store, settings=Settings()), raise_server_exceptions=False)
    response = client.post("/v1/search", json={"query": "alpha", "mode": "keyword"})
    _problem(response, 500)
    assert "bm25" not in response.text


def test_missing_query_is_422_naming_query(client: TestClient) -> None:
    problem = _problem(client.post("/v1/search", json={"mode": "keyword"}), 422)
    assert problem.errors
    assert [e.loc for e in problem.errors] == [["body", "query"]]
    assert problem.detail.startswith("query: ")


def test_two_invalid_fields_give_two_errors_and_one_joined_detail(client: TestClient) -> None:
    response = client.post("/v1/search", json={"query": 7, "mode": "keyword", "k": 0})
    problem = _problem(response, 422)
    assert problem.errors
    assert sorted(tuple(e.loc) for e in problem.errors) == [("body", "k"), ("body", "query")]
    parts = problem.detail.split("; ")
    assert len(parts) == 2
    assert {p.split(":", 1)[0] for p in parts} == {"k", "query"}


@pytest.mark.parametrize("k", ["ten", 1.5, None])
def test_non_integer_k_is_422(client: TestClient, k: object) -> None:
    response = client.post("/v1/search", json={"query": TARGET_QUERY, "mode": "keyword", "k": k})
    problem = _problem(response, 422)
    assert problem.errors
    assert problem.errors[0].loc == ["body", "k"]


def test_a_json_array_body_is_422(client: TestClient) -> None:
    response = client.post("/v1/search", json=[{"query": TARGET_QUERY}])
    problem = _problem(response, 422)
    assert problem.errors


def test_unknown_mode_is_checked_before_the_corpus() -> None:
    # An empty store is not loaded (503), but an invalid request is still the caller's 422.
    client = TestClient(create_app(store=InMemoryCorpusStore(), settings=Settings()))
    _problem(client.post("/v1/search", json={"query": "x", "mode": "dense"}), 422)
    _problem(client.post("/v1/search", json={"query": "x", "k": 51}), 422)


def test_a_server_default_outside_the_registry_is_a_422_problem(
    fixture_store: InMemoryCorpusStore,
) -> None:
    client = TestClient(create_app(store=fixture_store, settings=Settings(default_mode="dense")))
    problem = _problem(client.post("/v1/search", json={"query": TARGET_QUERY}), 422)
    assert problem.detail == "mode: unknown mode: dense"


@pytest.mark.parametrize("number", [-1, 0, 2**40])
def test_any_integer_not_loaded_is_404(client: TestClient, number: int) -> None:
    problem = _problem(client.get(f"/v1/issues/{number}"), 404)
    assert str(number) in problem.detail


@pytest.mark.parametrize("raw", ["1.5", "12abc", "%20"])
def test_non_integer_path_is_422(client: TestClient, raw: str) -> None:
    problem = _problem(client.get(f"/v1/issues/{raw}"), 422)
    assert problem.errors
    assert problem.errors[0].loc == ["path", "number"]


# --- readiness is not a /v1 error -----------------------------------------------------


def test_readiness_503_keeps_its_plain_body() -> None:
    client = TestClient(create_app(store=InMemoryCorpusStore(), settings=Settings()))
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "corpus not loaded"}


def test_health_bodies_are_unchanged(client: TestClient) -> None:
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ready", "corpus_version": "fixture"}


# --- additive-only request (AD-20) and no exclude on HTTP (AD-4) ----------------------


def test_unknown_request_fields_are_accepted_and_do_not_change_the_response(
    client: TestClient,
) -> None:
    plain = client.post("/v1/search", json={"query": TARGET_QUERY, "mode": "keyword"})
    extra = client.post(
        "/v1/search",
        json={"query": TARGET_QUERY, "mode": "keyword", "client": "mcp", "trace": {"x": 1}},
    )
    assert extra.status_code == 200
    assert extra.content == plain.content


def test_exclude_is_not_on_the_http_surface(client: TestClient) -> None:
    response = client.post(
        "/v1/search",
        json={"query": TARGET_QUERY, "mode": "keyword", "exclude": [TARGET_NUMBER]},
    )
    assert response.status_code == 200
    numbers = [r["issue"]["number"] for r in response.json()["results"]]
    assert numbers[0] == TARGET_NUMBER


def test_default_k_is_ten() -> None:
    assert SearchRequest(query="q").k == 10
    store = InMemoryCorpusStore([(_issue(n), "alpha") for n in range(1, 21)], corpus_version="v")
    client = TestClient(create_app(store=store, settings=Settings(default_mode="keyword")))
    results = SearchResponse.model_validate(
        client.post("/v1/search", json={"query": "alpha"}).json()
    ).results
    assert len(results) == 10


def test_k_50_returns_50_when_the_corpus_has_them() -> None:
    store = InMemoryCorpusStore([(_issue(n), "alpha") for n in range(1, 61)], corpus_version="v")
    client = TestClient(create_app(store=store, settings=Settings(default_mode="keyword")))
    response = client.post("/v1/search", json={"query": "alpha", "k": 50})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 50


# --- issue detail ---------------------------------------------------------------------


def _detail_client(body: str | None, *, with_body: bool = True) -> TestClient:
    record = IssueRecord(
        number=42,
        title="Crash on drain",
        url="https://example.test/42",
        kind="log_heavy",
        state="closed",
        outcome_status="duplicate",
        outcome_summary="Duplicate of 41",
        outcome_source="label",
        outcome_ref="41",
    )
    bodies = {42: body} if with_body else None
    store = InMemoryCorpusStore([(record, "crash drain")], corpus_version="v", bodies=bodies)
    return TestClient(create_app(store=store, settings=Settings()))


def test_a_null_body_is_present_as_null() -> None:
    raw = _detail_client(None, with_body=False).get("/v1/issues/42").json()
    assert "body" in raw["issue"]
    assert raw["issue"]["body"] is None


def test_issue_detail_maps_every_outcome_field() -> None:
    raw = _detail_client("stack trace\n" * 500).get("/v1/issues/42").json()
    body = IssueResponse.model_validate(raw)
    assert body.issue.kind == "log_heavy"
    assert body.issue.body == "stack trace\n" * 500
    assert raw["outcome"] == {
        "status": "duplicate",
        "summary": "Duplicate of 41",
        "source": "label",
        "ref": "41",
    }


def test_a_non_ascii_body_round_trips() -> None:
    text = "Zerstörung — 崩溃 ☃ \x00-free"
    assert _detail_client(text).get("/v1/issues/42").json()["issue"]["body"] == text


# --- the Retriever port and keyword over-fetch (AD-19) --------------------------------


class _SpyStore(InMemoryCorpusStore):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.asked: list[int] = []

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        self.asked.append(k)
        return super().keyword_search(query, k)


def _spy(n: int) -> _SpyStore:
    return _SpyStore([(_issue(i), "alpha " * (20 - i)) for i in range(1, n + 1)])


def test_keyword_over_fetches_by_the_exclude_size() -> None:
    store = _spy(10)
    KeywordRetriever(store).search("alpha", k=3, exclude=frozenset({1, 2, 99}))
    assert store.asked == [6]


def test_keyword_without_exclude_fetches_exactly_k() -> None:
    store = _spy(10)
    KeywordRetriever(store).search("alpha", k=4)
    assert store.asked == [4]


def test_excluding_several_top_hits_still_fills_k_in_rank_order() -> None:
    hits = KeywordRetriever(_spy(10)).search("alpha", k=3, exclude=frozenset({1, 3}))
    assert [h.issue.number for h in hits] == [2, 4, 5]


def test_excluding_every_hit_is_empty() -> None:
    hits = KeywordRetriever(_spy(3)).search("alpha", k=5, exclude=frozenset({1, 2, 3}))
    assert hits == []


def test_exclude_with_fewer_hits_than_k_returns_what_is_left() -> None:
    hits = KeywordRetriever(_spy(4)).search("alpha", k=10, exclude=frozenset({2}))
    assert [h.issue.number for h in hits] == [1, 3, 4]


def test_exclude_never_returns_more_than_k() -> None:
    # An absent excluded number over-fetches one extra row; it must be truncated away.
    hits = KeywordRetriever(_spy(10)).search("alpha", k=2, exclude=frozenset({999}))
    assert [h.issue.number for h in hits] == [1, 2]


def test_keyword_retriever_satisfies_the_retriever_port() -> None:
    retriever: Retriever = REGISTRY["keyword"].build(_spy(3))
    assert [h.issue.number for h in retriever.search("alpha", 2)] == [1, 2]


def test_available_takes_a_store_and_is_true_for_an_empty_one() -> None:
    assert REGISTRY["keyword"].available(InMemoryCorpusStore()) is True


def test_the_registry_cannot_be_mutated() -> None:
    with pytest.raises(TypeError):
        REGISTRY["dense"] = REGISTRY["keyword"]  # type: ignore[index]
    with pytest.raises(AttributeError):
        REGISTRY["keyword"].name = "x"  # type: ignore[misc]


# --- the fake store's get_issue -------------------------------------------------------


def test_fake_get_issue_returns_none_for_an_unknown_number() -> None:
    assert InMemoryCorpusStore([(_issue(1), "a")]).get_issue(2) is None


def test_fake_get_issue_keeps_the_issue_record_and_body() -> None:
    store = InMemoryCorpusStore([(_issue(1), "a")], bodies={1: "b"})
    assert store.get_issue(1) == IssueDetail(issue=_issue(1), body="b")
