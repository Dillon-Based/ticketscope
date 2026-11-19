"""Every workflow runs its `run` steps as `bash -eo pipefail`.

GitHub's default shell for `run` is `bash -e {0}`, with no pipefail, so `cmd | tee log` reports
`tee`'s status and a failing `cmd` leaves the job green. env-down's leftover check shipped that
way once (story 5.4 review). `defaults.run.shell: bash` makes GitHub run `bash --noprofile
--norc -eo pipefail {0}` for every step, so the rule holds without each step remembering it."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.target import REPO

WORKFLOWS = sorted((REPO / ".github" / "workflows").glob("*.yml"))


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_there_are_workflows_to_check() -> None:
    assert WORKFLOWS


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_the_workflow_runs_every_step_under_bash_with_pipefail(path: Path) -> None:
    doc = _load(path)
    assert doc.get("defaults", {}).get("run", {}).get("shell") == "bash", (
        f"{path.name}: add `defaults: run: shell: bash` above `jobs:`"
    )
    # Nothing narrows it back to the pipefail-less default.
    for name, job in doc["jobs"].items():
        job_shell = job.get("defaults", {}).get("run", {}).get("shell", "bash")
        assert job_shell == "bash", f"{path.name}: job {name} sets shell {job_shell!r}"
        for step in job.get("steps", []):
            if "run" in step:
                shell = step.get("shell", "bash")
                assert shell == "bash", f"{path.name}: step {step.get('name')!r} sets {shell!r}"
