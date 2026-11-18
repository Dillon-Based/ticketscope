"""The env-down leftover check (story 5.4, R3), driven on recorded `get-resources` output: no AWS.

`down.json` (after a teardown) is the clean oracle; `up.json` (an environment that is up) is the
positive control. Each kind of leftover is injected into `down.json` and must fail and be named."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.target import REPO

CHECK = REPO / "scripts" / "leftover_check.py"
WRAPPER = REPO / "scripts" / "leftover-check.sh"
FIXTURES = REPO / "tests" / "fixtures" / "aws"
ACCOUNT = "000000000000"

ENV_TAGS = [{"Key": "environment", "Value": "eks"}]
CLUSTER_TAGS = [{"Key": "elbv2.k8s.aws/cluster", "Value": "ticketscope-env"}]
ARNS = {
    "alb": f"arn:aws:elasticloadbalancing:us-east-1:{ACCOUNT}:loadbalancer/app/k8s-x/abc",
    "target group": f"arn:aws:elasticloadbalancing:us-east-1:{ACCOUNT}:targetgroup/k8s-x/abc",
    "volume": f"arn:aws:ec2:us-east-1:{ACCOUNT}:volume/vol-0123",
    "security group": f"arn:aws:ec2:us-east-1:{ACCOUNT}:security-group/sg-0123",
    "kms key": f"arn:aws:kms:us-east-1:{ACCOUNT}:key/11111111-2222-3333-4444-555555555555",
    "log group": f"arn:aws:logs:us-east-1:{ACCOUNT}:log-group:/aws/eks/ticketscope-env/cluster",
}


def _run(*args: str, files: list[Path] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK), *args, *[str(f) for f in files or []]],
        capture_output=True,
        text=True,
        check=False,
    )


def _write(tmp_path: Path, doc: Any, name: str = "listing.json") -> Path:
    path = tmp_path / name
    path.write_text(doc if isinstance(doc, str) else json.dumps(doc), encoding="utf-8")
    return path


def _tagging(*rows: tuple[str, list[dict[str, str]]]) -> dict[str, Any]:
    return {"ResourceTagMappingList": [{"ResourceARN": arn, "Tags": tags} for arn, tags in rows]}


@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_the_recording_taken_after_a_teardown_is_clean() -> None:
    result = _run(files=[FIXTURES / "down.json"])
    assert result.returncode == 0, result.stderr
    assert "clean" in result.stdout


@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
@pytest.mark.parametrize("kind", sorted(ARNS))
def test_each_kind_of_tagged_leftover_fails_and_is_named(kind: str, tmp_path: Path) -> None:
    listing = _write(tmp_path, _tagging((ARNS[kind], ENV_TAGS)))
    result = _run(files=[FIXTURES / "down.json", listing])
    assert result.returncode == 1
    assert ARNS[kind] in result.stdout


@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_a_tagged_network_interface_fails_and_is_named(tmp_path: Path) -> None:
    listing = _write(
        tmp_path,
        {"NetworkInterfaces": [{"NetworkInterfaceId": "eni-0abc", "TagSet": ENV_TAGS}]},
    )
    result = _run(files=[FIXTURES / "down.json", listing])
    assert result.returncode == 1
    assert "eni-0abc" in result.stdout and "network-interface" in result.stdout


def test_the_controllers_cluster_tag_alone_counts(tmp_path: Path) -> None:
    listing = _write(tmp_path, _tagging((ARNS["alb"], CLUSTER_TAGS)))
    result = _run(files=[listing])
    assert result.returncode == 1 and ARNS["alb"] in result.stdout


def test_the_recording_of_an_environment_that_is_up_lists_its_resources() -> None:
    result = _run("--list", files=[FIXTURES / "up.json"])
    assert result.returncode == 0
    for kind in ("loadbalancer", "targetgroup", "security-group", "volume"):
        assert f":{kind} " in result.stdout, kind
    # The same recording fails the check.
    assert _run(files=[FIXTURES / "up.json"]).returncode == 1


def test_foreign_and_bootstrap_resources_are_ignored(tmp_path: Path) -> None:
    listing = _write(
        tmp_path,
        _tagging(
            (ARNS["alb"], [{"Key": "environment", "Value": "someone-else"}]),
            (
                ARNS["volume"],
                [{"Key": "environment", "Value": "eks"}, {"Key": "stack", "Value": "bootstrap"}],
            ),
            (ARNS["kms key"], [{"Key": "stack", "Value": "bootstrap"}]),
            (ARNS["log group"], []),
        ),
    )
    result = _run(files=[listing])
    assert result.returncode == 0, result.stdout


@pytest.mark.criterion("ticketscope--e5-s4--AC-2")
@pytest.mark.parametrize(
    "content",
    [
        "",
        "not json",
        "[]",
        "{}",
        '{"ResourceTagMappingList": null}',
        '{"ResourceTagMappingList": [{}]}',
    ],
)
def test_an_unreadable_or_incomplete_listing_fails(content: str, tmp_path: Path) -> None:
    result = _run(files=[_write(tmp_path, content)])
    assert result.returncode != 0
    assert "clean" not in result.stdout


def test_a_missing_file_and_no_file_at_all_fail(tmp_path: Path) -> None:
    assert _run(files=[tmp_path / "absent.json"]).returncode != 0
    assert _run().returncode != 0


def test_list_still_fails_on_a_listing_it_cannot_read(tmp_path: Path) -> None:
    assert _run("--list", files=[_write(tmp_path, "oops")]).returncode != 0


@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_dry_run_injects_a_tagged_alb_and_fails_naming_it() -> None:
    result = _run("--dry-run")
    assert result.returncode == 1
    assert "loadbalancer" in result.stdout and "dry-run" in result.stdout


pytestmark_bash = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")


@pytestmark_bash
def test_the_wrapper_dry_run_needs_no_aws_and_fails() -> None:
    result = subprocess.run(
        [str(WRAPPER), "--dry-run"], capture_output=True, text=True, check=False
    )
    assert result.returncode == 1 and "dry-run" in result.stdout


@pytestmark_bash
@pytest.mark.criterion("ticketscope--e5-s4--AC-2")
def test_the_wrapper_fails_when_the_api_is_unreachable(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "aws"
    stub.write_text("#!/usr/bin/env bash\necho 'Could not connect' >&2\nexit 255\n")
    stub.chmod(0o755)
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin"}
    result = subprocess.run([str(WRAPPER)], capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 2 and "FAIL" in result.stderr
    assert "clean" not in result.stdout


@pytestmark_bash
def test_the_wrapper_fails_when_aws_prints_nothing(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "aws"
    stub.write_text("#!/usr/bin/env bash\nexit 0\n")
    stub.chmod(0o755)
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin"}
    result = subprocess.run([str(WRAPPER)], capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 2 and "clean" not in result.stdout


@pytestmark_bash
def test_the_wrapper_reads_clean_listings_and_filters_on_the_environment_tag(
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "aws.log"
    stub = bin_dir / "aws"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> "{log}"\n'
        'if [[ "$1" == ec2 ]]; then echo \'{"NetworkInterfaces": []}\'; '
        "else echo '{\"ResourceTagMappingList\": []}'; fi\n"
    )
    stub.chmod(0o755)
    env = {"PATH": f"{bin_dir}:/usr/bin:/bin"}
    result = subprocess.run([str(WRAPPER)], capture_output=True, text=True, check=False, env=env)
    assert result.returncode == 0, result.stderr
    calls = log.read_text()
    assert "Key=environment,Values=eks" in calls and "Key=elbv2.k8s.aws/cluster" in calls
    assert "describe-network-interfaces" in calls
    assert "bootstrap" not in calls


def test_the_check_has_no_destructive_verb() -> None:
    for path in (CHECK, WRAPPER):
        text = path.read_text(encoding="utf-8").lower()
        assert "delete" not in text and "terminate" not in text and "destroy" not in text, path
