"""Postgres adapter: the `CorpusStore` over pg_textsearch, plus the job-side writes.

Keyword search ranks with pg_textsearch BM25 inside Postgres (AD-9). Its `<@>`
operator returns negative scores (lower ranks first); this adapter negates them,
so `score` is higher-is-better (AD-4).
"""

import logging
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import psycopg

from ticketscope.core.model import (
    IssueDetail,
    IssueRecord,
    Kind,
    OutcomeSource,
    OutcomeStatus,
    Scored,
)

log = logging.getLogger(__name__)

_MIGRATE_LOCK_KEY = 0x7473_6D69  # "tsmi": serializes concurrent migrate runs

# The index is named explicitly: psycopg sends parameters out of line, and
# pg_textsearch needs the index name for parameterized queries.
_KEYWORD_SQL = """
SELECT number, title, url, kind, state,
       outcome_status, outcome_summary, outcome_source, outcome_ref, score
FROM (
    SELECT number, title, url, kind, state,
           outcome_status, outcome_summary, outcome_source, outcome_ref,
           search_text <@> to_bm25query(%(query)s, 'issue_search_bm25_idx') AS score
    FROM issue
    ORDER BY score, number
    LIMIT %(k)s
) AS ranked
WHERE score < 0
ORDER BY score, number
"""

# The `_KEYWORD_SQL` issue columns, in the same order, plus `body`.
_ISSUE_SQL = """
SELECT number, title, url, kind, state,
       outcome_status, outcome_summary, outcome_source, outcome_ref, body
FROM issue
WHERE number = %(number)s
"""


# Exact scan over one model's rows: `<=>` is cosine distance, so the score is `1 - distance`.
# The vector travels as a text literal (no pgvector Python package).
_DENSE_SQL = """
SELECT i.number, i.title, i.url, i.kind, i.state,
       i.outcome_status, i.outcome_summary, i.outcome_source, i.outcome_ref,
       1 - (e.embedding <=> %(vector)s::vector) AS score
FROM issue_embedding e
JOIN issue i ON i.number = e.issue_number
WHERE e.model_id = %(model)s
ORDER BY e.embedding <=> %(vector)s::vector, i.number
LIMIT %(k)s
"""


def vector_literal(vector: Sequence[float]) -> str:
    """A pgvector text literal, e.g. `[0.1,0.2]`."""
    return "[" + ",".join(repr(float(x)) for x in vector) + "]"


def _issue_record(row: Sequence[Any]) -> IssueRecord:
    """The first nine columns of a `_KEYWORD_SQL` or `_ISSUE_SQL` row."""
    return IssueRecord(
        number=row[0],
        title=row[1],
        url=row[2],
        kind=cast(Kind, row[3]),
        state=row[4],
        outcome_status=cast(OutcomeStatus, row[5]),
        outcome_summary=row[6],
        outcome_source=cast(OutcomeSource | None, row[7]),
        outcome_ref=row[8],
    )


class PostgresCorpusStore:
    """`CorpusStore` over the loaded corpus. One short connection per call."""

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        if k <= 0:
            return []
        with psycopg.connect(self._conninfo) as conn:
            rows = conn.execute(_KEYWORD_SQL, {"query": query, "k": k}).fetchall()
        return [Scored(issue=_issue_record(row), score=-float(row[9])) for row in rows]

    def get_issue(self, number: int) -> IssueDetail | None:
        with psycopg.connect(self._conninfo) as conn:
            row = conn.execute(_ISSUE_SQL, {"number": number}).fetchone()
        return None if row is None else IssueDetail(issue=_issue_record(row), body=row[9])

    def corpus_version(self) -> str | None:
        with psycopg.connect(self._conninfo) as conn:
            row = conn.execute("SELECT snapshot_version FROM corpus_meta LIMIT 1").fetchone()
        return None if row is None else str(row[0])

    def dense_search(self, model_id: str, vector: Sequence[float], k: int) -> list[Scored]:
        if k <= 0:
            return []
        params = {"model": model_id, "vector": vector_literal(vector), "k": k}
        with psycopg.connect(self._conninfo) as conn:
            rows = conn.execute(_DENSE_SQL, params).fetchall()
        return [Scored(issue=_issue_record(row), score=float(row[9])) for row in rows]

    def has_embeddings(self, model_id: str) -> bool:
        with psycopg.connect(self._conninfo) as conn:
            row = conn.execute(
                "SELECT EXISTS (SELECT 1 FROM issue_embedding WHERE model_id = %s)", (model_id,)
            ).fetchone()
        return bool(row and row[0])

    def embedding_model_id(self) -> str | None:
        with psycopg.connect(self._conninfo) as conn:
            row = conn.execute("SELECT embedding_model_id FROM corpus_meta LIMIT 1").fetchone()
        return None if row is None else _text(row[0])


# --- job side: migrate and load connect as the app owner (AD-7) ---------------------


def wait_for_database(conninfo: str, *, role: str | None, timeout_s: float) -> None:
    """Block until the database accepts connections and, if given, `role` exists."""
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            with psycopg.connect(conninfo) as conn:
                if role is None:
                    return
                found = conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,))
                if found.fetchone() is not None:
                    return
                reason = f"role {role} does not exist yet"
        except psycopg.OperationalError as exc:
            reason = str(exc).strip()
        if time.monotonic() >= deadline:
            raise TimeoutError(f"database not ready after {timeout_s:.0f}s: {reason}")
        log.info("waiting for database: %s", reason)
        time.sleep(3)


def apply_migrations(conninfo: str, migrations_dir: Path) -> list[str]:
    """Apply `migrations_dir/*.sql` in name order, each once, under an advisory lock.

    Returns the versions applied by this run.
    """
    files = sorted(migrations_dir.glob("*.sql"))
    applied: list[str] = []
    with psycopg.connect(conninfo, autocommit=True) as conn:
        conn.execute("SELECT pg_advisory_lock(%s)", (_MIGRATE_LOCK_KEY,))
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                " version text PRIMARY KEY,"
                " applied_at timestamptz NOT NULL DEFAULT now())"
            )
            done = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
            for path in files:
                version = path.stem
                if version in done:
                    continue
                log.info("applying migration %s", version)
                with conn.transaction():
                    # No parameters, so psycopg sends the whole file as one simple query.
                    conn.execute(path.read_bytes())
                    conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
                applied.append(version)
        finally:
            conn.execute("SELECT pg_advisory_unlock(%s)", (_MIGRATE_LOCK_KEY,))
    return applied


@dataclass(frozen=True, slots=True)
class IssueRow:
    """One row of the `issue` table as `load` writes it."""

    number: int
    title: str
    body: str | None
    url: str
    state: str
    state_reason: str | None
    created_at: datetime
    closed_at: datetime | None
    kind: Kind
    outcome_status: OutcomeStatus
    outcome_summary: str | None
    outcome_source: OutcomeSource | None
    outcome_ref: str | None
    search_text: str


_ISSUE_COLUMNS: Sequence[str] = (
    "number",
    "title",
    "body",
    "url",
    "state",
    "state_reason",
    "created_at",
    "closed_at",
    "kind",
    "outcome_status",
    "outcome_summary",
    "outcome_source",
    "outcome_ref",
    "search_text",
)


_COPY_SQL = (
    "COPY issue (number, title, body, url, state, state_reason, created_at, closed_at,"
    " kind, outcome_status, outcome_summary, outcome_source, outcome_ref, search_text)"
    " FROM STDIN"
)


@dataclass(frozen=True, slots=True)
class EmbeddingRow:
    """One row of `issue_embedding` as `load` writes it."""

    issue_number: int
    model_id: str
    vector: Sequence[float]


_COPY_EMBEDDING_SQL = "COPY issue_embedding (issue_number, model_id, embedding) FROM STDIN"


@dataclass(frozen=True, slots=True)
class CorpusMeta:
    """The single `corpus_meta` row's identity: what decides whether `load` reloads."""

    snapshot_version: str
    embedding_model_id: str | None
    preprocessing_version: str | None


def read_corpus_meta(conninfo: str) -> CorpusMeta | None:
    """The `corpus_meta` row, or `None` when nothing has been loaded yet."""
    with psycopg.connect(conninfo) as conn:
        row = conn.execute(
            "SELECT snapshot_version, embedding_model_id, preprocessing_version"
            " FROM corpus_meta LIMIT 1"
        ).fetchone()
    if row is None:
        return None
    return CorpusMeta(
        snapshot_version=_text(row[0]) or "",
        embedding_model_id=_text(row[1]),
        preprocessing_version=_text(row[2]),
    )


def _text(value: object) -> str | None:
    """A text column as `str`; psycopg returns bytes from a SQL_ASCII database."""
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def replace_corpus(
    conninfo: str,
    meta: CorpusMeta,
    rows: Iterable[IssueRow],
    embeddings: Iterable[EmbeddingRow] | None = None,
) -> int:
    """Replace every issue row, every embedding row and the single `corpus_meta` row in one
    transaction. `embeddings` is consumed after the issues are copied (the foreign key).

    On any error the transaction rolls back and the previous corpus stays.
    """
    count = 0
    with psycopg.connect(conninfo) as conn, conn.transaction():
        conn.execute("TRUNCATE issue, issue_embedding")
        with conn.cursor().copy(_COPY_SQL) as copy:
            for row in rows:
                values: tuple[Any, ...] = tuple(getattr(row, c) for c in _ISSUE_COLUMNS)
                copy.write_row(values)
                count += 1
        if embeddings is not None:
            with conn.cursor().copy(_COPY_EMBEDDING_SQL) as copy:
                for emb in embeddings:
                    copy.write_row((emb.issue_number, emb.model_id, vector_literal(emb.vector)))
        conn.execute("DELETE FROM corpus_meta")
        conn.execute(
            "INSERT INTO corpus_meta"
            " (snapshot_version, embedding_model_id, preprocessing_version, loaded_at)"
            " VALUES (%s, %s, %s, now())",
            (meta.snapshot_version, meta.embedding_model_id, meta.preprocessing_version),
        )
    return count
