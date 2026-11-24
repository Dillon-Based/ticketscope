"""`env-check.yml` (story 5.11), checked as parsed YAML: no AWS access, no runner. The live run is
a dispatch after merge; these tests keep the wiring from drifting."""

import re
import subprocess
from typing import Any

import pytest
import yaml

from tests.target import REPO

WORKFLOW = REPO / ".github" / "workflows" / "env-check.yml"
TEXT = WORKFLOW.read_text(encoding="utf-8")
DOC: dict[str, Any] = yaml.safe_load(TEXT)
JOBS: dict[str, Any] = DOC["jobs"]
# YAML 1.1 reads the key `on` as True.
_RAW: dict[Any, Any] = DOC
TRIGGERS: dict[str, Any] = _RAW["on"] if "on" in _RAW else _RAW[True]
SCRIPT = REPO / "scripts" / "dispatch-and-watch.sh"


def _run_text(job: str) -> str:
    return "\n".join(str(s.get("run", "")) for s in JOBS[job]["steps"])


@pytest.mark.criterion("ticketscope--e5-s11--AC-1")
def test_it_is_dispatch_only() -> None:
    assert set(TRIGGERS) == {"workflow_dispatch"}


@pytest.mark.criterion("ticketscope--e5-s11--AC-1")
def test_it_runs_up_then_down_then_leftover_then_a_verdict_in_sequence() -> None:
    assert JOBS["down"]["needs"] == "up"
    assert JOBS["leftover"]["needs"] == ["up", "down"]
    assert JOBS["verdict"]["needs"] == ["up", "down", "leftover"]
    assert "env-up.yml" in _run_text("up")
    assert "env-down.yml" in _run_text("down")
    assert "leftover-check.sh" in _run_text("leftover")


@pytest.mark.criterion("ticketscope--e5-s11--AC-2")
def test_down_runs_even_when_up_failed_so_nothing_is_left_up() -> None:
    condition = JOBS["down"]["if"]
    assert "!cancelled()" in condition
    assert "needs.up.outputs.run_id" in condition
    assert "success" not in condition


@pytest.mark.criterion("ticketscope--e5-s11--AC-1")
def test_the_verdict_is_green_only_when_all_three_succeeded() -> None:
    assert JOBS["verdict"]["if"] == "${{ always() }}"
    last = _run_text("verdict").splitlines()[-1]
    assert last == '[[ "$UP" == success && "$DOWN" == success && "$LEFTOVER" == success ]]'


@pytest.mark.criterion("ticketscope--e5-s11--AC-3")
def test_env_up_must_finish_under_thirty_minutes() -> None:
    run = _run_text("up")
    assert "total >= 1800" in run
    assert "env-up-stages" in TEXT


@pytest.mark.criterion("ticketscope--e5-s11--AC-4")
def test_no_cloud_key_is_stored_and_only_the_leftover_job_assumes_the_role() -> None:
    assert "secrets." not in TEXT.replace("secrets.GITHUB_TOKEN", "")
    assert not re.search(r"AWS_(ACCESS_KEY_ID|SECRET_ACCESS_KEY|SESSION_TOKEN)", TEXT)
    assert not re.search(r"(?<!\d)\d{12}(?!\d)", TEXT)
    for name, job in JOBS.items():
        configure = [
            s for s in job["steps"] if str(s.get("uses", "")).startswith("aws-actions/configure-")
        ]
        if name == "leftover":
            assert job["environment"] == "eks"
            assert job["permissions"]["id-token"] == "write"
            assert configure[0]["with"]["role-to-assume"] == "${{ vars.AWS_ROLE_ARN }}"
        else:
            assert not configure, name
            assert "id-token" not in job.get("permissions", {}), name
    assert DOC["permissions"] == {"contents": "read"}


def test_the_expiry_input_is_validated_to_the_range_env_up_accepts() -> None:
    assert "expiry_minutes" in TRIGGERS["workflow_dispatch"]["inputs"]
    assert "10#$INPUT_MINUTES < 5 || 10#$INPUT_MINUTES > 240" in _run_text("up")


def test_the_dispatch_script_is_executable_and_parses() -> None:
    assert SCRIPT.stat().st_mode & 0o111
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True)


def test_the_dispatch_script_refuses_missing_arguments() -> None:
    done = subprocess.run(["bash", str(SCRIPT)], capture_output=True, text=True, check=False)
    assert done.returncode == 2
    assert "usage:" in done.stderr


@pytest.mark.criterion("ticketscope--e5-s11--AC-1")
def test_up_waits_for_the_env_job_not_the_expire_job_and_the_final_check_follows_down() -> None:
    assert 'WATCH_JOB="env" scripts/dispatch-and-watch.sh env-up.yml' in _run_text("up")
    assert "WATCH_JOB" in SCRIPT.read_text(encoding="utf-8")
    assert "needs.down.outputs.run_id" in JOBS["leftover"]["if"]
