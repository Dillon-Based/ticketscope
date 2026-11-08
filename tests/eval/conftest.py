"""`eval_results` reads the eval Job's results line once and writes
`reports/eval-results.json` before any test that requests it asserts anything, so
`_kind-deploy.yml`'s always-run upload carries it even when a check fails (AD-17: the
cluster dies with the job). It then appends a markdown summary to `$GITHUB_STEP_SUMMARY`
when set, so the run's cost and scores show on the job page."""

import json
import os
from pathlib import Path
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


METRICS = ("recall@1", "recall@5", "recall@10", "mrr@10", "p95_latency_ms")
KIND_ROWS = ("short", "log_heavy", "overall")


def summary_markdown(results: dict[str, Any]) -> str:
    """Wall seconds, pairs by kind and each mode's per-kind metrics, as markdown."""
    lines = ["### Retrieval eval", "", f"Wall seconds: {results['wall_seconds']}", ""]
    for name, mode in sorted(results["modes"].items()):
        counts = ", ".join(f"{kind} {mode[kind]['pairs_scored']}" for kind in KIND_ROWS)
        lines += [f"**{name}** pairs: {counts}", ""]
        lines += ["| kind | " + " | ".join(METRICS) + " |", "|---|" + "---|" * len(METRICS)]
        for kind in KIND_ROWS:
            cells = " | ".join(f"{mode[kind][metric]:.4f}" for metric in METRICS)
            lines.append(f"| {kind} | {cells} |")
        lines.append("")
    skipped = ", ".join(results["skipped_modes"]) or "none"
    lines.append(f"Skipped modes: {skipped}")
    return "\n".join(lines) + "\n"


def write_job_summary(results: dict[str, Any], path: Path | None = None) -> None:
    """Append `summary_markdown` to `path`, default `$GITHUB_STEP_SUMMARY`; no-op if unset."""
    target = path or (
        Path(os.environ["GITHUB_STEP_SUMMARY"]) if "GITHUB_STEP_SUMMARY" in os.environ else None
    )
    if target is None:
        return
    with target.open("a", encoding="utf-8") as handle:
        handle.write(summary_markdown(results))


@pytest.fixture(scope="session")
def eval_results() -> dict[str, Any]:
    results = results_from_log(eval_log())
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_job_summary(results)
    return results
