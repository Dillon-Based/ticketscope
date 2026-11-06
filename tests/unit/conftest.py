import gzip
import shutil
from pathlib import Path

import pytest

from tests.target import SNAPSHOT_DIR
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord
from ticketscope.jobs.load.main import build_rows, read_kinds, read_snapshot


@pytest.fixture
def snapshot_dir(tmp_path: Path) -> Path:
    """The fixture laid out as the app image holds it: `fixture.jsonl.gz` + sidecar."""
    with (
        (SNAPSHOT_DIR / "fixture.jsonl").open("rb") as src,
        gzip.open(tmp_path / "fixture.jsonl.gz", "wb") as dst,
    ):
        shutil.copyfileobj(src, dst)
    shutil.copy(SNAPSHOT_DIR / "fixture-kinds.json", tmp_path / "fixture-kinds.json")
    return tmp_path


@pytest.fixture
def fixture_store(snapshot_dir: Path) -> InMemoryCorpusStore:
    """The fake store holding the fixture exactly as `load` would write it."""
    rows = build_rows(
        read_snapshot(snapshot_dir / "fixture.jsonl.gz"),
        read_kinds(snapshot_dir / "fixture-kinds.json"),
    )
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
                ),
                r.search_text,
            )
            for r in rows
        ),
        corpus_version="fixture",
    )
