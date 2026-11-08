"""[P1] scripts/render_readme_table.py keeps the README results table equal to its render of
eval/baseline.json (epic 2 story 4, risk R-004)."""

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests.target import REPO


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "render_readme_table", REPO / "scripts" / "render_readme_table.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rt = _load()

START, END = rt.START, rt.END


def _cell(pairs: int = 10, value: float = 0.5) -> dict[str, Any]:
    return {
        "pairs_scored": pairs,
        "recall@1": value,
        "recall@5": value,
        "recall@10": value,
        "mrr@10": value,
        "p95_latency_ms": 12.0,
    }


def _results(*modes: str) -> dict[str, Any]:
    return {
        "lineage": {"snapshot_version": "2026.11.1"},
        "modes": {m: {k: _cell() for k in ("short", "log_heavy", "overall")} for m in modes},
    }


def _readme(section: str = "") -> str:
    return f"# T\n\n{START}\n{section}{END}\n\ntail\n"


def _files(tmp_path: Path, results: dict[str, Any], readme: str) -> tuple[Path, Path]:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps(results), encoding="utf-8")
    path = tmp_path / "README.md"
    path.write_text(readme, encoding="utf-8")
    return baseline, path


def _run(baseline: Path, readme: Path, *flags: str) -> int:
    return int(rt.main(["--baseline", str(baseline), "--readme", str(readme), *flags]))


def test_committed_readme_equals_render_of_committed_baseline() -> None:
    baseline = json.loads((REPO / "eval" / "baseline.json").read_text(encoding="utf-8"))
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert rt.extract(readme) == rt.render(baseline)
    assert rt.main([]) == 0


def test_write_then_check_passes_and_write_is_idempotent(tmp_path: Path) -> None:
    baseline, readme = _files(tmp_path, _results("keyword"), _readme())
    assert _run(baseline, readme, "--check") == 1  # empty section differs
    assert _run(baseline, readme, "--write") == 0
    written = readme.read_text(encoding="utf-8")
    assert _run(baseline, readme) == 0
    assert _run(baseline, readme, "--write") == 0
    assert readme.read_text(encoding="utf-8") == written
    assert written.startswith("# T\n\n") and written.endswith("\ntail\n")


def test_hand_edited_number_fails_and_names_the_fix(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline, readme = _files(tmp_path, _results("keyword"), _readme())
    _run(baseline, readme, "--write")
    text = readme.read_text(encoding="utf-8")
    readme.write_text(text.replace("0.500", "0.501", 1), encoding="utf-8")
    assert _run(baseline, readme) == 1
    err = capsys.readouterr().err
    assert "differs" in err and "--write" in err


@pytest.mark.parametrize(
    "text",
    [
        f"x\n{END}\n",
        f"x\n{START}\n",
        "no markers\n",
        f"{START}\n{START}\n{END}\n",
        f"{START}\n{END}\n{END}\n",
        f"{END}\n{START}\n",
    ],
)
def test_marker_faults_fail_check_and_write(tmp_path: Path, text: str) -> None:
    baseline, readme = _files(tmp_path, _results("keyword"), text)
    assert _run(baseline, readme, "--check") == 1
    assert _run(baseline, readme, "--write") == 1
    assert readme.read_text(encoding="utf-8") == text


def test_missing_marker_error_names_the_marker() -> None:
    with pytest.raises(rt.RenderError, match="eval-results:end"):
        rt.extract(f"{START}\n")


def test_check_detects_line_ending_drift_and_write_preserves_surroundings(tmp_path: Path) -> None:
    baseline, readme = _files(tmp_path, _results("keyword"), _readme())
    section = rt.render(_results("keyword")).encode("utf-8")
    prefix = f"# T\r\n\r\n{START}\n".encode()
    suffix = f"{END}\r\n\r\ntail\r\n".encode()
    expected = prefix + section + suffix
    readme.write_bytes(expected)
    assert _run(baseline, readme, "--check") == 0
    readme.write_bytes(prefix + section.replace(b"\n", b"\r\n", 1) + suffix)
    assert _run(baseline, readme, "--check") == 1
    assert _run(baseline, readme, "--write") == 0
    assert readme.read_bytes() == expected
    assert _run(baseline, readme, "--check") == 0


def test_extra_mode_adds_rows_sorted_by_name_without_code_change() -> None:
    out = rt.render(_results("keyword", "dense"))
    rows = [line for line in out.splitlines() if line.startswith("| ") and "---" not in line][1:]
    assert [r.split(" | ")[:2] for r in rows] == [
        ["| dense", "short"],
        ["| dense", "log_heavy"],
        ["| dense", "overall"],
        ["| keyword", "short"],
        ["| keyword", "log_heavy"],
        ["| keyword", "overall"],
    ]
    assert out.endswith("|\n") and not out.endswith("\n\n")
    assert out.startswith("Snapshot version: 2026.11.1\n")


@pytest.mark.parametrize(
    ("value", "text"), [(0.0005, "0.001"), (0.12349999, "0.123"), (1, "1.000"), (0.5, "0.500")]
)
def test_numbers_print_three_decimals_and_pairs_stay_integers(value: float, text: str) -> None:
    results = _results("keyword")
    results["modes"]["keyword"]["short"] = _cell(pairs=10164, value=value)
    row = next(r for r in rt.render(results).splitlines() if "| short |" in r)
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[2] == "10164"
    assert cells[3:7] == [text] * 4
    assert cells[7] == "12.000"
    assert rt.render(results) == rt.render(copy.deepcopy(results))


def test_missing_kind_or_metric_exits_1_naming_mode_and_key(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    no_kind = _results("keyword")
    del no_kind["modes"]["keyword"]["log_heavy"]
    baseline, readme = _files(tmp_path, no_kind, _readme())
    assert _run(baseline, readme) == 1
    err = capsys.readouterr().err
    assert "keyword" in err and "log_heavy" in err

    no_metric = _results("keyword")
    del no_metric["modes"]["keyword"]["overall"]["recall@10"]
    baseline, readme = _files(tmp_path, no_metric, _readme())
    assert _run(baseline, readme, "--write") == 1
    err = capsys.readouterr().err
    assert "keyword" in err and "recall@10" in err


def test_ci_checks_job_runs_the_readme_check() -> None:
    from tests.unit.test_eval_workflow import CI, _block

    text = CI.read_text(encoding="utf-8")
    checks = _block(_block(text, "jobs", 0), "checks", 2)
    assert "run: python3 scripts/render_readme_table.py --check" in checks
