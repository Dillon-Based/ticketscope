"""Exercise the adapter's cutoff ordering against the kind PostgreSQL/pg_textsearch image."""

import json
import uuid

import pytest

from tests.smoke.test_gateway import _sql
from ticketscope.adapters.postgres import _KEYWORD_SQL

pytestmark = pytest.mark.kind


@pytest.mark.criterion("ticketscope--e2-s2--AC-3")
def test_postgres_selects_the_same_lowest_numbers_across_a_tied_cutoff() -> None:
    # A transaction-local schema keeps the pinned corpus and its BM25 index untouched.
    schema = f"tie_probe_{uuid.uuid4().hex}"
    query = _KEYWORD_SQL.replace("%(query)s", "'tieprobetoken'").replace("%(k)s", "10")
    ranked = f"SELECT json_agg(number ORDER BY score, number) FROM ({query}) AS hits;"
    output = _sql(
        f"BEGIN; CREATE SCHEMA {schema}; SET LOCAL search_path = {schema}, public;"
        "CREATE TABLE issue (LIKE public.issue INCLUDING DEFAULTS);"
        "INSERT INTO issue (number, title, url, state, created_at, kind, search_text)"
        " SELECT (n * 37) % 61, 'tie probe', 'probe', 'closed', now(), 'short',"
        " 'tieprobetoken' FROM generate_series(1, 60) AS n;"
        "CREATE INDEX issue_search_bm25_idx ON issue USING bm25 (search_text)"
        " WITH (text_config = 'english');" + ranked * 3 + "ROLLBACK;"
    )
    runs = [json.loads(line) for line in output.splitlines() if line.startswith("[")]
    assert runs == [list(range(1, 11))] * 3
