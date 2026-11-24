"""The failure drill (story 5.8, R10): what the probe log and the event timestamps say about a
node loss, the placement and archive checks, and the masked record. No AWS or cluster."""

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.failure_drill import analyze, archive_problems, mask, placement_ok, render_record
from tests.target import REPO

PY = REPO / "scripts" / "failure_drill.py"
ACCOUNT = "123456789012"
T0 = 1000


def _archive(**over: Any) -> dict[str, Any]:
    return {
        "continuous_archiving": "True",
        "last_archived_before": "000000010000000000000004",
        "last_archived_after": "000000020000000000000005",
        "last_failed": "",
        "server_before": "inc-1-1",
        "server_after": "inc-1-1",
        **over,
    }


def _events(**over: Any) -> dict[str, Any]:
    return {"terminated_at": T0, "promoted_at": T0 + 20, "archive": _archive(), **over}


def _probe(failed: range, until: int = 1060) -> list[str]:
    return [f"{t} {'000' if t in failed else '200'}" for t in range(T0 - 10, until)]


@pytest.mark.criterion("ticketscope--e5-s8--AC-2")
def test_a_survived_failure_reports_recovery_promotion_and_failed_count() -> None:
    result = analyze(_probe(range(T0 + 3, T0 + 31)), _events())
    assert result["verdict"] == "OK" and result["problems"] == []
    assert result["failed_requests"] == 28
    assert result["promotion_seconds"] == 20
    assert result["recovery_seconds"] == 31


def test_no_failure_seen_is_ok_with_zero_failed() -> None:
    result = analyze(_probe(range(0)), _events())
    assert result["verdict"] == "OK" and result["failed_requests"] == 0
    assert result["recovery_seconds"] == 0


def test_never_recovering_is_failed() -> None:
    result = analyze(_probe(range(T0 + 3, 2000)), _events())
    assert result["verdict"] == "FAILED"
    assert any("never succeeded again" in p for p in result["problems"])
    assert result["recovery_seconds"] is None


def test_no_promotion_is_failed() -> None:
    result = analyze(_probe(range(T0 + 3, T0 + 9)), _events(promoted_at=None))
    assert result["verdict"] == "FAILED" and any("promoted" in p for p in result["problems"])


@pytest.mark.parametrize("nodes,ok", [(["a", "b"], True), (["a", "a"], False), (["a"], False)])
def test_placement_needs_two_distinct_nodes(nodes: list[str], ok: bool) -> None:
    assert placement_ok(nodes) is ok


@pytest.mark.criterion("ticketscope--e5-s8--AC-3")
def test_an_archive_error_is_a_problem_and_a_clean_status_is_not() -> None:
    assert archive_problems(_archive()) == []
    failed = archive_problems(_archive(last_failed="000000030000000000000005"))
    assert any("failed to archive" in p for p in failed)
    assert archive_problems(_archive(last_failed="000000010000000000000003")) == []
    stopped = archive_problems(_archive(continuous_archiving="False"))
    assert any("not continuing" in p for p in stopped)
    stalled = archive_problems(_archive(last_archived_after="000000010000000000000004"))
    assert any("did not advance" in p for p in stalled)
    renamed = archive_problems(_archive(server_after="inc-1-2"))
    assert any("serverName" in p for p in renamed)
    bad = _events(archive=_archive(last_failed="000000030000000000000001"))
    assert analyze(_probe(range(0)), bad)["verdict"] == "FAILED"


def test_history_names_do_not_pass_for_an_archived_segment() -> None:
    history = archive_problems(_archive(last_archived_after="00000002.history"))
    assert any("did not advance" in p for p in history)
    stale = archive_problems(_archive(last_failed="00000002.partial"))
    assert stale == []
    no_switch = archive_problems(_archive(last_archived_after=""), switched=False)
    assert no_switch == []


@pytest.mark.parametrize("bad", [[], ["x"], ["1000 200 extra"], ["abc 200"]])
def test_an_unreadable_probe_log_raises(bad: list[str]) -> None:
    with pytest.raises(ValueError):
        analyze(bad, _events())


def test_a_probe_log_that_stops_before_the_termination_raises() -> None:
    with pytest.raises(ValueError, match="no probe at or after"):
        analyze([f"{t} 200" for t in range(T0 - 10, T0 - 1)], _events())


def test_an_empty_server_name_raises_rather_than_passing() -> None:
    with pytest.raises(ValueError, match="serverName"):
        analyze(_probe(range(0)), _events(archive=_archive(server_before="", server_after="")))


def test_missing_event_keys_raise() -> None:
    with pytest.raises(ValueError):
        analyze(_probe(range(0)), {"terminated_at": T0})


def test_the_cli_exits_0_1_and_2(tmp_path: Path) -> None:
    probe, events = tmp_path / "p", tmp_path / "e"
    events.write_text(json.dumps(_events()))

    def run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(PY), "analyze", "--probe", str(probe), "--events", str(events)],
            capture_output=True,
            text=True,
            check=False,
        )

    probe.write_text("\n".join(_probe(range(T0 + 3, T0 + 9))))
    ok = run()
    assert ok.returncode == 0 and json.loads(ok.stdout)["verdict"] == "OK"
    probe.write_text("\n".join(_probe(range(T0 + 3, 2000))))
    assert run().returncode == 1
    probe.write_text("garbage")
    assert run().returncode == 2


def test_masking_removes_ids_nodes_and_private_hostnames() -> None:
    text = (
        f"arn:aws:iam::{ACCOUNT}:role/r node ip-10-0-1-23.ec2.internal i-0123456789abcdef0 "
        "k8s-x.us-east-1.elb.amazonaws.com ABC.gr7.us-east-1.eks.amazonaws.com AKIAABCDEFGHIJKLMNOP"
    )
    masked = mask(text)
    assert not re.search(r"\b\d{12}\b", masked) and "ip-10-0" not in masked
    assert "i-0123" not in masked and "amazonaws.com" not in masked and "AKIA" not in masked


@pytest.mark.criterion("ticketscope--e5-s8--AC-4")
def test_the_record_holds_figures_commands_and_the_verdict_masked() -> None:
    result = analyze(_probe(range(T0 + 3, T0 + 31)), _events())
    result["placement"] = ["ip-10-0-1-1.ec2.internal", "ip-10-0-2-2.ec2.internal"]
    log = f"+ aws ec2 terminate-instances --instance-ids i-0abc1234def56789\nacct {ACCOUNT}\n"
    record = render_record(result, log)
    assert "Result: OK" in record and "Failed requests: 28" in record
    assert "Recovery seconds: 31" in record and "terminate-instances" in record
    assert ACCOUNT not in record and "i-0abc" not in record and "ip-10-0" not in record
    assert "node 1" in record and "node 2" in record


def test_the_committed_skeleton_says_not_yet_run_or_holds_a_record() -> None:
    text = (REPO / "docs" / "drills" / "failure-drill.md").read_text(encoding="utf-8")
    assert "not yet run" in text or "Result: OK" in text or "Result: FAILED" in text
