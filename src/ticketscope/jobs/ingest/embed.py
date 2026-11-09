"""Builds the embedding asset of a published snapshot, on a person's machine (AD-6, AD-17).

    uv run python -m ticketscope.jobs.ingest.embed tag --version 2026.11.1 --model-id M
    uv run python -m ticketscope.jobs.ingest.embed build --snapshot out/2026.11.1.jsonl.gz \
        --sha256 <snapshot sha> --version 2026.11.1 --model-id M --out-dir out

`build` embeds from the checksum-verified published snapshot only (never the raw dump, which
holds unmasked text). It writes `<tag>.jsonl.gz` and `<tag>.jsonl.gz.sha256` into `--out-dir`,
and `<tag>.manifest.json` beside them for the Release notes (not published: the manifest is
also line 1 of the asset). Texts come from core's `embedding_text`, the same function `load`
uses when it computes, so the asset and a computed corpus cannot differ in preprocessing.
"""

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any

from ticketscope.adapters.embedder import FastEmbedEmbedder, model_file_sha256
from ticketscope.adapters.embedding_asset import AssetManifest, write_asset
from ticketscope.adapters.release import (
    ChecksumMismatch,
    embeddings_asset_name,
    embeddings_tag,
    sha256_file,
)
from ticketscope.core.derive import preprocessing_version
from ticketscope.core.ports import Embedder
from ticketscope.jobs.load.main import EmbeddingStats, embedding_rows, read_snapshot

RUNTIME_PACKAGES = ("fastembed", "onnxruntime")


def asset_key(version: str, model_id: str) -> tuple[str, str]:
    """The Release tag and file name for a snapshot version and model, with the
    preprocessing version core currently writes (the one source of the key)."""
    pre = preprocessing_version(embeddings=True)
    return embeddings_tag(version, model_id, pre), embeddings_asset_name(version, model_id, pre)


def runtime_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for package in RUNTIME_PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "unknown"
    return versions


def build_asset(
    snapshot: Path,
    snapshot_sha256: str,
    version: str,
    embedder: Embedder,
    model_sha256: str,
    out_dir: Path,
) -> tuple[AssetManifest, Path, float]:
    """Write the asset for `snapshot` into `out_dir`: (manifest, asset path, embed seconds).

    Raises `ChecksumMismatch` before any embedding when the snapshot is not the pinned one,
    and `ValueError` (deleting the partial file) when the written count differs from the
    snapshot's."""
    actual = sha256_file(snapshot)
    if actual != snapshot_sha256.strip().lower():
        raise ChecksumMismatch(snapshot, snapshot_sha256, actual)
    count = sum(1 for _ in read_snapshot(snapshot))
    dimension = len(embedder.embed(["dimension probe"])[0])
    pre = preprocessing_version(embeddings=True)
    manifest = AssetManifest(
        snapshot=version,
        model_id=embedder.model_id,
        model_sha256=model_sha256,
        preprocessing_version=pre,
        runtime=runtime_versions(),
        dimension=dimension,
        count=count,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / embeddings_asset_name(version, embedder.model_id, pre)
    if path.exists():
        raise FileExistsError(f"{path} already exists; not overwriting")
    stats = EmbeddingStats()
    rows = ((r.issue_number, r.model_id, r.vector) for r in embedding_rows(
        read_snapshot(snapshot), embedder, stats
    ))  # fmt: skip
    try:
        written = write_asset(path, manifest, rows)
        if written != count:
            raise ValueError(f"wrote {written} vectors for {count} issues")
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return manifest, path, stats.seconds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a snapshot's embedding asset.")
    sub = parser.add_subparsers(dest="command", required=True)
    tag = sub.add_parser("tag", help="print the Release tag and asset name")
    build = sub.add_parser("build", help="embed a verified snapshot into an asset")
    for p in (tag, build):
        p.add_argument("--version", required=True, help="snapshot version")
        p.add_argument("--model-id", required=True)
    build.add_argument("--snapshot", type=Path, required=True)
    build.add_argument("--sha256", required=True, help="the snapshot's pinned SHA-256")
    build.add_argument("--out-dir", type=Path, required=True)
    build.add_argument("--cache-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    release_tag, asset = asset_key(args.version, args.model_id)
    if args.command == "tag":
        print(release_tag)
        print(asset)
        return 0

    embedder = FastEmbedEmbedder(args.model_id, args.cache_dir)
    try:
        model_sha = model_file_sha256(args.model_id, args.cache_dir)
        manifest, path, seconds = build_asset(
            args.snapshot, args.sha256, args.version, embedder, model_sha, args.out_dir
        )
    except (ValueError, OSError) as exc:
        print(f"embed: {exc}", file=sys.stderr)
        return 1
    digest = sha256_file(path)
    (args.out_dir / f"{path.name}.sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    report: dict[str, Any] = {
        **manifest.model_dump(),
        "tag": release_tag,
        "asset": path.name,
        "sha256": digest,
        "embed_seconds": round(seconds, 1),
    }
    (args.out_dir / f"{release_tag}.manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(f"embed: wrote {path} ({manifest.count} vectors, {seconds:.0f} s in the model)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
