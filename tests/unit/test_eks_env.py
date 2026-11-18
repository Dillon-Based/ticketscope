"""scripts/eks-env.sh prints the exports the hand-run EKS steps need, from a fake `aws`, and
prints nothing on stdout when it fails (so `eval` of it does nothing)."""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO

SCRIPT = REPO / "scripts" / "eks-env.sh"
HOST = "ticketscope.example.test"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")

# A fake aws that answers the three queries by their subcommand; SIGNED_OUT makes sts fail.
FAKE_AWS = """#!/usr/bin/env bash
case "$*" in
  *"sts get-caller-identity"*) [ -n "$SIGNED_OUT" ] && exit 255; echo 000000000000 ;;
  *"acm list-certificates"*) echo "arn:aws:acm:us-east-1:000000000000:certificate/abc" ;;
  *"route53 list-hosted-zones-by-name"*) echo "/hostedzone/ZTESTZONE" ;;
  *"route53 list-hosted-zones"*) echo "$ZONES" ;;
  *) exit 1 ;;
esac
"""


def _run(
    tmp_path: Path, *, host: str | None = HOST, **env: str
) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    aws = bin_dir / "aws"
    aws.write_text(FAKE_AWS, encoding="utf-8")
    aws.chmod(aws.stat().st_mode | stat.S_IEXEC)
    full_env = {
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "SIGNED_OUT": "",
        "ZONES": f"{HOST}.",
        # Never the repo's own tfvars: the fake values must not land beside real ones.
        "TICKETSCOPE_TFVARS": str(tmp_path / "terraform.tfvars"),
        **env,
    }
    return subprocess.run(
        ["bash", str(SCRIPT), *([host] if host else [])],
        capture_output=True,
        text=True,
        env=full_env,
        check=False,
    )


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
def test_it_prints_the_exports_and_a_cd_to_the_repo(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    for expected in (
        "export AWS_PROFILE=ticketscope-sso",
        "export REG=000000000000.dkr.ecr.us-east-1.amazonaws.com",
        "export TICKETSCOPE_ZONE_ID=ZTESTZONE",
        f"export TICKETSCOPE_HOSTNAME={HOST}",
    ):
        assert expected in lines
    assert any(line.startswith("export CERT=arn:aws:acm:") for line in lines)
    assert lines[-1].startswith("cd ") and str(REPO) in lines[-1]


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
def test_it_prints_nothing_on_stdout_when_not_signed_in(tmp_path: Path) -> None:
    result = _run(tmp_path, SIGNED_OUT="1")
    assert result.returncode != 0
    assert result.stdout == ""
    assert "aws-login.sh" in result.stderr


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
def test_it_finds_the_hostname_from_the_one_ticketscope_zone(tmp_path: Path) -> None:
    result = _run(tmp_path, host=None)
    assert result.returncode == 0, result.stderr
    assert f"export TICKETSCOPE_HOSTNAME={HOST}" in result.stdout.splitlines()


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
@pytest.mark.parametrize("zones", ["", f"{HOST}.\tticketscope.other.test."])
def test_it_needs_exactly_one_zone_when_given_no_hostname(tmp_path: Path, zones: str) -> None:
    result = _run(tmp_path, host=None, ZONES=zones)
    assert result.returncode != 0 and result.stdout == ""
    assert "exactly one" in result.stderr
