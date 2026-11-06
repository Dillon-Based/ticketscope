"""Schema v2, the v2 fixture and `load`'s snapshot reader (story 13)."""

import gzip
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from tests.target import SNAPSHOT_DIR
from ticketscope.core.derive import derive_kind
from ticketscope.core.snapshot import SnapshotIssueV2
from ticketscope.jobs.ingest import schema as schema_module
from ticketscope.jobs.load.main import build_rows, read_kinds, read_snapshot

V1_LINE = {
    "number": 1,
    "url": "https://github.com/kubernetes/kubernetes/issues/1",
    "title": "v1",
    "body": None,
    "state": "closed",
    "state_reason": "completed",
    "created_at": "2025-01-01T00:00:00Z",
    "closed_at": "2025-01-02T00:00:00Z",
    "labels": [],
    "comments": [],
    "timeline": [],
}


def _schema() -> dict[str, Any]:
    return json.loads((SNAPSHOT_DIR / "schema-v2.json").read_text(encoding="utf-8"))


def _lines() -> list[dict[str, Any]]:
    text = (SNAPSHOT_DIR / "fixture.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _gz(path: Path, *records: object) -> Path:
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return path


# --- schema v2 ---------------------------------------------------------------------------


def test_schema_is_valid_draft_2020_12() -> None:
    schema = _schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].endswith("/snapshot/schema-v2.json")
    Draft202012Validator.check_schema(schema)


def test_committed_schema_matches_the_model() -> None:
    """Fails when `SnapshotIssueV2` changes until the schema is regenerated:
    uv run python -m ticketscope.jobs.ingest.schema --write"""
    assert (SNAPSHOT_DIR / "schema-v2.json").read_text(encoding="utf-8") == schema_module.render()


def test_drift_is_detected(tmp_path: Path) -> None:
    drifted = schema_module.schema_v2()
    drifted["properties"].pop("key")
    path = tmp_path / "schema-v2.json"
    path.write_text(json.dumps(drifted))
    asset = _gz(tmp_path / "a.jsonl.gz", *_lines())
    assert schema_module.main(["--check", str(asset), "--schema", str(path)]) == 1


def test_schema_and_model_agree_on_fields() -> None:
    assert set(_schema()["properties"]) == set(SnapshotIssueV2.model_fields)


def test_schema_refuses_a_v1_line() -> None:
    validator = Draft202012Validator(_schema())
    assert list(validator.iter_errors(V1_LINE))


# --- check (the publish script's validation) ---------------------------------------------


def test_check_counts_a_valid_asset(tmp_path: Path) -> None:
    asset = _gz(tmp_path / "a.jsonl.gz", *_lines())
    assert schema_module.check(asset) == len(_lines())
    assert schema_module.main(["--check", str(asset)]) == 0


def test_check_names_a_schema_invalid_line(tmp_path: Path) -> None:
    asset = _gz(tmp_path / "a.jsonl.gz", _lines()[0], V1_LINE)
    with pytest.raises(ValueError, match=r"a.jsonl.gz:2: schema v2"):
        schema_module.check(asset)
    assert schema_module.main(["--check", str(asset)]) == 1


def test_check_runs_the_model_too(tmp_path: Path) -> None:
    # Schema-valid, but the model's rule (closed exactly when resolved) fails.
    bad = {**_lines()[0], "state": "open"}
    asset = _gz(tmp_path / "a.jsonl.gz", bad)
    with pytest.raises(ValueError, match=r"a.jsonl.gz:1: model"):
        schema_module.check(asset)


def test_check_refuses_an_empty_asset(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty"):
        schema_module.check(_gz(tmp_path / "a.jsonl.gz"))


# --- the v2 fixture (test design P2 "fixture and load move to v2", case 1) ---------------


def test_fixture_validates_against_schema_v2() -> None:
    validator = Draft202012Validator(_schema(), format_checker=Draft202012Validator.FORMAT_CHECKER)
    for line in _lines():
        errors = list(validator.iter_errors(line))
        assert not errors, f"issue {line.get('number')}: {errors[0].message}"


def test_fixture_parses_as_snapshot_issue_v2() -> None:
    issues = [SnapshotIssueV2.model_validate(line) for line in _lines()]
    numbers = [i.number for i in issues]
    assert numbers == list(range(900001, 900009))
    assert all(i.url == f"https://bugs.mojang.com/browse/{i.key}" for i in issues)


def test_fixture_records_kinds_outside_the_schema_and_they_hold() -> None:
    kinds = read_kinds(SNAPSHOT_DIR / "fixture-kinds.json")
    issues = [SnapshotIssueV2.model_validate(line) for line in _lines()]
    assert set(kinds) == {i.number for i in issues}
    assert set(kinds.values()) == {"short", "log_heavy"}
    assert all("kind" not in line for line in _lines())
    assert {i.number: derive_kind(i) for i in issues} == kinds


def test_fixture_log_heavy_issues_use_jira_blocks() -> None:
    kinds = read_kinds(SNAPSHOT_DIR / "fixture-kinds.json")
    for line in _lines():
        if kinds[line["number"]] == "log_heavy":
            assert "{code" in line["body"] or "{noformat}" in line["body"]
            assert "```" not in line["body"]


def test_sidecar_rejects_an_unknown_kind(tmp_path: Path) -> None:
    path = tmp_path / "kinds.json"
    path.write_text(json.dumps({"900001": "medium"}))
    with pytest.raises(ValueError, match="unknown kind"):
        read_kinds(path)


# --- load reads v2 (case 2) --------------------------------------------------------------


def test_load_builds_one_row_per_issue(snapshot_dir: Path) -> None:
    rows = list(
        build_rows(
            read_snapshot(snapshot_dir / "fixture.jsonl.gz"),
            read_kinds(snapshot_dir / "fixture-kinds.json"),
        )
    )
    issues = {i.number: i for i in (SnapshotIssueV2.model_validate(x) for x in _lines())}
    assert len(rows) == len(issues)
    assert {r.outcome_status for r in rows} == {"unknown"}
    assert all(r.outcome_source is None for r in rows)
    assert all(r.state_reason is None for r in rows)
    assert all(r.closed_at == issues[r.number].resolved_at for r in rows)
    assert all(r.title in r.search_text for r in rows)


def test_load_fails_on_an_issue_without_a_kind(snapshot_dir: Path) -> None:
    with pytest.raises(ValueError, match="no kind"):
        list(build_rows(read_snapshot(snapshot_dir / "fixture.jsonl.gz"), {}))


def test_load_reports_the_bad_line(tmp_path: Path) -> None:
    path = _gz(tmp_path / "bad.jsonl.gz", {"number": 1})
    with pytest.raises(ValueError, match=r"bad.jsonl.gz:1"):
        list(read_snapshot(path))


def test_load_refuses_a_v1_line(tmp_path: Path) -> None:
    path = _gz(tmp_path / "v1.jsonl.gz", _lines()[0], V1_LINE)
    with pytest.raises(ValueError, match=r"v1.jsonl.gz:2: invalid snapshot issue"):
        list(read_snapshot(path))
