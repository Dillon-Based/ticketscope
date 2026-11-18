"""`env-down.yml` (story 5.4), checked as text and as parsed YAML: no AWS access, no runner. The
live run is a person's step; these tests keep the wiring from drifting."""

import re
import subprocess
from typing import Any

import pytest
import yaml

from tests.target import REPO

WORKFLOW = REPO / ".github" / "workflows" / "env-down.yml"
TEXT = WORKFLOW.read_text(encoding="utf-8")
DOC: dict[str, Any] = yaml.safe_load(TEXT)
JOBS: dict[str, Any] = DOC["jobs"]
UP = yaml.safe_load((REPO / ".github" / "workflows" / "env-up.yml").read_text(encoding="utf-8"))
_RAW: dict[Any, Any] = DOC
TRIGGERS: dict[str, Any] = _RAW["on"] if "on" in _RAW else _RAW[True]


def _step(job: str, fragment: str) -> dict[str, Any]:
    (found,) = [s for s in JOBS[job]["steps"] if fragment in str(s.get("name", ""))]
    return found


def test_it_runs_on_dispatch_and_an_hourly_schedule_and_never_on_a_pull_request() -> None:
    assert set(TRIGGERS) == {"workflow_dispatch", "schedule"}
    (entry,) = TRIGGERS["schedule"]
    minute, hour, *rest = entry["cron"].split()
    assert re.fullmatch(r"\d+", minute) and hour == "*" and rest == ["*", "*", "*"]
    assert "pull_request" not in TEXT and "push:" not in TEXT


def test_it_shares_env_ups_concurrency_group_without_cancelling() -> None:
    assert DOC["concurrency"] == {"group": "eks-environment", "cancel-in-progress": False}
    assert DOC["concurrency"] == UP["concurrency"]


@pytest.mark.criterion("ticketscope--e5-s4--AC-1")
def test_oidc_is_granted_only_to_jobs_on_the_eks_environment_and_no_key_is_stored() -> None:
    assert DOC["permissions"] == {"contents": "read"}
    assert "secrets." not in TEXT
    assert not re.search(r"AWS_(ACCESS_KEY_ID|SECRET_ACCESS_KEY|SESSION_TOKEN)", TEXT)
    assert not re.search(r"(?<!\d)\d{12}(?!\d)", TEXT)
    for name, job in JOBS.items():
        assert job["environment"] == "eks", name
        assert job["permissions"]["id-token"] == "write", name
        configure = [
            s for s in job["steps"] if str(s.get("uses", "")).startswith("aws-actions/configure-")
        ]
        assert configure[0]["with"]["role-to-assume"] == "${{ vars.AWS_ROLE_ARN }}", name
        assert configure[0]["with"]["mask-aws-account-id"] is True, name


def test_the_sweep_skips_an_unexpired_or_untagged_environment_with_a_summary_line() -> None:
    run = _step("find", "Decide")["run"]
    assert 'EVENT" != "schedule"' in run  # a dispatch always tears down
    assert '"expires_at"' in run and "describe-vpcs" in run
    assert "which has not passed; skipped" in run
    assert "no valid expires_at tag" in run and "expired at" in run
    # The comparison is on epoch seconds, never on the strings.
    assert 'date -u -d "$expires" +%s' in run
    assert JOBS["teardown"]["if"] == "needs.find.outputs.teardown == 'true'"
    assert "teardown" in JOBS["find"]["outputs"]
    # With no environment, the check runs on its own and its failure fails the run.
    assert "scripts/leftover-check.sh" in run and "exit 1" in run


def test_the_teardown_runs_the_script_then_the_check_then_the_stage_times() -> None:
    names = [str(s.get("name", s.get("uses", ""))) for s in JOBS["teardown"]["steps"]]
    order = [
        next(i for i, n in enumerate(names) if fragment in n)
        for fragment in (
            "Read the bootstrap facts",
            "Write the kubeconfig",
            "Tear down in AD-24 order",
            "Leftover check",
            "Stage times",
        )
    ]
    assert order == sorted(order)
    assert "scripts/eks-teardown.sh" in _step("teardown", "Tear down")["run"]
    check_run = _step("teardown", "Leftover check")["run"]
    assert "scripts/leftover-check.sh" in check_run
    # Piped through tee: without pipefail a failing check would leave the job green.
    assert "set -o pipefail" in check_run
    assert _step("teardown", "Stage times")["if"] == "always()"
    # The summary is public: stage times and a verdict only, never the listing.
    summary = _step("teardown", "Stage times")["run"]
    assert "tail -n 1" in summary and "cat " not in summary


def test_nothing_in_it_destroys_or_names_the_bootstrap_stack() -> None:
    assert "-chdir=infra/bootstrap" not in TEXT and "infra/bootstrap" not in TEXT
    assert "stack=bootstrap" not in TEXT and "arn:aws" not in TEXT
    assert "terraform destroy" not in TEXT  # it is scripts/eks-teardown.sh that destroys `env`
    assert "--force" not in TEXT and "finalizers" not in TEXT


def test_the_inputs_never_reach_a_shell_by_interpolation() -> None:
    for name, job in JOBS.items():
        for step in job["steps"]:
            run = str(step.get("run", ""))
            for expression in re.findall(r"\$\{\{[^}]*\}\}", run):
                assert not expression.startswith("${{ inputs"), (name, expression)
                assert not expression.startswith("${{ github.event"), (name, expression)


def test_the_check_script_lists_and_the_workflow_scripts_pass_a_syntax_check() -> None:
    for script in ("eks-teardown.sh", "leftover-check.sh"):
        result = subprocess.run(
            ["bash", "-n", str(REPO / "scripts" / script)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
    ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert (
        "shellcheck scripts/eks-teardown.sh" in ci and "shellcheck scripts/leftover-check.sh" in ci
    )
