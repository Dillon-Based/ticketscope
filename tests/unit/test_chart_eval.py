"""The eval Job on offline renders (story 2.1, AD-7, AD-22): off by default, and when
enabled a hook after load that runs `ticketscope-eval` as `ticketscope_ro` under a deadline."""

import re
import shutil

import pytest

from tests.unit.test_chart_backup import _IMAGE_TAGS, TICKETSCOPE, _docs, _render

pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="needs helm")

KIND_VALUES = ("-f", str(TICKETSCOPE / "values-kind.yaml"))


def _ticketscope(*args: str) -> list[str]:
    return _render(TICKETSCOPE, *KIND_VALUES, *_IMAGE_TAGS, *args)


def _eval_job() -> str:
    [job] = _docs(_ticketscope("--set", "eval.enabled=true"), "Job", "ticketscope-eval")
    return job


def _hook_weight(job: str) -> int:
    match = re.search(r'helm\.sh/hook-weight: "(-?\d+)"', job)
    assert match, job
    return int(match.group(1))


def test_default_values_render_no_eval_job() -> None:
    docs = _ticketscope()
    assert _docs(docs, "Job", "ticketscope-eval") == []
    assert "ticketscope-eval" not in "\n".join(docs)


def test_enabled_renders_the_eval_job_running_ticketscope_eval() -> None:
    assert 'command: ["ticketscope-eval"]' in _eval_job()


def test_eval_job_reads_the_database_as_ticketscope_ro_only() -> None:
    job = _eval_job()
    secrets = re.findall(r"secretKeyRef:\s*\n\s*name: (\S+)", job)
    assert secrets and set(secrets) == {"ticketscope-db-ro"}
    assert "ticketscope-db-app" not in job


def test_eval_job_is_a_hook_after_load() -> None:
    job = _eval_job()
    [load] = _docs(_ticketscope("--set", "eval.enabled=true"), "Job", "ticketscope-load")
    assert "helm.sh/hook: post-install,post-upgrade" in job
    assert "helm.sh/hook-delete-policy: before-hook-creation" in job
    assert _hook_weight(job) > _hook_weight(load)


def test_eval_job_has_an_active_deadline() -> None:
    assert "activeDeadlineSeconds: 2700" in _eval_job()
    job = _docs(
        _ticketscope("--set", "eval.enabled=true", "--set", "eval.activeDeadlineSeconds=60"),
        "Job",
        "ticketscope-eval",
    )[0]
    assert "activeDeadlineSeconds: 60" in job
