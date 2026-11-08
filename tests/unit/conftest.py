import gzip
import hashlib
import logging
import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from opentelemetry import trace
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

from tests.target import SNAPSHOT_DIR
from ticketscope import telemetry
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord
from ticketscope.jobs.load.main import build_rows, read_snapshot


@pytest.fixture(autouse=True)
def _isolate_process_bootstrap(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Job mains run in-process here; real provider registration is tested in a child.

    Do not consume OpenTelemetry's write-once global provider. Undo instrumentation,
    environment and logger changes even when a job assertion fails.
    """
    monkeypatch.setattr(trace, "set_tracer_provider", lambda provider: None)
    opt_in = telemetry.SEMCONV_OPT_IN_VAR
    # Saved by hand: monkeypatch.delenv on an absent variable records no undo, so a
    # value the app writes later would outlive the test.
    opt_in_before = os.environ.get(opt_in)
    logger = logging.getLogger("httpx2")
    level = logger.level
    instrumentor = PsycopgInstrumentor()
    was_instrumented = instrumentor.is_instrumented_by_opentelemetry
    try:
        yield
    finally:
        if opt_in_before is None:
            os.environ.pop(opt_in, None)
        else:
            os.environ[opt_in] = opt_in_before
        logger.setLevel(level)
        if not was_instrumented and instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.uninstrument()


@pytest.fixture
def snapshot_dir(tmp_path: Path) -> Path:
    """The fixture laid out as `load` finds a local asset: `<dir>/fixture.jsonl.gz`."""
    with (
        (SNAPSHOT_DIR / "fixture.jsonl").open("rb") as src,
        gzip.open(tmp_path / "fixture.jsonl.gz", "wb") as dst,
    ):
        shutil.copyfileobj(src, dst)
    return tmp_path


@pytest.fixture
def fixture_sha256(snapshot_dir: Path) -> str:
    """The SHA-256 of `snapshot_dir`'s fixture asset, as a pin would hold it."""
    return hashlib.sha256((snapshot_dir / "fixture.jsonl.gz").read_bytes()).hexdigest()


@pytest.fixture
def fixture_store(snapshot_dir: Path) -> InMemoryCorpusStore:
    """The fake store holding the fixture exactly as `load` would write it."""
    rows = list(build_rows(read_snapshot(snapshot_dir / "fixture.jsonl.gz")))
    return InMemoryCorpusStore(
        (
            (
                IssueRecord(
                    number=r.number,
                    title=r.title,
                    url=r.url,
                    kind=r.kind,
                    state=r.state,
                    outcome_status=r.outcome_status,
                    outcome_summary=r.outcome_summary,
                    outcome_source=r.outcome_source,
                    outcome_ref=r.outcome_ref,
                ),
                r.search_text,
            )
            for r in rows
        ),
        corpus_version="fixture",
        bodies={r.number: r.body for r in rows},
    )
