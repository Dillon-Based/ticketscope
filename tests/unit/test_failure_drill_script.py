"""scripts/failure-drill.sh end to end against stub `kubectl`, `aws`, `curl` and `uv` (story 5.8,
R10): the refusal on a shared node, the termination, the events and the record. No cluster."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.target import REPO

SCRIPT = REPO / "scripts" / "failure-drill.sh"
ACCOUNT = "123456789012"

pytestmark = pytest.mark.skipif(
    shutil.which("jq") is None or shutil.which("python3") is None, reason="needs jq and python3"
)

# The stub `kubectl` keeps the primary in $STUB/primary; the first `get ... -o json` of the
# Cluster after the termination flips it, so promotion is observed.
KUBECTL = r"""#!/usr/bin/env bash
args="$*"
case "$args" in
  *"get pod -l cnpg.io/cluster=ticketscope-db,cnpg.io/podRole=instance -o json"*)
    cat "$STUB/pods.json" ;;
  *"jsonpath={.status.currentPrimary}"*)
    if [[ -f "$STUB/terminated" && -z "${STUB_NO_PROMOTION:-}" ]]; then printf 'ticketscope-db-2'
    else printf 'ticketscope-db-1'; fi ;;
  *"get pod ticketscope-db-1 -o"*) printf 'ip-10-0-1-1.ec2.internal' ;;
  *"get node "*) printf 'aws:///us-east-1a/i-0abc1234def56789' ;;
  *"get cluster.postgresql.cnpg.io ticketscope-db -o json"*)
    if [[ -f "$STUB/switched" ]]; then f=after
    elif [[ -f "$STUB/terminated" ]]; then f=mid
    else f=before; fi
    cat "$STUB/cluster-$f.json" ;;
  *" wait "*) ;;
  *"exec ticketscope-db-2 "*) touch "$STUB/switched"; echo "pg_switch_wal" ;;
  *) echo "stub kubectl: unexpected $args" >&2; exit 9 ;;
esac
"""
AWS = r"""#!/usr/bin/env bash
echo "$*" >>"$STUB/aws-calls"
touch "$STUB/terminated"
echo shutting-down
"""
CURL = r"""#!/usr/bin/env bash
# fails for the first STUB_FAILS probes after the termination, then answers 200
if [[ -f "$STUB/terminated" ]]; then
  n=$(($(cat "$STUB/n" 2>/dev/null || echo 0) + 1)); echo "$n" >"$STUB/n"
  if ((n <= ${STUB_FAILS:-2})); then printf '000'; exit 0; fi
fi
printf '200'
"""
UV = r"""#!/usr/bin/env bash
shift 2
exec python3 "$@"
"""


def _cluster(archived: str, **status: Any) -> dict[str, Any]:
    return {
        "spec": {
            "plugins": [
                {"name": "barman-cloud.cloudnative-pg.io", "parameters": {"serverName": "inc-1-1"}}
            ]
        },
        "status": {
            "lastArchivedWAL": archived,
            "conditions": [{"type": "ContinuousArchiving", "status": "True"}],
            **status,
        },
    }


def _drill(tmp: Path, nodes: list[str], **env: str) -> subprocess.CompletedProcess[str]:
    stub, bin_dir = tmp / "stub", tmp / "bin"
    stub.mkdir()
    bin_dir.mkdir()
    ready = {"conditions": [{"type": "Ready", "status": "True"}]}
    pods = {
        "items": [
            {"spec": {"nodeName": n}, "status": ready if n else {"phase": "Pending"}} for n in nodes
        ]
    }
    (stub / "pods.json").write_text(json.dumps(pods))
    (stub / "cluster-before.json").write_text(json.dumps(_cluster("000000010000000000000004")))
    after = _cluster("000000020000000000000005", **json.loads(env.pop("STATUS", "{}")))
    (stub / "cluster-after.json").write_text(json.dumps(after))
    # After promotion the new timeline's .history file is the last archived name, as in life.
    mid = _cluster("00000002.history")
    (stub / "cluster-mid.json").write_text(json.dumps(mid))
    for name, body in (("kubectl", KUBECTL), ("aws", AWS), ("curl", CURL), ("uv", UV)):
        (bin_dir / name).write_text(body)
        (bin_dir / name).chmod(0o755)
    kubeconfig = tmp / "kubeconfig"
    kubeconfig.write_text("x")
    return subprocess.run(
        [
            str(SCRIPT),
            "--kubeconfig",
            str(kubeconfig),
            "--url",
            "https://ticketscope.example.test",
            "--out",
            str(tmp / "out"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env={
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "STUB": str(stub),
            "SETTLE_SECONDS": "2",
            "PROMOTE_TIMEOUT": "5",
            "RECOVER_TIMEOUT": "20",
            "ARCHIVE_TIMEOUT": "10",
            **env,
        },
    )


NODES = ["ip-10-0-1-1.ec2.internal", "ip-10-0-2-2.ec2.internal"]


@pytest.mark.criterion("ticketscope--e5-s8--AC-2")
def test_a_survived_node_loss_exits_0_and_writes_a_masked_record(tmp_path: Path) -> None:
    result = _drill(tmp_path, NODES)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "failure drill: OK" in result.stdout
    assert (
        "terminate-instances --instance-ids i-0abc1234def56789"
        in (tmp_path / "stub" / "aws-calls").read_text()
    )
    record = (tmp_path / "out" / "failure-drill.md").read_text()
    assert "Result: OK" in record and "Failed requests: 2" in record
    assert "node 1" in record and "node 2" in record
    assert "i-0abc" not in record and "ip-10-0" not in record and ACCOUNT not in record
    events = json.loads((tmp_path / "out" / "events.json").read_text())
    assert events["archive"]["server_before"] == events["archive"]["server_after"] == "inc-1-1"


def test_instances_on_one_node_are_refused_and_nothing_is_terminated(tmp_path: Path) -> None:
    result = _drill(tmp_path, [NODES[0], NODES[0]])
    assert result.returncode == 1
    assert "share a node" in result.stderr + result.stdout
    assert not (tmp_path / "stub" / "aws-calls").exists()


def test_a_pending_standby_with_no_node_is_refused_and_nothing_is_terminated(
    tmp_path: Path,
) -> None:
    result = _drill(tmp_path, [NODES[0], ""])
    assert result.returncode == 1
    assert "scheduled and Ready" in result.stderr + result.stdout
    assert not (tmp_path / "stub" / "aws-calls").exists()


def test_no_promotion_exits_1_and_the_record_says_so(tmp_path: Path) -> None:
    result = _drill(tmp_path, NODES, STUB_NO_PROMOTION="1")
    assert result.returncode == 1
    assert "no standby was promoted" in (tmp_path / "out" / "failure-drill.md").read_text()


@pytest.mark.criterion("ticketscope--e5-s8--AC-3")
def test_an_archive_error_after_promotion_exits_1(tmp_path: Path) -> None:
    result = _drill(tmp_path, NODES, STATUS='{"lastFailedWAL": "000000030000000000000001"}')
    assert result.returncode == 1
    assert "failed to archive" in (tmp_path / "out" / "failure-drill.md").read_text()


def test_the_script_terminates_only_the_primarys_instance_and_keeps_two_instances() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.count("terminate-instances") >= 1 and "instances: 1" not in text
    assert "scale" not in text.lower()
