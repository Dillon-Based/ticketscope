"""`PostgresCorpusStore.get_issue` against a fake psycopg connection (AD-4).

The fake records each statement and its parameters, so the tests show the number is
sent out of line and a row maps to `IssueDetail` with its body."""

from typing import Any

import pytest

from ticketscope.adapters import postgres
from ticketscope.adapters.postgres import PostgresCorpusStore
from ticketscope.core.model import IssueDetail, IssueRecord


class _Result:
    def __init__(self, row: tuple[Any, ...] | None) -> None:
        self.row = row

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.row


class _Conn:
    def __init__(self) -> None:
        self.row: tuple[Any, ...] | None = None
        self.statements: list[tuple[str, Any]] = []

    def __enter__(self) -> _Conn:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sql: str, params: Any = None) -> _Result:
        self.statements.append((sql, params))
        return _Result(self.row)


@pytest.fixture
def conn(monkeypatch: pytest.MonkeyPatch) -> _Conn:
    fake = _Conn()
    monkeypatch.setattr(postgres.psycopg, "connect", lambda conninfo: fake)
    return fake


def test_get_issue_maps_a_row_with_its_body(conn: _Conn) -> None:
    conn.row = (
        900003,
        "t",
        "https://bugs.mojang.com/browse/MCD-9003",
        "log_heavy",
        "closed",
        "duplicate",
        "Resolved as Duplicate",
        "label",
        "https://bugs.mojang.com/browse/MCD-1",
        "the body\nwith a trace",
    )
    assert PostgresCorpusStore("dsn").get_issue(900003) == IssueDetail(
        issue=IssueRecord(
            number=900003,
            title="t",
            url="https://bugs.mojang.com/browse/MCD-9003",
            kind="log_heavy",
            state="closed",
            outcome_status="duplicate",
            outcome_summary="Resolved as Duplicate",
            outcome_source="label",
            outcome_ref="https://bugs.mojang.com/browse/MCD-1",
        ),
        body="the body\nwith a trace",
    )


def test_get_issue_keeps_a_null_body(conn: _Conn) -> None:
    conn.row = (1, "t", "u", "short", "open", "unknown", None, None, None, None)
    found = PostgresCorpusStore("dsn").get_issue(1)
    assert found is not None
    assert found.body is None


def test_get_issue_is_none_when_no_row(conn: _Conn) -> None:
    assert PostgresCorpusStore("dsn").get_issue(42) is None


def test_get_issue_sends_the_number_as_a_parameter(conn: _Conn) -> None:
    PostgresCorpusStore("dsn").get_issue(42)
    [(sql, params)] = conn.statements
    assert params == {"number": 42}
    assert "42" not in sql
    assert "%(number)s" in sql
    assert "body" in sql
