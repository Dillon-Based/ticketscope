"""The eval's search reuse rests on one property of both SQL queries: the leading rows of a
longer fetch are exactly a shorter fetch's rows (`jobs.eval.score.SearchReuseStore`). Both
order by score, then issue number, so this holds by construction; these tests check it on
real Postgres, where keyword ranks through the pg_textsearch BM25 index, with whole groups of
tied scores straddling every cut."""

from dataclasses import replace

import pytest

from tests.postgres.test_dense_postgres import META, MODEL, _row
from ticketscope.adapters.postgres import EmbeddingRow, PostgresCorpusStore, replace_corpus
from ticketscope.core.model import Scored

# 30 issues in three score groups of ten: every cut from 1 to 25 rows falls inside or at the
# edge of a tie group, so a tie-break that differs by LIMIT would show.
TEXTS = {
    **{n: "launcher crash launcher crash" for n in range(1, 11)},
    **{n: "launcher crash" for n in range(11, 21)},
    **{n: "launcher crash on startup with extra words" for n in range(21, 31)},
}
VECTORS = {
    **{n: [1.0, 0.0] for n in range(1, 11)},
    **{n: [1.0, 1.0] for n in range(11, 21)},
    **{n: [0.0, 1.0] for n in range(21, 31)},
}
LONGEST = 25


@pytest.fixture
def tied(pg_conninfo: str) -> PostgresCorpusStore:
    rows = [replace(_row(n), search_text=text) for n, text in TEXTS.items()]
    embeddings = [EmbeddingRow(n, MODEL, v) for n, v in VECTORS.items()]
    replace_corpus(pg_conninfo, META, rows, embeddings)
    return PostgresCorpusStore(pg_conninfo)


def _numbers(hits: list[Scored]) -> list[int]:
    return [hit.issue.number for hit in hits]


def test_a_shorter_keyword_fetch_is_the_head_of_a_longer_one(tied: PostgresCorpusStore) -> None:
    hits = tied.keyword_search("launcher crash", LONGEST)
    longest = _numbers(hits)
    assert len(longest) == LONGEST
    # The fixture's point: ties span the cuts (25 rows, at most three distinct scores).
    assert len({hit.score for hit in hits}) <= 3
    for k in range(1, LONGEST):
        assert _numbers(tied.keyword_search("launcher crash", k)) == longest[:k], k


def test_a_shorter_dense_fetch_is_the_head_of_a_longer_one(tied: PostgresCorpusStore) -> None:
    query = [1.0, 0.2]
    hits = tied.dense_search(MODEL, query, LONGEST)
    longest = _numbers(hits)
    assert len(longest) == LONGEST
    assert len({round(hit.score, 9) for hit in hits}) <= 3
    for k in range(1, LONGEST):
        assert _numbers(tied.dense_search(MODEL, query, k)) == longest[:k], k
