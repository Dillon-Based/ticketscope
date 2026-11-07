import gzip
import hashlib
import shutil
from pathlib import Path

import pytest

from tests.target import SNAPSHOT_DIR
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord
from ticketscope.jobs.load.main import build_rows, read_snapshot


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
