"""load: the only writer of corpus tables (AD-7). Loads the pinned snapshot (AD-6).

Flow: compare the pin with the `corpus_meta` row and stop when the snapshot version,
the embedding model (none yet) and core's preprocessing version all match (`no-op`).
Otherwise fetch `<version>.jsonl.gz` from its Release (or `<snapshot_dir>`), verify it
against the pinned SHA-256, derive each issue's kind and outcome with core (AD-8), and
replace the issues and the `corpus_meta` row in one transaction. Schema v2 only; any
other line is refused. Ends with one `load report:` log line (AD-22).
"""

import gzip
import logging
import sys
import time
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import get_args

from ticketscope import telemetry
from ticketscope.adapters.postgres import (
    CorpusMeta,
    IssueRow,
    read_corpus_meta,
    replace_corpus,
    wait_for_database,
)
from ticketscope.adapters.release import fetch_snapshot
from ticketscope.core.derive import derive_kind, derive_outcome, preprocessing_version, search_text
from ticketscope.core.model import Kind, OutcomeStatus
from ticketscope.core.snapshot import SnapshotIssueV2
from ticketscope.settings import Settings

log = logging.getLogger("ticketscope.load")

BUDGET_SECONDS = 600  # initiative R10: a load fits its spin-up share


def read_snapshot(path: Path) -> Iterator[SnapshotIssueV2]:
    """Yield the issues of a gzipped JSONL snapshot, validating each line as schema v2."""
    with gzip.open(path, "rt", encoding="utf-8") as lines:
        for lineno, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                yield SnapshotIssueV2.model_validate_json(line)
            except ValueError as exc:
                raise ValueError(f"{path}:{lineno}: invalid snapshot issue: {exc}") from exc


def build_rows(
    issues: Iterable[SnapshotIssueV2], counts: Counter[str] | None = None
) -> Iterator[IssueRow]:
    """One row per issue, kind and outcome derived by core. `counts` gets `kind:<kind>`
    and `outcome:<status>` per issue."""
    for issue in issues:
        kind = derive_kind(issue)
        outcome = derive_outcome(issue)
        if counts is not None:
            counts[f"kind:{kind}"] += 1
            counts[f"outcome:{outcome.status}"] += 1
        yield IssueRow(
            number=issue.number,
            title=issue.title,
            body=issue.body,
            url=issue.url,
            state=issue.state,
            state_reason=None,
            created_at=issue.created_at,
            closed_at=issue.resolved_at,
            kind=kind,
            outcome_status=outcome.status,
            outcome_summary=outcome.summary,
            outcome_source=outcome.source,
            outcome_ref=outcome.ref,
            search_text=search_text(issue),
        )


def pinned_meta(snapshot_version: str) -> CorpusMeta:
    """The `corpus_meta` row this code would write for the pin."""
    return CorpusMeta(
        snapshot_version=snapshot_version,
        embedding_model_id=None,
        preprocessing_version=preprocessing_version(),
    )


def reload_reason(current: CorpusMeta | None, wanted: CorpusMeta) -> str | None:
    """Why the corpus must be reloaded, or `None` when it already matches the pin."""
    if current is None:
        return "no corpus loaded"
    changed = [
        f"{field} {getattr(current, field)!r} -> {getattr(wanted, field)!r}"
        for field in ("snapshot_version", "embedding_model_id", "preprocessing_version")
        if getattr(current, field) != getattr(wanted, field)
    ]
    return "; ".join(changed) or None


def report_line(version: str, count: int, counts: Counter[str], seconds: float, budget: int) -> str:
    """The one `load report:` line: count, kind and outcome shares, time against budget."""

    def share(key: str) -> str:
        return f"{100 * counts[key] / count:.1f}%" if count else "0.0%"

    kinds = " ".join(f"kind.{k}={share(f'kind:{k}')}" for k in get_args(Kind))
    outcomes = " ".join(f"outcome.{s}={share(f'outcome:{s}')}" for s in get_args(OutcomeStatus))
    within = "true" if seconds <= budget else "false"
    return (
        f"load report: snapshot={version} issues={count} {kinds} {outcomes}"
        f" load_seconds={seconds:.1f} budget_seconds={budget} within_budget={within}"
    )


def main() -> int:
    settings = Settings()
    provider = telemetry.setup(telemetry.SERVICE_JOBS, settings.otlp_endpoint)
    # httpx2 logs each request URL at INFO; the Release redirect carries a signed query.
    logging.getLogger("httpx2").setLevel(logging.WARNING)
    try:
        with telemetry.job_span(provider, "load") as failed:
            code = run(settings)
            if code:
                failed()
        return code
    finally:
        provider.shutdown()  # flush the job's spans before the process exits


def run(settings: Settings) -> int:
    """The load itself: 0 on success or no-op, 1 with the previous corpus kept."""
    version = settings.snapshot_version
    if not settings.snapshot_sha256.strip():
        log.error(
            "TICKETSCOPE_SNAPSHOT_SHA256 is empty: snapshot %s has no pinned checksum;"
            " previous corpus kept",
            version,
        )
        return 1
    conninfo = settings.conninfo()
    wanted = pinned_meta(version)
    try:
        wait_for_database(conninfo, role=None, timeout_s=settings.db_wait_timeout_seconds)
        reason = reload_reason(read_corpus_meta(conninfo), wanted)
        if reason is None:
            log.info(
                "no-op: corpus already holds snapshot %s with preprocessing %s",
                version,
                wanted.preprocessing_version,
            )
            return 0
        log.info("reloading snapshot %s: %s", version, reason)
        started = time.monotonic()  # load_seconds: fetch, derive and write
        path = fetch_snapshot(
            settings.snapshot_base_url,
            version,
            settings.snapshot_dir,
            settings.snapshot_sha256,
            timeout=settings.snapshot_download_timeout_seconds,
        )
        counts: Counter[str] = Counter()
        count = replace_corpus(conninfo, wanted, build_rows(read_snapshot(path), counts))
    except Exception:
        log.exception("load of snapshot %s failed; previous corpus kept", version)
        return 1
    seconds = time.monotonic() - started
    line = report_line(version, count, counts, seconds, BUDGET_SECONDS)
    log.log(logging.INFO if seconds <= BUDGET_SECONDS else logging.WARNING, line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
