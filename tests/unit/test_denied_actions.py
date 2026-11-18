"""scripts/denied-actions.sh turns the AccessDenied messages of a run's logs into the list of
actions to add to the deploy role. The messages below are the shapes the first live `env-up`
runs produced (account ids replaced with a fake one), so the extractor is checked against what
AWS really prints."""

import shutil
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO

SCRIPT = REPO / "scripts" / "denied-actions.sh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")

GET_ROLE = (
    "Error: unable to get role (ticketscope-deploy): operation error IAM: GetRole, https "
    "response error StatusCode: 403, AccessDenied: User: arn:aws:sts::000000000000:assumed-role/"
    "ticketscope-deploy/GitHubActions is not authorized to perform: iam:GetRole on resource: "
    "role ticketscope-deploy because no identity-based policy allows the iam:GetRole action"
)
SSM = (
    "Error: reading SSM Parameter: AccessDeniedException: User: arn:aws:sts::000000000000:"
    "assumed-role/ticketscope-deploy/x is not authorized to perform: ssm:GetParameter on "
    "resource: arn:aws:ssm:us-east-1::parameter/aws/service/eks/optimized-ami/1.36/release "
    "because no identity-based policy allows the ssm:GetParameter action"
)
SLR = (
    "Error: creating EKS Node Group: InvalidRequestException: Failed to validate if SLR: "
    "AWSServiceRoleForAmazonEKSNodegroup already exists due to missing permissions for "
    "'iam:GetRole'"
)


def _run(tmp_path: Path, *logs: str, missing: bool = False) -> subprocess.CompletedProcess[str]:
    paths: list[str] = []
    for i, text in enumerate(logs):
        path = tmp_path / f"log{i}.log"
        path.write_text(text + "\n", encoding="utf-8")
        paths.append(str(path))
    if missing:
        paths.append(str(tmp_path / "never-written.log"))
    return subprocess.run(
        ["bash", str(SCRIPT), *paths], capture_output=True, text=True, check=False
    )


@pytest.mark.criterion("ticketscope--e5-s3--AC-8")
def test_it_lists_each_denied_action_once_with_its_resource(tmp_path: Path) -> None:
    result = _run(tmp_path, GET_ROLE + "\n" + SSM, GET_ROLE)
    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "iam:GetRole on role ticketscope-deploy",
        "ssm:GetParameter on "
        "arn:aws:ssm:us-east-1::parameter/aws/service/eks/optimized-ami/1.36/release",
    ]


@pytest.mark.criterion("ticketscope--e5-s3--AC-8")
def test_it_reads_the_eks_message_that_names_no_resource(tmp_path: Path) -> None:
    result = _run(tmp_path, SLR)
    assert result.stdout.splitlines() == ["iam:GetRole on (resource not reported)"]


@pytest.mark.criterion("ticketscope--e5-s3--AC-8")
def test_it_never_prints_an_account_id(tmp_path: Path) -> None:
    line = (
        "AccessDenied: is not authorized to perform: ec2:CreateVpc on resource: "
        "arn:aws:ec2:us-east-1:123456789012:vpc/* because no identity-based policy allows it"
    )
    result = _run(tmp_path, line)
    assert result.stdout.splitlines() == ["ec2:CreateVpc on arn:aws:ec2:us-east-1:<acct>:vpc/*"]
    assert "123456789012" not in result.stdout


@pytest.mark.criterion("ticketscope--e5-s3--AC-8")
def test_it_prints_nothing_and_succeeds_when_nothing_was_denied_or_a_log_is_missing(
    tmp_path: Path,
) -> None:
    clean = _run(tmp_path, "Apply complete! Resources: 46 added.", missing=True)
    assert clean.returncode == 0 and clean.stdout == ""
    absent = subprocess.run(
        ["bash", str(SCRIPT), str(tmp_path / "none.log")], capture_output=True, text=True
    )
    assert absent.returncode == 0 and absent.stdout == ""
