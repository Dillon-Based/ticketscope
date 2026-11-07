"""`read_corpus_meta` and `replace_corpus` against a fake psycopg connection (story 5).

The fake records each statement and whether it ran inside the transaction, so the tests
show the swap writes all three meta columns in the same transaction as the issues."""

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest

from ticketscope.adapters import postgres
from ticketscope.adapters.postgres import CorpusMeta, IssueRow


class _Result:
    def __init__(self, row: tuple[Any, ...] | None) -> None:
        self.row = row

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.row


class _Copy:
    def __init__(self, conn: _Conn) -> None:
        self.conn = conn

    def __enter__(self) -> _Copy:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def write_row(self, values: tuple[Any, ...]) -> None:
        self.conn.copied.append(values)


class _Cursor:
    def __init__(self, conn: _Conn) -> None:
        self.conn = conn

    def copy(self, sql: str) -> _Copy:
        self.conn.log.append(("COPY", self.conn.in_tx))
        return _Copy(self.conn)


class _Tx:
    def __init__(self, conn: _Conn) -> None:
        self.conn = conn

    def __enter__(self) -> None:
        self.conn.in_tx = True

    def __exit__(self, exc_type: object, *rest: object) -> None:
        self.conn.in_tx = False
        self.conn.outcome = "rollback" if exc_type else "commit"


class _Conn:
    def __init__(self, row: tuple[Any, ...] | None = None) -> None:
        self.row = row
        self.in_tx = False
        self.outcome = ""
        self.log: list[tuple[str, bool]] = []
        self.params: list[tuple[Any, ...] | None] = []
        self.copied: list[tuple[Any, ...]] = []

    def __enter__(self) -> _Conn:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> _Result:
        self.log.append((sql.split()[0], self.in_tx))
        self.params.append(params)
        return _Result(self.row)

    def transaction(self) -> _Tx:
        return _Tx(self)

    def cursor(self) -> _Cursor:
        return _Cursor(self)


@pytest.fixture
def conn(monkeypatch: pytest.MonkeyPatch) -> _Conn:
    fake = _Conn()
    monkeypatch.setattr(postgres.psycopg, "connect", lambda conninfo: fake)
    return fake


def _row(number: int) -> IssueRow:
    return IssueRow(
        number=number,
        title=f"t{number}",
        body=None,
        url=f"https://bugs.mojang.com/browse/MC-{number}",
        state="closed",
        state_reason=None,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        closed_at=datetime(2025, 1, 2, tzinfo=UTC),
        kind="short",
        outcome_status="fixed",
        outcome_summary="Fixed",
        outcome_source="label",
        outcome_ref=None,
        search_text=f"t{number}\n\n",
    )


def test_read_corpus_meta_is_none_on_an_empty_table(conn: _Conn) -> None:
    assert postgres.read_corpus_meta("dsn") is None


def test_read_corpus_meta_returns_the_three_identity_columns(conn: _Conn) -> None:
    conn.row = ("2026.11.1", None, "pre1.kind2-t3.outcome3")
    assert postgres.read_corpus_meta("dsn") == CorpusMeta(
        "2026.11.1", None, "pre1.kind2-t3.outcome3"
    )


def test_read_corpus_meta_decodes_bytes_from_a_sql_ascii_database(conn: _Conn) -> None:
    conn.row = (b"2026.11.1", b"model", b"pre1.kind2-t3.outcome3")
    assert postgres.read_corpus_meta("dsn") == CorpusMeta(
        "2026.11.1", "model", "pre1.kind2-t3.outcome3"
    )


def test_read_corpus_meta_of_a_story_1_row_has_no_preprocessing(conn: _Conn) -> None:
    conn.row = ("fixture", None, None)
    assert postgres.read_corpus_meta("dsn") == CorpusMeta("fixture", None, None)


def test_replace_corpus_writes_issues_and_all_meta_columns_in_one_transaction(
    conn: _Conn,
) -> None:
    meta = CorpusMeta("2026.11.1", None, "pre1.kind2-t3.outcome3")
    assert postgres.replace_corpus("dsn", meta, [_row(1), _row(2)]) == 2
    assert [op for op, _ in conn.log] == ["TRUNCATE", "COPY", "DELETE", "INSERT"]
    assert all(in_tx for _, in_tx in conn.log)
    assert conn.outcome == "commit"
    assert conn.params[-1] == ("2026.11.1", None, "pre1.kind2-t3.outcome3")
    assert [values[0] for values in conn.copied] == [1, 2]
    assert len(conn.copied[0]) == 14


def test_replace_corpus_rolls_back_when_the_rows_fail_midway(conn: _Conn) -> None:
    def rows() -> Iterator[IssueRow]:
        yield _row(1)
        raise ValueError("bad line")

    with pytest.raises(ValueError, match="bad line"):
        postgres.replace_corpus("dsn", CorpusMeta("v", None, "p"), rows())
    assert conn.outcome == "rollback"
    assert "INSERT" not in [op for op, _ in conn.log]
