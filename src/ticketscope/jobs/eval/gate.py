"""The eval gate: fail a PR whose retrieval scores drop below the committed baseline.

`check` is a pure function over two results documents (the shape `jobs.eval.main` logs) and
a flag saying whether the same diff changes the baseline. Recall@10 and MRR@10 are gated per
mode and per kind (short, log_heavy, overall) with an inclusive absolute tolerance; Recall@1/5
and p95 latency are reported, never gated. A changed baseline stands in for a human decision
to accept a drop, so it must equal this run's results. The CLI finds that diff against the PR
base commit and appends the report to `$GITHUB_STEP_SUMMARY`.
"""

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from ticketscope.jobs.eval.score import KINDS as SCORED_KINDS

BASELINE_PATH = "eval/baseline.json"
TOLERANCE = Decimal("0.005")
GATED_METRICS = ("recall@10", "mrr@10")
REPORTED_METRICS = ("recall@1", "recall@5", "p95_latency_ms")
KINDS = (*SCORED_KINDS, "overall")
LINEAGE_FIELDS = ("snapshot_version", "embedding_model_id", "preprocessing_version")
LOG_HEAVY_FLOOR = 200

Doc = Mapping[str, Any]


def _lineage_value(field: str, value: Any) -> Any:
    """Null, "none" and "" are the same embedding model id (keyword has none)."""
    if field == "embedding_model_id" and (
        value is None or str(value).strip().lower() in ("", "none")
    ):
        return None
    return value


def _number(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return Decimal(str(round(float(value), 6)))


def _dict(value: Any) -> dict[str, Any]:
    """`value` as a dict, or an empty one when it is not an object."""
    return cast("dict[str, Any]", value) if isinstance(value, Mapping) else {}


def _modes(doc: Doc) -> dict[str, Any]:
    return _dict(doc.get("modes"))


def _metric(doc: Doc, mode: str, kind: str, metric: str) -> Decimal | None:
    return _number(_dict(_dict(_modes(doc).get(mode)).get(kind)).get(metric))


def _floor_decision_problem(baseline: Doc) -> str | None:
    """None when `kind_floor_decision` is absent or complete; else what is wrong with it."""
    if "kind_floor_decision" not in baseline:
        return None
    raw = baseline["kind_floor_decision"]
    if not isinstance(raw, Mapping):
        return "kind_floor_decision is not an object with a date and a reason"
    decision = _dict(raw)
    missing = [
        key
        for key in ("date", "reason")
        if not isinstance(decision.get(key), str) or not str(decision[key]).strip()
    ]
    if missing:
        return f"kind_floor_decision is missing {' and '.join(missing)}"
    return None


def check(baseline: Doc, results: Doc, baseline_changed: bool) -> tuple[list[str], list[str]]:
    """Compare a run to the baseline: (failure lines, report lines). No failures means pass."""
    failures: list[str] = []
    report: list[str] = ["### Eval gate", ""]
    base_modes = _modes(baseline)
    run_modes = _modes(results)

    problem = _floor_decision_problem(baseline)
    if problem:
        failures.append(f"baseline: {problem}")

    # Lineage: a changed baseline is allowed to move it, and is checked for equality below.
    base_lineage = _dict(baseline.get("lineage"))
    run_lineage = _dict(results.get("lineage"))
    for field in LINEAGE_FIELDS:
        want = _lineage_value(field, base_lineage.get(field))
        got = _lineage_value(field, run_lineage.get(field))
        if want != got:
            failures.append(
                f"lineage {field}: baseline {want!r}, run {got!r}"
                + (" (changed baseline does not equal this run)" if baseline_changed else "")
            )

    # Kind floor, on the run.
    decided = "kind_floor_decision" in baseline and problem is None
    for mode in sorted(run_modes):
        count = _dict(_dict(run_modes[mode]).get("log_heavy")).get("pairs_scored")
        short = not isinstance(count, int) or count < LOG_HEAVY_FLOOR
        if short and not decided:
            failures.append(
                f"mode {mode}, kind log_heavy: pairs_scored {count} is below the floor of "
                f"{LOG_HEAVY_FLOOR} and the baseline has no dated kind_floor_decision"
            )

    # Modes.
    for mode in sorted(base_modes):
        if mode not in run_modes:
            suffix = " (changed baseline still lists it)" if baseline_changed else ""
            failures.append(f"mode {mode}: in the baseline but missing from this run{suffix}")
    new_modes = sorted(set(run_modes) - set(base_modes))
    for mode in new_modes:
        report.append(f"New mode {mode}: not in the baseline, not gated.")

    # Metrics.
    rows = ["| mode | kind | metric | baseline | run | delta |", "|---|---|---|---|---|---|"]
    for mode in sorted(set(base_modes) & set(run_modes)):
        for kind in KINDS:
            for metric in (*GATED_METRICS, *REPORTED_METRICS):
                want = _metric(baseline, mode, kind, metric)
                got = _metric(results, mode, kind, metric)
                if want is None or got is None:
                    if metric in GATED_METRICS:
                        failures.append(f"mode {mode}, kind {kind}, metric {metric}: missing")
                    continue
                delta = got - want
                gated = metric in GATED_METRICS
                rows.append(
                    f"| {mode} | {kind} | {metric}{'' if gated else ' (reported)'} "
                    f"| {want} | {got} | {delta:+} |"
                )
                if not gated:
                    continue
                if baseline_changed:
                    if abs(delta) > TOLERANCE:
                        failures.append(
                            f"mode {mode}, kind {kind}, metric {metric}: changed baseline {want} "
                            f"differs from this run {got} by more than {TOLERANCE}"
                        )
                elif -delta > TOLERANCE:
                    failures.append(
                        f"mode {mode}, kind {kind}, metric {metric}: dropped {-delta} "
                        f"({want} to {got}), over the {TOLERANCE} tolerance"
                    )
    report += ["", *rows, ""]
    if baseline_changed:
        report.append("The baseline is updated in this diff and is checked against this run.")
    report.append("FAILED" if failures else "PASSED")
    if failures:
        report += ["", *(f"- {line}" for line in failures)]
    return failures, report


def baseline_updated(base_sha: str, repo: Path | None = None) -> bool:
    """True when HEAD changes `eval/baseline.json` against `base_sha`. Raises if git cannot say."""
    done = subprocess.run(
        ["git", "diff", "--name-only", base_sha, "HEAD", "--", BASELINE_PATH],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        raise RuntimeError(f"cannot diff against base {base_sha!r}: {done.stderr.strip()}")
    return BASELINE_PATH in done.stdout.split()


def baseline_existed(base_sha: str, repo: Path | None = None) -> bool:
    """True when `base_sha` already carries `eval/baseline.json`. Raises if git cannot say."""
    done = subprocess.run(
        ["git", "ls-tree", "--name-only", base_sha, "--", BASELINE_PATH],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        raise RuntimeError(f"cannot read base {base_sha!r}: {done.stderr.strip()}")
    return BASELINE_PATH in done.stdout.split()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate eval results against the baseline.")
    parser.add_argument("--baseline", type=Path, default=Path(BASELINE_PATH))
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--base-sha", default="")
    args = parser.parse_args(argv)

    def emit(lines: Sequence[str]) -> None:
        text = "\n".join(lines) + "\n"
        print(text)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as handle:
                handle.write(text)

    if not args.baseline.is_file():
        # "No baseline" is only for a repo that never had one: deleting it must not open the gate.
        if args.base_sha:
            try:
                existed = baseline_existed(args.base_sha)
            except RuntimeError as error:
                print(f"eval gate: {error}", file=sys.stderr)
                return 1
            if existed:
                emit(
                    [
                        "### Eval gate",
                        "",
                        "FAILED",
                        "",
                        f"- {args.baseline} was deleted in this diff",
                    ]
                )
                return 1
        emit(["### Eval gate", "", f"No baseline at {args.baseline}: nothing to compare, passing."])
        return 0
    if not args.base_sha:
        print("eval gate: --base-sha is required when a baseline exists", file=sys.stderr)
        return 1
    try:
        changed = baseline_updated(args.base_sha)
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        results = json.loads(args.results.read_text(encoding="utf-8"))
    except (OSError, ValueError, RuntimeError) as error:
        print(f"eval gate: {error}", file=sys.stderr)
        return 1
    failures, report = check(baseline, results, changed)
    emit(report)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
