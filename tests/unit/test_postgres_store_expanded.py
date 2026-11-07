"""`PostgresCorpusStore` reads after story 1.6's shared row helper (AD-4, AD-19).

Story 1.6 moved `keyword_search`'s row mapping into `_issue_record`, shared with
`get_issue`. These pin the keyword mapping, its score sign, the `k <= 0` short
circuit, and that operator characters reach BM25 as a bound parameter, unescaped.
"""

from typing import Any

import pytest

from ticketscope.adapters import postgres
from ticketscope.adapters.postgres import PostgresCorpusStore
from ticketscope.core.model import IssueRecord, Scored


class _Result:
    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self.rows = rows

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.rows[0] if self.rows else None


class _Conn:
    def __init__(self) -> None:
        self.rows: list[tuple[Any, ...]] = []
        self.statements: list[tuple[str, Any]] = []
        self.conninfos: list[str] = []

    def __enter__(self) -> _Conn:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sql: str, params: Any = None) -> _Result:
        self.statements.append((sql, params))
        return _Result(self.rows)


@pytest.fixture
def conn(monkeypatch: pytest.MonkeyPatch) -> _Conn:
    fake = _Conn()

    def connect(conninfo: str) -> _Conn:
        fake.conninfos.append(conninfo)
        return fake

    monkeypatch.setattr(postgres.psycopg, "connect", connect)
    return fake


_ROW = (
    7,
    "title",
    "https://bugs.mojang.com/browse/MC-7",
    "short",
    "closed",
    "fixed",
    "Resolved as Fixed",
    "label",
    None,
)


def test_keyword_row_maps_to_scored_with_a_positive_score(conn: _Conn) -> None:
    conn.rows = [(*_ROW, -3.25), (8, *_ROW[1:], -1.0)]
    hits = PostgresCorpusStore("dsn").keyword_search("q", 5)
    assert hits[0] == Scored(
        issue=IssueRecord(
            number=7,
            title="title",
            url="https://bugs.mojang.com/browse/MC-7",
            kind="short",
            state="closed",
            outcome_status="fixed",
            outcome_summary="Resolved as Fixed",
            outcome_source="label",
            outcome_ref=None,
        ),
        score=3.25,
    )
    assert [h.score for h in hits] == [3.25, 1.0]
    assert conn.conninfos == ["dsn"]


@pytest.mark.parametrize("k", [0, -1])
def test_keyword_with_no_slots_never_connects(conn: _Conn, k: int) -> None:
    assert PostgresCorpusStore("dsn").keyword_search("q", k) == []
    assert conn.conninfos == []


def test_operator_characters_are_sent_as_a_parameter_unchanged(conn: _Conn) -> None:
    query = "crash & launcher | (java:!) !! \"x'; DROP TABLE issue; --"
    PostgresCorpusStore("dsn").keyword_search(query, 11)
    [(sql, params)] = conn.statements
    assert params == {"query": query, "k": 11}
    assert "DROP" not in sql
    assert "%(query)s" in sql
    assert "%(k)s" in sql


def test_get_issue_opens_one_connection_with_one_statement(conn: _Conn) -> None:
    conn.rows = [(*_ROW, "body")]
    found = PostgresCorpusStore("dsn").get_issue(7)
    assert found is not None
    assert found.issue.number == 7
    assert found.body == "body"
    assert conn.conninfos == ["dsn"]
    assert len(conn.statements) == 1


def test_get_issue_and_keyword_share_the_issue_mapping(conn: _Conn) -> None:
    store = PostgresCorpusStore("dsn")
    conn.rows = [(*_ROW, -2.0)]
    [hit] = store.keyword_search("q", 1)
    conn.rows = [(*_ROW, "body")]
    found = store.get_issue(7)
    assert found is not None
    assert found.issue == hit.issue
