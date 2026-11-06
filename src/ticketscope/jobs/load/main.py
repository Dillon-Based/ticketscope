"""load: the only writer of corpus tables (AD-7). Loads the pinned snapshot (AD-6).

Reads `<snapshot_dir>/<version>.jsonl.gz` and the expected-kinds sidecar
`<snapshot_dir>/<version>-kinds.json`, then replaces the issues and the single
`corpus_meta` row in one transaction.

Until story 5, each issue's kind comes from the sidecar and every outcome is
`unknown`.
"""

import gzip
import json
import logging
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import cast, get_args

from ticketscope.adapters.postgres import IssueRow, replace_corpus, wait_for_database
from ticketscope.core.model import Kind
from ticketscope.core.snapshot import SnapshotIssue
from ticketscope.settings import Settings

log = logging.getLogger("ticketscope.load")


def read_snapshot(path: Path) -> Iterator[SnapshotIssue]:
    """Yield the issues of a gzipped JSONL snapshot, validating each line."""
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        for lineno, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                yield SnapshotIssue.model_validate_json(line)
            except ValueError as exc:
                raise ValueError(f"{path}:{lineno}: invalid snapshot issue: {exc}") from exc


def read_kinds(path: Path) -> dict[int, Kind]:
    """Read the expected-kinds sidecar: a JSON object of issue number to kind."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a JSON object")
    allowed = get_args(Kind)
    kinds: dict[int, Kind] = {}
    for number, kind in cast(dict[str, object], raw).items():
        if kind not in allowed:
            raise ValueError(f"{path}: issue {number}: unknown kind {kind!r}")
        kinds[int(number)] = cast(Kind, kind)
    return kinds


def search_text(issue: SnapshotIssue) -> str:
    return f"{issue.title}\n\n{issue.body or ''}"


def build_rows(issues: Iterable[SnapshotIssue], kinds: dict[int, Kind]) -> Iterator[IssueRow]:
    for issue in issues:
        kind = kinds.get(issue.number)
        if kind is None:
            raise ValueError(f"issue {issue.number} has no kind in the sidecar")
        yield IssueRow(
            number=issue.number,
            title=issue.title,
            body=issue.body,
            url=issue.url,
            state=issue.state,
            state_reason=issue.state_reason,
            created_at=issue.created_at,
            closed_at=issue.closed_at,
            kind=kind,
            outcome_status="unknown",
            outcome_summary=None,
            outcome_source=None,
            outcome_ref=None,
            search_text=search_text(issue),
        )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings()
    version = settings.snapshot_version
    snapshot = settings.snapshot_dir / f"{version}.jsonl.gz"
    sidecar = settings.snapshot_dir / f"{version}-kinds.json"
    conninfo = settings.conninfo()
    try:
        kinds = read_kinds(sidecar)
        rows = build_rows(read_snapshot(snapshot), kinds)
        wait_for_database(conninfo, role=None, timeout_s=settings.db_wait_timeout_seconds)
        count = replace_corpus(conninfo, version, rows)
    except Exception:
        log.exception("load of snapshot %s failed; previous corpus kept", version)
        return 1
    log.info("loaded snapshot %s: %d issues", version, count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
