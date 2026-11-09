"""Dense search and the embedding transaction against real Postgres with pgvector
(test design rows B, C and the roles and exact-scan rows)."""

from collections.abc import Iterator
from datetime import UTC, datetime

import psycopg
import pytest

from tests import dense_oracle as oracle
from ticketscope.adapters.postgres import (
    CorpusMeta,
    EmbeddingRow,
    IssueRow,
    PostgresCorpusStore,
    replace_corpus,
)
from ticketscope.core.fakes import HashEmbedder
from ticketscope.core.modes import DenseRetriever

MODEL = "model-a"
META = CorpusMeta("snap", MODEL, "pre1.x.emb1")


def _row(number: int) -> IssueRow:
    return IssueRow(
        number=number,
        title=f"t{number}",
        body=None,
        url=f"u{number}",
        state="closed",
        state_reason=None,
        created_at=datetime(2020, 1, 1, tzinfo=UTC),
        closed_at=None,
        kind="short",
        outcome_status="fixed",
        outcome_summary=None,
        outcome_source=None,
        outcome_ref=None,
        search_text=f"t{number}",
    )


def _embeddings(model: str = MODEL) -> Iterator[EmbeddingRow]:
    for number, vector in oracle.VECTORS.items():
        yield EmbeddingRow(number, model, vector)


@pytest.fixture
def loaded(pg_conninfo: str) -> PostgresCorpusStore:
    rows = [_row(n) for n in oracle.VECTORS]
    assert replace_corpus(pg_conninfo, META, rows, _embeddings()) == 4
    return PostgresCorpusStore(pg_conninfo)


def test_the_cosine_oracle_through_sql(loaded: PostgresCorpusStore) -> None:
    hits = loaded.dense_search(MODEL, oracle.QUERY, 10)
    assert [h.issue.number for h in hits] == list(oracle.ORDER)
    for hit in hits:
        expected = float(oracle.COSINE[hit.issue.number])
        assert hit.score == pytest.approx(expected, abs=oracle.TOLERANCE)
    assert loaded.has_embeddings(MODEL) and not loaded.has_embeddings("nope")
    assert loaded.embedding_model_id() == MODEL
    assert loaded.dense_search(MODEL, oracle.QUERY, 0) == []


def test_another_models_rows_of_another_dimension_cause_no_dimension_error(
    pg_conninfo: str, loaded: PostgresCorpusStore
) -> None:
    with psycopg.connect(pg_conninfo, autocommit=True) as conn:
        conn.execute(
            "INSERT INTO issue_embedding VALUES (1, 'model-b', '[1,2,3]'),"
            " (2, 'model-b', '[3,2,1]')"
        )
    assert [h.issue.number for h in loaded.dense_search(MODEL, oracle.QUERY, 10)] == [1, 2, 3, 4]
    # And the other way round, with the other model's dimension.
    assert [h.issue.number for h in loaded.dense_search("model-b", (1.0, 2.0, 3.0), 10)] == [1, 2]


def test_exclusion_keeps_the_slots_through_the_real_adapter(pg_conninfo: str) -> None:
    embedder = HashEmbedder(MODEL, dim=256)
    texts = {n: f"word{n} shared" for n in range(1, 8)}
    vectors = embedder.embed(list(texts.values()))
    rows = [_row(n) for n in texts]
    embeddings = [EmbeddingRow(n, MODEL, v) for n, v in zip(texts, vectors, strict=True)]
    replace_corpus(pg_conninfo, META, rows, embeddings)
    retriever = DenseRetriever(PostgresCorpusStore(pg_conninfo), embedder)
    top = [h.issue.number for h in retriever.search("word3 shared", k=3)]
    assert top[0] == 3
    hits = retriever.search("word3 shared", k=3, exclude=frozenset({3}))
    assert len(hits) == 3 and 3 not in {h.issue.number for h in hits}


def test_a_failure_after_the_issues_are_copied_rolls_everything_back(
    pg_conninfo: str, loaded: PostgresCorpusStore
) -> None:
    def failing() -> Iterator[EmbeddingRow]:
        yield EmbeddingRow(1, MODEL, (1.0, 0.0))
        raise RuntimeError("embedder died")

    with pytest.raises(RuntimeError):
        replace_corpus(pg_conninfo, CorpusMeta("new", MODEL, "pre1.x.emb1"), [_row(9)], failing())
    assert loaded.corpus_version() == "snap"
    assert [h.issue.number for h in loaded.dense_search(MODEL, oracle.QUERY, 10)] == [1, 2, 3, 4]
    assert loaded.get_issue(9) is None


def test_a_reload_leaves_no_embedding_for_an_issue_that_left(
    pg_conninfo: str, loaded: PostgresCorpusStore
) -> None:
    replace_corpus(pg_conninfo, META, [_row(1)], [EmbeddingRow(1, MODEL, (1.0, 0.0))])
    assert [h.issue.number for h in loaded.dense_search(MODEL, oracle.QUERY, 10)] == [1]
    with psycopg.connect(pg_conninfo) as conn:
        [(count,)] = conn.execute("SELECT count(*) FROM issue_embedding").fetchall()
    assert count == 1


def test_a_keyword_only_load_clears_embeddings(
    pg_conninfo: str, loaded: PostgresCorpusStore
) -> None:
    replace_corpus(pg_conninfo, CorpusMeta("snap", None, "pre1.x"), [_row(1)])
    assert loaded.has_embeddings(MODEL) is False
    assert loaded.embedding_model_id() is None


def test_the_read_only_role_reads_and_cannot_write(
    pg_conninfo: str, loaded: PostgresCorpusStore
) -> None:
    with psycopg.connect(pg_conninfo, autocommit=True) as conn:
        conn.execute("SET ROLE ticketscope_ro")
        [(count,)] = conn.execute("SELECT count(*) FROM issue_embedding").fetchall()
        assert count == 4
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("INSERT INTO issue_embedding VALUES (1, 'x', '[1]')")


def test_dense_is_an_exact_scan_with_no_vector_index(
    pg_conninfo: str, loaded: PostgresCorpusStore
) -> None:
    with psycopg.connect(pg_conninfo) as conn:
        indexes = conn.execute(
            "SELECT indexdef FROM pg_indexes WHERE tablename = 'issue_embedding'"
        ).fetchall()
        assert all("USING btree" in str(definition) for (definition,) in indexes)  # the pkey
        conn.execute("SET enable_indexscan = off; SET enable_bitmapscan = off")
        plan = "\n".join(
            row[0]
            for row in conn.execute(
                "EXPLAIN SELECT i.number FROM issue_embedding e JOIN issue i"
                " ON i.number = e.issue_number WHERE e.model_id = 'model-a'"
                " ORDER BY e.embedding <=> '[1,0]'::vector, i.number LIMIT 10"
            ).fetchall()
        )
    assert "Sort" in plan and "hnsw" not in plan.lower() and "ivfflat" not in plan.lower()
