"""Fetch the pinned embedding model into a cache directory, for the `model` build stage.

This is the only place that reads Hugging Face (AD-21). It downloads
`Qdrant/bge-small-en-v1.5-onnx-Q` at one commit, fails unless the ONNX file's SHA-256 matches
the pin, points `refs/main` at that commit so fastembed's offline load reads the pinned
snapshot, and then loads the model once with the network disabled.

    python fetch_model.py REVISION SHA256 CACHE_DIR [--model-id BAAI/bge-small-en-v1.5]
        [--snapshot-dir DIR]   # tests: verify an existing snapshot, skip the download

Nothing is written to CACHE_DIR unless the digest matches.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HF_REPO = "Qdrant/bge-small-en-v1.5-onnx-Q"
MODEL_FILE = "model_optimized.onnx"


class ModelPinError(Exception):
    """The fetched model is not the pinned one."""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def verify_snapshot(snapshot: Path, expected_sha256: str) -> Path:
    """The ONNX file under `snapshot`, after checking its digest."""
    model = snapshot / MODEL_FILE
    if not model.is_file():
        raise ModelPinError(f"{MODEL_FILE} is missing from {snapshot}")
    actual = file_sha256(model)
    if actual != expected_sha256:
        raise ModelPinError(
            f"{MODEL_FILE} sha256 mismatch: expected {expected_sha256}, actual {actual}"
        )
    return model


def _download(revision: str, stage: Path) -> Path:
    from huggingface_hub import snapshot_download  # pyright: ignore[reportMissingTypeStubs]

    return Path(snapshot_download(repo_id=HF_REPO, revision=revision, cache_dir=str(stage)))


_LOAD = (
    "import sys; from fastembed import TextEmbedding; "
    "m = TextEmbedding(model_name=sys.argv[1], cache_dir=sys.argv[2]); "
    "[v] = list(m.embed(['pin check'])); print(len(v))"
)


def _offline_load(model_id: str, cache_dir: Path, revision: str) -> None:
    # A fresh process: huggingface_hub reads HF_HUB_OFFLINE when it is imported, and this one
    # imported it to download. Offline, a lookup that misses fails instead of fetching `main`.
    env = {**os.environ, "HF_HUB_OFFLINE": "1"}
    result = subprocess.run(
        [sys.executable, "-c", _LOAD, model_id, str(cache_dir)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != "384":
        raise ModelPinError(f"the offline load failed: {result.stdout}{result.stderr}")
    snapshots = cache_dir / f"models--{HF_REPO.replace('/', '--')}" / "snapshots"
    found = sorted(p.name for p in snapshots.iterdir())
    if found != [revision]:
        raise ModelPinError(f"the cache holds snapshots {found}, expected only {revision}")


def fetch(revision: str, sha256: str, cache_dir: Path, model_id: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        snapshot = _download(revision, stage)
        verify_snapshot(snapshot, sha256)
        refs = stage / f"models--{HF_REPO.replace('/', '--')}" / "refs"
        refs.mkdir(parents=True, exist_ok=True)
        (refs / "main").write_text(revision, encoding="utf-8")
        _offline_load(model_id, stage, revision)
        cache_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(stage, cache_dir, symlinks=True, dirs_exist_ok=True)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision")
    parser.add_argument("sha256")
    parser.add_argument("cache_dir", type=Path)
    parser.add_argument("--model-id", default="BAAI/bge-small-en-v1.5")
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        if args.snapshot_dir is not None:
            verify_snapshot(args.snapshot_dir, args.sha256)
        else:
            fetch(args.revision, args.sha256, args.cache_dir, args.model_id)
    except ModelPinError as exc:
        print(f"fetch_model: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
