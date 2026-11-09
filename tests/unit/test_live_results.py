"""[P1] scripts/live_results.py turns a CI run into trace live-verification results."""

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.target import REPO


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "live_results", REPO / "scripts" / "live_results.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve annotations through sys.modules
    spec.loader.exec_module(module)
    return module


live_results = _load()


def _junit(path: Path, cases: list[tuple[str, str, str, list[str]]]) -> Path:
    """cases: (classname, name, outcome, criteria)."""
    body = []
    for classname, name, outcome, criteria in cases:
        props = "".join(f'<property name="criterion" value="{c}" />' for c in criteria)
        inner = f"<properties>{props}</properties>" if props else ""
        if outcome == "failed":
            inner += '<failure message="boom" />'
        elif outcome == "skipped":
            inner += '<skipped message="nope" />'
        body.append(f'<testcase classname="{classname}" name="{name}">{inner}</testcase>')
    path.write_text(
        f"<testsuites><testsuite>{''.join(body)}</testsuite></testsuites>", encoding="utf-8"
    )
    return path


NEEDS_OK = {
    "checks": "success",
    "charts": "success",
    "images": "skipped",
    "integrated-check": "success",
}
FIT = {"peak_memory_mib": "4164", "free_disk": "76G", "kind_up_to_api_ready_seconds": "229"}


@pytest.fixture
def reports(tmp_path: Path) -> dict[str, list[object]]:
    unit = _junit(
        tmp_path / "unit.xml",
        [
            ("tests.unit.test_telemetry", "test_spans", "passed", []),
            ("tests.unit.test_x", "test_y", "passed", []),
        ],
    )
    kind = _junit(
        tmp_path / "kind.xml",
        [
            (
                "tests.smoke.test_gateway",
                "test_on_demand_backup_completes_to_seaweedfs",
                "passed",
                [],
            ),
            ("tests.smoke.test_gateway", "test_logs", "passed", ["ticketscope--e1-s9--AC-3"]),
        ],
    )
    upgrade = _junit(
        tmp_path / "kind-upgrade.xml",
        [
            (
                "tests.smoke.test_gateway",
                "test_load_log_has_the_report",
                "passed",
                ["ticketscope--e1-s9--AC-3"],
            )
        ],
    )
    return {p.name: live_results.read_junit(p) for p in (unit, kind, upgrade)}


def _by_criterion(results: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {r["requirement_id"]: r for r in results}


def test_a_green_run_passes_every_run_level_criterion_and_skips_unbuilt_images(
    reports: dict[str, list[object]],
) -> None:
    results = _by_criterion(live_results.build_results(reports, NEEDS_OK, FIT, "https://run"))
    for local in (
        "s1--AC-1",
        "s1--AC-4",
        "s8--AC-1",
        "s9--AC-2",
        "s10--AC-2",
        "s11--AC-3",
        "s10--AC-4",
        "s9--AC-3",
    ):
        assert results[f"ticketscope--e1-{local}"]["status"] == "pass", local
    assert results["ticketscope--e1-s1--AC-2"]["status"] == "skipped"
    assert all(r["evidence"].startswith("https://run") for r in results.values())


def test_ids_are_unique_and_sequential(reports: dict[str, list[object]]) -> None:
    results = live_results.build_results(reports, NEEDS_OK, FIT, "https://run")
    assert [r["id"] for r in results] == [
        f"ticketscope--e1-LIVE-{n:03d}" for n in range(1, len(results) + 1)
    ]


def test_a_failed_tagged_case_fails_its_criterion(tmp_path: Path) -> None:
    kind = _junit(
        tmp_path / "kind.xml",
        [("t", "a", "passed", ["X--AC-1"]), ("t", "b", "failed", ["X--AC-1"])],
    )
    results = _by_criterion(
        live_results.build_results({"kind.xml": live_results.read_junit(kind)}, NEEDS_OK, None, "u")
    )
    assert results["X--AC-1"]["status"] == "fail"
    assert results["ticketscope--e1-s8--AC-1"]["status"] == "fail"


def test_a_failed_job_fails_the_run_level_criteria(reports: dict[str, list[object]]) -> None:
    results = _by_criterion(
        live_results.build_results(reports, {**NEEDS_OK, "checks": "failure"}, FIT, "u")
    )
    for local in ("s1--AC-1", "s8--AC-1", "s9--AC-2", "s10--AC-2", "s11--AC-3"):
        assert results[f"ticketscope--e1-{local}"]["status"] == "fail", local


def test_missing_evidence_is_left_out_not_guessed(tmp_path: Path) -> None:
    results = _by_criterion(live_results.build_results({}, {"images": "skipped"}, None, "u"))
    assert set(results) == {"ticketscope--e1-s1--AC-2"}


def test_a_skipped_kind_deploy_is_recorded_as_skipped_not_left_out(
    reports: dict[str, list[object]],
) -> None:
    only_unit = {"unit.xml": reports["unit.xml"]}
    needs = {**NEEDS_OK, "integrated-check": "skipped"}
    results = _by_criterion(live_results.build_results(only_unit, needs, None, "https://run"))
    assert results["ticketscope--e1-s1--AC-1"]["status"] == "skipped"
    assert "kind deploy skipped" in results["ticketscope--e1-s1--AC-1"]["evidence"]
    # A kind job that failed before it wrote a report is not turned into a skip.
    failed = {**NEEDS_OK, "integrated-check": "failure"}
    assert "ticketscope--e1-s1--AC-1" not in _by_criterion(
        live_results.build_results(only_unit, failed, None, "u")
    )


def test_runner_fit_without_ready_time_fails(reports: dict[str, list[object]]) -> None:
    fit = {**FIT, "kind_up_to_api_ready_seconds": "n/a"}
    results = _by_criterion(live_results.build_results(reports, NEEDS_OK, fit, "u"))
    assert results["ticketscope--e1-s1--AC-4"]["status"] == "fail"


def test_integrated_cases_in_the_default_run_fail_deselection(tmp_path: Path) -> None:
    unit = _junit(
        tmp_path / "unit.xml", [("tests.integrated.test_done_when", "test_x", "passed", [])]
    )
    results = _by_criterion(
        live_results.build_results({"unit.xml": live_results.read_junit(unit)}, NEEDS_OK, None, "u")
    )
    assert results["ticketscope--e1-s11--AC-3"]["status"] == "fail"


def test_main_writes_a_manifest_trace_can_read(
    tmp_path: Path, reports: dict[str, list[object]]
) -> None:
    folder = tmp_path / "reports"
    folder.mkdir()
    _junit(folder / "unit.xml", [("tests.unit.test_telemetry", "test_spans", "passed", [])])
    (folder / "runner-fit.json").write_text(json.dumps(FIT), encoding="utf-8")
    out = tmp_path / "live.json"
    needs = json.dumps({k: {"result": v} for k, v in NEEDS_OK.items()})
    assert (
        live_results.main(
            [
                "--sha",
                "e2c04e5",
                "--run-url",
                "u",
                "--needs",
                needs,
                "--reports",
                str(folder),
                "--out",
                str(out),
            ]
        )
        == 0
    )
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["schema_version"].split(".")[0] == "0"
    assert manifest["source_sha"] == "e2c04e5"
    assert {r["status"] for r in manifest["results"]} <= {"pass", "fail", "blocked", "skipped"}
