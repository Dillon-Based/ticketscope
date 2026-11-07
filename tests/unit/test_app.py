"""The plan's I/O matrix through `create_app`, with the fake store injected."""

import pytest
from fastapi.testclient import TestClient

from tests.target import NO_MATCH_QUERY, TARGET_NUMBER, TARGET_QUERY
from ticketscope.contract.search import SearchResponse
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import Scored
from ticketscope.http.app import create_app
from ticketscope.settings import Settings


@pytest.fixture
def client(fixture_store: InMemoryCorpusStore) -> TestClient:
    return TestClient(create_app(store=fixture_store, settings=Settings(default_mode="keyword")))


def test_best_match(client: TestClient) -> None:
    response = client.post("/v1/search", json={"query": TARGET_QUERY, "mode": "keyword"})
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
        assert result.issue.number >= 900000
    # Outcomes are derived by core at load (story 5); the target is resolved Fixed.
    assert body.results[0].outcome.status == "fixed"
    raw = response.json()["results"][0]
    assert set(raw) == {"rank", "score", "issue", "outcome"}
    assert set(raw["issue"]) == {"number", "title", "url", "kind", "state"}
    assert set(raw["outcome"]) == {"status", "summary", "source", "ref"}


def test_mode_omitted_uses_the_settings_default(fixture_store: InMemoryCorpusStore) -> None:
    client = TestClient(create_app(store=fixture_store, settings=Settings(default_mode="keyword")))
    response = client.post("/v1/search", json={"query": TARGET_QUERY})
    assert response.status_code == 200
    assert response.json()["mode"] == "keyword"


def test_unknown_mode_is_422(client: TestClient) -> None:
    response = client.post("/v1/search", json={"query": TARGET_QUERY, "mode": "nope"})
    assert response.status_code == 422


def test_mode_outside_the_registry_is_422(client: TestClient) -> None:
    response = client.post("/v1/search", json={"query": TARGET_QUERY, "mode": "dense"})
    assert response.status_code == 422


def test_no_match_is_empty(client: TestClient) -> None:
    response = client.post("/v1/search", json={"query": NO_MATCH_QUERY, "mode": "keyword"})
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

    def corpus_version(self) -> str | None:
        raise ConnectionError("database down")


def test_not_ready_when_database_unreachable() -> None:
    client = TestClient(create_app(store=_BrokenStore(), settings=Settings()))
    assert client.get("/readyz").status_code == 503
    assert client.get("/healthz").status_code == 200
