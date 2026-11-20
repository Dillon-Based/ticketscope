"""scripts/restore-drill.sh end to end against a stub `kubectl` and `uv` (story 5.7, R9): the
recovery Cluster it applies, the stages, the exit codes and the record it writes. No cluster."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.target import REPO

SCRIPT = REPO / "scripts" / "restore-drill.sh"
ACCOUNT = "000000000000"
ROLE = f"arn:aws:iam::{ACCOUNT}:role/ticketscope-env-cnpg-backup"
META = {"snapshot_version": "2026.11.1", "loaded_at": "2026-11-20 19:50:00+00"}

pytestmark = pytest.mark.skipif(
    shutil.which("jq") is None or shutil.which("python3") is None, reason="needs jq and python3"
)

SOURCE_CLUSTER = {
    "spec": {
        "imageName": f"{ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com/ticketscope-postgres:18-x",
        "storage": {"size": "1Gi", "storageClass": "gp3"},
        "resources": {"limits": {"memory": "512Mi"}},
        "serviceAccountTemplate": {
            "metadata": {"annotations": {"eks.amazonaws.com/role-arn": ROLE}}
        },
        "plugins": [{"parameters": {"serverName": "inc-1-1"}}],
    }
}

KUBECTL = r"""#!/usr/bin/env bash
args="$*"
case "$args" in
  *"get cluster.postgresql.cnpg.io ticketscope-db -o jsonpath"*) printf 'inc-1-1' ;;
  *"get cluster.postgresql.cnpg.io ticketscope-db -o json"*) cat "$STUB/source-cluster.json" ;;
  *"get pod -l cnpg.io/cluster="*)
    cluster="${args#*cnpg.io/cluster=}"; printf '%s-1' "${cluster%%,*}" ;;
  *"exec ticketscope-db-1 "*) cat "$STUB/source-snapshot.json" ;;
  *"exec ticketscope-restore-1 "*) cat "$STUB/restored-snapshot.json" ;;
  *"get backup.postgresql.cnpg.io"*) printf 'completed' ;;
  *"apply -f -"*) { echo '---'; cat; } >>"$STUB/applied.yaml" ;;
  *" wait "*) [[ -z "${STUB_WAIT_FAILS:-}" ]] ;;
  *" delete "*) echo "$args" >>"$STUB/deleted" ;;
  *) echo "stub kubectl: unexpected $args" >&2; exit 9 ;;
esac
"""
UV = r"""#!/usr/bin/env bash
# `uv run python <script> ...`: expected-issues needs GitHub, so it is answered here.
shift 2
if [[ "$2" == "expected-issues" ]]; then echo "${STUB_EXPECTED:-1200}"; else exec python3 "$@"; fi
"""


def _snapshot(**over: Any) -> dict[str, Any]:
    return {"corpus_meta": META, "issues": 1200, "digest": "abc", **over}


def _drill(tmp: Path, restored: dict[str, Any], **env: str) -> subprocess.CompletedProcess[str]:
    stub = tmp / "stub"
    bin_dir = tmp / "bin"
    stub.mkdir()
    bin_dir.mkdir()
    (stub / "source-cluster.json").write_text(json.dumps(SOURCE_CLUSTER))
    (stub / "source-snapshot.json").write_text(json.dumps(_snapshot()))
    (stub / "restored-snapshot.json").write_text(json.dumps(restored))
    for name, body in (("kubectl", KUBECTL), ("uv", UV)):
        (bin_dir / name).write_text(body)
        (bin_dir / name).chmod(0o755)
    kubeconfig = tmp / "kubeconfig"
    kubeconfig.write_text("x")
    return subprocess.run(
        [str(SCRIPT), "--kubeconfig", str(kubeconfig), "--out", str(tmp / "out")],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "STUB": str(stub), **env},
    )


def test_a_matching_restore_exits_0_and_writes_a_masked_record(tmp_path: Path) -> None:
    result = _drill(tmp_path, _snapshot())
    assert result.returncode == 0, result.stdout + result.stderr
    assert "restore drill: OK" in result.stdout
    record = (tmp_path / "out" / "restore-drill.md").read_text()
    assert "Result: OK" in record and "| backup |" in record and "| compare |" in record
    assert ACCOUNT not in record


def test_the_recovery_cluster_reads_the_sources_server_name_and_does_not_archive(
    tmp_path: Path,
) -> None:
    _drill(tmp_path, _snapshot())
    docs = [d for d in yaml.safe_load_all((tmp_path / "stub" / "applied.yaml").read_text()) if d]
    (cluster,) = [d for d in docs if d["kind"] == "Cluster"]
    assert cluster["metadata"]["name"] == "ticketscope-restore"
    assert cluster["spec"]["bootstrap"]["recovery"]["source"] == "source-cluster"
    (external,) = cluster["spec"]["externalClusters"]
    assert external["plugin"]["name"] == "barman-cloud.cloudnative-pg.io"
    assert external["plugin"]["parameters"] == {
        "barmanObjectName": "ticketscope-backup",
        "serverName": "inc-1-1",
    }
    assert "plugins" not in cluster["spec"]
    assert cluster["spec"]["instances"] == 1
    assert cluster["spec"]["storage"] == {"size": "1Gi", "storageClass": "gp3"}
    annotations = cluster["spec"]["serviceAccountTemplate"]["metadata"]["annotations"]
    assert annotations["eks.amazonaws.com/role-arn"] == ROLE
    (backup,) = [d for d in docs if d["kind"] == "Backup"]
    assert backup["metadata"]["name"].startswith("ticketscope-db-ondemand-inc-1-1-drill-")
    assert "ticketscope-restore" in (tmp_path / "stub" / "deleted").read_text()


def test_a_differing_restore_exits_1_names_the_field_and_is_recorded(tmp_path: Path) -> None:
    result = _drill(tmp_path, _snapshot(issues=1199, digest="zzz"))
    assert result.returncode == 1
    assert "issues: source 1200, restored 1199" in result.stdout
    record = (tmp_path / "out" / "restore-drill.md").read_text()
    assert "Result: FAILED" in record and "digest: source abc, restored zzz" in record


def test_a_count_that_is_not_the_releases_fails_even_when_source_and_restore_agree(
    tmp_path: Path,
) -> None:
    result = _drill(tmp_path, _snapshot(), STUB_EXPECTED="1201")
    assert result.returncode == 1
    assert "the pinned Release publishes 1201" in result.stdout


def test_a_recovery_cluster_that_never_gets_ready_exits_1_without_a_record(tmp_path: Path) -> None:
    result = _drill(tmp_path, _snapshot(), STUB_WAIT_FAILS="1")
    assert result.returncode == 1
    assert not (tmp_path / "out" / "restore-drill.md").exists()
    assert "ticketscope-restore" in (tmp_path / "stub" / "deleted").read_text()
