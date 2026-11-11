"""The chart's snapshot pin (story 5, AD-25): the load Job carries the pinned version,
checksum and base URL, refuses to render without a checksum, and the kind values file
does not override the pin."""

import shutil
import subprocess

import pytest

from tests.target import REPO, snapshot_pin

CHART = REPO / "deploy" / "charts" / "ticketscope"
# Backups need an environment's destinationPath (story 8); the pin does not care.
_IMAGE_TAGS = [
    "--set-string",
    "image.app.tag=t",
    "--set-string",
    "image.postgres.tag=18-t",
    "--set",
    "backup.enabled=false",
    # mcp refuses to render without a host (story 4.1).
    "--set",
    "hostname=ticketscope.test",
]

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")


def _template(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["helm", "template", "t", str(CHART), *_IMAGE_TAGS, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _load_job(rendered: str) -> str:
    [doc] = [d for d in rendered.split("\n---\n") if "name: ticketscope-load\n" in d]
    return doc


def _env(job: str, name: str) -> str:
    lines = job.splitlines()
    i = next(n for n, line in enumerate(lines) if line.strip() == f"- name: {name}")
    return lines[i + 1].split("value:", 1)[1].strip().strip('"')


@pytest.mark.parametrize("values", [[], ["-f", str(CHART / "values-kind.yaml")]])
def test_load_job_env_carries_the_values_pin(values: list[str]) -> None:
    result = _template(*values)
    assert result.returncode == 0, result.stderr
    job = _load_job(result.stdout)
    pin = snapshot_pin()
    assert _env(job, "TICKETSCOPE_SNAPSHOT_VERSION") == pin["version"]
    assert _env(job, "TICKETSCOPE_SNAPSHOT_SHA256") == pin["sha256"]
    assert _env(job, "TICKETSCOPE_SNAPSHOT_BASE_URL") == pin["baseUrl"]
    assert _env(job, "TICKETSCOPE_SNAPSHOT_DIR") == "/snapshots"


def test_load_job_mounts_a_writable_snapshots_volume() -> None:
    job = _load_job(_template().stdout)
    assert "mountPath: /snapshots" in job
    assert "emptyDir" in job


def test_empty_checksum_fails_to_render() -> None:
    result = _template("--set-string", "snapshot.sha256=")
    assert result.returncode != 0
    assert "snapshot.sha256 is required" in result.stderr


def test_pin_is_a_full_sha256() -> None:
    sha = snapshot_pin()["sha256"]
    assert len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)
