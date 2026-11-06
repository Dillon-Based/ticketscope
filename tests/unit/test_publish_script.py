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
