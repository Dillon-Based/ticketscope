"""The eval gate (story 2.3, risk R-003): the decision table, mode-set cases, the CLI and
diff detection on a temporary git repository."""

import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from ticketscope.jobs.eval import gate

LINEAGE = {
    "snapshot_version": "2026.11.1",
    "embedding_model_id": None,
    "preprocessing_version": "p1",
}


def _kind(recall: float, mrr: float, pairs: int = 300) -> dict[str, Any]:
    return {
        "recall@1": 0.2,
        "recall@5": 0.4,
        "recall@10": recall,
        "mrr@10": mrr,
        "p95_latency_ms": 10.0,
        "pairs_scored": pairs,
    }


def _mode(recall: float = 0.5, mrr: float = 0.3, log_pairs: int = 300) -> dict[str, Any]:
    return {
        "short": _kind(recall, mrr, 9000),
        "log_heavy": _kind(recall, mrr, log_pairs),
        "overall": _kind(recall, mrr, 9000 + log_pairs),
    }


def _doc(**modes: dict[str, Any]) -> dict[str, Any]:
    return {"modes": modes or {"keyword": _mode()}, "lineage": dict(LINEAGE)}


def _run(baseline: dict[str, Any], results: dict[str, Any], changed: bool = False) -> list[str]:
    return gate.check(baseline, results, changed)[0]


def test_identical_run_passes_and_reports() -> None:
    failures, report = gate.check(_doc(), _doc(), False)
    assert failures == []
    assert "PASSED" in report


def test_log_heavy_recall_drop_of_0_006_fails_naming_mode_kind_metric() -> None:
    run = _doc()
    run["modes"]["keyword"]["log_heavy"]["recall@10"] = 0.494
    (failure,) = _run(_doc(), run)
    assert "keyword" in failure and "log_heavy" in failure and "recall@10" in failure


@pytest.mark.parametrize(("before", "after", "fails"), [(0.400, 0.395, False), (0.5, 0.4949, True)])
def test_tolerance_is_inclusive_and_float_safe(before: float, after: float, fails: bool) -> None:
    base, run = _doc(), _doc()
    base["modes"]["keyword"]["short"]["recall@10"] = before
    run["modes"]["keyword"]["short"]["recall@10"] = after
    assert bool(_run(base, run)) is fails


def test_overall_rise_does_not_hide_log_heavy_mrr_drop() -> None:
    run = _doc()
    run["modes"]["keyword"]["overall"]["mrr@10"] = 0.4
    run["modes"]["keyword"]["log_heavy"]["mrr@10"] = 0.294
    (failure,) = _run(_doc(), run)
    assert "log_heavy" in failure and "mrr@10" in failure


def test_recall_1_5_and_p95_are_reported_never_gated() -> None:
    run = _doc()
    for kind in gate.KINDS:
        row = run["modes"]["keyword"][kind]
        row["recall@1"] -= 0.1
        row["recall@5"] -= 0.1
        row["p95_latency_ms"] *= 100
    failures, report = gate.check(_doc(), run, False)
    assert failures == []
    assert any("p95_latency_ms (reported)" in line for line in report)


def test_any_drop_passes_when_baseline_changed_and_equals_run() -> None:
    run = _doc(keyword=_mode(recall=0.3, mrr=0.1))
    assert _run(run, copy.deepcopy(run), changed=True) == []


def test_hand_edited_baseline_that_differs_from_run_fails() -> None:
    edited = _doc(keyword=_mode(recall=0.6))
    assert _run(edited, _doc(), changed=True)
    assert _run(_doc(keyword=_mode(recall=0.504)), _doc(), changed=True) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("snapshot_version", "2026.12.1"),
        ("embedding_model_id", "bge-small"),
        ("preprocessing_version", "p2"),
    ],
)
def test_lineage_drift_fails_naming_the_field(field: str, value: str) -> None:
    run = _doc()
    run["lineage"][field] = value
    (failure,) = _run(_doc(), run)
    assert field in failure
    assert _run(run, run, changed=True) == []


@pytest.mark.parametrize("other", [None, "none", ""])
def test_null_none_and_empty_embedding_ids_match(other: str | None) -> None:
    base, run = _doc(), _doc()
    base["lineage"]["embedding_model_id"] = None
    run["lineage"]["embedding_model_id"] = other
    assert _run(base, run) == []


def test_missing_gated_mode_fails_unless_baseline_changed() -> None:
    base = _doc(keyword=_mode(), dense=_mode())
    run = _doc(keyword=_mode())
    (failure,) = _run(base, run)
    assert "dense" in failure
    assert _run(_doc(keyword=_mode()), run, changed=True) == []


def test_new_mode_passes_and_is_reported() -> None:
    failures, report = gate.check(_doc(), _doc(keyword=_mode(), dense=_mode(0.1, 0.1)), False)
    assert failures == []
    assert any("dense" in line for line in report)


def test_log_heavy_floor() -> None:
    low = _doc(keyword=_mode(log_pairs=199))
    (failure,) = _run(_doc(), low)
    assert "log_heavy" in failure and "keyword" in failure
    assert _run(_doc(), _doc(keyword=_mode(log_pairs=200))) == []
    decided = _doc()
    decided["kind_floor_decision"] = {"date": "2026-11-08", "reason": "thin log-heavy margin"}
    assert _run(decided, low) == []


@pytest.mark.parametrize(
    "decision",
    [{"date": "2026-11-08"}, {"reason": "r"}, {"date": "", "reason": "r"}, "yes"],
)
def test_incomplete_floor_decision_fails(decision: Any) -> None:
    base = _doc()
    base["kind_floor_decision"] = decision
    assert _run(base, _doc(keyword=_mode(log_pairs=199)))


def _write(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    _write(tmp_path / "eval" / "baseline.json", _doc())
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def test_baseline_updated_detects_a_change_against_the_base(repo: Path) -> None:
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "a.txt").write_text("b", encoding="utf-8")
    _git(repo, "commit", "-qam", "unrelated")
    assert gate.baseline_updated(base, repo) is False
    _write(repo / "eval" / "baseline.json", _doc(keyword=_mode(0.1, 0.1)))
    _git(repo, "commit", "-qam", "baseline")
    assert gate.baseline_updated(base, repo) is True


def test_baseline_updated_fails_loudly_when_the_base_is_unavailable(repo: Path) -> None:
    with pytest.raises(RuntimeError, match="cannot diff"):
        gate.baseline_updated("0" * 40, repo)


def test_cli_without_a_baseline_passes_with_a_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(tmp_path / "results.json", _doc())
    code = gate.main(
        ["--baseline", str(tmp_path / "none.json"), "--results", str(tmp_path / "results.json")]
    )
    assert code == 0
    assert "No baseline" in capsys.readouterr().out


def test_cli_fails_on_regression_and_writes_the_step_summary(
    repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base = _git(repo, "rev-parse", "HEAD")
    results = tmp_path / "results.json"
    _write(results, _doc(keyword=_mode(recall=0.4)))
    summary = tmp_path / "summary.md"
    monkeypatch.chdir(repo)
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    argv = ["--baseline", "eval/baseline.json", "--results", str(results), "--base-sha", base]
    assert gate.main(argv) == 1
    assert "recall@10" in summary.read_text(encoding="utf-8")
    # The same PR also updates the baseline to its run: passes.
    _write(repo / "eval" / "baseline.json", json.loads(results.read_text(encoding="utf-8")))
    _git(repo, "commit", "-qam", "update baseline")
    assert gate.main(argv) == 0


def test_cli_fails_when_the_baseline_was_deleted_in_the_diff(
    repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "rm", "-q", "eval/baseline.json")
    _git(repo, "commit", "-qm", "delete baseline")
    _write(tmp_path / "results.json", _doc())
    monkeypatch.chdir(repo)
    argv = ["--results", str(tmp_path / "results.json"), "--base-sha", base]
    assert gate.main(argv) == 1


def test_cli_fails_when_the_base_commit_is_unavailable(
    repo: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _write(tmp_path / "results.json", _doc())
    monkeypatch.chdir(repo)
    argv = ["--results", str(tmp_path / "results.json"), "--base-sha", "0" * 40]
    assert gate.main(argv) == 1


def test_a_regressed_dense_ranking_fails_once_dense_is_in_the_baseline() -> None:
    base = _doc(keyword=_mode(), dense=_mode(0.8, 0.6), hybrid=_mode(0.82, 0.62))
    run = _doc(keyword=_mode(), dense=_mode(0.8, 0.5), hybrid=_mode(0.82, 0.62))
    failures = _run(base, run)
    assert failures and all("mode dense" in f and "mrr@10" in f for f in failures)
    assert _run(base, run, changed=True) != []  # a changed baseline must equal the run
    assert _run(run, run, changed=True) == []
