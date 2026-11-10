"""The embedding asset (story 4): its content, its Release name and pin, its fetch, its
builder and its notes."""

import gzip
import hashlib
import json
import re
from pathlib import Path

import httpx2
import pytest

from tests.target import CHART_VALUES, embeddings_pin
from ticketscope.adapters.embedding_asset import (
    AssetManifest,
    AssetRecord,
    read_manifest,
    read_records,
    write_asset,
)
from ticketscope.adapters.release import (
    ChecksumMismatch,
    embeddings_asset_name,
    embeddings_asset_url,
    embeddings_tag,
    fetch_embeddings,
    read_embeddings_pin,
    sha256_file,
)
from ticketscope.core import derive
from ticketscope.core.fakes import HashEmbedder
from ticketscope.jobs.ingest import embed, notes
from ticketscope.jobs.load.main import read_snapshot

MODEL = "BAAI/bge-small-en-v1.5"
PRE = derive.preprocessing_version(embeddings=True)
MANIFEST = AssetManifest(
    snapshot="2026.11.1",
    model_id=MODEL,
    model_sha256="ab" * 32,
    preprocessing_version=PRE,
    runtime={"fastembed": "0.9.1", "onnxruntime": "1.2.3"},
    dimension=3,
    count=2,
)


def test_the_tag_carries_snapshot_model_and_preprocessing() -> None:
    assert embeddings_tag("2026.11.1", MODEL, PRE) == (
        "embeddings-2026.11.1-BAAI_bge-small-en-v1.5-pre1.kind2-t3.outcome3.emb1"
    )
    assert embeddings_asset_name("2026.11.1", MODEL, PRE).endswith(".jsonl.gz")
    assert embeddings_asset_url("https://x.invalid/dl/", "2026.11.1", MODEL, PRE) == (
        "https://x.invalid/dl/embeddings-2026.11.1-BAAI_bge-small-en-v1.5-pre1.kind2-t3.outcome3"
        ".emb1/embeddings-2026.11.1-BAAI_bge-small-en-v1.5-pre1.kind2-t3.outcome3.emb1.jsonl.gz"
    )


def test_the_name_changes_with_each_part_of_the_key() -> None:
    base = embeddings_tag("2026.11.1", MODEL, PRE)
    assert embeddings_tag("2026.11.2", MODEL, PRE) != base
    assert embeddings_tag("2026.11.1", "other/model", PRE) != base
    assert embeddings_tag("2026.11.1", MODEL, "pre2.x.emb1") != base


def test_the_builder_names_the_asset_from_core_s_preprocessing_version() -> None:
    tag, name = embed.asset_key("2026.11.1", MODEL)
    assert tag == embeddings_tag("2026.11.1", MODEL, derive.preprocessing_version(embeddings=True))
    assert name == f"{tag}.jsonl.gz"


# --- content: only issue number, model id and vector, plus a manifest --------------------------


def test_the_asset_round_trips_the_manifest_and_records(tmp_path: Path) -> None:
    path = tmp_path / "a.jsonl.gz"
    rows = [(7, MODEL, [0.5, -0.25, 1.0]), (9, MODEL, [0.0, 0.1, 0.2])]
    assert write_asset(path, MANIFEST, rows) == 2
    assert read_manifest(path) == MANIFEST
    records = list(read_records(path))
    assert [(r.issue, r.model) for r in records] == [(7, MODEL), (9, MODEL)]
    assert records[0].vector == [0.5, -0.25, 1.0]


def test_float32_values_round_trip_exactly(tmp_path: Path) -> None:
    import struct

    value = struct.unpack("f", struct.pack("f", 0.1234567))[0]
    path = tmp_path / "a.jsonl.gz"
    write_asset(path, MANIFEST, [(1, MODEL, [value])])
    [record] = read_records(path)
    assert struct.unpack("f", struct.pack("f", record.vector[0]))[0] == value


def test_every_record_holds_only_issue_model_and_vector(tmp_path: Path) -> None:
    path = tmp_path / "a.jsonl.gz"
    write_asset(path, MANIFEST, [(7, MODEL, [0.5, 0.5, 0.5])])
    with gzip.open(path, "rt", encoding="utf-8") as f:
        manifest_line, *record_lines = f.read().splitlines()
    assert set(json.loads(manifest_line)) == set(AssetManifest.model_fields)
    for line in record_lines:
        assert set(json.loads(line)) == {"issue", "model", "vector"}


def test_a_record_with_a_text_field_is_refused() -> None:
    with pytest.raises(ValueError, match="title"):
        AssetRecord.parse('{"issue":1,"model":"m","vector":[1.0],"title":"leak"}')


def test_a_built_asset_carries_no_text_or_identifier(tmp_path: Path, snapshot_dir: Path) -> None:
    sha = hashlib.sha256((snapshot_dir / "fixture.jsonl.gz").read_bytes()).hexdigest()
    _manifest, path, _s = embed.build_asset(
        snapshot_dir / "fixture.jsonl.gz", sha, "fixture", HashEmbedder("m"), "cd" * 32, tmp_path
    )
    with gzip.open(path, "rt", encoding="utf-8") as f:
        text = f.read()
    for issue in read_snapshot(snapshot_dir / "fixture.jsonl.gz"):
        assert issue.title not in text
        assert issue.url not in text
    assert not re.search(r"\[~|@|\[email masked\]|\[secret masked\]|https?://", text)


def test_the_manifest_mismatch_names_each_difference() -> None:
    assert (
        MANIFEST.mismatch(snapshot="2026.11.1", model_id=MODEL, preprocessing_version=PRE) is None
    )
    wrong = MANIFEST.mismatch(snapshot="2026.12.1", model_id="x", preprocessing_version=PRE)
    assert wrong is not None and "snapshot" in wrong and "model_id" in wrong


# --- the builder -----------------------------------------------------------------------------


def test_the_builder_refuses_a_snapshot_with_another_checksum_before_embedding(
    tmp_path: Path, snapshot_dir: Path
) -> None:
    embedder = HashEmbedder("m")
    out = tmp_path / "out"
    with pytest.raises(ChecksumMismatch):
        embed.build_asset(
            snapshot_dir / "fixture.jsonl.gz", "0" * 64, "fixture", embedder, "ab" * 32, out
        )
    assert embedder.calls == [] and not out.exists()


def test_the_builder_never_overwrites_an_asset(tmp_path: Path, snapshot_dir: Path) -> None:
    sha = sha256_file(snapshot_dir / "fixture.jsonl.gz")
    args = (snapshot_dir / "fixture.jsonl.gz", sha, "fixture", HashEmbedder("m"), "ab" * 32)
    embed.build_asset(*args, tmp_path)
    with pytest.raises(FileExistsError):
        embed.build_asset(*args, tmp_path)


def test_the_builder_records_dimension_count_and_runtime(
    tmp_path: Path, snapshot_dir: Path
) -> None:
    sha = sha256_file(snapshot_dir / "fixture.jsonl.gz")
    manifest, path, _s = embed.build_asset(
        snapshot_dir / "fixture.jsonl.gz",
        sha,
        "fixture",
        HashEmbedder("m", dim=16),
        "ab" * 32,
        tmp_path,
    )
    assert (manifest.dimension, manifest.count, manifest.snapshot) == (16, 8, "fixture")
    assert manifest.preprocessing_version == PRE and manifest.model_sha256 == "ab" * 32
    assert set(manifest.runtime) == set(embed.RUNTIME_PACKAGES)
    assert read_manifest(path) == manifest


def test_the_tag_command_prints_tag_and_asset(capsys: pytest.CaptureFixture[str]) -> None:
    assert embed.main(["tag", "--version", "2026.11.1", "--model-id", MODEL]) == 0
    tag, asset = capsys.readouterr().out.split()
    assert tag == embeddings_tag("2026.11.1", MODEL, PRE) and asset == f"{tag}.jsonl.gz"


# --- fetch -----------------------------------------------------------------------------------

BASE = "https://example.invalid/download"
BODY = b"\x1f\x8b pretend gzip" * 100
SHA = hashlib.sha256(BODY).hexdigest()


def test_fetch_downloads_the_named_asset_and_verifies_it(tmp_path: Path) -> None:
    seen: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(str(request.url))
        return httpx2.Response(200, content=BODY)

    path = fetch_embeddings(
        BASE, "2026.11.1", MODEL, PRE, tmp_path, SHA, timeout=5,
        transport=httpx2.MockTransport(handler),
    )  # fmt: skip
    assert seen == [embeddings_asset_url(BASE, "2026.11.1", MODEL, PRE)]
    assert path.name == embeddings_asset_name("2026.11.1", MODEL, PRE) and path.read_bytes() == BODY


def test_fetch_with_a_wrong_checksum_deletes_the_download(tmp_path: Path) -> None:
    transport = httpx2.MockTransport(lambda r: httpx2.Response(200, content=b"tampered"))
    with pytest.raises(ChecksumMismatch):
        fetch_embeddings(
            BASE, "2026.11.1", MODEL, PRE, tmp_path, SHA, timeout=5, transport=transport
        )
    assert list(tmp_path.iterdir()) == []


def test_fetch_with_an_empty_pin_is_refused_before_any_request(tmp_path: Path) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise AssertionError("requested with no pin")

    with pytest.raises(ValueError, match="TICKETSCOPE_EMBEDDINGS_SHA256"):
        fetch_embeddings(
            BASE, "2026.11.1", MODEL, PRE, tmp_path, " ", timeout=5,
            transport=httpx2.MockTransport(handler),
        )  # fmt: skip


# --- the pin reader and the pin in values.yaml ------------------------------------------------


def test_the_pin_reader_reads_the_values_file() -> None:
    pin = read_embeddings_pin(CHART_VALUES)
    assert set(pin) == {"modelId", "assetVersion", "sha256"}
    assert pin == embeddings_pin()


def test_the_pin_reader_reads_set_values(tmp_path: Path) -> None:
    values = tmp_path / "values.yaml"
    values.write_text(
        'snapshot:\n  version: "1"\nembeddings:\n  computeOnKind: false\n  # note\n'
        '  modelId: "a/b"\n  assetVersion: "2026.11.1"\n  sha256: "abc"\n\napi:\n  x: 1\n',
        encoding="utf-8",
    )
    assert read_embeddings_pin(values) == {
        "modelId": "a/b",
        "assetVersion": "2026.11.1",
        "sha256": "abc",
    }


def test_the_pin_reader_refuses_a_block_without_the_asset_keys(tmp_path: Path) -> None:
    values = tmp_path / "values.yaml"
    values.write_text('embeddings:\n  modelId: "a/b"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="assetVersion"):
        read_embeddings_pin(values)


def test_the_pinned_model_is_the_findings_decision_and_the_dockerfile_s() -> None:
    pin = embeddings_pin()
    assert pin["modelId"] == MODEL
    dockerfile = (CHART_VALUES.parents[3] / "images" / "app.Dockerfile").read_text("utf-8")
    assert f"ARG EMBEDDING_MODEL_ID={pin['modelId']}" in dockerfile


def test_a_pinned_asset_is_whole_and_matches_the_snapshot_pin() -> None:
    from tests.target import snapshot_pin

    pin = embeddings_pin()
    if not pin["assetVersion"] and not pin["sha256"]:
        pytest.skip("no embeddings pin merged yet (the person-run publish step)")
    assert re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]), "a pinned asset needs its SHA-256"
    assert pin["assetVersion"] == snapshot_pin()["version"]


def test_no_environment_file_overrides_the_embeddings_pin() -> None:
    for env_file in CHART_VALUES.parent.glob("values-*.yaml"):
        text = env_file.read_text(encoding="utf-8")
        assert "assetVersion" not in text, env_file.name
        assert not re.search(r"^embeddings:\n(?:[ #].*\n)*?  sha256:", text, re.MULTILINE)


# --- notes -----------------------------------------------------------------------------------

REPORT = {
    **MANIFEST.model_dump(),
    "tag": embeddings_tag("2026.11.1", MODEL, PRE),
    "asset": embeddings_asset_name("2026.11.1", MODEL, PRE),
    "sha256": "ef" * 32,
    "embed_seconds": 1146.2,
}


def test_notes_carry_commit_counts_checksum_timed_load_and_attribution() -> None:
    text = notes.render_embedding_notes(REPORT, 95.5, "abc1234")
    assert "`abc1234`" in text and notes.ATTRIBUTION in text
    assert "Vectors: 2, 3 dimensions each" in text
    assert "ef" * 32 in text and "ab" * 32 in text
    assert "95.5 s (budget 600 s)" in text and "asset download" in text
    assert "fastembed 0.9.1" in text and PRE in text


def test_notes_pass_the_mask_sweep() -> None:
    text = notes.render_embedding_notes(REPORT, 1.0, "abc1234")
    assert not re.search(r"\[~|[\w.]+@[\w.]+\.\w+|(?i:token|secret)\s*[:=]", text)


def test_notes_refuse_a_load_over_the_budget() -> None:
    with pytest.raises(ValueError, match="over the 600 s budget"):
        notes.render_embedding_notes(REPORT, 600.1, "abc1234")


def test_the_notes_cli_needs_exactly_one_input(tmp_path: Path) -> None:
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps(REPORT), encoding="utf-8")
    assert (
        notes.main(["--load-seconds", "1", "--commit", "c", "--embeddings-manifest", str(manifest)])
        == 0
    )
    with pytest.raises(SystemExit):
        notes.main(["--load-seconds", "1", "--commit", "c"])
