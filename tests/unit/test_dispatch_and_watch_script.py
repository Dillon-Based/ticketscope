"""scripts/dispatch-and-watch.sh end to end against stub `gh`, `date` and `sleep` (story 5.11): the
run id it finds, the $GITHUB_OUTPUT hand-off, and the WATCH_JOB wait. No GitHub, no waiting."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.target import REPO

SCRIPT = REPO / "scripts" / "dispatch-and-watch.sh"

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="needs jq")

# `date -d` is GNU only; the script runs on ubuntu runners, so the stub stands in for it.
DATE = "#!/usr/bin/env bash\necho 2026-01-01T00:00:00Z\n"
SLEEP = "#!/usr/bin/env bash\nexit 0\n"
# `gh run list` prints $STUB/list (a run id, or nothing); `gh run view` prints the next state file
# of $STUB/views (one JSON per line, the last one repeats); `gh run watch` exits $STUB_WATCH_RC.
GH = r"""#!/usr/bin/env bash
echo "$*" >>"$STUB/gh-calls"
case "$1 $2" in
  "workflow run") ;;
  "run list") cat "$STUB/list" 2>/dev/null ;;
  "run watch") exit "${STUB_WATCH_RC:-0}" ;;
  "run view")
    n=$(($(cat "$STUB/n" 2>/dev/null || echo 0) + 1)); echo "$n" >"$STUB/n"
    total=$(wc -l <"$STUB/views")
    ((n > total)) && n=$total
    sed -n "${n}p" "$STUB/views" ;;
  *) echo "stub gh: unexpected $*" >&2; exit 9 ;;
esac
"""


def _run(
    tmp_path: Path,
    *args: str,
    list_out: str = "77",
    views: list[dict[str, object]] | None = None,
    watch_rc: int = 0,
    watch_job: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    stub = tmp_path / "stub"
    stub.mkdir()
    for name, body in (("gh", GH), ("date", DATE), ("sleep", SLEEP)):
        (stub / name).write_text(body, encoding="utf-8")
        (stub / name).chmod(0o755)
    (stub / "list").write_text(list_out, encoding="utf-8")
    (stub / "views").write_text("\n".join(json.dumps(v) for v in views or []) + "\n")
    out = tmp_path / "github-output"
    env = {
        **os.environ,
        "PATH": f"{stub}:{os.environ['PATH']}",
        "STUB": str(stub),
        "GH_REPO": "o/r",
        "GITHUB_OUTPUT": str(out),
        "STUB_WATCH_RC": str(watch_rc),
    }
    env.pop("WATCH_JOB", None)
    if watch_job:
        env["WATCH_JOB"] = watch_job
    done = subprocess.run(
        ["bash", str(SCRIPT), *args], capture_output=True, text=True, check=False, env=env
    )
    return done, stub


def _job(name: str, status: str, conclusion: str = "") -> dict[str, str]:
    return {"name": name, "status": status, "conclusion": conclusion}


def test_it_requires_gh_repo(tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k != "GH_REPO"}
    done = subprocess.run(
        ["bash", str(SCRIPT), "w.yml", "main"], capture_output=True, text=True, env=env, check=False
    )
    assert done.returncode != 0
    assert "GH_REPO" in done.stderr


def test_without_watch_job_it_publishes_the_run_id_and_returns_the_watch_status(
    tmp_path: Path,
) -> None:
    done, stub = _run(tmp_path, "env-up.yml", "main", "-f", "sha=abc", watch_rc=1)
    assert done.returncode == 1
    assert "run-id: 77" in done.stdout
    assert (tmp_path / "github-output").read_text() == "run_id=77\n"
    calls = (stub / "gh-calls").read_text()
    assert "workflow run env-up.yml --ref main -f sha=abc" in calls
    assert "run watch 77 --interval 30 --exit-status" in calls


def test_it_fails_when_no_run_appears(tmp_path: Path) -> None:
    done, _ = _run(tmp_path, "env-up.yml", "main", list_out="")
    assert done.returncode == 1
    assert "found no run" in done.stderr
    assert not (tmp_path / "github-output").exists()


def test_watch_job_success_ends_the_wait_while_the_run_is_still_going(tmp_path: Path) -> None:
    views = [
        {"status": "in_progress", "conclusion": "", "jobs": [_job("env", "in_progress")]},
        {
            "status": "in_progress",
            "conclusion": "",
            "jobs": [_job("env", "completed", "success"), _job("expire", "in_progress")],
        },
    ]
    done, stub = _run(tmp_path, "env-up.yml", "main", views=views, watch_job="env")
    assert done.returncode == 0
    assert "job env: success" in done.stdout
    assert "run watch" not in (stub / "gh-calls").read_text()


def test_watch_job_failure_is_the_exit_status(tmp_path: Path) -> None:
    views = [
        {"status": "in_progress", "conclusion": "", "jobs": [_job("env", "completed", "failure")]}
    ]
    done, _ = _run(tmp_path, "env-up.yml", "main", views=views, watch_job="env")
    assert done.returncode == 1
    assert "job env: failure" in done.stdout


def test_a_run_that_ends_without_the_watched_job_completing_fails(tmp_path: Path) -> None:
    views = [{"status": "completed", "conclusion": "cancelled", "jobs": [_job("env", "queued")]}]
    done, _ = _run(tmp_path, "env-up.yml", "main", views=views, watch_job="env")
    assert done.returncode == 1
    assert "ended cancelled without job env completing" in done.stderr
