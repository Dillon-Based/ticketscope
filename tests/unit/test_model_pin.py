"""The embedding model is pinned by commit and file digest (story 5.13, DW-6)."""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.target import REPO

SCRIPT = REPO / "images" / "fetch_model.py"
DOCKERFILE = REPO / "images" / "app.Dockerfile"


def _run(snapshot: Path, sha: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "r" * 40,
            sha,
            str(snapshot / "out"),
            "--snapshot-dir",
            str(snapshot),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.criterion("ticketscope--e5-s13--AC-1")
def test_a_wrong_digest_fails_naming_both_digests(tmp_path: Path) -> None:
    (tmp_path / "model_optimized.onnx").write_bytes(b"tiny model")
    actual = hashlib.sha256(b"tiny model").hexdigest()
    expected = "0" * 64
    result = _run(tmp_path, expected)
    assert result.returncode != 0
    assert expected in result.stderr and actual in result.stderr
    assert not (tmp_path / "out").exists()


@pytest.mark.criterion("ticketscope--e5-s13--AC-1")
def test_a_matching_digest_passes(tmp_path: Path) -> None:
    (tmp_path / "model_optimized.onnx").write_bytes(b"tiny model")
    assert _run(tmp_path, hashlib.sha256(b"tiny model").hexdigest()).returncode == 0


@pytest.mark.criterion("ticketscope--e5-s13--AC-1")
def test_a_missing_model_file_fails(tmp_path: Path) -> None:
    result = _run(tmp_path, "0" * 64)
    assert result.returncode != 0
    assert "model_optimized.onnx" in result.stderr


@pytest.mark.criterion("ticketscope--e5-s13--AC-2")
def test_the_dockerfile_pins_a_revision_and_a_digest() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8")
    revision = re.search(r"^ARG EMBEDDING_MODEL_REVISION=([0-9a-f]+)$", text, re.MULTILINE)
    sha = re.search(r"^ARG EMBEDDING_MODEL_SHA256=([0-9a-f]+)$", text, re.MULTILINE)
    assert revision and len(revision.group(1)) == 40
    assert sha and len(sha.group(1)) == 64


_HF_READ = re.compile(r"huggingface_hub|hf_hub_download|huggingface\.co")


@pytest.mark.criterion("ticketscope--e5-s13--AC-2")
def test_fetch_model_is_the_only_place_that_reads_hugging_face() -> None:
    assert _HF_READ.search(SCRIPT.read_text(encoding="utf-8"))
    assert not _HF_READ.search(DOCKERFILE.read_text(encoding="utf-8"))
    # fastembed downloads on construction, unpinned: only the script may build one in the image.
    assert "TextEmbedding(" not in DOCKERFILE.read_text(encoding="utf-8")
    for root in ("src", "deploy"):
        for path in (REPO / root).rglob("*"):
            if path.is_file() and path.suffix in {".py", ".yaml", ".sh", ".tpl"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert not _HF_READ.search(text), path.relative_to(REPO)
