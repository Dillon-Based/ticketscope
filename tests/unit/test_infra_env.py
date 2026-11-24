"""infra/env (AD-15, AD-23) and scripts/eks-deploy.sh, checked as text before any apply (story
5.2): no AWS access and no terraform binary needed."""

import re
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO

ENV = REPO / "infra" / "env"
CI = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
SCRIPT = REPO / "scripts" / "eks-deploy.sh"


def _tf(name: str) -> str:
    return (ENV / name).read_text(encoding="utf-8")


def _all_tf() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(ENV.glob("*.tf")))


def _code(text: str) -> str:
    """Terraform text without comments, so a comment cannot satisfy or trip a check."""
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def test_versions_match_bootstrap_and_the_state_is_in_the_bootstrap_bucket() -> None:
    versions = _tf("versions.tf")
    bootstrap = (REPO / "infra" / "bootstrap" / "versions.tf").read_text(encoding="utf-8")
    for pin in ('required_version = "~> 1.17"', 'version = "~> 6.0"'):
        assert pin in versions and pin in bootstrap
    assert 'key          = "env/terraform.tfstate"' in versions
    assert "use_lockfile = true" in versions
    # The bucket name carries the account id, so it is never committed.
    assert not re.search(r"^\s*bucket\s*=", versions, re.MULTILINE)


@pytest.mark.criterion("ticketscope--e5-s2--AC-4")
def test_every_resource_carries_the_environment_tag() -> None:
    versions = _tf("versions.tf")
    assert "default_tags" in versions
    assert "environment = var.environment" in versions
    assert 'default     = "eks"' in _tf("variables.tf")


@pytest.mark.criterion("ticketscope--e5-s2--AC-4")
def test_ebs_volumes_get_the_environment_tag_from_the_csi_driver() -> None:
    eks = _tf("eks.tf")
    assert "aws-ebs-csi-driver" in eks
    assert re.search(r"extraVolumeTags\s*=\s*\{\s*environment\s*=\s*var\.environment", eks)


def test_terraform_owns_no_helm_release_no_kms_key_and_no_control_plane_logs() -> None:
    code = _code(_all_tf())
    assert "helm_release" not in code
    assert 'provider "helm"' not in code
    assert "aws_kms_key" not in code
    assert "create_kms_key              = false" in code
    assert "enabled_log_types           = []" in code
    assert "create_cloudwatch_log_group = false" in code
    assert "auto_mode" not in code and "fargate" not in code.lower()


def test_cluster_is_1_36_on_two_graviton_nodes_with_the_two_addons() -> None:
    assert 'default     = "1.36"' in _tf("variables.tf")
    assert 'default     = "t4g.medium"' in _tf("variables.tf")
    assert re.search(r"variable \"node_count\" \{[^}]*default\s*=\s*2\b", _tf("variables.tf"))
    eks = _tf("eks.tf")
    assert 'ami_type       = "AL2023_ARM_64_STANDARD"' in eks
    assert 'source  = "terraform-aws-modules/eks/aws"' in eks
    assert 'version = "~> 21.0"' in eks
    assert "vpc-cni" in eks and "aws-ebs-csi-driver" in eks
    assert "min_size     = var.node_count" in eks and "max_size     = var.node_count" in eks


@pytest.mark.criterion("ticketscope--e5-s2--AC-4")
def test_api_endpoint_is_public_and_nodes_admit_no_inbound_internet() -> None:
    code = _code(_all_tf())
    assert "endpoint_public_access  = true" in code
    # No security group or rule of our own: the module's node group admits only the cluster
    # and itself, and the load balancer controller adds the ALB's listener-port rules.
    assert "aws_security_group" not in code
    assert "aws_vpc_security_group_ingress_rule" not in code
    assert not re.search(r"\bingress\b", code)
    assert "node_security_group_additional_rules" not in code
    # The only 0.0.0.0/0 is the public route table's default route to the internet gateway.
    assert code.count("0.0.0.0/0") == 1
    assert re.search(
        r'route \{\s*cidr_block = "0\.0\.0\.0/0"\s*gateway_id = aws_internet_gateway', code
    )


def test_vpc_has_two_public_subnets_and_no_nat() -> None:
    vpc = _code(_tf("vpc.tf"))
    assert "aws_nat_gateway" not in vpc and "aws_eip" not in vpc
    assert "aws_internet_gateway" in vpc
    assert "map_public_ip_on_launch = true" in vpc
    assert '"kubernetes.io/role/elb"' in vpc
    assert "slice(data.aws_availability_zones.available.names, 0, 2)" in _tf("main.tf")


def test_irsa_roles_use_the_prefix_the_deploy_role_manages() -> None:
    irsa = _code(_tf("irsa.tf"))
    names = re.findall(r'^\s*(?:name|policy_name)\s*=\s*"([^"]+)"', irsa, re.MULTILINE)
    assert len(names) == 8
    assert all(n.startswith("ticketscope-env-") for n in names)
    assert "attach_load_balancer_controller_policy = true" in irsa
    assert "attach_external_dns_policy" in irsa
    # external-dns writes only into the bootstrap zone.
    assert 'external_dns_hosted_zone_arns = ["arn:aws:route53:::hostedzone/${var.zone_id}"]' in irsa
    assert '"platform:aws-load-balancer-controller"' in irsa
    assert '"platform:external-dns"' in irsa
    eks = _code(_tf("eks.tf"))
    assert 'iam_role_name            = "ticketscope-env-cluster"' in eks
    assert 'iam_role_name            = "ticketscope-env-node"' in eks


def test_outputs_carry_what_the_deploy_script_reads() -> None:
    outputs = _tf("outputs.tf")
    for name in (
        "cluster_name",
        "vpc_id",
        "lb_controller_role_arn",
        "external_dns_role_arn",
        "cnpg_backup_role_arn",
        "backup_bucket",
    ):
        assert f'output "{name}"' in outputs
    outputs_read = re.findall(r"^out (\w+)|\$\(out (\w+)\)", SCRIPT.read_text(encoding="utf-8"))
    assert outputs_read


def test_no_account_specific_value_is_committed() -> None:
    text = _all_tf() + (REPO / "deploy" / "charts" / "platform" / "values-eks.yaml").read_text(
        encoding="utf-8"
    )
    assert not re.search(r"\b\d{12}\b", text)
    # An ARN may name the account only through the variable, never by a value.
    assert "arn:aws:iam::" not in text.replace("arn:aws:iam::${var.account_id}:", "")


@pytest.mark.criterion("ticketscope--e5-s2--AC-5")
def test_ci_terraform_job_checks_infra_env() -> None:
    job = CI.split("\n  terraform:\n", 1)[1].split("\n  changes:\n", 1)[0]
    for command in ("fmt -check", "init -backend=false", "validate"):
        assert f"terraform -chdir=infra/env {command}" in job


@pytest.mark.criterion("ticketscope--e5-s2--AC-3")
def test_ci_chart_job_runs_the_eks_render_tests_and_lints_the_eks_values() -> None:
    job = CI.split("\n  charts:\n", 1)[1].split("\n  terraform:\n", 1)[0]
    assert "tests/unit/test_chart_eks.py" in job
    assert "values-eks.yaml" in job
    assert "helm repo add eks https://aws.github.io/eks-charts" in job
    assert "helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/" in job


def _run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(script), *args], capture_output=True, text=True, check=False)


def test_deploy_script_without_input_exits_non_zero_with_usage_and_installs_nothing() -> None:
    result = _run(SCRIPT)
    assert result.returncode != 0
    assert "usage:" in result.stderr
    result = _run(SCRIPT, "--tag", "abc", "--hostname", "h", "--certificate-arn", "a")
    assert result.returncode != 0 and "usage:" in result.stderr


def test_deploy_script_with_a_missing_kubeconfig_exits_non_zero() -> None:
    result = _run(
        SCRIPT,
        "--kubeconfig",
        "/nonexistent/kubeconfig",
        "--tag",
        "abc",
        "--hostname",
        "h.test",
        "--certificate-arn",
        "arn",
        "--ecr-registry",
        "r",
        "--incarnation",
        "inc-1-1",
    )
    assert result.returncode != 0
    assert "not found" in result.stderr


def test_deploy_script_installs_in_the_required_order_and_times_each_stage() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    order = [
        text.index('stage "crds"'),
        text.index('stage "platform"'),
        text.index('stage "ticketscope"'),
        text.index('stage "api-mcp-ready"'),
        text.index('stage "https-answers"'),
    ]
    assert order == sorted(order)
    # The CRDs are installed by the shared script, in order: Gateway API's, then the controller's.
    crds = (SCRIPT.parent / "eks-crds.sh").read_text(encoding="utf-8")
    assert text.index("scripts/eks-crds.sh") < text.index("helm upgrade --install platform")
    assert crds.index("standard-install.yaml") < crds.index("gateway-crds.yaml")
    assert text.index("helm upgrade --install platform") < text.index(
        "helm upgrade --install ticketscope"
    )
    # The stage timer is the shared scripts/lib/stages.sh, sourced and titled by the script.
    assert 'source "$ROOT/scripts/lib/stages.sh"' in text
    assert "stage times" in (SCRIPT.parent / "lib" / "stages.sh").read_text(encoding="utf-8")
    assert "terraform apply" not in text and "helm_release" not in text


@pytest.mark.criterion("ticketscope--e5-s3--AC-10")
def test_the_admin_role_gets_cluster_admin_unless_it_applied_the_stack_itself() -> None:
    eks = (ENV / "eks.tf").read_text(encoding="utf-8")
    assert 'data "aws_iam_roles" "admin"' in eks
    assert "AmazonEKSClusterAdminPolicy" in eks
    assert "merge({" in eks and "local.admin_access_entry" in eks
    # Two entries for one principal fail, and the creator-admin entry names the applier.
    assert ":assumed-role/${var.admin_role_name}/" in eks and "!local.admin_applies" in eks
    variables = (ENV / "variables.tf").read_text(encoding="utf-8")
    assert 'default     = "AccountFullAccessRole"' in variables
    assert not re.search(r"(?<!\d)\d{12}(?!\d)", eks + variables)
