"""Hybrid retrieval: reciprocal rank fusion over keyword and dense (AD-19)."""

from collections.abc import Iterable, Iterator

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from tests.factories import search_payload
from ticketscope.contract.search import Problem, SearchResponse
from ticketscope.core.fakes import HashEmbedder, InMemoryCorpusStore
from ticketscope.core.model import IssueRecord, Scored
from ticketscope.core.modes import REGISTRY, RRF_K, HybridRetriever
from ticketscope.http.app import create_app
from ticketscope.settings import Settings

MODEL = "hash-fake"


def _issue(number: int) -> IssueRecord:
    return IssueRecord(number=number, title=f"t{number}", url="u", kind="short", state="closed")


class Ranked:
    """A retriever with a fixed ranking that honours `k` and `exclude` like a real one."""

    def __init__(self, numbers: Iterable[int]) -> None:
        self._numbers = list(numbers)
        self.asked: list[tuple[int, frozenset[int]]] = []

    def search(self, query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]:
        self.asked.append((k, exclude))
        kept = [n for n in self._numbers if n not in exclude]
        return [Scored(issue=_issue(n), score=0.0) for n in kept[:k]]


def _numbers(hits: list[Scored]) -> list[int]:
    return [h.issue.number for h in hits]


def test_a_known_pair_of_rankings_fuses_to_a_known_order() -> None:
    # keyword A=1 B=2 C=3, dense B=1 A=2 D=3, with 1,2,3,4 as A,B,C,D:
    #   B 1/62+1/61, A 1/61+1/62 (equal: tie -> number), C 1/63, D 1/63 (tie -> number).
    hybrid = HybridRetriever(Ranked([1, 2, 3]), Ranked([2, 1, 4]))
    hits = hybrid.search("q", k=10)
    assert _numbers(hits) == [1, 2, 3, 4]
    assert hits[0].score == pytest.approx(1 / (RRF_K + 1) + 1 / (RRF_K + 2))
    assert hits[2].score == pytest.approx(1 / (RRF_K + 3))


def test_agreement_beats_a_single_high_rank() -> None:
    # 9 is first in keyword only; 5 is second in both -> 2/(62) > 1/61.
    hits = HybridRetriever(Ranked([9, 5]), Ranked([7, 5])).search("q", k=3)
    assert _numbers(hits) == [5, 7, 9]  # 7 and 9 tie at 1/61: lower number first
    assert hits[0].score == pytest.approx(2 / (RRF_K + 2))


def test_ties_break_on_issue_number() -> None:
    hits = HybridRetriever(Ranked([30]), Ranked([20])).search("q", k=2)
    assert _numbers(hits) == [20, 30]
    assert hits[0].score == hits[1].score


def test_an_excluded_issue_never_scores_and_costs_no_slot() -> None:
    keyword, dense = Ranked([1, 2, 3, 4]), Ranked([1, 3, 2, 4])
    hits = HybridRetriever(keyword, dense).search("q", k=2, exclude=frozenset({1}))
    assert len(hits) == 2
    assert 1 not in _numbers(hits)
    # Each side was asked for k + |exclude| and told what to leave out.
    assert keyword.asked == [(3, frozenset({1}))]
    assert dense.asked == [(3, frozenset({1}))]
    # With 1 out, keyword ranks 2,3 and dense ranks 3,2: a tie broken by number.
    assert _numbers(hits) == [2, 3]


def test_k_larger_than_either_side_returns_the_union() -> None:
    hits = HybridRetriever(Ranked([1, 2]), Ranked([3])).search("q", k=50)
    assert _numbers(hits) == [1, 3, 2]  # 1 and 3 tie at 1/61: number; 2 is 1/62
    assert [h.score for h in hits] == pytest.approx(
        [1 / (RRF_K + 1), 1 / (RRF_K + 1), 1 / (RRF_K + 2)]
    )
    assert HybridRetriever(Ranked([]), Ranked([])).search("q", k=5) == []


def test_k_zero_is_empty_and_asks_nobody() -> None:
    keyword = Ranked([1])
    assert HybridRetriever(keyword, Ranked([1])).search("q", k=0) == []
    assert keyword.asked == []


def test_fusion_is_reproducible() -> None:
    first = HybridRetriever(Ranked([4, 3, 2, 1]), Ranked([1, 2, 3, 4])).search("q", k=4)
    again = HybridRetriever(Ranked([4, 3, 2, 1]), Ranked([1, 2, 3, 4])).search("q", k=4)
    assert first == again
    # 1 and 4 tie at 1/61 + 1/64 and outscore 2 and 3 (1/62 + 1/63): ties break on number.
    assert _numbers(first) == [1, 4, 2, 3]


# --- the registry ----------------------------------------------------------------------------


def _store(*, embedded: bool = True) -> InMemoryCorpusStore:
    embedder = HashEmbedder(MODEL)
    texts = {1: "kernel panic on boot", 2: "texture glitch near spawn", 3: "boot loop after update"}
    vectors = dict(zip(texts, embedder.embed(list(texts.values())), strict=True))
    return InMemoryCorpusStore(
        [(_issue(n), text) for n, text in texts.items()],
        corpus_version="v1",
        embeddings={MODEL: vectors} if embedded else None,
        embedding_model=MODEL if embedded else None,
    )


def test_hybrid_registers_as_rrf_and_needs_what_dense_needs() -> None:
    mode = REGISTRY["hybrid"]
    assert (mode.name, mode.score_kind) == ("hybrid", "rrf")
    assert mode.available(_store(), HashEmbedder(MODEL)) is True
    assert mode.available(_store(), None) is False
    assert mode.available(_store(embedded=False), HashEmbedder(MODEL)) is False
    assert mode.available(_store(), HashEmbedder("other")) is False
    with pytest.raises(ValueError, match="embedder"):
        mode.build(_store(), None)


def test_the_registry_builds_a_hybrid_retriever() -> None:
    retriever = REGISTRY["hybrid"].build(_store(), HashEmbedder(MODEL))
    assert isinstance(retriever, HybridRetriever)
    assert _numbers(retriever.search("kernel panic on boot", k=3))[0] == 1


# --- /v1 and the span tree -------------------------------------------------------------------


@pytest.fixture
def exporter() -> InMemorySpanExporter:
    return InMemorySpanExporter()


@pytest.fixture
def provider(exporter: InMemorySpanExporter) -> Iterator[TracerProvider]:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    yield provider
    provider.shutdown()


def _client(
    store: InMemoryCorpusStore,
    *,
    with_embedder: bool = True,
    provider: TracerProvider | None = None,
) -> TestClient:
    settings = Settings(default_mode="keyword", embedding_model_id=MODEL if with_embedder else "")
    embedder = HashEmbedder(MODEL) if with_embedder else None
    app = create_app(store=store, settings=settings, tracer_provider=provider, embedder=embedder)
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "query", ["boot", "java.lang.NullPointerException at net.minecraft.client.Main " * 40]
)
def test_v1_serves_hybrid_with_ranked_issues_and_outcomes(query: str) -> None:
    response = _client(_store()).post("/v1/search", json=search_payload(query, mode="hybrid"))
    assert response.status_code == 200
    body = SearchResponse.model_validate(response.json())
    assert (body.mode, body.score_kind, body.corpus_version) == ("hybrid", "rrf", "v1")
    assert [r.rank for r in body.results] == list(range(1, len(body.results) + 1))
    assert body.results and all(r.outcome.status for r in body.results)
    scores = [r.score for r in body.results]
    assert scores == sorted(scores, reverse=True)


def test_v1_hybrid_is_503_problem_json_without_embeddings() -> None:
    response = _client(_store(embedded=False), with_embedder=False).post(
        "/v1/search", json=search_payload("boot", mode="hybrid")
    )
    assert response.status_code == 503
    assert "hybrid" in Problem.model_validate(response.json()).detail


def _named(spans: Iterable[ReadableSpan], name: str) -> ReadableSpan:
    [span] = [s for s in spans if s.name == name]
    return span


def test_hybrid_emits_retrieval_hybrid_with_the_embeddings_child(
    provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    client = _client(_store(), provider=provider)
    assert client.post("/v1/search", json=search_payload("boot", mode="hybrid")).status_code == 200
    spans = exporter.get_finished_spans()
    retrieval = _named(spans, "retrieval hybrid")
    embeddings = _named(spans, f"embeddings {MODEL}")
    assert retrieval.attributes is not None
    assert retrieval.attributes["ticketscope.retrieval.mode"] == "hybrid"
    assert embeddings.parent is not None and retrieval.context is not None
    assert embeddings.parent.span_id == retrieval.context.span_id
