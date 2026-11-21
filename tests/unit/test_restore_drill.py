"""The restore drill (story 5.7, R9): the comparison that decides whether a restored cluster holds
the source's corpus, the masking of the committed record, and the drill script's wiring. Nothing
here touches AWS or a cluster."""

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.restore_drill import compare, mask, render_record
from tests.target import REPO

SCRIPT = REPO / "scripts" / "restore-drill.sh"
PY = REPO / "scripts" / "restore_drill.py"
ACCOUNT = "000000000000"
META = {
    "snapshot_version": "2026.11.1",
    "embedding_model_id": "m",
    "preprocessing_version": "1",
    "loaded_at": "2026-11-20 19:50:00+00",
}


def _snap(**over: Any) -> dict[str, Any]:
    return {"corpus_meta": dict(META), "issues": 1200, "digest": "abc123", **over}


def test_a_matching_restore_has_no_differences() -> None:
    assert compare(_snap(), _snap(), 1200) == []


def test_a_differing_count_is_named() -> None:
    assert compare(_snap(), _snap(issues=1199), 1200) == [
        "issues: source 1200, restored 1199",
        "release: restored 1199, the pinned Release publishes 1200",
    ]


def test_a_differing_digest_is_named() -> None:
    assert compare(_snap(), _snap(digest="zzz"), 1200) == ["digest: source abc123, restored zzz"]


def test_a_differing_corpus_meta_field_is_named() -> None:
    other = {**META, "snapshot_version": "2026.10.9"}
    assert compare(_snap(), _snap(corpus_meta=other), 1200) == [
        "corpus_meta.snapshot_version: source 2026.11.1, restored 2026.10.9"
    ]


def test_equal_to_each_other_but_not_to_the_release_still_fails() -> None:
    assert compare(_snap(), _snap(), 1201) == [
        "release: restored 1200, the pinned Release publishes 1201"
    ]


@pytest.mark.parametrize(
    "bad",
    [{}, {"issues": 1}, _snap(issues="12"), _snap(corpus_meta=None), _snap(digest="")],
)
def test_an_unreadable_snapshot_raises_so_it_never_reads_as_a_match(bad: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        compare(_snap(), bad, 1200)


def _write(path: Path, data: dict[str, Any]) -> str:
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_the_cli_exits_0_on_a_match_1_on_a_difference_2_on_unreadable_input(tmp_path: Path) -> None:
    good = _write(tmp_path / "a.json", _snap())
    off = _write(tmp_path / "b.json", _snap(issues=1))

    def run(*files: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(PY), "compare", *files, "--expected", "1200"],
            capture_output=True,
            text=True,
            check=False,
        )

    ok = run(good, good)
    assert ok.returncode == 0 and "restore drill: OK" in ok.stdout
    bad = run(good, off)
    assert bad.returncode == 1 and "issues: source 1200, restored 1" in bad.stdout
    missing = run(good, str(tmp_path / "nope.json"))
    assert missing.returncode == 2


def test_masking_removes_account_ids_arns_and_private_hostnames() -> None:
    text = (
        f"role arn:aws:iam::{ACCOUNT}:role/ticketscope-env-cnpg-backup "
        f"bucket ticketscope-{ACCOUNT}\n"
        "https://8CD3DE84B5B944AF51825083866BF05E.gr7.us-east-1.eks.amazonaws.com\n"
        "k8s-x-1234.us-east-1.elb.amazonaws.com AKIAABCDEFGHIJKLMNOP "
        "ASIAABCDEFGHIJKLMNOP\n"
    )
    masked = mask(text)
    assert not re.search(r"\b\d{12}\b", masked)
    assert ACCOUNT not in masked and "8CD3DE84" not in masked
    assert "elb.amazonaws.com" not in masked and "eks.amazonaws.com" not in masked
    assert "AKIA" not in masked and "ASIA" not in masked
    assert "ticketscope-env-cnpg-backup" in masked


def test_the_record_holds_commands_timings_and_the_verdict_masked() -> None:
    result = {
        "verdict": "OK",
        "differences": [],
        "stages": [{"stage": "backup", "seconds": 61}, {"stage": "restore", "seconds": 240}],
        "source": _snap(),
        "restored": _snap(),
        "expected": 1200,
    }
    log = f"+ kubectl -n ticketscope get cluster ticketscope-db\nbucket ticketscope-{ACCOUNT}\n"
    record = render_record(result, log)
    assert "| backup | 61 |" in record and "| restore | 240 |" in record
    assert "Result: OK" in record and "kubectl -n ticketscope get cluster" in record
    assert ACCOUNT not in record


def test_committed_drill_records_hold_no_account_id_or_credential() -> None:
    records = sorted((REPO / "docs" / "drills").glob("*.md"))
    assert records, "docs/drills has no record"
    for path in records:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\b\d{12}\b", text), path.name
        assert not re.search(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b", text), path.name
        assert not re.search(r"(?i)aws_secret_access_key|aws_session_token|BEGIN [A-Z ]*KEY", text)
        assert "amazonaws.com" not in text.replace("sts.amazonaws.com", ""), path.name


def test_the_script_restores_by_recovery_through_the_plugin_and_never_archives() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "bootstrap:" in text and "recovery:" in text and "externalClusters:" in text
    assert "barman-cloud.cloudnative-pg.io" in text and "serverName" in text
    assert "ticketscope-restore" in text and "scripts/eks-backup.sh" in text
    # Read-only recovery: no WAL archiver entry on the recovered cluster.
    assert "isWALArchiver" not in text
    assert "restore_drill.py compare" in text


def test_the_backup_role_trusts_the_recovery_clusters_account() -> None:
    irsa = (REPO / "infra" / "env" / "irsa.tf").read_text(encoding="utf-8")
    assert '"ticketscope:ticketscope-restore"' in irsa


def test_the_script_without_arguments_is_a_usage_error() -> None:
    result = subprocess.run([str(SCRIPT)], capture_output=True, text=True, check=False)
    assert result.returncode == 2 and "usage:" in result.stderr
