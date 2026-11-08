"""Expanded coverage for story 2.4: malformed baselines, CLI behaviour, marker edge cases."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.target import REPO
from tests.unit.test_readme_table import END, START, _files, _readme, _results, _run, rt

SCRIPT = REPO / "scripts" / "render_readme_table.py"


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def test_cli_check_passes_on_committed_files_and_fails_on_drift(tmp_path: Path) -> None:
    ok = _cli()
    assert ok.returncode == 0 and "matches" in ok.stdout
    baseline, readme = _files(tmp_path, _results("keyword"), _readme("stale\n"))
    bad = _cli("--baseline", str(baseline), "--readme", str(readme))
    assert bad.returncode == 1 and "--write" in bad.stderr and bad.stdout == ""


def test_cli_write_then_check_roundtrip(tmp_path: Path) -> None:
    baseline, readme = _files(tmp_path, _results("keyword", "hybrid"), _readme())
    args = ("--baseline", str(baseline), "--readme", str(readme))
    assert _cli(*args, "--write").returncode == 0
    assert _cli(*args, "--check").returncode == 0
    assert "| hybrid | overall |" in readme.read_text(encoding="utf-8")


def test_check_and_write_are_mutually_exclusive() -> None:
    assert _cli("--check", "--write").returncode == 2


def test_missing_and_invalid_inputs_exit_1_without_traceback(tmp_path: Path) -> None:
    baseline, readme = _files(tmp_path, _results("keyword"), _readme())
    missing = _cli("--baseline", str(tmp_path / "nope.json"), "--readme", str(readme))
    assert missing.returncode == 1 and "Traceback" not in missing.stderr
    baseline.write_text("{not json", encoding="utf-8")
    broken = _cli("--baseline", str(baseline), "--readme", str(readme), "--write")
    assert broken.returncode == 1 and "Traceback" not in broken.stderr
    assert readme.read_text(encoding="utf-8") == _readme()
    gone = _cli("--baseline", str(baseline), "--readme", str(tmp_path / "none.md"))
    assert gone.returncode == 1


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.pop("lineage"),
        lambda r: r.update(lineage=None),
        lambda r: r.update(lineage={}),
        lambda r: r.pop("modes"),
        lambda r: r.update(modes=[]),
        lambda r: r["modes"].update(keyword=None),
    ],
)
def test_structurally_invalid_baseline_raises_render_error(mutate: Any) -> None:
    results = _results("keyword")
    mutate(results)
    with pytest.raises(rt.RenderError):
        rt.render(results)


@pytest.mark.parametrize("bad", [True, "0.5", None, [0.5]])
def test_non_numeric_metric_values_are_rejected(bad: Any) -> None:
    results = _results("keyword")
    results["modes"]["keyword"]["short"]["mrr@10"] = bad
    with pytest.raises(rt.RenderError, match="mrr@10"):
        rt.render(results)


@pytest.mark.parametrize("bad", [10.0, 10.5, True, "10"])
def test_pairs_scored_must_be_an_integer(bad: Any) -> None:
    results = _results("keyword")
    results["modes"]["keyword"]["short"]["pairs_scored"] = bad
    with pytest.raises(rt.RenderError, match="pairs_scored"):
        rt.render(results)


def test_extra_keys_and_kinds_in_baseline_are_ignored() -> None:
    results = _results("keyword")
    results["k"] = 10
    results["modes"]["keyword"]["extra_kind"] = {"junk": 1}
    results["modes"]["keyword"]["short"]["first_member_ranks"] = [[1, None]]
    assert rt.render(results) == rt.render(_results("keyword"))


def test_render_row_count_is_modes_times_three() -> None:
    out = rt.render(_results("a", "b", "c"))
    body = [ln for ln in out.splitlines() if ln.startswith("| ")]
    assert len(body) == 2 + 9  # header + separator + rows


def test_splice_preserves_text_outside_markers_and_handles_missing_newline() -> None:
    inline = f"head\n{START}old{END}\ntail\n"
    out = rt.splice(inline, "NEW\n")
    assert out.startswith("head\n") and out.endswith("tail\n")
    assert rt.extract(out) == "NEW\n"
    assert rt.splice(out, "NEW\n") == out


def test_unicode_outside_markers_survives_write(tmp_path: Path) -> None:
    text = "# Tïtle\n\n" + f"{START}\n{END}\n" + "ünïcode tail\n"
    baseline = tmp_path / "b.json"
    baseline.write_text(json.dumps(_results("keyword")), encoding="utf-8")
    readme = tmp_path / "R.md"
    readme.write_bytes(text.encode("utf-8"))
    assert _run(baseline, readme, "--write") == 0
    data = readme.read_bytes().decode("utf-8")
    assert data.startswith("# Tïtle\n\n") and data.endswith("ünïcode tail\n")


def test_committed_readme_has_each_marker_exactly_once_in_order() -> None:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    assert text.count(START) == 1 and text.count(END) == 1
    assert text.index(START) < text.index(END)


def test_committed_readme_lists_every_baseline_mode_and_kind() -> None:
    baseline = json.loads((REPO / "eval" / "baseline.json").read_text(encoding="utf-8"))
    section = rt.extract((REPO / "README.md").read_text(encoding="utf-8"))
    for mode in baseline["modes"]:
        for kind in ("short", "log_heavy", "overall"):
            assert f"| {mode} | {kind} |" in section
    assert baseline["lineage"]["snapshot_version"] in section
