"""`env-down.yml` (story 5.4), checked as text and as parsed YAML: no AWS access, no runner. The
live run is a person's step; these tests keep the wiring from drifting."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
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
    # env-up holds the group on its `env` job only, so its sleeping expire job never blocks this.
    assert DOC["concurrency"] == UP["jobs"]["env"]["concurrency"]


def test_a_dispatch_can_ask_to_tear_down_only_an_expired_environment() -> None:
    inputs = TRIGGERS["workflow_dispatch"]["inputs"]
    assert set(inputs) == {"only_if_expired"}
    only = inputs["only_if_expired"]
    assert only["type"] == "boolean" and only["default"] is False and only["required"] is False
    decide = _step("find", "Decide")
    assert decide["env"]["ONLY_IF_EXPIRED"] == "${{ inputs.only_if_expired }}"
    assert '"$ONLY_IF_EXPIRED" != "true"' in decide["run"]


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
    teardown = _step("teardown", "Tear down")
    assert "scripts/eks-teardown.sh" in teardown["run"]
    # The DNS check gets the hostname and zone id from the same discovery env-up uses.
    facts = _step("teardown", "Read the bootstrap facts")["run"]
    assert "starts_with(Name, 'ticketscope.')" in facts
    assert "TICKETSCOPE_HOSTNAME=$hostname" in facts and "TICKETSCOPE_ZONE_ID=$zone_id" in facts
    assert '--hostname "$TICKETSCOPE_HOSTNAME" --zone-id "$TICKETSCOPE_ZONE_ID"' in teardown["run"]
    # Exit 3 (destroyed, stale DNS) still runs the leftover check, and the job still fails.
    assert teardown["id"] == "teardown"
    assert "((rc == 0 || rc == 3))" in teardown["run"] and 'exit "$rc"' in teardown["run"]
    assert "set -o pipefail" in teardown["run"] and "|| rc=$?" in teardown["run"]
    check = _step("teardown", "Leftover check")
    assert check["if"] == "${{ !cancelled() && steps.teardown.outputs.destroyed == 'true' }}"
    check_run = check["run"]
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


# The `find` decision, run as bash against stubs of `aws`, `date` (GNU `-d` is not on every
# machine) and scripts/leftover-check.sh.
AWS_STUB = """#!/usr/bin/env bash
cat "$VPCS_FILE"
"""
DATE_STUB = f"""#!{sys.executable}
import datetime, sys, time
args = sys.argv[1:]
if "-d" in args:
    when = datetime.datetime.strptime(args[args.index("-d") + 1], "%Y-%m-%dT%H:%M:%SZ")
    print(int(when.replace(tzinfo=datetime.timezone.utc).timestamp()))
else:
    print(int(time.time()))
"""


def _vpcs(expires: str | None) -> str:
    tags = [{"Key": "environment", "Value": "eks"}]
    if expires is not None:
        tags.append({"Key": "expires_at", "Value": expires})
    return json.dumps({"Vpcs": [{"VpcId": "vpc-0", "Tags": tags}]})


def _decide(tmp_path: Path, event: str, only_if_expired: str, vpcs: str) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    (tmp_path / "scripts").mkdir(parents=True)
    bin_dir.mkdir()
    for name, body in (("aws", AWS_STUB), ("date", DATE_STUB)):
        (bin_dir / name).write_text(body)
        (bin_dir / name).chmod(0o755)
    check = tmp_path / "scripts" / "leftover-check.sh"
    check.write_text("#!/usr/bin/env bash\nexit 0\n")
    check.chmod(0o755)
    (tmp_path / "vpcs.json").write_text(vpcs)
    output, summary = tmp_path / "output", tmp_path / "summary"
    result = subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", _step("find", "Decide")["run"]],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env={
            "PATH": f"{bin_dir}:/usr/bin:/bin",
            "VPCS_FILE": str(tmp_path / "vpcs.json"),
            "EVENT": event,
            "ONLY_IF_EXPIRED": only_if_expired,
            "GITHUB_OUTPUT": str(output),
            "GITHUB_STEP_SUMMARY": str(summary),
        },
    )
    assert result.returncode == 0, result.stderr
    return {
        "teardown": output.read_text().strip() if output.exists() else "",
        "summary": summary.read_text() if summary.exists() else "",
    }


PAST, FUTURE = "2000-01-01T00:00:00Z", "2999-01-01T00:00:00Z"


@pytest.mark.criterion("ticketscope--e5-s4--AC-3")
@pytest.mark.skipif(shutil.which("jq") is None, reason="needs jq")
@pytest.mark.parametrize(
    ("event", "only_if_expired", "expires", "teardown"),
    [
        ("workflow_dispatch", "false", FUTURE, "true"),  # a plain dispatch tears down now
        ("workflow_dispatch", "true", FUTURE, "false"),  # a late expire never hits a newer env
        ("workflow_dispatch", "true", None, "false"),  # nor a hand-run (untagged) one
        ("workflow_dispatch", "true", PAST, "true"),
        ("schedule", "", FUTURE, "false"),
        ("schedule", "", PAST, "true"),
    ],
)
def test_the_find_decision(
    tmp_path: Path, event: str, only_if_expired: str, expires: str | None, teardown: str
) -> None:
    decided = _decide(tmp_path, event, only_if_expired, _vpcs(expires))
    assert decided["teardown"] == f"teardown={teardown}"


@pytest.mark.skipif(shutil.which("jq") is None, reason="needs jq")
def test_an_expire_dispatch_with_no_environment_runs_only_the_leftover_check(
    tmp_path: Path,
) -> None:
    decided = _decide(tmp_path, "workflow_dispatch", "true", json.dumps({"Vpcs": []}))
    assert decided["teardown"] == "teardown=false"
    assert "nothing tagged is left" in decided["summary"]
