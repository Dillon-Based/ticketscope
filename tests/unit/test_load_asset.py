"""`load` from a pinned embedding asset (story 4), over the I/O matrix, with the database faked.

The asset is built by `embed.build_asset` from the fixture snapshot with the hash embedder
and sits in `snapshot_dir`, so `fetch_embeddings` takes its local-file path.
"""

import logging
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from ticketscope.adapters import embedder as embedder_mod
from ticketscope.adapters.embedding_asset import (
    AssetManifest,
    AssetRecord,
    read_manifest,
    read_records,
    write_asset,
)
from ticketscope.adapters.postgres import CorpusMeta, EmbeddingRow, IssueRow
from ticketscope.adapters.release import embeddings_asset_name, sha256_file
from ticketscope.core import derive
from ticketscope.core.fakes import HashEmbedder
from ticketscope.jobs.ingest.embed import build_asset
from ticketscope.jobs.load import main as load

MODEL = "model-x"
PRE_EMB = derive.preprocessing_version(embeddings=True)
ASSET_NAME = embeddings_asset_name("fixture", MODEL, PRE_EMB)


class FakeDb:
    """`corpus_meta`, the issue rows and the embedding rows; a write is all or nothing."""

    def __init__(self, meta: CorpusMeta | None = None) -> None:
        self.meta = meta
        self.rows: list[IssueRow] = []
        self.embeddings: list[EmbeddingRow] | None = None
        self.replace_calls = 0

    def read_corpus_meta(self, conninfo: str) -> CorpusMeta | None:
        return self.meta

    def replace_corpus(
        self,
        conninfo: str,
        meta: CorpusMeta,
        rows: Iterable[IssueRow],
        embeddings: Iterable[EmbeddingRow] | None = None,
    ) -> int:
        self.replace_calls += 1
        new_rows = list(rows)
        new_embeddings = list(embeddings) if embeddings is not None else None
        self.meta, self.rows, self.embeddings = meta, new_rows, new_embeddings
        return len(new_rows)


@dataclass
class Asset:
    path: Path
    sha256: str


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch) -> FakeDb:
    fake = FakeDb()
    monkeypatch.setattr(load, "read_corpus_meta", fake.read_corpus_meta)
    monkeypatch.setattr(load, "replace_corpus", fake.replace_corpus)
    monkeypatch.setattr(load, "wait_for_database", lambda *a, **k: None)
    return fake


@pytest.fixture(autouse=True)
def _env(snapshot_dir: Path, fixture_sha256: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_DIR", str(snapshot_dir))
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_VERSION", "fixture")
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_SHA256", fixture_sha256)
    monkeypatch.setenv("TICKETSCOPE_SNAPSHOT_BASE_URL", "https://releases.invalid/download")


@pytest.fixture
def no_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_a: object, **_k: object) -> None:
        raise AssertionError("an embedding model was loaded although an asset is pinned")

    monkeypatch.setattr(embedder_mod, "FastEmbedEmbedder", boom)


@pytest.fixture
def asset(snapshot_dir: Path, fixture_sha256: str) -> Asset:
    path = _build(snapshot_dir, fixture_sha256)
    return Asset(path, sha256_file(path))


def _build(snapshot_dir: Path, fixture_sha256: str) -> Path:
    _manifest, path, _seconds = build_asset(
        snapshot_dir / "fixture.jsonl.gz",
        fixture_sha256,
        "fixture",
        HashEmbedder(MODEL),
        "ab" * 32,
        snapshot_dir,
    )
    assert path.name == ASSET_NAME
    return path


def _pin(monkeypatch: pytest.MonkeyPatch, sha256: str, **extra: str) -> None:
    monkeypatch.setenv("TICKETSCOPE_EMBEDDING_MODEL_ID", MODEL)
    monkeypatch.setenv("TICKETSCOPE_EMBEDDINGS_ASSET_VERSION", "fixture")
    monkeypatch.setenv("TICKETSCOPE_EMBEDDINGS_SHA256", sha256)
    for name, value in extra.items():
        monkeypatch.setenv(f"TICKETSCOPE_{name.upper()}", value)


def _rewrite(
    asset: Asset,
    edit: Callable[[list[AssetRecord]], Sequence[AssetRecord]],
    manifest: Callable[[AssetManifest], AssetManifest] = lambda m: m,
) -> Asset:
    """Replace the asset with an edited copy (same name) and return its new checksum."""
    records = list(read_records(asset.path))
    new_manifest = manifest(read_manifest(asset.path))
    asset.path.unlink()
    write_asset(asset.path, new_manifest, ((r.issue, r.model, r.vector) for r in edit(records)))
    return Asset(asset.path, sha256_file(asset.path))


# --- pinned load -----------------------------------------------------------------------------


@pytest.mark.usefixtures("no_model")
def test_pinned_load_writes_one_embedding_per_issue_and_computes_nothing(
    db: FakeDb, asset: Asset, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _pin(monkeypatch, asset.sha256)
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    assert db.meta == CorpusMeta("fixture", MODEL, PRE_EMB)
    assert db.embeddings is not None
    assert sorted(e.issue_number for e in db.embeddings) == sorted(r.number for r in db.rows)
    assert len(db.embeddings) == len(db.rows) == 8
    assert {e.model_id for e in db.embeddings} == {MODEL}
    [line] = [r.getMessage() for r in caplog.records if r.getMessage().startswith("load report:")]
    assert "embeddings_loaded=8" in line and "embedding_seconds" not in line


@pytest.mark.usefixtures("no_model")
def test_vectors_are_the_embedders_vectors(
    db: FakeDb, asset: Asset, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pin(monkeypatch, asset.sha256)
    assert load.main() == 0
    assert db.embeddings is not None
    by_number = {r.number: r for r in db.rows}
    expected = HashEmbedder(MODEL)
    for emb in db.embeddings:
        row = by_number[emb.issue_number]
        [vector] = expected.embed([derive.embedding_text(row.title, row.body)])
        assert list(emb.vector) == pytest.approx(vector, abs=1e-7)


@pytest.mark.usefixtures("no_model")
def test_pinned_load_wins_over_compute_on_kind(
    db: FakeDb, asset: Asset, monkeypatch: pytest.MonkeyPatch
) -> None:
    _pin(monkeypatch, asset.sha256, embeddings_compute="true")
    assert load.main() == 0
    assert db.embeddings is not None and len(db.embeddings) == 8


@pytest.mark.usefixtures("no_model")
def test_a_second_load_is_a_no_op(
    db: FakeDb, asset: Asset, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _pin(monkeypatch, asset.sha256)
    assert load.main() == 0
    caplog.set_level(logging.INFO)
    assert load.main() == 0
    assert db.replace_calls == 1
    assert "no-op" in caplog.text
    assert load.reload_reason(db.meta, load.pinned_meta("fixture", MODEL)) is None


@pytest.mark.usefixtures("no_model")
def test_a_changed_preprocessing_version_reloads_even_with_snapshot_and_model_equal(
    db: FakeDb, asset: Asset, monkeypatch: pytest.MonkeyPatch
) -> None:
    db.meta = CorpusMeta("fixture", MODEL, "pre0.old.emb0")
    _pin(monkeypatch, asset.sha256)
    assert load.main() == 0
    assert db.replace_calls == 1 and db.meta == CorpusMeta("fixture", MODEL, PRE_EMB)


# --- failures keep the previous corpus -------------------------------------------------------


def _previous(db: FakeDb) -> CorpusMeta:
    db.meta = CorpusMeta("2026.10.1", None, "pre0.old")
    return db.meta


@pytest.mark.usefixtures("no_model")
def test_a_wrong_checksum_fails_with_its_reason_and_changes_nothing(
    db: FakeDb, asset: Asset, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    previous = _previous(db)
    _pin(monkeypatch, "0" * 64)
    assert load.main() == 1
    assert "does not match the pinned" in caplog.text and asset.sha256 in caplog.text
    assert db.meta == previous and db.replace_calls == 0


@pytest.mark.usefixtures("no_model")
@pytest.mark.parametrize("case", ["missing", "extra", "dimension", "duplicate", "model"])
def test_bad_coverage_fails_the_load_and_keeps_the_previous_corpus(
    db: FakeDb,
    asset: Asset,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    case: str,
) -> None:
    def edit(records: list[AssetRecord]) -> list[AssetRecord]:
        first = records[0]
        match case:
            case "missing":
                return records[:-1]
            case "extra":
                return [*records, AssetRecord(issue=999999, model=MODEL, vector=first.vector)]
            case "dimension":
                return [
                    AssetRecord(issue=first.issue, model=MODEL, vector=[1.0, 0.0]),
                    *records[1:],
                ]
            case "duplicate":
                return [*records, first]
            case _:
                return [
                    AssetRecord(issue=first.issue, model="other", vector=first.vector),
                    *records[1:],
                ]

    bad = _rewrite(asset, edit)
    previous = _previous(db)
    _pin(monkeypatch, bad.sha256)
    assert load.main() == 1
    assert "previous corpus kept" in caplog.text
    # The write is all or nothing: the fake only commits when the whole write succeeds.
    assert db.meta == previous and db.embeddings is None


@pytest.mark.usefixtures("no_model")
def test_an_asset_for_another_preprocessing_version_is_refused(
    db: FakeDb, asset: Asset, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    bad = _rewrite(
        asset, lambda r: r, lambda m: m.model_copy(update={"preprocessing_version": "pre9"})
    )
    previous = _previous(db)
    _pin(monkeypatch, bad.sha256)
    assert load.main() == 1
    assert "manifest preprocessing_version 'pre9'" in caplog.text
    assert db.meta == previous


@pytest.mark.usefixtures("no_model")
def test_a_manifest_count_that_disagrees_with_the_records_is_refused(
    db: FakeDb, asset: Asset, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    bad = _rewrite(asset, lambda r: r, lambda m: m.model_copy(update={"count": 7}))
    previous = _previous(db)
    _pin(monkeypatch, bad.sha256)
    assert load.main() == 1
    assert "manifest count 7" in caplog.text
    assert db.meta == previous


# --- the pin itself --------------------------------------------------------------------------


@pytest.mark.usefixtures("no_model")
def test_a_pinned_version_with_an_empty_checksum_returns_1(
    db: FakeDb, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    previous = _previous(db)
    _pin(monkeypatch, "")
    assert load.main() == 1
    assert "TICKETSCOPE_EMBEDDINGS_SHA256 is empty" in caplog.text
    assert db.meta == previous and db.replace_calls == 0


@pytest.mark.usefixtures("no_model")
def test_a_checksum_without_a_version_returns_1(
    db: FakeDb, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("TICKETSCOPE_EMBEDDING_MODEL_ID", MODEL)
    monkeypatch.setenv("TICKETSCOPE_EMBEDDINGS_SHA256", "ab" * 32)
    assert load.main() == 1
    assert "TICKETSCOPE_EMBEDDINGS_ASSET_VERSION is empty" in caplog.text


@pytest.mark.usefixtures("no_model")
def test_an_asset_built_from_another_snapshot_than_the_pin_returns_1(
    db: FakeDb, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _pin(monkeypatch, "ab" * 32, embeddings_asset_version="2026.10.1")
    assert load.main() == 1
    assert "another snapshot" in caplog.text


@pytest.mark.usefixtures("no_model")
def test_a_pinned_asset_without_a_model_id_returns_1(
    db: FakeDb, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _pin(monkeypatch, "ab" * 32, embedding_model_id="")
    assert load.main() == 1
    assert "TICKETSCOPE_EMBEDDING_MODEL_ID is empty" in caplog.text


def test_no_pin_keeps_the_keyword_only_path(db: FakeDb) -> None:
    assert load.main() == 0
    assert db.meta == CorpusMeta("fixture", None, derive.preprocessing_version())
    assert db.embeddings is None
