"""`env-up.yml` and its pieces (story 5.3), checked as text and as parsed YAML: no AWS access, no
runner. The live run is a person's step; these tests keep the wiring from drifting."""

import json
import re
import subprocess
import tomllib
from typing import Any

import pytest
import yaml

from tests.target import REPO

WORKFLOW = REPO / ".github" / "workflows" / "env-up.yml"
TEXT = WORKFLOW.read_text(encoding="utf-8")
DOC: dict[str, Any] = yaml.safe_load(TEXT)
JOBS: dict[str, Any] = DOC["jobs"]
SCRIPT = (REPO / "scripts" / "eks-deploy.sh").read_text(encoding="utf-8")
CI = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
# YAML 1.1 reads the key `on` as True.
_RAW: dict[Any, Any] = DOC
TRIGGERS: dict[str, Any] = _RAW["on"] if "on" in _RAW else _RAW[True]


def _steps(job: str) -> list[dict[str, Any]]:
    return JOBS[job]["steps"]


def _step(job: str, fragment: str) -> dict[str, Any]:
    (found,) = [s for s in _steps(job) if fragment in str(s.get("name", ""))]
    return found


def _index(job: str, fragment: str) -> int:
    return _steps(job).index(_step(job, fragment))


@pytest.mark.criterion("ticketscope--e5-s3--AC-3")
def test_no_aws_credential_is_stored_and_every_aws_job_assumes_the_role_through_oidc() -> None:
    assert "secrets." not in TEXT
    assert not re.search(r"AWS_(ACCESS_KEY_ID|SECRET_ACCESS_KEY|SESSION_TOKEN)", TEXT)
    assert not re.search(r"(?<!\d)\d{12}(?!\d)", TEXT)
    for name, job in JOBS.items():
        assert job["environment"] == "eks", name
        assert job["permissions"]["id-token"] == "write", name
        configure = [
            s for s in job["steps"] if str(s.get("uses", "")).startswith("aws-actions/configure-")
        ]
        assert configure, name
        assert configure[0]["with"]["role-to-assume"] == "${{ vars.AWS_ROLE_ARN }}", name
        assert configure[0]["with"]["mask-aws-account-id"] is True, name
    assert DOC["permissions"] == {"contents": "read"}


def test_it_is_dispatch_only_and_takes_a_sha_and_expiry_hours_defaulting_to_four() -> None:
    assert set(TRIGGERS) == {"workflow_dispatch"}
    inputs = TRIGGERS["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"sha", "expiry_hours"}
    assert inputs["sha"]["required"] is True
    assert inputs["expiry_hours"]["default"] == "4"
    assert DOC["concurrency"]["cancel-in-progress"] is False


@pytest.mark.criterion("ticketscope--e5-s3--AC-1")
def test_bad_input_fails_in_a_job_that_has_made_no_aws_call() -> None:
    steps = _steps("plan")
    validate = _index("plan", "Validate the inputs")
    first_aws = next(
        i
        for i, s in enumerate(steps)
        if str(s.get("uses", "")).startswith("aws-actions/") or "aws " in str(s.get("run", ""))
    )
    assert validate < first_aws
    run = steps[validate]["run"]
    assert "^[0-9a-f]{40}$" in run and "10#$INPUT_HOURS < 1" in run and "> 24" in run
    # The messages name the input.
    assert "input sha" in run and "input expiry_hours" in run
    # Inputs reach the shell through env, never interpolated into the script.
    assert "${{" not in run
    for name in ("build", "images", "env"):
        assert "plan" in JOBS[name]["needs"]


@pytest.mark.criterion("ticketscope--e5-s3--AC-6")
def test_the_build_is_skipped_when_both_images_exist_and_is_multi_arch() -> None:
    present = _step("plan", "Are both images")["run"]
    assert "ticketscope-app" in present and "ticketscope-postgres" in present
    assert '"18-$SHA"' in present and "describe-images" in present
    assert JOBS["plan"]["outputs"]["images_present"]
    for name in ("build", "images"):
        assert JOBS[name]["if"] == "needs.plan.outputs.images_present != 'true'"
    matrix = JOBS["build"]["strategy"]["matrix"]["include"]
    assert {(m["runner"], m["arch"]) for m in matrix} == {
        ("ubuntu-24.04", "amd64"),
        ("ubuntu-24.04-arm", "arm64"),
    }
    build = "\n".join(str(s.get("run", "")) for s in _steps("build"))
    assert 'docker buildx build --platform "linux/$ARCH"' in build
    assert "push-by-digest=true" in build
    assert "images/app.Dockerfile" in build and "images/postgres.Dockerfile" in build
    join = "\n".join(str(s.get("run", "")) for s in _steps("images"))
    assert "imagetools create" in join and "-amd64" in join and "-arm64" in join
    assert 'join ticketscope-app "$SHA"' in join
    assert 'join ticketscope-postgres "18-$SHA"' in join
    # A skipped build must not skip the env job, and a failed one must.
    condition = JOBS["env"]["if"]
    assert "needs.build.result" in condition and "needs.images.result" in condition
    assert '"success","skipped"' in condition
    # The images are outside the clock.
    assert "clock-start" not in json.dumps(JOBS["build"]) + json.dumps(JOBS["images"])


@pytest.mark.criterion("ticketscope--e5-s3--AC-1")
def test_the_clock_starts_at_terraform_apply_and_stops_after_the_smoke_check() -> None:
    steps = _steps("env")
    init = _index("env", "terraform init")
    apply = _index("env", "terraform apply")
    kubeconfig = _index("env", "kubeconfig")
    deploy = _index("env", "Deploy the releases")
    smoke = _index("env", "Smoke check")
    assert init < apply < kubeconfig < deploy < smoke
    apply_run = steps[apply]["run"]
    assert apply_run.index("clock-start") < apply_run.index("terraform -chdir=infra/env apply")
    for i, step in enumerate(steps):
        if i != apply:
            assert "clock-start" not in str(step.get("run", "")) or i > smoke, step.get("name")
    smoke_run = steps[smoke]["run"]
    assert smoke_run.index("pytest -m eks tests/eks") < smoke_run.index("clock-end")
    assert "clock-end" not in "".join(str(s.get("run", "")) for s in steps[:smoke])
    assert "TICKETSCOPE_PUBLIC_URL" in smoke_run
    # Preparation (installs, AWS reads, init) sits before the clock.
    for fragment in ("Install dig", "Read the bootstrap facts"):
        assert _index("env", fragment) < apply


@pytest.mark.criterion("ticketscope--e5-s3--AC-5")
def test_a_failed_deploy_or_smoke_leaves_the_environment_up() -> None:
    assert "terraform destroy" not in TEXT and "env-down" not in TEXT.replace("story 5.4", "")
    assert "helm uninstall" not in TEXT
    summary = _step("env", "Job summary")
    assert summary["if"] == "always()"
    upload = _steps("env")[-1]
    assert upload["uses"].startswith("actions/upload-artifact@") and upload["if"] == "always()"
    assert "environment was left up" in summary["run"]
    # The smoke step is a plain step: when it fails the job fails, so the run is red.
    assert "continue-on-error" not in TEXT
    # A failed smoke still writes its row, keeps its exit status, and stops no clock.
    smoke = _step("env", "Smoke check")
    run = smoke["run"]
    assert "|| rc=$?" in run and 'exit "$rc"' in run
    assert run.index("'smoke") < run.index("clock-end") < run.index('exit "$rc"')
    assert "((rc == 0))" in run
    assert smoke["env"]["GITHUB_TOKEN"] == "${{ github.token }}"
    # The deploy.* rows are written after the deploy step and before the smoke step.
    rows = _step("env", "Record the deploy stage times")
    assert rows["if"] == "always()" and "deploy.%s" in rows["run"]
    deploy, record, check = (
        _index("env", "Deploy the releases"),
        _index("env", "Record the deploy"),
        _index("env", "Smoke check"),
    )
    assert deploy < record < check


@pytest.mark.criterion("ticketscope--e5-s3--AC-2")
def test_the_summary_and_artifact_list_each_stage_and_the_log_never_leaves_the_runner() -> None:
    summary = _step("env", "Job summary")["run"]
    assert "GITHUB_STEP_SUMMARY" in summary
    assert "env-up-stages/stages.json" in summary
    assert "total < 1800" in summary
    upload = _steps("env")[-1]["with"]["path"]
    assert "stages.json" in upload and "stages.md" in upload
    # The deploy log holds ARNs (a failing Gateway dump): it is never an artifact.
    assert "deploy.log" not in upload
    for fragment in ("terraform apply", "Write the kubeconfig", "Smoke check"):
        assert "$STAGES" in _step("env", fragment)["run"]


@pytest.mark.criterion("ticketscope--e5-s3--AC-2")
def test_dns_visible_is_measured_on_the_zones_name_servers_before_the_public_resolver() -> None:
    order = [
        SCRIPT.index('stage "api-mcp-ready"'),
        SCRIPT.index('stage "dns_visible"'),
        SCRIPT.index('stage "dns_public"'),
        SCRIPT.index('stage "https-answers"'),
    ]
    assert order == sorted(order)
    visible = SCRIPT[order[1] : order[2]]
    assert "get-hosted-zone" in visible and "DelegationSet.NameServers" in visible
    assert 'wait_dns "$ns"' in visible
    public = SCRIPT[order[2] : order[3]]
    assert 'wait_dns "$PUBLIC_RESOLVER"' in public


@pytest.mark.criterion("ticketscope--e5-s3--AC-4")
def test_the_input_hours_become_the_expiry_tag_on_every_environment_resource() -> None:
    facts = _step("env", "Read the bootstrap facts")
    assert facts["env"]["EXPIRY_HOURS"] == "${{ inputs.expiry_hours }}"
    assert "TF_VAR_expires_at=$expires_at" in facts["run"]
    assert "+$((10#$EXPIRY_HOURS)) hours" in facts["run"]
    versions = (REPO / "infra" / "env" / "versions.tf").read_text(encoding="utf-8")
    assert "expires_at = var.expires_at" in versions and "default_tags" in versions
    variables = (REPO / "infra" / "env" / "variables.tf").read_text(encoding="utf-8")
    assert 'variable "expires_at"' in variables
    # The apply reads the variable from the environment, so nothing else sets it.
    assert "-var" not in _step("env", "terraform apply")["run"]


def test_the_deploy_reuses_the_script_and_the_smoke_uses_the_tests_directory() -> None:
    deploy = _step("env", "Deploy the releases")["run"]
    assert "scripts/eks-deploy.sh" in deploy and "--certificate-arn" in deploy
    assert "helm upgrade" not in deploy
    assert "tests/eks" in _step("env", "Smoke check")["run"]


def test_the_eks_marker_is_registered_and_excluded_from_default_runs() -> None:
    pytest_config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    options = pytest_config["tool"]["pytest"]["ini_options"]
    assert "not eks" in options["addopts"] and "not kind" in options["addopts"]
    assert any(m.startswith("eks:") for m in options["markers"])


def test_deploy_script_keeps_its_usage_error_with_the_dns_stages_added() -> None:
    result = subprocess.run(
        [str(REPO / "scripts" / "eks-deploy.sh")], capture_output=True, text=True, check=False
    )
    assert result.returncode == 2 and "usage:" in result.stderr


def test_ci_runs_a_static_workflow_check() -> None:
    assert "actionlint" in CI and "shellcheck scripts/eks-deploy.sh" in CI
