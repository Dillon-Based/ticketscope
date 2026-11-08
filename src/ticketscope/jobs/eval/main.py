"""eval: score the loaded corpus's labelled pairs as `ticketscope_ro` (AD-7, AD-22).

Runs as a Helm hook after load, rendered only when `eval.enabled` is set. Reads the
`corpus_meta` row, loads `<eval_pairs_dir>/<snapshot_version>.jsonl` (so lineage and ground
truth cannot disagree), scores every available mode, and logs one
`ticketscope-eval results: <json>` line carrying the corpus lineage. CI reads that line
from the Job's log; the pod's filesystem is gone once it completes.
"""

import json
import logging
import sys
import time

from ticketscope import telemetry
from ticketscope.adapters.postgres import PostgresCorpusStore, read_corpus_meta
from ticketscope.core.pairs import read_pairs
from ticketscope.jobs.eval.score import score
from ticketscope.settings import Settings

log = logging.getLogger("ticketscope.eval")

RESULTS_PREFIX = "ticketscope-eval results: "


def main() -> int:
    settings = Settings()
    provider = telemetry.setup(telemetry.SERVICE_JOBS, settings.otlp_endpoint)
    try:
        with telemetry.job_span(provider, "eval") as failed:
            code = run(settings)
            if code:
                failed()
        return code
    finally:
        provider.shutdown()  # flush the job's spans before the process exits


def run(settings: Settings) -> int:
    """Score the loaded corpus: 0 with the results line logged, 1 on any failure."""
    conninfo = settings.conninfo()
    try:
        meta = read_corpus_meta(conninfo)
        if meta is None:
            log.error("eval failed: no corpus loaded (corpus_meta is empty)")
            return 1
        path = settings.eval_pairs_dir / f"{meta.snapshot_version}.jsonl"
        if not path.is_file():
            log.error("eval failed: no pairs file %s for snapshot %s", path, meta.snapshot_version)
            return 1
        pairs = read_pairs(path.read_bytes())
        log.info("scoring %d pairs from %s", len(pairs), path)
        started = time.monotonic()
        # ~21,000 short connections: no per-call psycopg spans in the job's one trace.
        with telemetry.untraced():
            results = score(PostgresCorpusStore(conninfo), pairs)
        seconds = time.monotonic() - started
    except Exception:
        log.exception("eval failed")
        return 1
    line = {
        **results,
        "lineage": {
            "snapshot_version": meta.snapshot_version,
            "embedding_model_id": meta.embedding_model_id,
            "preprocessing_version": meta.preprocessing_version,
        },
        "pairs_file": str(path),
        "wall_seconds": round(seconds, 1),
    }
    log.info("%s%s", RESULTS_PREFIX, json.dumps(line, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
