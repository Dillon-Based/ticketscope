"""The plan's I/O matrix through `create_app`, with the fake store injected."""

import json
from collections.abc import Sequence

import httpx2
import pytest
from fastapi.testclient import TestClient

from tests.factories import search_payload
from tests.target import NO_MATCH_QUERY, SNAPSHOT_DIR, TARGET_NUMBER, TARGET_QUERY
from ticketscope.contract.search import IssueResponse, Problem, SearchResponse
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueDetail, Scored
from ticketscope.core.modes import REGISTRY
from ticketscope.http import app as app_module
from ticketscope.http.app import create_app
from ticketscope.settings import Settings

FIXTURE_NUMBER_FLOOR = 900_000  # Synthetic issues sit above real Mojang ids.


@pytest.fixture
def client(fixture_store: InMemoryCorpusStore) -> TestClient:
    return TestClient(create_app(store=fixture_store, settings=Settings(default_mode="keyword")))


def test_best_match(client: TestClient) -> None:
    response = client.post("/v1/search", json=search_payload(TARGET_QUERY, mode="keyword"))
    assert response.status_code == 200
    body = SearchResponse.model_validate(response.json())
    assert body.mode == "keyword"
    assert body.score_kind == "bm25"
    assert body.corpus_version == "fixture"
    assert body.results[0].issue.number == TARGET_NUMBER
    assert [r.rank for r in body.results] == list(range(1, len(body.results) + 1))
    scores = [r.score for r in body.results]
    assert scores == sorted(scores, reverse=True)
    for result in body.results:
        assert result.issue.number >= FIXTURE_NUMBER_FLOOR
    # Outcomes are derived by core at load (story 5); the target is resolved Fixed.
    assert body.results[0].outcome.status == "fixed"
    raw = response.json()["results"][0]
    assert set(raw) == {"rank", "score", "issue", "outcome"}
    assert set(raw["issue"]) == {"number", "title", "url", "kind", "state", "key"}
    assert set(raw["outcome"]) == {"status", "summary", "source", "ref"}


def test_mode_omitted_uses_the_settings_default(fixture_store: InMemoryCorpusStore) -> None:
    client = TestClient(create_app(store=fixture_store, settings=Settings(default_mode="keyword")))
    response = client.post("/v1/search", json=search_payload(TARGET_QUERY))
    assert response.status_code == 200
    assert response.json()["mode"] == "keyword"


def _problem(response: httpx2.Response, status: int) -> Problem:
    """Assert `response` is an RFC 9457 problem with `status`; return its body."""
    assert response.status_code == status, response.text
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = Problem.model_validate(response.json())
    assert problem.type == "about:blank"
    assert problem.status == status
    assert problem.title
    assert problem.detail
    return problem


def test_unknown_mode_is_422(client: TestClient) -> None:
    response = client.post("/v1/search", json=search_payload(TARGET_QUERY, mode="nope"))
    problem = _problem(response, 422)
    assert problem.title == "Unprocessable Content"
    assert problem.errors
    assert problem.errors[0].loc == ["body", "mode"]


def test_mode_outside_the_registry_is_422(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    # `hybrid` is a contract mode: take it out of the registry to reach the registry check.
    monkeypatch.setattr(app_module, "REGISTRY", {"keyword": REGISTRY["keyword"]})
    response = client.post("/v1/search", json=search_payload(TARGET_QUERY, mode="hybrid"))
    problem = _problem(response, 422)
    assert problem.detail == "mode: unknown mode: hybrid"
    assert problem.errors
    assert [(e.loc, e.msg) for e in problem.errors] == [(["body", "mode"], "unknown mode: hybrid")]


def test_malformed_json_body_is_422_naming_the_body(client: TestClient) -> None:
    response = client.post(
        "/v1/search",
        content=b'{"query": "x", "mode": ',
        headers={"content-type": "application/json"},
    )
    problem = _problem(response, 422)
    assert problem.errors
    assert not problem.detail[0].isdigit()
    assert problem.detail.startswith("body: ")


@pytest.mark.parametrize("k", [0, 51, -1])
def test_k_out_of_bounds_is_422(client: TestClient, k: int) -> None:
    response = client.post("/v1/search", json=search_payload(TARGET_QUERY, mode="keyword", k=k))
    problem = _problem(response, 422)
    assert problem.errors
    assert [e.loc for e in problem.errors] == [["body", "k"]]
    assert problem.detail.startswith("k: Input should be")
    assert isinstance(response.json()["detail"], str)


@pytest.mark.parametrize("k", [1, 50])
def test_k_edges_return_at_most_k(client: TestClient, k: int) -> None:
    response = client.post("/v1/search", json=search_payload(TARGET_QUERY, mode="keyword", k=k))
    assert response.status_code == 200
    results = SearchResponse.model_validate(response.json()).results
    assert 1 <= len(results) <= k
    assert results[0].issue.number == TARGET_NUMBER


def test_operator_characters_are_searched_as_text(client: TestClient) -> None:
    query = 'zephyrcache & eviction | (stalls:!) !! "node drain'
    response = client.post("/v1/search", json=search_payload(query, mode="keyword"))
    assert response.status_code == 200
    assert response.json()["results"][0]["issue"]["number"] == TARGET_NUMBER


def test_a_pasted_log_of_4kb_ranks(client: TestClient) -> None:
    frame = "\tat net.minecraft.zephyrcache.Eviction.stall(Eviction.java:42)\n"
    query = "java.lang.IllegalStateException: node drain\n" + frame * 80
    assert len(query.encode()) >= 4096
    response = client.post("/v1/search", json=search_payload(query, mode="keyword"))
    assert response.status_code == 200
    assert response.json()["results"][0]["issue"]["number"] == TARGET_NUMBER


def test_search_is_503_when_corpus_not_loaded() -> None:
    client = TestClient(create_app(store=InMemoryCorpusStore(), settings=Settings()))
    response = client.post("/v1/search", json=search_payload(TARGET_QUERY, mode="keyword"))
    assert _problem(response, 503).detail == "corpus not loaded"


def _fixture_body(number: int) -> str | None:
    for line in (SNAPSHOT_DIR / "fixture.jsonl").read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["number"] == number:
            return record["body"]
    raise AssertionError(f"{number} not in fixture")


def test_issue_detail(client: TestClient) -> None:
    response = client.get(f"/v1/issues/{TARGET_NUMBER}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    raw = response.json()
    assert set(raw) == {"issue", "outcome"}
    assert set(raw["issue"]) == {"number", "title", "url", "kind", "state", "key", "body"}
    assert set(raw["outcome"]) == {"status", "summary", "source", "ref"}
    body = IssueResponse.model_validate(raw)
    assert body.issue.number == TARGET_NUMBER
    assert body.issue.body == _fixture_body(TARGET_NUMBER)
    assert body.issue.body
    hit = client.post("/v1/search", json=search_payload(TARGET_QUERY, mode="keyword")).json()
    top = hit["results"][0]
    assert raw["outcome"] == top["outcome"]
    assert {k: v for k, v in raw["issue"].items() if k != "body"} == top["issue"]


def test_unknown_issue_is_404(client: TestClient) -> None:
    problem = _problem(client.get("/v1/issues/1"), 404)
    assert problem.title == "Not Found"
    assert "1" in problem.detail


def test_non_integer_issue_number_is_422(client: TestClient) -> None:
    problem = _problem(client.get("/v1/issues/abc"), 422)
    assert problem.errors
    assert problem.errors[0].loc == ["path", "number"]
    assert problem.detail.startswith("number: ")


def test_issue_is_503_when_corpus_not_loaded() -> None:
    client = TestClient(create_app(store=InMemoryCorpusStore(), settings=Settings()))
    assert _problem(client.get("/v1/issues/1"), 503).detail == "corpus not loaded"


def test_unknown_route_is_a_problem(client: TestClient) -> None:
    _problem(client.get("/v1/nope"), 404)


def test_no_match_is_empty(client: TestClient) -> None:
    response = client.post("/v1/search", json=search_payload(NO_MATCH_QUERY, mode="keyword"))
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_ready_when_corpus_loaded(client: TestClient) -> None:
    assert client.get("/healthz").status_code == 200
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["corpus_version"] == "fixture"


def test_not_ready_when_corpus_not_loaded() -> None:
    client = TestClient(create_app(store=InMemoryCorpusStore(), settings=Settings()))
    assert client.get("/readyz").status_code == 503
    assert client.get("/healthz").status_code == 200


class _BrokenStore:
    def keyword_search(self, query: str, k: int) -> list[Scored]:
        raise ConnectionError("database down")

    def get_issue(self, number: int) -> IssueDetail | None:
        raise ConnectionError("database down")

    def get_issue_by_key(self, key: str) -> IssueDetail | None:
        raise ConnectionError("database down")

    def corpus_version(self) -> str | None:
        raise ConnectionError("database down")

    def dense_search(self, model_id: str, vector: Sequence[float], k: int) -> list[Scored]:
        raise ConnectionError("database down")

    def has_embeddings(self, model_id: str) -> bool:
        raise ConnectionError("database down")

    def embedding_model_id(self) -> str | None:
        raise ConnectionError("database down")


def test_not_ready_when_database_unreachable() -> None:
    client = TestClient(create_app(store=_BrokenStore(), settings=Settings()))
    assert client.get("/readyz").status_code == 503
    assert client.get("/healthz").status_code == 200


def test_store_failure_is_a_500_problem() -> None:
    client = TestClient(
        create_app(store=_BrokenStore(), settings=Settings()), raise_server_exceptions=False
    )
    problem = _problem(client.get("/v1/issues/1"), 500)
    assert "database down" not in problem.detail
