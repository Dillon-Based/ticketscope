"""Snapshot schema v2: generated from `core.snapshot.SnapshotIssueV2` (AD-6).

`snapshot/schema-v2.json` is this module's output, committed; a unit test fails when the
committed file drifts from the model. Regenerate it after changing the model:

    uv run python -m ticketscope.jobs.ingest.schema --write

`check` validates a gzipped JSONL asset line by line against the schema and the model;
the publish script runs it before the timed load:

    uv run python -m ticketscope.jobs.ingest.schema --check out/2026.11.1.jsonl.gz
"""

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from ticketscope.core.snapshot import SnapshotIssueV2

SCHEMA_PATH = Path("snapshot/schema-v2.json")
SCHEMA_ID = "https://github.com/Dillon-Based/ticketscope/snapshot/schema-v2.json"


def schema_v2() -> dict[str, Any]:
    """The JSON Schema (draft 2020-12) of one schema v2 snapshot line."""
    generated = SnapshotIssueV2.model_json_schema()
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        **generated,
        "title": "ticketscope corpus snapshot issue, schema v2",
        "description": (
            "One line of a corpus snapshot (gzipped JSONL, one issue per line), Mojang Jira. "
            "Generated from ticketscope.core.snapshot.SnapshotIssueV2; do not edit by hand."
        ),
    }


def render() -> str:
    return json.dumps(schema_v2(), indent=2, ensure_ascii=False) + "\n"


def check(path: Path, schema: dict[str, Any] | None = None) -> int:
    """Validate every line of the gzipped JSONL `path`. Returns the line count; raises
    `ValueError` naming the first bad line, or when the asset is empty."""
    validator = Draft202012Validator(
        schema or schema_v2(), format_checker=Draft202012Validator.FORMAT_CHECKER
    )
    count = 0
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        for lineno, line in enumerate(lines, start=1):
            try:
                record = json.loads(line)
            except ValueError as exc:
                raise ValueError(f"{path}:{lineno}: not JSON: {exc}") from exc
            errors = validator.iter_errors(record)  # pyright: ignore[reportUnknownMemberType]
            error = next(iter(errors), None)
            if error is not None:
                raise ValueError(f"{path}:{lineno}: schema v2: {error.message}")
            try:
                SnapshotIssueV2.model_validate(record)
            except ValueError as exc:
                raise ValueError(f"{path}:{lineno}: model: {exc}") from exc
            count += 1
    if count == 0:
        raise ValueError(f"{path}: the snapshot is empty")
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or check snapshot schema v2.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help=f"regenerate {SCHEMA_PATH}")
    group.add_argument("--check", type=Path, metavar="ASSET", help="validate a .jsonl.gz")
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    args = parser.parse_args(argv)
    if args.write:
        args.schema.write_text(render(), encoding="utf-8")
        print(f"wrote {args.schema}")
        return 0
    committed = json.loads(args.schema.read_text(encoding="utf-8"))
    if committed != schema_v2():
        print(f"{args.schema} drifts from SnapshotIssueV2; rerun with --write", file=sys.stderr)
        return 1
    try:
        count = check(args.check, committed)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"{count} issues valid against schema v2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
