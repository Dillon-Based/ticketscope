"""infra/bootstrap (AD-15): the policy templates rendered with plain substitution and checked
before any apply, the Terraform ignore patterns, the tracked-file secret scan, and ci.yml's
`terraform` job. No AWS access and no terraform binary needed."""

import fnmatch
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.target import REPO

BOOTSTRAP = REPO / "infra" / "bootstrap"
POLICIES = BOOTSTRAP / "policies"
CI = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

# Obviously fake values; the real ones live in an untracked tfvars.
VARS = {
    "account_id": "000000000000",
    "region": "us-east-1",
    "repo": "example-owner/example-repo",
    "bucket": "ticketscope-test-bucket",
    "oidc_provider_arn": (
        "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com"
    ),
    "admin_principal_arn": "arn:aws:iam::000000000000:user/example-admin",
}

READ_PREFIXES = ("Get", "List", "Describe", "Head", "Simulate", "View")


def render(name: str) -> Any:
    text = (POLICIES / name).read_text(encoding="utf-8")
    for key, value in VARS.items():
        text = text.replace("${" + key + "}", value)
    assert "${" not in text, f"{name}: unsubstituted placeholder"
    return json.loads(text)


def statements(policy: Any) -> list[dict[str, Any]]:
    stmts = policy["Statement"]
    return stmts if isinstance(stmts, list) else [stmts]


def as_list(value: Any) -> list[str]:
    return value if isinstance(value, list) else [value]


def is_write(action: str) -> bool:
    return not action.split(":", 1)[1].startswith(READ_PREFIXES)


def all_strings(node: Any) -> list[str]:
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [s for v in node.values() for s in all_strings(v)]
    if isinstance(node, list):
        return [s for v in node for s in all_strings(v)]
    return []


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_trust_policy_has_one_exact_sub_and_the_sts_audience() -> None:
    policy = render("deploy-trust.json.tftpl")
    (stmt,) = statements(policy)
    assert stmt["Effect"] == "Allow"
    assert stmt["Action"] == "sts:AssumeRoleWithWebIdentity"
    assert stmt["Principal"] == {"Federated": VARS["oidc_provider_arn"]}
    cond = stmt["Condition"]
    assert cond["StringEquals"] == {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": f"repo:{VARS['repo']}:environment:eks",
    }
    assert "StringLike" not in cond
    assert not any("*" in s for s in all_strings(cond))


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_trust_template_names_the_repo_variable_and_has_no_wildcard() -> None:
    text = (POLICIES / "deploy-trust.json.tftpl").read_text(encoding="utf-8")
    assert "${repo}" in text
    assert "environment:eks" in text
    assert "*" not in text


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_deploy_permissions_never_reach_bootstrap_state_or_write_on_star() -> None:
    policy = render("deploy-permissions.json.tftpl")
    for stmt in statements(policy):
        resources = as_list(stmt["Resource"])
        actions = as_list(stmt["Action"])
        assert not any("bootstrap" in r for r in resources), stmt
        if "*" in resources:
            assert not any(is_write(a) for a in actions), stmt
        assert "NotResource" not in stmt and "NotAction" not in stmt
        assert not any(a in ("*", "s3:*", "iam:*") for a in actions)


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_deploy_permissions_scope_s3_to_env_and_backups_and_iam_to_ticketscope() -> None:
    policy = render("deploy-permissions.json.tftpl")
    bucket_arn = f"arn:aws:s3:::{VARS['bucket']}"
    s3_objects: set[str] = set()
    for stmt in statements(policy):
        actions = as_list(stmt["Action"])
        resources = as_list(stmt["Resource"])
        if any(a.startswith("s3:") for a in actions):
            for r in resources:
                assert r.startswith(bucket_arn), r
                if r != bucket_arn:
                    s3_objects.add(r)
            if bucket_arn in resources:
                prefixes = stmt["Condition"]["StringLike"]["s3:prefix"]
                assert sorted(as_list(prefixes)) == ["backups/*", "env/*"]
        if any(a.startswith("iam:") and is_write(a) for a in actions):
            assert resources, stmt
            for r in resources:
                pattern = r"arn:aws:iam::\d+:(role|policy|instance-profile)/ticketscope-env-\*"
                assert re.fullmatch(pattern, r), r
                for bootstrap_name in ("ticketscope-deploy", "ticketscope-readonly"):
                    arn = f"arn:aws:iam::{VARS['account_id']}:role/{bootstrap_name}"
                    assert not fnmatch.fnmatchcase(arn, r), (arn, r)
    assert s3_objects == {f"{bucket_arn}/env/*", f"{bucket_arn}/backups/*"}


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_readonly_extras_allow_only_reads() -> None:
    policy = render("readonly-extras.json.tftpl")
    for stmt in statements(policy):
        assert stmt["Effect"] == "Allow"
        assert not any(is_write(a) for a in as_list(stmt["Action"])), stmt


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_identifying_variables_have_no_defaults_and_region_is_us_east_1() -> None:
    text = (BOOTSTRAP / "variables.tf").read_text(encoding="utf-8")
    for name in ("account_id", "alert_email", "domain", "admin_principal_arn", "repo"):
        block = re.search(rf'variable "{name}" \{{(.*?)\n\}}', text, re.S)
        assert block, name
        assert "default" not in block.group(1), name
    assert "us-east-1" in (BOOTSTRAP / "versions.tf").read_text(encoding="utf-8")


def infra_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "infra"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [REPO / p for p in out]


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_no_account_id_email_or_key_in_tracked_infra_files() -> None:
    files = infra_files()
    assert files
    for path in files:
        assert path.suffix != ".tfvars", path
        if path.name == ".terraform.lock.hcl":
            continue  # provider hashes
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"(?<!\d)\d{12}(?!\d)", text), f"{path}: 12-digit account id"
        assert not re.search(r"A[KS]IA[0-9A-Z]{16}", text), f"{path}: access key"
        assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text), f"{path}: email"
        assert "aws_secret_access_key" not in text


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_gitignore_covers_terraform_local_files_but_not_the_lock() -> None:
    lines = (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
    for pattern in (
        "*.tfstate*",
        "*.tfplan",
        ".terraform/",
        "*.tfvars",
        "infra/bootstrap/backend.tf",
    ):
        assert pattern in lines, pattern
    assert ".terraform.lock.hcl" not in lines


def _job(name: str) -> str:
    start = CI.index(f"\n  {name}:\n")
    rest = CI[start + 1 :]
    following = re.search(r"\n  [a-z][\w-]*:\n", rest[len(name) + 4 :])
    return rest[: len(name) + 4 + following.start()] if following else rest


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_ci_terraform_job_checks_bootstrap_without_a_backend_and_gates_evidence() -> None:
    job = _job("terraform")
    assert "terraform -chdir=infra/bootstrap fmt -check" in job
    assert "terraform -chdir=infra/bootstrap init -backend=false" in job
    assert "terraform -chdir=infra/bootstrap validate" in job
    assert "configure-aws-credentials" not in job
    needs = re.search(r"needs: \[([^\]]+)\]", _job("evidence"))
    assert needs and "terraform" in [n.strip() for n in needs.group(1).split(",")]
    paths = (REPO / ".github" / "kind-paths.yml").read_text(encoding="utf-8")
    assert "infra" not in paths


@pytest.mark.criterion("ticketscope--e5-s1--AC-1")
def test_admin_login_script_clears_env_checks_identity_and_hides_the_account_id() -> None:
    script = (REPO / "scripts" / "aws-admin-login.sh").read_text(encoding="utf-8")
    assert "unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE" in script
    assert "*:user/ticketscope-admin" in script and "exit 1" in script
    assert not re.search(r"(?<!\d)\d{12}(?!\d)", script)
    assert "--query Account" not in script
