"""What the live tracer run found (story 5.2), kept as offline checks so none of it regresses:
the trusted ServiceAccount names match the chart's, the Gateway API bundle is the one the
controller is built for, and the captured aws fixtures show the environment up and then gone."""

import json
import re
from typing import Any

import pytest
import yaml

from tests.target import REPO

ENV = REPO / "infra" / "env"
PLATFORM = REPO / "deploy" / "charts" / "platform"
FIXTURES = REPO / "tests" / "fixtures" / "aws"


def _fixture(name: str) -> list[dict[str, Any]]:
    doc = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = doc["ResourceTagMappingList"]
    return rows


def _types(rows: list[dict[str, Any]]) -> set[str]:
    # arn:aws:<service>:<region>:<account>:<type>/<id> -> "<service>:<type>"
    out = set()
    for row in rows:
        parts = row["ResourceARN"].split(":", 5)
        out.add(f"{parts[2]}:{re.split('[/:]', parts[5])[0]}")
    return out


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
def test_trusted_service_accounts_equal_the_names_the_chart_renders() -> None:
    """The release prefix once renamed them and AssumeRoleWithWebIdentity returned 403."""
    irsa = (ENV / "irsa.tf").read_text(encoding="utf-8")
    trusted = set(re.findall(r'"platform:([a-z-]+)"', irsa))
    values = yaml.safe_load((PLATFORM / "values-eks.yaml").read_text(encoding="utf-8"))
    pinned = {
        values["aws-load-balancer-controller"]["serviceAccount"]["name"],
        values["external-dns"]["serviceAccount"]["name"],
    }
    assert trusted == pinned == {"aws-load-balancer-controller", "external-dns"}


@pytest.mark.criterion("ticketscope--e5-s2--AC-1")
def test_the_gateway_api_bundle_is_the_one_the_controller_is_built_for() -> None:
    """Against v1.3.0 the controller disabled ALBGatewayAPI (ReferenceGrant served no v1)."""
    script = (REPO / "scripts" / "eks-deploy.sh").read_text(encoding="utf-8")
    match = re.search(
        r'GATEWAY_API_VERSION="\$\{GATEWAY_API_VERSION:-v(\d+)\.(\d+)\.\d+\}"', script
    )
    assert match, "GATEWAY_API_VERSION default not found in eks-deploy.sh"
    assert (int(match.group(1)), int(match.group(2))) >= (1, 6)


@pytest.mark.criterion("ticketscope--e5-s2--AC-4")
def test_the_up_fixture_finds_the_alb_target_group_security_group_and_volumes() -> None:
    rows = _fixture("up.json")
    assert {
        "elasticloadbalancing:loadbalancer",
        "elasticloadbalancing:targetgroup",
        "ec2:security-group",
        "ec2:volume",
    } <= _types(rows)
    for row in rows:
        tags = {t["Key"]: t["Value"] for t in row["Tags"]}
        assert tags.get("environment") == "eks", row["ResourceARN"]


@pytest.mark.criterion("ticketscope--e5-s2--AC-4")
def test_the_down_fixture_is_empty() -> None:
    assert _fixture("down.json") == []


@pytest.mark.criterion("ticketscope--e5-s2--AC-4")
@pytest.mark.parametrize("name", ["up.json", "down.json"])
def test_the_fixtures_carry_no_account_id_resource_id_or_uuid(name: str) -> None:
    text = (FIXTURES / name).read_text(encoding="utf-8")
    assert not re.search(r"\b(?!0{12}\b)\d{12}\b", text)
    assert not re.search(r"\b(vpc|sg|subnet|vol|i|eni|igw|rtb)-[0-9a-f]{8,17}\b", text)
    assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", text)


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
def test_the_deploy_and_the_ci_check_install_the_same_crds() -> None:
    """One installer, so the CI dry run validates against what the deploy installs."""
    deploy = (REPO / "scripts" / "eks-deploy.sh").read_text(encoding="utf-8")
    check = (REPO / "scripts" / "check-eks-gateway.sh").read_text(encoding="utf-8")
    assert "scripts/eks-crds.sh" in deploy and "scripts/eks-crds.sh" in check
    assert "standard-install.yaml" not in deploy


@pytest.mark.criterion("ticketscope--e5-s2--AC-5")
def test_ci_runs_the_gateway_check_and_the_evidence_job_waits_for_it() -> None:
    ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert re.search(r"^  eks-gateway:\n", ci, re.MULTILINE)
    assert "run: scripts/check-eks-gateway.sh" in ci
    needs = re.search(r"needs: \[(checks, charts[^\]]*)\]", ci)
    assert needs and "eks-gateway" in needs.group(1)
