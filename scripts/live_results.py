#!/usr/bin/env python3
"""Turn one CI run into trace live-verification results (bmad-tea-trace input).

    python3 scripts/live_results.py --sha <commit> --run-url <url> --needs '<toJSON(needs)>' \
        --reports <dir> --out live-verification-results.json

Reads the JUnit files and `runner-fit.json` the CI jobs upload into `<dir>`, plus each
job's result, and writes one result per acceptance criterion the run establishes:

- tests tagged `@pytest.mark.criterion(...)` (see tests/conftest.py): pass when every
  tagged case passed, fail when any failed, skipped when any was skipped;
- criteria about the CI run itself (story 1 AC-1/2/4, story 8 AC-1, story 9 AC-2,
  story 10 AC-2/4, story 11 AC-3), from job results and named reports.

Only observations go in: a criterion whose evidence is missing from the run is left out,
never guessed. Standard library only, so CI runs it without installing the project.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

EPIC = "ticketscope--e1"
SCHEMA_VERSION = "0.1.0"


@dataclass
class Case:
    report: str
    classname: str
    name: str
    outcome: str  # passed | failed | skipped
    criteria: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.classname}::{self.name}"


def read_junit(path: Path) -> list[Case]:
    cases: list[Case] = []
    for testcase in ET.parse(path).getroot().iter("testcase"):
        if testcase.find("failure") is not None or testcase.find("error") is not None:
            outcome = "failed"
        elif testcase.find("skipped") is not None:
            outcome = "skipped"
        else:
            outcome = "passed"
        criteria = [
            p.get("value", "")
            for p in testcase.iter("property")
            if p.get("name") == "criterion" and p.get("value")
        ]
        cases.append(
            Case(
                path.name,
                testcase.get("classname", ""),
                testcase.get("name", ""),
                outcome,
                criteria,
            )
        )
    return cases


def _status(cases: list[Case]) -> str:
    if any(c.outcome == "failed" for c in cases):
        return "fail"
    if any(c.outcome == "skipped" for c in cases):
        return "skipped"
    return "pass"


def _summary(cases: list[Case]) -> str:
    counts = {o: sum(c.outcome == o for c in cases) for o in ("passed", "failed", "skipped")}
    return f"{counts['passed']} passed, {counts['failed']} failed, {counts['skipped']} skipped"


def build_results(
    reports: dict[str, list[Case]],
    needs: dict[str, str],
    runner_fit: dict[str, str] | None,
    run_url: str,
) -> list[dict[str, str]]:
    """`reports` maps a JUnit file name to its cases; `needs` maps a job id to its result."""
    out: list[tuple[str, str, str, str]] = []  # criterion, title, status, evidence

    def job(name: str) -> str:
        return needs.get(name, "missing")

    # Tagged tests.
    tagged: dict[str, list[Case]] = {}
    for cases in reports.values():
        for case in cases:
            for criterion in case.criteria:
                tagged.setdefault(criterion, []).append(case)
    for criterion, cases in sorted(tagged.items()):
        names = ", ".join(f"{c.label} [{c.outcome}] ({c.report})" for c in cases)
        out.append(
            (criterion, f"tagged tests for {criterion}", _status(cases), f"{run_url} — {names}")
        )

    unit = reports.get("unit.xml")
    kind = reports.get("kind.xml")
    upgrade = reports.get("kind-upgrade.xml")
    jobs = (
        f"checks={job('checks')}, charts={job('charts')}, images={job('images')}, "
        f"integrated-check={job('integrated-check')}"
    )

    def all_ok(*names: str) -> bool:
        return all(job(n) == "success" for n in names)

    if unit is not None and kind is not None:
        ok = all_ok("checks", "integrated-check") and _status(kind) == "pass" and bool(kind)
        out.append(
            (
                f"{EPIC}-s1--AC-1",
                "PR ci.yml: ruff, pyright, pytest, lint-imports pass; "
                "_kind-deploy brings up both releases and passes smoke",
                "pass" if ok else "fail",
                f"{run_url} — {jobs}; unit: {_summary(unit)}; kind: {_summary(kind)}",
            )
        )

    elif unit is not None and kind is None and job("integrated-check") in ("skipped", "success"):
        # No kind-relevant path changed (.github/kind-paths.yml), so no cluster was deployed.
        out.append(
            (
                f"{EPIC}-s1--AC-1",
                "PR ci.yml: ruff, pyright, pytest, lint-imports pass; "
                "_kind-deploy brings up both releases and passes smoke",
                "skipped",
                f"{run_url} — {jobs}; kind deploy skipped: no path it depends on changed",
            )
        )

    images = job("images")
    if images in ("success", "failure", "skipped"):
        out.append(
            (
                f"{EPIC}-s1--AC-2",
                "images/ change builds linux/amd64 and linux/arm64",
                {"success": "pass", "failure": "fail", "skipped": "skipped"}[images],
                f"{run_url} — images job {images}"
                + (
                    " (no images/ change and not a workflow_dispatch run)"
                    if images == "skipped"
                    else ""
                ),
            )
        )

    if runner_fit is not None:
        keys = ("peak_memory_mib", "free_disk", "kind_up_to_api_ready_seconds")
        ok = all(str(runner_fit.get(k, "")).strip() not in ("", "n/a") for k in keys)
        out.append(
            (
                f"{EPIC}-s1--AC-4",
                "_kind-deploy job summary shows peak memory, free disk, "
                "kind-up to api Ready wall clock",
                "pass" if ok else "fail",
                f"{run_url} — runner fit: "
                + ", ".join(f"{k}={runner_fit.get(k, '')}" for k in keys),
            )
        )

    if kind is not None:
        backup = [c for c in kind if c.name == "test_on_demand_backup_completes_to_seaweedfs"]
        ok = (
            all_ok("checks", "charts", "integrated-check")
            and _status(kind) == "pass"
            and bool(backup)
        )
        out.append(
            (
                f"{EPIC}-s8--AC-1",
                "PR ci.yml: checks and charts pass; "
                "_kind-deploy passes every kind smoke test incl. (7)",
                "pass" if ok else "fail",
                f"{run_url} — {jobs}; kind: {_summary(kind)}; backup test (7) "
                + (backup[0].outcome if backup else "absent"),
            )
        )

    if unit is not None:
        telemetry = [c for c in unit if c.classname.endswith("test_telemetry")]
        ok = job("checks") == "success" and bool(telemetry) and _status(telemetry) == "pass"
        out.append(
            (
                f"{EPIC}-s9--AC-2",
                "ruff, ruff format, pyright, lint-imports, pytest all pass incl. test_telemetry.py",
                "pass" if ok else "fail",
                f"{run_url} — checks={job('checks')}; unit: {_summary(unit)}; "
                f"test_telemetry.py: {_summary(telemetry)}",
            )
        )
        out.append(
            (
                f"{EPIC}-s10--AC-2",
                "ruff, pyright, lint-imports, pytest pass "
                "(preprocessing_version asserted in the unit suite)",
                "pass" if job("checks") == "success" else "fail",
                f"{run_url} — checks={job('checks')}; unit: {_summary(unit)}",
            )
        )
        integrated_in_unit = [c for c in unit if c.classname.startswith("tests.integrated")]
        ok = (
            job("checks") == "success"
            and not integrated_in_unit
            and not any(c.outcome == "failed" for c in unit)
        )
        out.append(
            (
                f"{EPIC}-s11--AC-3",
                "uv run pytest without a cluster deselects the integrated module "
                "and unit tests pass",
                "pass" if ok else "fail",
                f"{run_url} — default `uv run pytest` (no cluster): {_summary(unit)}; "
                f"integrated cases collected: {len(integrated_in_unit)}",
            )
        )

    if upgrade is not None:
        report = [c for c in upgrade if c.name == "test_load_log_has_the_report"]
        ok = bool(report) and _status(upgrade) == "pass"
        out.append(
            (
                f"{EPIC}-s10--AC-4",
                "first smoke run after an in-place kind-up.sh upgrade passes (3)",
                "pass" if ok else "fail",
                f"{run_url} — after a second kind-up.sh on the same cluster, "
                f"one smoke run: {_summary(upgrade)}; "
                "test (3) " + (report[0].outcome if report else "absent"),
            )
        )

    by_criterion: dict[str, tuple[str, str, str]] = {}
    for criterion, title, status, evidence in out:
        if criterion in by_criterion:  # a tagged test and a run-level rule for one criterion
            prev = by_criterion[criterion]
            worst = (
                "fail"
                if "fail" in (prev[1], status)
                else ("skipped" if "skipped" in (prev[1], status) else "pass")
            )
            by_criterion[criterion] = (prev[0], worst, f"{prev[2]} | {evidence}")
        else:
            by_criterion[criterion] = (title, status, evidence)
    return [
        {
            "id": f"{EPIC}-LIVE-{n:03d}",
            "requirement_id": criterion,
            "title": t,
            "status": s,
            "evidence": e,
        }
        for n, (criterion, (t, s, e)) in enumerate(sorted(by_criterion.items()), start=1)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sha", required=True, help="commit the run verified")
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--needs", required=True, help="JSON of the workflow's `needs` context")
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--producer", default="GitHub Actions ci (scripts/live_results.py)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    needs = {name: str(value.get("result", "")) for name, value in json.loads(args.needs).items()}
    reports = {p.name: read_junit(p) for p in sorted(args.reports.rglob("*.xml"))}
    fit_path = next(iter(sorted(args.reports.rglob("runner-fit.json"))), None)
    runner_fit = json.loads(fit_path.read_text(encoding="utf-8")) if fit_path else None

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source_sha": args.sha,
        "observed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "producer": args.producer,
        "results": build_results(reports, needs, runner_fit, args.run_url),
    }
    args.out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    statuses = [r["status"] for r in manifest["results"]]
    print(
        f"{len(statuses)} results: "
        + ", ".join(f"{s}={statuses.count(s)}" for s in sorted(set(statuses)))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
