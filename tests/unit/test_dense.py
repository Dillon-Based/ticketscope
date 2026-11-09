"""Dense retrieval through story 3.1's seams, with the hash fake: no model, no database."""

import logging
import weakref
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import IO

import pytest
from fastapi.testclient import TestClient
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode

from tests import dense_oracle as oracle
from tests.factories import search_payload
from ticketscope import telemetry
from ticketscope.adapters.embedder import TracedEmbedder
from ticketscope.adapters.postgres import CorpusMeta, EmbeddingRow, IssueRow
from ticketscope.contract.search import Problem, SearchResponse
from ticketscope.core import derive
from ticketscope.core.fakes import HashEmbedder, InMemoryCorpusStore, cosine
from ticketscope.core.model import IssueRecord
from ticketscope.core.modes import REGISTRY, DenseRetriever
from ticketscope.http.app import create_app
from ticketscope.jobs.load import main as load
from ticketscope.settings import Settings

MODEL = "hash-fake"


def _issue(number: int) -> IssueRecord:
    return IssueRecord(number=number, title=f"t{number}", url="u", kind="short", state="closed")


def _oracle_store() -> InMemoryCorpusStore:
    return InMemoryCorpusStore(
        [(_issue(n), "") for n in oracle.VECTORS],
        corpus_version="v",
        embeddings={MODEL: oracle.VECTORS},
        embedding_model=MODEL,
    )


class FixedEmbedder:
    """Embeds every text to `QUERY`, so the store's vectors alone decide the ranking."""

    model_id = MODEL

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [list(oracle.QUERY) for _ in texts]


# --- the cosine oracle (R-001) ---------------------------------------------------------------


def test_cosine_oracle_order_and_scores() -> None:
    hits = DenseRetriever(_oracle_store(), FixedEmbedder()).search("anything", k=10)
    assert [h.issue.number for h in hits] == list(oracle.ORDER)
    for hit in hits:
        assert hit.score == pytest.approx(
            float(oracle.COSINE[hit.issue.number]), abs=oracle.TOLERANCE
        )


def test_cosine_is_not_a_distance_or_an_inner_product() -> None:
    scores = {h.issue.number: h.score for h in _oracle_store().dense_search(MODEL, oracle.QUERY, 4)}
    assert scores[1] > scores[4]  # a distance would reverse the order
    assert scores[1] == pytest.approx(1.0)
    assert scores[2] == pytest.approx(2**-0.5)  # an inner product would give 1.0
    assert scores[4] == pytest.approx(-1.0)


def test_ties_break_on_issue_number() -> None:
    store = InMemoryCorpusStore(
        [(_issue(n), "") for n in (5, 2, 9)],
        embeddings={MODEL: {5: (1.0, 0.0), 2: (1.0, 0.0), 9: (1.0, 0.0)}},
    )
    assert [h.issue.number for h in store.dense_search(MODEL, (1.0, 0.0), 10)] == [2, 5, 9]


def test_exclusion_keeps_k_slots() -> None:
    retriever = DenseRetriever(_oracle_store(), FixedEmbedder())
    hits = retriever.search("q", k=2, exclude=frozenset({1}))
    assert [h.issue.number for h in hits] == [2, 3]
    assert retriever.search("q", k=0) == []


def test_the_store_is_asked_for_k_plus_the_exclusions() -> None:
    asked: list[int] = []

    class Spy(InMemoryCorpusStore):
        def dense_search(self, model_id: str, vector: Sequence[float], k: int):  # type: ignore[override]
            asked.append(k)
            return super().dense_search(model_id, vector, k)

    store = Spy([(_issue(n), "") for n in oracle.VECTORS], embeddings={MODEL: oracle.VECTORS})
    DenseRetriever(store, FixedEmbedder()).search("q", k=2, exclude=frozenset({1, 2}))
    assert asked == [4]


def test_another_models_rows_do_not_disturb_the_configured_one() -> None:
    store = InMemoryCorpusStore(
        [(_issue(n), "") for n in oracle.VECTORS],
        embeddings={MODEL: oracle.VECTORS, "other": {1: (1.0, 0.0, 0.0), 2: (0.0, 1.0, 0.0)}},
    )
    assert [h.issue.number for h in store.dense_search(MODEL, oracle.QUERY, 10)] == [1, 2, 3, 4]


def test_cosine_of_a_zero_vector_is_zero() -> None:
    assert cosine((0.0, 0.0), (1.0, 0.0)) == 0.0


# --- the hash fake and the shared preprocessing ----------------------------------------------


def test_hash_embedder_is_deterministic_and_normalised() -> None:
    embedder = HashEmbedder()
    a, b = embedder.embed(["alpha beta", "alpha beta"])
    assert a == b
    assert sum(x * x for x in a) == pytest.approx(1.0)
    assert cosine(embedder.embed(["alpha beta gamma"])[0], a) > cosine(
        embedder.embed(["zulu yankee"])[0], a
    )


def test_embedding_text_equals_the_live_query_text_after_the_same_cut() -> None:
    body = "x" * (derive.EMBEDDING_MAX_CHARS * 2)
    document = derive.embedding_text("Title", body)
    live_query = derive.cut_for_embedding(f"Title\n\n{body}")
    assert document == live_query
    assert len(document) == derive.EMBEDDING_MAX_CHARS
    assert derive.embedding_text("T", None) == "T\n\n"


def test_dense_cuts_the_query_like_a_document() -> None:
    embedder = HashEmbedder(MODEL)
    DenseRetriever(_dense_corpus(embedder), embedder).search("y" * 10_000, k=1)
    assert embedder.calls[-1] == ["y" * derive.EMBEDDING_MAX_CHARS]


def test_preprocessing_version_default_is_unchanged_and_embeddings_append_the_rule() -> None:
    assert derive.preprocessing_version() == "pre1.kind2-t3.outcome3"
    assert derive.preprocessing_version(embeddings=True) == "pre1.kind2-t3.outcome3.emb1"


# --- the registry ----------------------------------------------------------------------------


def test_dense_entry_scores_cosine_and_is_gated_on_embeddings() -> None:
    mode = REGISTRY["dense"]
    assert (mode.name, mode.score_kind) == ("dense", "cosine")
    embedder = HashEmbedder(MODEL)
    assert mode.available(_oracle_store(), embedder) is True
    assert mode.available(_oracle_store(), None) is False
    assert mode.available(_oracle_store(), HashEmbedder("another-model")) is False
    assert mode.available(InMemoryCorpusStore(), embedder) is False
    assert isinstance(mode.build(_oracle_store(), embedder), DenseRetriever)
    with pytest.raises(ValueError, match="embedder"):
        mode.build(_oracle_store(), None)


# --- /v1 and readiness -----------------------------------------------------------------------


def _client(
    store: InMemoryCorpusStore,
    *,
    model_id: str = "",
    embedder: HashEmbedder | None = None,
    provider: TracerProvider | None = None,
) -> TestClient:
    settings = Settings(default_mode="keyword", embedding_model_id=model_id)
    app = create_app(store=store, settings=settings, tracer_provider=provider, embedder=embedder)
    return TestClient(app, raise_server_exceptions=False)


def _dense_corpus(
    embedder: HashEmbedder, *, stored_model: str | None = MODEL
) -> InMemoryCorpusStore:
    texts = {1: "kernel panic on boot", 2: "texture glitch near spawn", 3: "boot loop after update"}
    return InMemoryCorpusStore(
        [(_issue(n), text) for n, text in texts.items()],
        corpus_version="v1",
        embeddings={
            embedder.model_id: dict(zip(texts, embedder.embed(list(texts.values())), strict=True))
        },
        embedding_model=stored_model,
    )


def test_dense_search_returns_ranked_cosine_results() -> None:
    embedder = HashEmbedder(MODEL)
    client = _client(_dense_corpus(embedder), model_id=MODEL, embedder=embedder)
    response = client.post("/v1/search", json=search_payload("kernel panic on boot", mode="dense"))
    assert response.status_code == 200
    body = SearchResponse.model_validate(response.json())
    assert (body.mode, body.score_kind, body.corpus_version) == ("dense", "cosine", "v1")
    assert body.results[0].issue.number == 1
    assert body.results[0].score == pytest.approx(1.0)
    assert [r.rank for r in body.results] == [1, 2, 3]
    scores = [r.score for r in body.results]
    assert scores == sorted(scores, reverse=True)


def test_dense_is_503_problem_json_when_unavailable() -> None:
    # The flag-off path: no model configured, no embedder, nothing embedded.
    client = _client(InMemoryCorpusStore([(_issue(1), "alpha")], corpus_version="v1"))
    response = client.post("/v1/search", json=search_payload("alpha", mode="dense"))
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "dense" in Problem.model_validate(response.json()).detail
    keyword = client.post("/v1/search", json=search_payload("alpha", mode="keyword"))
    assert keyword.status_code == 200


def test_readiness_without_a_configured_model_is_ready_on_a_keyword_only_corpus() -> None:
    client = _client(InMemoryCorpusStore([(_issue(1), "alpha")], corpus_version="v1"))
    assert client.get("/readyz").status_code == 200


def test_readiness_is_ready_when_the_model_ids_match() -> None:
    embedder = HashEmbedder(MODEL)
    client = _client(_dense_corpus(embedder), model_id=MODEL, embedder=embedder)
    assert client.get("/readyz").status_code == 200


@pytest.mark.parametrize("stored", ["another-model", None])
def test_readiness_fails_naming_both_ids_when_they_differ(stored: str | None) -> None:
    embedder = HashEmbedder(MODEL)
    client = _client(
        _dense_corpus(embedder, stored_model=stored), model_id=MODEL, embedder=embedder
    )
    response = client.get("/readyz")
    assert response.status_code == 503
    reason = response.json()["reason"]
    assert MODEL in reason
    assert repr(stored) in reason


# --- spans -----------------------------------------------------------------------------------


@pytest.fixture
def exporter() -> InMemorySpanExporter:
    return InMemorySpanExporter()


@pytest.fixture
def provider(exporter: InMemorySpanExporter) -> Iterator[TracerProvider]:
    provider = telemetry.tracer_provider(telemetry.SERVICE_API, "")
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    yield provider
    provider.shutdown()


def _named(spans: Iterable[ReadableSpan], name: str) -> ReadableSpan:
    [span] = [s for s in spans if s.name == name]
    return span


def test_dense_search_emits_an_embeddings_span_under_retrieval_dense(
    provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    embedder = HashEmbedder(MODEL)
    client = _client(_dense_corpus(embedder), model_id=MODEL, embedder=embedder, provider=provider)
    assert client.post("/v1/search", json=search_payload("kernel", mode="dense")).status_code == 200
    spans = exporter.get_finished_spans()
    retrieval = _named(spans, "retrieval dense")
    embeddings = _named(spans, f"embeddings {MODEL}")
    assert embeddings.kind == SpanKind.INTERNAL
    assert embeddings.parent is not None and retrieval.context is not None
    assert embeddings.parent.span_id == retrieval.context.span_id
    attrs = embeddings.attributes or {}
    assert attrs["gen_ai.operation.name"] == "embeddings"
    assert attrs["gen_ai.request.model"] == MODEL
    assert "kernel" not in str(list(attrs.values()))  # no query text on the span


def test_probes_stay_untraced_with_a_model_configured(
    provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    embedder = HashEmbedder(MODEL)
    client = _client(_dense_corpus(embedder), model_id=MODEL, embedder=embedder, provider=provider)
    assert client.get("/readyz").status_code == 200
    assert exporter.get_finished_spans() == ()


def test_an_embedder_error_sets_the_embeddings_span_to_error(
    provider: TracerProvider, exporter: InMemorySpanExporter
) -> None:
    class Failing:
        model_id = MODEL

        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            raise RuntimeError("model blew up")

    traced = TracedEmbedder(Failing(), telemetry.get_tracer(provider))
    with pytest.raises(RuntimeError):
        traced.embed(["x"])
    assert (
        _named(exporter.get_finished_spans(), f"embeddings {MODEL}").status.status_code
        == StatusCode.ERROR
    )


# --- load ------------------------------------------------------------------------------------


class FakeDb:
    """A transactional stand-in: `replace_corpus` swaps state only after every row and
    embedding was consumed, as the real transaction commits only on success."""

    def __init__(self) -> None:
        self.meta: CorpusMeta | None = CorpusMeta("old", None, "pre0.old")
        self.rows: list[IssueRow] = []
        self.embeddings: list[EmbeddingRow] = []

    def read_corpus_meta(self, conninfo: str) -> CorpusMeta | None:
        return self.meta

    def replace_corpus(
        self,
        conninfo: str,
        meta: CorpusMeta,
        rows: Iterable[IssueRow],
        embeddings: Iterable[EmbeddingRow] | None = None,
    ) -> int:
        new_rows = list(rows)
        new_embeddings = list(embeddings or [])
        self.meta, self.rows, self.embeddings = meta, new_rows, new_embeddings
        return len(new_rows)


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, snapshot_dir: Path, fixture_sha256: str) -> FakeDb:
    fake = FakeDb()
    monkeypatch.setattr(load, "read_corpus_meta", fake.read_corpus_meta)
    monkeypatch.setattr(load, "replace_corpus", fake.replace_corpus)
    monkeypatch.setattr(load, "wait_for_database", lambda *a, **k: None)
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_DIR", str(snapshot_dir))
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_VERSION", "fixture")
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", fixture_sha256)
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_BASE_URL", "https://releases.invalid/download")
    return fake


def test_load_with_the_flag_off_computes_nothing(db: FakeDb) -> None:
    embedder = HashEmbedder(MODEL)
    assert load.run(Settings(), embedder) == 0
    assert db.meta == CorpusMeta("fixture", None, derive.preprocessing_version())
    assert db.embeddings == []
    assert embedder.calls == []


def test_flag_on_load_embeds_every_issue_and_records_the_model(
    db: FakeDb, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    embedder = HashEmbedder(MODEL)
    assert load.run(Settings(embeddings_compute=True), embedder) == 0
    assert db.meta == CorpusMeta("fixture", MODEL, derive.preprocessing_version(embeddings=True))
    assert {e.issue_number for e in db.embeddings} == {r.number for r in db.rows}
    assert {e.model_id for e in db.embeddings} == {MODEL}
    first = db.rows[0]
    assert db.embeddings[0].issue_number == first.number
    [text] = [t for batch in embedder.calls for t in batch][:1]
    assert text == derive.embedding_text(first.title, first.body)
    assert f"embeddings={len(db.rows)}" in caplog.text
    # A second load matches corpus_meta and does nothing.
    assert load.reload_reason(db.meta, load.pinned_meta("fixture", MODEL)) is None


def test_the_toggle_changes_corpus_meta_so_the_next_load_reloads(db: FakeDb) -> None:
    assert load.reload_reason(load.pinned_meta("fixture"), load.pinned_meta("fixture", MODEL)) == (
        "embedding_model_id None -> 'hash-fake'; "
        "preprocessing_version 'pre1.kind2-t3.outcome3' -> 'pre1.kind2-t3.outcome3.emb1'"
    )


def test_compute_without_a_model_id_fails_and_keeps_the_previous_corpus(db: FakeDb) -> None:
    assert load.run(Settings(embeddings_compute=True)) == 1
    assert db.meta == CorpusMeta("old", None, "pre0.old")


def test_an_embedder_failure_exits_1_and_the_previous_corpus_answers(db: FakeDb) -> None:
    class Failing:
        model_id = MODEL

        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            raise RuntimeError("embedder down")

    assert load.run(Settings(embeddings_compute=True), Failing()) == 1
    assert db.meta == CorpusMeta("old", None, "pre0.old")
    assert db.rows == [] and db.embeddings == []


def test_embedding_rows_batch_and_count(snapshot_dir: Path) -> None:
    embedder = HashEmbedder(MODEL)
    stats = load.EmbeddingStats()
    issues = load.read_snapshot(snapshot_dir / "fixture.jsonl.gz")
    rows = list(load.embedding_rows(issues, embedder, stats, batch_size=3))
    assert stats.count == len(rows) == 8
    assert [len(batch) for batch in embedder.calls] == [3, 3, 2]


def test_load_finishes_embedding_before_writing_and_streams_rows(
    db: FakeDb, monkeypatch: pytest.MonkeyPatch
) -> None:
    embedder = HashEmbedder(MODEL)
    replace = db.replace_corpus

    def write(
        conninfo: str,
        meta: CorpusMeta,
        rows: Iterable[IssueRow],
        embeddings: Iterable[EmbeddingRow] | None = None,
    ) -> int:
        assert sum(map(len, embedder.calls)) == 8  # inference has finished before TRUNCATE
        assert embeddings is not None and iter(embeddings) is embeddings
        return replace(conninfo, meta, rows, embeddings)

    monkeypatch.setattr(load, "replace_corpus", write)
    assert load.run(Settings(embeddings_compute=True), embedder) == 0
    assert len(db.embeddings) == 8


def test_embedding_spool_bounds_vector_memory_and_round_trips(snapshot_dir: Path) -> None:
    class Vector(list[float]):
        pass

    live: weakref.WeakValueDictionary[int, Vector] = weakref.WeakValueDictionary()
    peaks: list[int] = []
    batches: list[int] = []

    class TrackingEmbedder:
        model_id = MODEL

        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            batches.append(len(texts))
            vectors: list[list[float]] = []
            for _ in texts:
                vector = Vector([0.1, -0.12345678901234567, 1.0])
                live[id(vector)] = vector
                vectors.append(vector)
            peaks.append(len(live))
            return vectors

    issue = next(load.read_snapshot(snapshot_dir / "fixture.jsonl.gz"))
    issues = (issue.model_copy(update={"number": n}) for n in range(160))
    stats = load.EmbeddingStats()
    with load.spooled_embedding_rows(issues, TrackingEmbedder(), stats) as rows:
        assert stats.count == 160  # all inference finished before the consumer starts
        assert max(batches) == load.EMBEDDING_BATCH_SIZE == 8
        assert max(peaks) <= load.EMBEDDING_BATCH_SIZE + 1
        for number, row in enumerate(rows):
            assert row == EmbeddingRow(number, MODEL, [0.1, -0.12345678901234567, 1.0])
    assert not live


@pytest.mark.parametrize("failure", ["inference", "write", None])
def test_embedding_spool_closes_on_success_or_failure(
    snapshot_dir: Path, monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    files: list[IO[str]] = []
    temporary_file = load.TemporaryFile

    def open_spool(*, mode: str, encoding: str) -> IO[str]:
        spool = temporary_file(mode=mode, encoding=encoding)
        files.append(spool)
        return spool

    monkeypatch.setattr(load, "TemporaryFile", open_spool)

    class FailingEmbedder(HashEmbedder):
        def embed(self, texts: Sequence[str]) -> list[list[float]]:
            if failure == "inference" and self.calls:
                raise RuntimeError("inference failed")
            return super().embed(texts)

    issue = next(load.read_snapshot(snapshot_dir / "fixture.jsonl.gz"))
    issues = (issue.model_copy(update={"number": n}) for n in range(16))

    def consume() -> None:
        with load.spooled_embedding_rows(
            issues, FailingEmbedder(MODEL), load.EmbeddingStats()
        ) as rows:
            if failure == "write":
                next(rows)
                raise RuntimeError("write failed")
            assert len(list(rows)) == 16

    if failure:
        with pytest.raises(RuntimeError, match=f"{failure} failed"):
            consume()
    else:
        consume()
    assert len(files) == 1 and files[0].closed
