"""load: the only writer of corpus tables (AD-7). Loads the pinned snapshot (AD-6).

Flow: compare the pin with the `corpus_meta` row and stop when the snapshot version,
the embedding model (none unless `TICKETSCOPE_EMBEDDINGS_COMPUTE` is on) and core's
preprocessing version all match (`no-op`).
Otherwise fetch `<version>.jsonl.gz` from its Release (or `<snapshot_dir>`), verify it
against the pinned SHA-256, derive each issue's kind and outcome with core (AD-8), and
replace the issues, any embeddings and the `corpus_meta` row in one transaction. Schema v2 only; any
other line is refused. Ends with one `load report:` log line (AD-22).
"""

import gzip
import json
import logging
import sys
import time
from collections import Counter
from collections.abc import Generator, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryFile
from typing import TextIO, cast, get_args

from ticketscope import telemetry
from ticketscope.adapters.postgres import (
    CorpusMeta,
    EmbeddingRow,
    IssueRow,
    read_corpus_meta,
    replace_corpus,
    wait_for_database,
)
from ticketscope.adapters.release import fetch_snapshot
from ticketscope.core.derive import (
    derive_kind,
    derive_outcome,
    embedding_text,
    preprocessing_version,
    search_text,
)
from ticketscope.core.model import Kind, OutcomeStatus
from ticketscope.core.ports import Embedder
from ticketscope.core.snapshot import SnapshotIssueV2
from ticketscope.settings import Settings

log = logging.getLogger("ticketscope.load")

BUDGET_SECONDS = 600  # initiative R10: a load fits its spin-up share
# Long inputs make ONNX's inference workspace much larger than the output vectors.
# Keep that workspace bounded as well as the corpus-wide vector storage.
EMBEDDING_BATCH_SIZE = 8


@dataclass(slots=True)
class EmbeddingStats:
    """What the embedding pass did: vectors written and seconds spent in the model."""

    count: int = 0
    seconds: float = 0.0


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


def embedding_rows(
    issues: Iterable[SnapshotIssueV2],
    embedder: Embedder,
    stats: EmbeddingStats,
    batch_size: int = EMBEDDING_BATCH_SIZE,
) -> Iterator[EmbeddingRow]:
    """One row per issue, embedded in batches of `batch_size` from core's embedding text."""
    batch: list[SnapshotIssueV2] = []

    def flush() -> Iterator[EmbeddingRow]:
        started = time.monotonic()
        vectors = embedder.embed([embedding_text(i.title, i.body) for i in batch])
        stats.seconds += time.monotonic() - started
        if len(vectors) != len(batch):
            raise ValueError(f"embedder returned {len(vectors)} vectors for {len(batch)} texts")
        for issue, vector in zip(batch, vectors, strict=True):
            stats.count += 1
            yield EmbeddingRow(issue.number, embedder.model_id, vector)
        batch.clear()

    for issue in issues:
        batch.append(issue)
        if len(batch) >= batch_size:
            yield from flush()
    if batch:
        yield from flush()


@contextmanager
def spooled_embedding_rows(
    issues: Iterable[SnapshotIssueV2], embedder: Embedder, stats: EmbeddingStats
) -> Generator[Iterator[EmbeddingRow]]:
    """Finish inference into a disk file before yielding rows to the write transaction.

    Only an inference batch and one serialized row are resident. TemporaryFile is
    disk-backed from the first write and closes on inference or database failure.
    JSON preserves the Python float values without changing preprocessing or vectors.
    """
    with TemporaryFile(mode="w+t", encoding="utf-8") as spool:
        for row in embedding_rows(issues, embedder, stats):
            spool.write(json.dumps((row.issue_number, row.model_id, row.vector)))
            spool.write("\n")
        spool.seek(0)
        yield _read_embedding_spool(spool)


def _read_embedding_spool(spool: TextIO) -> Iterator[EmbeddingRow]:
    for line in spool:
        # This private file contains only the typed rows written immediately above.
        number, model_id, vector = cast(tuple[int, str, list[float]], json.loads(line))
        yield EmbeddingRow(number, model_id, vector)


def pinned_meta(snapshot_version: str, embedding_model_id: str | None = None) -> CorpusMeta:
    """The `corpus_meta` row this code would write for the pin. With an embedding model id,
    the row records it and the embedding rule in the preprocessing version."""
    return CorpusMeta(
        snapshot_version=snapshot_version,
        embedding_model_id=embedding_model_id,
        preprocessing_version=preprocessing_version(embeddings=embedding_model_id is not None),
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


def report_line(
    version: str,
    count: int,
    counts: Counter[str],
    seconds: float,
    budget: int,
    embeddings: EmbeddingStats | None = None,
) -> str:
    """The one `load report:` line: count, kind and outcome shares, time against budget,
    and the embedding count and seconds when embeddings were computed."""

    def share(key: str) -> str:
        return f"{100 * counts[key] / count:.1f}%" if count else "0.0%"

    kinds = " ".join(f"kind.{k}={share(f'kind:{k}')}" for k in get_args(Kind))
    outcomes = " ".join(f"outcome.{s}={share(f'outcome:{s}')}" for s in get_args(OutcomeStatus))
    within = "true" if seconds <= budget else "false"
    embedded = (
        f" embeddings={embeddings.count} embedding_seconds={embeddings.seconds:.1f}"
        if embeddings is not None
        else ""
    )
    return (
        f"load report: snapshot={version} issues={count} {kinds} {outcomes}{embedded}"
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


def run(settings: Settings, embedder: Embedder | None = None) -> int:
    """The load itself: 0 on success or no-op, 1 with the previous corpus kept.

    Embeddings are computed only when `settings.embeddings_compute` is on; `embedder` lets a
    caller inject one, else the baked model is loaded when needed."""
    version = settings.snapshot_version
    if not settings.snapshot_sha256.strip():
        log.error(
            "TICKETSCOPE_SNAPSHOT_SHA256 is empty: snapshot %s has no pinned checksum;"
            " previous corpus kept",
            version,
        )
        return 1
    conninfo = settings.conninfo()
    compute = settings.embeddings_compute
    if compute and not (settings.embedding_model_id or embedder):
        log.error("TICKETSCOPE_EMBEDDINGS_COMPUTE is on but no embedding model id is set")
        return 1
    model_id = (embedder.model_id if embedder else settings.embedding_model_id) if compute else None
    wanted = pinned_meta(version, model_id)
    stats = EmbeddingStats() if compute else None
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
        rows = build_rows(read_snapshot(path), counts)
        if stats is None:
            count = replace_corpus(conninfo, wanted, rows)
        else:
            if embedder is None:
                from ticketscope.adapters.embedder import FastEmbedEmbedder

                embedder = FastEmbedEmbedder(
                    settings.embedding_model_id, settings.embedding_cache_dir
                )
            # Embed before the write transaction opens: TRUNCATE takes ACCESS EXCLUSIVE,
            # which would block the live api for the whole CPU pass.
            with spooled_embedding_rows(read_snapshot(path), embedder, stats) as embedded:
                count = replace_corpus(conninfo, wanted, rows, embedded)
    except Exception:
        log.exception("load of snapshot %s failed; previous corpus kept", version)
        return 1
    seconds = time.monotonic() - started
    line = report_line(version, count, counts, seconds, BUDGET_SECONDS, stats)
    log.log(logging.INFO if seconds <= BUDGET_SECONDS else logging.WARNING, line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
