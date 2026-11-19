"""scripts/bootstrap_drift.py: the deploy role's live policy against the bootstrap template.

Story 5.4's first env-down runs failed with AccessDenied because the template had gained actions
and bootstrap had not been re-applied. The check tells that apart before a dispatch. The live
policy here is the rendered template, edited the way drift would edit it; no AWS."""

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from scripts.bootstrap_drift import compare, render
from tests.target import REPO

TEMPLATE = REPO / "infra" / "bootstrap" / "policies" / "deploy-permissions.json.tftpl"
SCRIPT = REPO / "scripts" / "bootstrap_drift.py"
VALUES = {"account_id": "000000000000", "region": "us-east-1", "bucket": "ticketscope-000000000000"}


def _expected() -> dict[str, Any]:
    return render(TEMPLATE.read_text(encoding="utf-8"), VALUES)


def _statement(policy: dict[str, Any], sid: str) -> dict[str, Any]:
    (found,) = [s for s in policy["Statement"] if s.get("Sid") == sid]
    return found


def _run(tmp_path: Path, live: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    live_file = tmp_path / "live.json"
    live_file.write_text(json.dumps(live), encoding="utf-8")
    args = ["--template", str(TEMPLATE), "--account-id", VALUES["account_id"]]
    args += ["--region", VALUES["region"], "--bucket", VALUES["bucket"], "--live", str(live_file)]
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def test_the_template_renders_with_every_variable_filled() -> None:
    expected = _expected()
    text = json.dumps(expected)
    assert "${" not in text and expected["Statement"]


def test_a_role_that_matches_the_template_passes(tmp_path: Path) -> None:
    result = _run(tmp_path, _expected())
    assert result.returncode == 0, result.stdout + result.stderr
    assert "matches" in result.stdout


def test_an_action_missing_from_the_role_is_drift_and_named(tmp_path: Path) -> None:
    # The story 5.4 case: the template gained tag:GetResources, the role had not.
    live = copy.deepcopy(_expected())
    discovery = _statement(live, "ReadOnlyDiscovery")
    discovery["Action"] = [a for a in discovery["Action"] if a != "tag:GetResources"]
    result = _run(tmp_path, live)
    assert result.returncode == 1
    assert "ReadOnlyDiscovery: Action tag:GetResources missing from the role" in result.stdout
    assert "re-apply bootstrap" in result.stdout


def test_an_extra_action_or_statement_on_the_role_is_drift() -> None:
    expected = _expected()
    live = copy.deepcopy(expected)
    _statement(live, "ReadOnlyDiscovery")["Action"].append("s3:DeleteBucket")
    live["Statement"].append(
        {"Sid": "HandAdded", "Effect": "Allow", "Action": "*", "Resource": "*"}
    )
    lines = compare(expected, live)
    assert "ReadOnlyDiscovery: Action s3:DeleteBucket on the role, not in the template" in lines
    assert "HandAdded: on the role, not in the template" in lines


def test_a_single_string_and_a_one_item_list_compare_equal() -> None:
    # AWS may return a one-item Action or Resource as a plain string.
    expected = _expected()
    live = copy.deepcopy(expected)
    for stmt in live["Statement"]:
        for key in ("Action", "Resource"):
            if isinstance(stmt.get(key), list) and len(stmt[key]) == 1:
                stmt[key] = stmt[key][0]
    assert compare(expected, live) == []


def test_account_ids_never_reach_the_output(tmp_path: Path) -> None:
    live = copy.deepcopy(_expected())
    _statement(live, "StateAndBackupsObjects")["Resource"] = [
        "arn:aws:s3:::ticketscope-123456789012/x"
    ]
    result = _run(tmp_path, live)
    assert result.returncode == 1
    assert "123456789012" not in result.stdout and "<acct>" in result.stdout


def test_unreadable_input_is_an_error_not_a_match(tmp_path: Path) -> None:
    bad = tmp_path / "live.json"
    bad.write_text("not json", encoding="utf-8")
    args = ["--template", str(TEMPLATE), "--account-id", "0" * 12, "--region", "us-east-1"]
    args += ["--bucket", "b", "--live", str(bad)]
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )
    assert result.returncode == 2
