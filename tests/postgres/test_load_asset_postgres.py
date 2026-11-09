"""`load` from a pinned embedding asset against real Postgres with pgvector (test design row C,
story 4): rows per issue, the no-op, and all-or-nothing failures that keep the old corpus."""

import gzip
import hashlib
import shutil
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

from tests.target import SNAPSHOT_DIR
from ticketscope.adapters.embedding_asset import (
    AssetRecord,
    read_manifest,
    read_records,
    write_asset,
)
from ticketscope.adapters.postgres import PostgresCorpusStore, read_corpus_meta
from ticketscope.adapters.release import embeddings_asset_name, sha256_file
from ticketscope.core import derive
from ticketscope.core.fakes import HashEmbedder
from ticketscope.jobs.ingest.embed import build_asset
from ticketscope.jobs.load import main as load

MODEL = "model-x"
PRE_EMB = derive.preprocessing_version(embeddings=True)


def _counts(conninfo: str) -> tuple[int, int, str | None]:
    with psycopg.connect(conninfo) as conn:
        [(issues, embeddings, model)] = conn.execute(
            "SELECT (SELECT count(*) FROM issue), (SELECT count(*) FROM issue_embedding),"
            " (SELECT embedding_model_id FROM corpus_meta)"
        ).fetchall()
    return issues, embeddings, model


@pytest.fixture
def snapshot_dir(tmp_path: Path) -> Path:
    with (
        (SNAPSHOT_DIR / "fixture.jsonl").open("rb") as src,
        gzip.open(tmp_path / "fixture.jsonl.gz", "wb") as dst,
    ):
        shutil.copyfileobj(src, dst)
    return tmp_path


@pytest.fixture
def fixture_sha256(snapshot_dir: Path) -> str:
    return hashlib.sha256((snapshot_dir / "fixture.jsonl.gz").read_bytes()).hexdigest()


@pytest.fixture(autouse=True)
def _empty(pg_conninfo: str) -> Iterator[None]:
    with psycopg.connect(pg_conninfo, autocommit=True) as conn:
        conn.execute("TRUNCATE issue, issue_embedding")
        conn.execute("DELETE FROM corpus_meta")
    yield


@pytest.fixture
def pinned(
    pg_conninfo: str,
    snapshot_dir: Path,
    fixture_sha256: str,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Settings that pin the fixture snapshot and its embedding asset (built in `snapshot_dir`)."""
    params = dict(part.split("=", 1) for part in pg_conninfo.split())
    monkeypatch.setenv("TICKETSCOPE_DB_HOST", params["host"])
    monkeypatch.setenv("TICKETSCOPE_DB_PORT", params["port"])
    monkeypatch.setenv("TICKETSCOPE_DB_NAME", params["dbname"])
    monkeypatch.setenv("TICKETSCOPE_DB_USER", params["user"])
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_DIR", str(snapshot_dir))
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_VERSION", "fixture")
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", fixture_sha256)
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_BASE_URL", "https://releases.invalid/download")
    monkeypatch.setenv("TICKETSCOPE_EMBEDDING_MODEL_ID", MODEL)
    monkeypatch.setenv("TICKETSCOPE_EMBEDDINGS_ASSET_VERSION", "fixture")
    _m, path, _s = build_asset(
        snapshot_dir / "fixture.jsonl.gz", fixture_sha256, "fixture", HashEmbedder(MODEL),
        "ab" * 32, snapshot_dir,
    )  # fmt: skip
    assert path.name == embeddings_asset_name("fixture", MODEL, PRE_EMB)
    monkeypatch.setenv("TICKETSCOPE_EMBEDDINGS_SHA256", sha256_file(path))
    return path


def test_a_pinned_load_gives_one_embedding_per_issue_and_the_model_in_corpus_meta(
    pg_conninfo: str, pinned: Path
) -> None:
    assert load.main() == 0
    issues, embeddings, model = _counts(pg_conninfo)
    assert issues == embeddings == 8 and model == MODEL
    meta = read_corpus_meta(pg_conninfo)
    assert meta is not None and meta.preprocessing_version == PRE_EMB
    store = PostgresCorpusStore(pg_conninfo)
    assert store.has_embeddings(MODEL)
    [vector] = HashEmbedder(MODEL).embed(["Anything"])
    assert len(store.dense_search(MODEL, vector, 3)) == 3


def test_a_second_load_is_a_no_op(pg_conninfo: str, pinned: Path) -> None:
    assert load.main() == 0
    with psycopg.connect(pg_conninfo) as conn:
        [(first,)] = conn.execute("SELECT loaded_at FROM corpus_meta").fetchall()
    assert load.main() == 0
    with psycopg.connect(pg_conninfo) as conn:
        [(second,)] = conn.execute("SELECT loaded_at FROM corpus_meta").fetchall()
    assert first == second


def _rewrite(path: Path, records: list[AssetRecord]) -> str:
    manifest = read_manifest(path)
    path.unlink()
    write_asset(path, manifest, ((r.issue, r.model, r.vector) for r in records))
    return sha256_file(path)


@pytest.mark.parametrize("case", ["bytes", "missing", "extra", "dimension"])
def test_a_bad_asset_fails_the_load_and_keeps_the_previous_corpus(
    pg_conninfo: str, pinned: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    assert load.main() == 0  # the good corpus the failures must keep
    before = _counts(pg_conninfo)
    with psycopg.connect(pg_conninfo, autocommit=True) as conn:
        conn.execute("UPDATE corpus_meta SET preprocessing_version = 'pre0.old.emb0'")
    records = list(read_records(pinned))
    match case:
        case "bytes":
            monkeypatch.setenv("TICKETSCOPE_EMBEDDINGS_SHA256", "0" * 64)
        case "missing":
            monkeypatch.setenv("TICKETSCOPE_EMBEDDINGS_SHA256", _rewrite(pinned, records[:-1]))
        case "extra":
            extra = AssetRecord(issue=999999, model=MODEL, vector=records[0].vector)
            monkeypatch.setenv("TICKETSCOPE_EMBEDDINGS_SHA256", _rewrite(pinned, [*records, extra]))
        case _:
            short = AssetRecord(issue=records[0].issue, model=MODEL, vector=[1.0, 0.0])
            monkeypatch.setenv(
                "TICKETSCOPE_EMBEDDINGS_SHA256", _rewrite(pinned, [short, *records[1:]])
            )
    assert load.main() == 1
    assert _counts(pg_conninfo) == before  # issues, embeddings and corpus_meta all unchanged
    meta = read_corpus_meta(pg_conninfo)
    assert meta is not None and meta.preprocessing_version == "pre0.old.emb0"
