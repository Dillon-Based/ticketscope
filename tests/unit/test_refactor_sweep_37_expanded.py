"""Expanded coverage for story 3.7 (refactor sweep): the shared helpers keep behaviour."""

from typing import Any

import pytest

from tests.factories import issue_record
from ticketscope.adapters import postgres
from ticketscope.core.model import Scored
from ticketscope.core.modes import _without

COLUMNS = [c.strip() for c in postgres._ISSUE_COLUMNS_SQL.split(",")]


def _hits(*numbers: int) -> list[Scored]:
    return [Scored(issue=issue_record(n), score=float(n)) for n in numbers]


def test_without_drops_excluded_and_trims_to_k() -> None:
    out = _without(_hits(1, 2, 3, 4), frozenset({2}), 2)
    assert [h.issue.number for h in out] == [1, 3]


def test_without_keeps_order_and_handles_empty_exclude() -> None:
    assert [h.issue.number for h in _without(_hits(5, 3, 9), frozenset(), 10)] == [5, 3, 9]


@pytest.mark.parametrize("k", [0, -1, -5])
def test_without_non_positive_k_is_empty(k: int) -> None:
    assert _without(_hits(1, 2), frozenset(), k) == []


def test_issue_columns_are_the_nine_record_fields_in_reader_order() -> None:
    assert COLUMNS == [
        "number", "title", "url", "kind", "state",
        "outcome_status", "outcome_summary", "outcome_source", "outcome_ref",
    ]  # fmt: skip


def test_keyword_sql_selects_columns_then_score_in_both_levels() -> None:
    cols = postgres._ISSUE_COLUMNS_SQL
    assert f"SELECT {cols}, score" in postgres._KEYWORD_SQL
    assert f"SELECT {cols},\n" in postgres._KEYWORD_SQL
    assert "{" not in postgres._KEYWORD_SQL


def test_issue_sql_selects_columns_then_body() -> None:
    assert f"SELECT {postgres._ISSUE_COLUMNS_SQL}, body" in " ".join(postgres._ISSUE_SQL.split())


def test_dense_sql_prefixes_every_column_and_ends_with_score() -> None:
    expected = ", ".join(f"i.{c}" for c in COLUMNS)
    assert f"SELECT {expected},\n       1 - (e.embedding" in postgres._DENSE_SQL
    assert "AS score" in postgres._DENSE_SQL


class _Conn:
    def __init__(self, row: Any, log: list[Any]) -> None:
        self.row, self.log = row, log

    def __enter__(self) -> _Conn:
        return self

    def __exit__(self, *a: object) -> None:
        self.log.append("closed")

    def execute(self, sql: str, params: Any = None) -> _Conn:
        self.log.append((sql, params))
        return self

    def fetchone(self) -> Any:
        return self.row


def test_fetchone_passes_sql_params_and_closes_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    log: list[Any] = []
    seen: list[str] = []

    def connect(conninfo: str) -> _Conn:
        seen.append(conninfo)
        return _Conn(("x",), log)

    monkeypatch.setattr(postgres.psycopg, "connect", connect)
    assert postgres._fetchone("dsn", "SELECT 1", (1,)) == ("x",)
    assert seen == ["dsn"] and log == [("SELECT 1", (1,)), "closed"]


def test_store_methods_map_missing_rows_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(postgres.psycopg, "connect", lambda _c: _Conn(None, []))
    store = postgres.PostgresCorpusStore("dsn")
    assert store.get_issue(1) is None
    assert store.corpus_version() is None
    assert store.embedding_model_id() is None
    assert store.has_embeddings("m") is False
    assert postgres.read_corpus_meta("dsn") is None


def test_store_methods_map_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(postgres.psycopg, "connect", lambda _c: _Conn(("v1",), []))
    store = postgres.PostgresCorpusStore("dsn")
    assert store.corpus_version() == "v1"
    monkeypatch.setattr(postgres.psycopg, "connect", lambda _c: _Conn((True,), []))
    assert store.has_embeddings("m") is True
