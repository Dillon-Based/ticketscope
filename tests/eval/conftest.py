"""`eval_results` reads the eval Job's results line once and writes
`reports/eval-results.json` before any test that requests it asserts anything, so
`_kind-deploy.yml`'s always-run upload carries it even when a check fails (AD-17: the
cluster dies with the job)."""

import json
from typing import Any

import pytest

from tests.smoke.test_gateway import _kubectl
from tests.target import REPO
from ticketscope.jobs.eval.main import RESULTS_PREFIX

EVAL_JOB = "ticketscope-eval"
RESULTS_PATH = REPO / "reports" / "eval-results.json"


def eval_log() -> str:
    """The log of the eval Job's Succeeded pod (newest if several)."""
    pods = _kubectl(
        "get",
        "pod",
        "-l",
        f"job-name={EVAL_JOB}",
        "--field-selector",
        "status.phase=Succeeded",
        "--sort-by",
        ".metadata.creationTimestamp",
        "-o",
        "jsonpath={.items[*].metadata.name}",
    ).split()
    assert pods, f"no Succeeded {EVAL_JOB} pod"
    return _kubectl("logs", pods[-1])


def results_from_log(log: str) -> dict[str, Any]:
    """The JSON after `RESULTS_PREFIX` on the one results line (JSON-formatted or plain)."""
    found: list[str] = []
    for line in log.splitlines():
        message = line
        try:
            record = json.loads(line)
        except ValueError:
            record = None
        if isinstance(record, dict) and isinstance(record.get("message"), str):
            message = record["message"]
        if message.startswith(RESULTS_PREFIX):
            found.append(message.removeprefix(RESULTS_PREFIX))
    assert len(found) == 1, f"expected one results line in the {EVAL_JOB} log, got {len(found)}"
    return json.loads(found[0])


@pytest.fixture(scope="session")
def eval_results() -> dict[str, Any]:
    results = results_from_log(eval_log())
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return results
