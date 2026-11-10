"""`scripts/publish-snapshot.sh` refuses before ingest unless it runs from a clean
checkout of `main` equal to `origin/main` (story 13, I/O matrix "Not main / dirty")."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO

SCRIPT = REPO / "scripts" / "publish-snapshot.sh"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")

GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, env={**os.environ, **GIT_ENV}
    )


@pytest.fixture
def checkout(tmp_path: Path) -> tuple[Path, Path]:
    """A clone of a one-commit `main`, holding the script, plus a PATH whose `uv`, `gh`
    and `docker` only record that they were called."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-q", "-b", "main")
    (origin / "scripts").mkdir()
    shutil.copy(SCRIPT, origin / "scripts" / "publish-snapshot.sh")
    _git(origin, "add", ".")
    _git(origin, "commit", "-q", "-m", "init")
    work = tmp_path / "work"
    _git(tmp_path, "clone", "-q", str(origin), str(work))

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls"
    for tool in ("uv", "gh", "docker"):
        stub = bin_dir / tool
        stub.write_text(f'#!/usr/bin/env bash\necho {tool} "$@" >> "{calls}"\n')
        stub.chmod(0o755)
    return work, bin_dir


def _run(work: Path, bin_dir: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **GIT_ENV, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    return subprocess.run(
        ["bash", str(work / "scripts" / "publish-snapshot.sh")],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _no_tool_ran(work: Path) -> bool:
    return not (work.parent / "calls").exists()


def test_refuses_off_main(checkout: tuple[Path, Path]) -> None:
    work, bin_dir = checkout
    _git(work, "checkout", "-q", "-b", "feature")
    result = _run(work, bin_dir)
    assert result.returncode != 0
    assert "publish only from main, not feature" in result.stderr
    assert _no_tool_ran(work)


def test_refuses_a_dirty_checkout(checkout: tuple[Path, Path]) -> None:
    work, bin_dir = checkout
    (work / "stray.txt").write_text("x")
    result = _run(work, bin_dir)
    assert result.returncode != 0
    assert "not clean" in result.stderr
    assert _no_tool_ran(work)


def test_refuses_when_head_is_not_origin_main(checkout: tuple[Path, Path]) -> None:
    work, bin_dir = checkout
    _git(work, "commit", "-q", "--allow-empty", "-m", "unpushed")
    result = _run(work, bin_dir)
    assert result.returncode != 0
    assert "HEAD is not origin/main" in result.stderr
    assert _no_tool_ran(work)


def test_clean_main_passes_the_guards(checkout: tuple[Path, Path]) -> None:
    work, bin_dir = checkout
    result = _run(work, bin_dir)
    # The stubs make a later step fail; the guards themselves let the run through.
    assert result.returncode != 0
    assert "publish only from main" not in result.stderr
    assert "not clean" not in result.stderr
    assert "HEAD is not origin/main" not in result.stderr
    assert not _no_tool_ran(work)


def test_script_never_clobbers_or_deletes() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    commands = "\n".join(
        line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
    )
    assert "--clobber" not in commands
    assert "release delete" not in commands
    assert "gh release create" in commands
    assert '--target "$COMMIT"' in commands


# --- the embedding phase (story 4) -------------------------------------------------------------

TAG = "embeddings-2026.11.1-BAAI_bge-small-en-v1.5-pre1.kind2-t3.outcome3.emb1"
UV_STUB = """#!/usr/bin/env bash
echo "uv $*" >> "$STUB_CALLS"
case "$*" in
  *read_embeddings_pin*) echo "BAAI/bge-small-en-v1.5" ;;
  *read_snapshot_pin*) echo "2026.11.1 {sha}" ;;
  *ingest.embed\\ tag*) echo "{tag}"; echo "{tag}.jsonl.gz" ;;
  *ingest.embed\\ build*) echo "built" >&2 ;;
esac
"""
GH_STUB = """#!/usr/bin/env bash
echo "gh $*" >> "$STUB_CALLS"
case "$*" in
  "repo view"*) echo "owner/repo" ;;
  "api"*) echo "refs/tags/{taken}" ;;
  "release list"*) echo "snapshot-2026.11.1" ;;
esac
"""


def _stub_embedding_tools(work: Path, bin_dir: Path, taken: str) -> dict[str, str]:
    calls = work.parent / "embed-calls"
    (bin_dir / "uv").write_text(UV_STUB.format(sha="a" * 64, tag=TAG))
    (bin_dir / "gh").write_text(GH_STUB.format(taken=taken))
    for tool in ("uv", "gh"):
        (bin_dir / tool).chmod(0o755)
    return {"STUB_CALLS": str(calls)}


def _run_embeddings_only(work: Path, bin_dir: Path, extra: dict[str, str]) -> str:
    env = {
        **os.environ,
        **GIT_ENV,
        **extra,
        "OUT_DIR": str(work.parent / "out"),
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
    }
    result = subprocess.run(
        ["bash", str(work / "scripts" / "publish-snapshot.sh"), "--embeddings-only", "2026.11.1"],
        cwd=work, env=env, capture_output=True, text=True, timeout=60,
    )  # fmt: skip
    assert result.returncode != 0
    return result.stderr


def test_a_published_embedding_asset_name_stops_the_run_before_anything_is_uploaded(
    checkout: tuple[Path, Path],
) -> None:
    work, bin_dir = checkout
    env = _stub_embedding_tools(work, bin_dir, taken=TAG)
    stderr = _run_embeddings_only(work, bin_dir, env)
    assert f"tag {TAG} already exists" in stderr
    calls = Path(env["STUB_CALLS"]).read_text()
    assert "release create" not in calls
    assert "ingest.embed build" not in calls  # refused before the long embedding pass


def test_the_embedding_phase_embeds_the_verified_snapshot_and_attaches_with_the_guards(
    checkout: tuple[Path, Path],
) -> None:
    work, bin_dir = checkout
    env = _stub_embedding_tools(work, bin_dir, taken="embeddings-2026.10.1-other")
    stderr = _run_embeddings_only(work, bin_dir, env)  # stops at the stub's missing asset file
    assert "the embedding asset" in stderr and "was not written" in stderr
    calls = Path(env["STUB_CALLS"]).read_text()
    # Embedded from the downloaded published snapshot with its pinned checksum, not from a dump.
    assert "gh release download snapshot-2026.11.1" in calls
    assert f"--sha256 {'a' * 64}" in calls and "--snapshot" in calls
    assert "mongo" not in calls.lower()


def test_embedding_script_text_guards() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    commands = "\n".join(
        line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
    )
    assert commands.count("gh release create") == 2  # the snapshot and the embeddings
    assert commands.count('--target "$COMMIT"') == 2
    assert "--clobber" not in commands and "release delete" not in commands
    assert "embeddings-only" in commands
    # Timed load of the asset, inside the same budget and notes as the snapshot's.
    assert 'EMBEDDINGS_FILE="$asset"' in commands and "--embeddings-manifest" in commands
