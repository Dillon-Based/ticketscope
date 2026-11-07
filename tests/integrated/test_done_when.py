"""The epic's integrated check (story 11): its Done when, as five checks on the kind cluster.

Marker `kind`; needs `TICKETSCOPE_GATEWAY_URL` and `TICKETSCOPE_GATEWAY_HOST` plus `kubectl`
on the cluster, like the smoke suite, and network access to download the pinned asset. CI
runs it in the `integrated-check` job before the smoke suite, on the freshly deployed state:
`uv run pytest -m kind tests/integrated tests/smoke`. The checks run in file order, each one
test, so a broken part fails exactly its own check:

1. Schema (R1; stories 13, 5): the pinned asset validates against the committed
   `snapshot/schema-v2.json`, and the loaded corpus is that asset (version and issues).
2. Kind and outcome (R2; story 5): every loaded issue has a valid kind and outcome.
3. `/v1` and page (R3, R4, R-004; stories 5, 6, 7): each golden query returns its expected
   issue in the top-k with outcomes through `/v1/search` and the page; a recorded known
   keyword miss is reported, not gated.
4. Trace (R6; story 9): one search reaches Tempo as the AD-10 span tree.
5. Backup (R5, R7; story 8): an on-demand backup completes to SeaweedFS.

The helpers come from the smoke module (only its `_` names; never a `test_*` name, which
pytest would collect here again).
"""

import gzip
import hashlib
import json
import os
import warnings
from pathlib import Path
from typing import Any, get_args

import httpx2
import pytest
from jsonschema import Draft202012Validator

from tests.integrated.golden import (
    GoldenRow,
    page_rank,
    results_without_outcome,
    summary_table,
    twin_verdict,
)
from tests.smoke.test_gateway import (
    GOLDEN,
    OUTCOMES,
    PIN,
    _assert_on_demand_backup_completes,
    _corpus_meta,
    _gateway,
    _page,
    _poll_trace,
    _search_with_traceparent,
    _sql,
    _tempo,
)
from tests.target import SNAPSHOT_DIR, snapshot_pin
from ticketscope.adapters.release import fetch_snapshot
from ticketscope.contract.search import IssueKind, SearchResponse

pytestmark = pytest.mark.kind

KINDS: tuple[str, ...] = get_args(IssueKind)


def _sql_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def _numbers_digest(numbers: list[int]) -> str:
    """What `md5(string_agg(number::text, ',' ORDER BY number))` gives for `numbers`."""
    joined = ",".join(str(n) for n in sorted(numbers))
    return hashlib.md5(joined.encode(), usedforsecurity=False).hexdigest()


# (1) ---------------------------------------------------------------------------------------


def test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2(
    pytestconfig: pytest.Config,
) -> None:
    pin = snapshot_pin()
    # The checksum-verified asset, kept in pytest's cache so a local rerun does not
    # download it again (a cached copy is checked against the same pin).
    path = fetch_snapshot(
        pin["baseUrl"],
        pin["version"],
        pytestconfig.cache.mkdir("ticketscope-snapshot"),
        pin["sha256"],
        timeout=300,
    )
    schema = json.loads((SNAPSHOT_DIR / "schema-v2.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    numbers: list[int] = []
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        for lineno, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            record: dict[str, Any] = json.loads(line)
            error = next(validator.iter_errors(record), None)
            assert error is None, (
                f"{path.name} line {lineno} (issue {record.get('number')}): {error.message}"
                f" at {list(error.absolute_path)}"
            )
            numbers.append(int(record["number"]))
    assert numbers, f"{path.name} is empty"

    assert _corpus_meta()[0] == pin["version"]
    count, digest = (
        _sql("SELECT count(*), md5(string_agg(number::text, ',' ORDER BY number)) FROM issue")
        .strip()
        .split("|")
    )
    assert (int(count), digest) == (len(numbers), _numbers_digest(numbers)), (
        f"loaded issues differ from {path.name}: {count} rows vs {len(numbers)} lines"
    )


# (2) ---------------------------------------------------------------------------------------


def test_every_loaded_issue_has_a_valid_kind_and_outcome() -> None:
    bad = _sql(
        "SELECT number || ' ' || coalesce(kind, 'NULL') || ' ' || coalesce(outcome_status, 'NULL')"
        f" FROM issue WHERE kind IS NULL OR kind NOT IN ({_sql_list(KINDS)})"
        f" OR outcome_status IS NULL OR outcome_status NOT IN ({_sql_list(OUTCOMES)})"
        " ORDER BY number LIMIT 20"
    ).split("\n")
    bad = [row for row in bad if row.strip()]
    assert not bad, f"issues with an invalid kind or outcome (number kind outcome): {bad}"
    kinds = set(_sql("SELECT DISTINCT kind FROM issue").split())
    assert kinds == set(KINDS), kinds
    assert int(_sql("SELECT count(DISTINCT outcome_status) FROM issue")) > 1


# (3) ---------------------------------------------------------------------------------------


def _report(table: str, capsys: pytest.CaptureFixture[str]) -> None:
    """The golden table in the pytest output and, in CI, the job summary."""
    with capsys.disabled():
        print("\n" + table)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as out:
            out.write("\n### Integrated check: " + table + "\n")


def test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page(
    capsys: pytest.CaptureFixture[str],
) -> None:
    k, mode = int(GOLDEN["k"]), str(GOLDEN["mode"])
    assert GOLDEN["snapshot_version"] == PIN
    url, host = _gateway()
    rows: list[GoldenRow] = []
    failures: list[str] = []
    try:
        for entry in GOLDEN["queries"]:
            entry_id = str(entry["id"])
            expected = entry["expected_issue"]
            gated = not entry["known_keyword_miss"]

            response = httpx2.post(
                f"{url}/v1/search",
                json={"query": entry["query"], "mode": mode, "k": k},
                headers={"Host": host},
                timeout=30,
            )
            assert response.status_code == 200, f"{entry_id}: {response.text}"
            raw: dict[str, Any] = response.json()
            no_outcome = results_without_outcome(raw.get("results") or [], OUTCOMES)
            assert not no_outcome, f"{entry_id}: results without a contract outcome: {no_outcome}"
            body = SearchResponse.model_validate(raw)
            assert body.mode == mode and body.corpus_version == PIN, (entry_id, body.mode)
            assert len(body.results) <= k, entry_id
            ranked = [r.issue.number for r in body.results]
            verdict = twin_verdict(
                bool(entry["known_keyword_miss"]), int(expected["number"]), ranked
            )
            rows.append(GoldenRow(entry_id, str(entry["kind"]), str(expected["key"]), verdict))
            if verdict.status == "fail":
                failures.append(
                    f"{entry_id}: expected {expected['number']} ({expected['key']}) not in top-{k};"
                    f" returned {ranked}"
                )
            elif verdict.status == "known-miss":
                warnings.warn(f"golden {entry_id}: {verdict.note}", stacklevel=1)

            _, page = _page(str(entry["query"]))
            assert page.rows, f"{entry_id}: the page has no rows"
            bad_rows = [r["rank"] for r in page.rows if r["data-outcome"] not in OUTCOMES]
            assert not bad_rows, f"{entry_id}: page rows without a contract outcome: {bad_rows}"
            # A gated twin found through /v1 must be on the page too, whatever its row count.
            if gated and verdict.rank is not None:
                hrefs = [r["href"] for r in page.rows]
                if page_rank(hrefs, str(expected["key"])) is None:
                    failures.append(
                        f"{entry_id}: the page has no row for {expected['key']}"
                        f" (/v1 rank {verdict.rank}); hrefs {hrefs}"
                    )
    finally:
        # Whatever rows were collected, even when an assert above stopped the loop.
        _report(summary_table(rows, k=k, mode=mode), capsys)
    assert not failures, "\n".join(failures)


# (4) ---------------------------------------------------------------------------------------


def test_one_search_reaches_tempo_as_the_ad10_tree() -> None:
    trace_id = _search_with_traceparent()
    _poll_trace(lambda: _tempo(trace_id))


# (5) ---------------------------------------------------------------------------------------


def test_an_on_demand_backup_completes_to_seaweedfs() -> None:
    _assert_on_demand_backup_completes("integrated")
