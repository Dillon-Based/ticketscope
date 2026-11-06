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

from ticketscope.core.model import IssueRecord, Kind, OutcomeSource, OutcomeStatus, Scored

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
    ORDER BY score
    LIMIT %(k)s
) AS ranked
WHERE score < 0
ORDER BY score, number
"""


class PostgresCorpusStore:
    """`CorpusStore` over the loaded corpus. One short connection per call."""

    def __init__(self, conninfo: str) -> None:
        self._conninfo = conninfo

    def keyword_search(self, query: str, k: int) -> list[Scored]:
        if k <= 0:
            return []
        with psycopg.connect(self._conninfo) as conn:
            rows = conn.execute(_KEYWORD_SQL, {"query": query, "k": k}).fetchall()
        return [
            Scored(
                issue=IssueRecord(
                    number=row[0],
                    title=row[1],
                    url=row[2],
                    kind=cast(Kind, row[3]),
                    state=row[4],
                    outcome_status=cast(OutcomeStatus, row[5]),
                    outcome_summary=row[6],
                    outcome_source=cast(OutcomeSource | None, row[7]),
                    outcome_ref=row[8],
                ),
                score=-float(row[9]),
            )
            for row in rows
        ]

    def corpus_version(self) -> str | None:
        with psycopg.connect(self._conninfo) as conn:
            row = conn.execute("SELECT snapshot_version FROM corpus_meta LIMIT 1").fetchone()
        return None if row is None else str(row[0])


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


def replace_corpus(conninfo: str, snapshot_version: str, rows: Iterable[IssueRow]) -> int:
    """Replace every issue row and the single `corpus_meta` row in one transaction.

    On any error the transaction rolls back and the previous corpus stays.
    """
    count = 0
    with psycopg.connect(conninfo) as conn, conn.transaction():
        conn.execute("TRUNCATE issue")
        with conn.cursor().copy(_COPY_SQL) as copy:
            for row in rows:
                values: tuple[Any, ...] = tuple(getattr(row, c) for c in _ISSUE_COLUMNS)
                copy.write_row(values)
                count += 1
        conn.execute("DELETE FROM corpus_meta")
        conn.execute(
            "INSERT INTO corpus_meta (snapshot_version, loaded_at) VALUES (%s, now())",
            (snapshot_version,),
        )
    return count
