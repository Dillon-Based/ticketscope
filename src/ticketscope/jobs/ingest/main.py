"""ingest: a restored Public Jira Dataset v7 dump to a schema v2 corpus snapshot (AD-6).

Reads the Mojang instance's MCL, REALMS and MCD documents from a MongoDB on the person's
machine (`mongorestore` of the dump), selects and masks them (`jira.select`), and writes
`<out>/<version>.jsonl.gz` (sorted by number, gzip mtime 0), its `.sha256`, the
`<version>-kinds.json` sidecar for the timed load, and `report.json`.

Run by a person through `scripts/publish-snapshot.sh`, never by a workflow (AD-17).
Needs the `ingest` dependency group (pymongo), which the app image leaves out.

Exit codes: 0 complete, 1 failure, 2 bad usage.
"""

import argparse
import gzip
import hashlib
import json
import logging
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ticketscope.core.derive import derive_kind
from ticketscope.jobs.ingest import jira

log = logging.getLogger("ticketscope.ingest")

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2

SCHEMA_VERSION = 2
REPORT = "report.json"
DEFAULT_URI = "mongodb://127.0.0.1:27017"
DEFAULT_DATABASE = "JiraReposAnon"
_VERSION = re.compile(r"^\d{4}\.(0[1-9]|1[0-2])\.[1-9]\d*$")
_KEY = re.compile(r"^[A-Z][A-Z0-9_]*-[1-9]\d*$")


@dataclass(frozen=True, slots=True)
class Options:
    version: str
    out_dir: Path
    exclusions: Path
    mongo_uri: str = DEFAULT_URI
    database: str = DEFAULT_DATABASE


# --- exclusions ----------------------------------------------------------------------------


def read_exclusions(path: Path) -> frozenset[str]:
    """Jira issue keys such as `MCL-123`, one per line; `#` starts a comment."""
    keys: set[str] = set()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.split("#", 1)[0].strip()
        if not text:
            continue
        if not _KEY.match(text):
            raise ValueError(f"{path}:{lineno}: expected a Jira issue key, got {text!r}")
        keys.add(text)
    return frozenset(keys)


# --- outputs -------------------------------------------------------------------------------


def _write_atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def write_outputs(out_dir: Path, version: str, selection: jira.Selection) -> dict[str, Any]:
    """The asset, its checksum, the kinds sidecar (for the timed load only) and the report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    issues = sorted(selection.issues, key=lambda issue: issue.number)
    asset = f"{version}.jsonl.gz"
    payload = "".join(issue.model_dump_json() + "\n" for issue in issues).encode("utf-8")
    # mtime=0 and no file name: the same issues give the same bytes.
    compressed = gzip.compress(payload, compresslevel=9, mtime=0)
    digest = hashlib.sha256(compressed).hexdigest()
    _write_atomic(out_dir / asset, compressed)
    _write_atomic(out_dir / f"{asset}.sha256", f"{digest}  {asset}\n".encode())

    kinds = {str(issue.number): derive_kind(issue) for issue in issues}
    _write_atomic(out_dir / f"{version}-kinds.json", json.dumps(kinds, indent=0).encode())

    report: dict[str, Any] = {
        "version": version,
        "schema_version": SCHEMA_VERSION,
        **jira.report(selection),
        "asset": asset,
        "sha256": digest,
    }
    _write_atomic(out_dir / REPORT, (json.dumps(report, indent=2) + "\n").encode())
    log.info(
        "wrote %s: %d issues (%d short, %d log_heavy), %d in-subset duplicate pairs",
        asset,
        report["count"],
        report["kinds"]["short"],
        report["kinds"]["log_heavy"],
        report["pairs"]["total"],
    )
    return report


def run(options: Options, docs: Iterable[jira.Document]) -> dict[str, Any]:
    """Select from `docs` (in `_id` order) and write the outputs. Returns the report."""
    exclusions = read_exclusions(options.exclusions)
    selection = jira.select(docs, exclusions=exclusions)
    log.info(
        "selected %d issues (%d open targets, %d repeated keys dropped, %d excluded, "
        "%d skipped for a bad time)",
        len(selection.issues),
        selection.open_targets,
        selection.repeated_keys_dropped,
        selection.excluded,
        selection.bad_time,
    )
    if not selection.issues:
        raise ValueError("no issues selected; is the dump restored into the database?")
    return write_outputs(options.out_dir, options.version, selection)


# --- entry point ---------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ticketscope-ingest", description=__doc__)
    parser.add_argument("--version", required=True, help="snapshot version, YYYY.MM.N")
    parser.add_argument("--out-dir", type=Path, default=Path("out"))
    parser.add_argument("--mongo-uri", default=DEFAULT_URI)
    parser.add_argument("--database", default=DEFAULT_DATABASE)
    parser.add_argument("--exclusions", type=Path, default=Path("snapshot/exclusions.txt"))
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = _parser().parse_args(argv)
    if not _VERSION.match(args.version):
        log.error("--version must be YYYY.MM.N, got %r", args.version)
        return EXIT_USAGE
    options = Options(
        version=args.version,
        out_dir=args.out_dir,
        exclusions=args.exclusions,
        mongo_uri=args.mongo_uri,
        database=args.database,
    )
    try:
        # Imported here so the rest of ingest needs no pymongo (it is not in the app image).
        from ticketscope.adapters.jira_dump import open_issues

        docs = open_issues(options.mongo_uri, options.database, jira.INSTANCE, jira.PROJECTS)
        run(options, docs)
    except Exception:
        log.exception("ingest failed")
        return EXIT_FAILED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
