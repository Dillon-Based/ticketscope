import gzip
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from tests.target import SNAPSHOT_DIR
from ticketscope.core.snapshot import SnapshotIssue
from ticketscope.jobs.load.main import build_rows, read_kinds, read_snapshot

AD6_FIELDS = {
    "number",
    "title",
    "body",
    "state",
    "state_reason",
    "created_at",
    "closed_at",
    "labels",
    "comments",
    "timeline",
}


def _schema() -> dict[str, Any]:
    return json.loads((SNAPSHOT_DIR / "schema-v1.json").read_text())


def _lines() -> list[dict[str, Any]]:
    text = (SNAPSHOT_DIR / "fixture.jsonl").read_text()
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def test_schema_is_valid_draft_2020_12() -> None:
    schema = _schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    Draft202012Validator.check_schema(schema)


def test_schema_requires_every_ad6_field() -> None:
    schema = _schema()
    assert set(schema["required"]) >= AD6_FIELDS
    comment = schema["properties"]["comments"]["items"]
    assert set(comment["required"]) >= {"author_association", "body", "created_at"}


def test_schema_and_model_agree_on_fields() -> None:
    assert set(_schema()["properties"]) == set(SnapshotIssue.model_fields)


def test_fixture_validates_against_the_schema() -> None:
    validator = Draft202012Validator(_schema(), format_checker=Draft202012Validator.FORMAT_CHECKER)
    for line in _lines():
        errors = list(validator.iter_errors(line))
        assert not errors, f"issue {line.get('number')}: {errors[0].message}"


def test_fixture_parses_as_snapshot_issue() -> None:
    issues = [SnapshotIssue.model_validate(line) for line in _lines()]
    assert len(issues) >= 6
    numbers = [i.number for i in issues]
    assert len(set(numbers)) == len(numbers)
    assert all(n >= 900000 for n in numbers)


def test_fixture_has_timeline_events_that_ad6_names() -> None:
    events = {e.event for line in _lines() for e in SnapshotIssue.model_validate(line).timeline}
    assert {"marked_as_duplicate", "cross-referenced"} <= events


def test_sidecar_covers_every_issue_with_both_kinds() -> None:
    kinds = read_kinds(SNAPSHOT_DIR / "fixture-kinds.json")
    assert set(kinds) == {line["number"] for line in _lines()}
    assert set(kinds.values()) == {"short", "log_heavy"}


def test_sidecar_rejects_an_unknown_kind(tmp_path: Path) -> None:
    path = tmp_path / "kinds.json"
    path.write_text(json.dumps({"900001": "medium"}))
    with pytest.raises(ValueError, match="unknown kind"):
        read_kinds(path)


def test_load_builds_one_row_per_issue(snapshot_dir: Path) -> None:
    rows = list(
        build_rows(
            read_snapshot(snapshot_dir / "fixture.jsonl.gz"),
            read_kinds(snapshot_dir / "fixture-kinds.json"),
        )
    )
    assert len(rows) == len(_lines())
    assert {r.outcome_status for r in rows} == {"unknown"}
    assert all(r.outcome_source is None for r in rows)
    assert all(r.title in r.search_text for r in rows)


def test_load_fails_on_an_issue_without_a_kind(snapshot_dir: Path) -> None:
    with pytest.raises(ValueError, match="no kind"):
        list(build_rows(read_snapshot(snapshot_dir / "fixture.jsonl.gz"), {}))


def test_load_reports_the_bad_line(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl.gz"
    with gzip.open(path, "wt") as f:
        f.write('{"number": 1}\n')
    with pytest.raises(ValueError, match=r"bad.jsonl.gz:1"):
        list(read_snapshot(path))
