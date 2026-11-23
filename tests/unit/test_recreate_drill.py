"""The recreate drill (story 5.9, R11): the comparison of two incarnations, the before/after check
of the first one's folder, and the masked record. Nothing here touches AWS or a cluster."""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.recreate_drill import archive_diff, compare, render_record
from tests.target import REPO

PY = REPO / "scripts" / "recreate_drill.py"
ACCOUNT = "000000000000"
META = {
    "snapshot_version": "2026.11.1",
    "embedding_model_id": "m",
    "preprocessing_version": "1",
    "loaded_at": "2026-11-23T17:06:19+00:00",
}


def _facts(**over: Any) -> dict[str, Any]:
    return {"corpus_meta": dict(META), "issues": 1200, "digest": "abc123", **over}


def _listing(*rows: tuple[str, int, str]) -> dict[str, Any]:
    return {"Contents": [{"Key": k, "Size": s, "ETag": e} for k, s, e in rows]}


BASE = [("backups/a/base/1/data.tar", 10, '"e1"'), ("backups/a/wals/0/1.gz", 5, '"e2"')]


@pytest.mark.criterion("ticketscope--e5-s9--AC-2")
def test_equal_facts_match() -> None:
    assert compare(_facts(), _facts()) == []


@pytest.mark.criterion("ticketscope--e5-s9--AC-2")
@pytest.mark.parametrize(
    ("second", "fragment"),
    [
        (_facts(issues=1199), "issues: first 1200, second 1199"),
        (_facts(digest="zzz"), "digest"),
        (_facts(corpus_meta={**META, "loaded_at": "2026-11-23T18:00:00+00:00"}), "loaded_at"),
        (_facts(corpus_meta={**META, "snapshot_version": "2026.11.2"}), "snapshot_version"),
        (
            _facts(corpus_meta={k: v for k, v in META.items() if k != "embedding_model_id"}),
            "embedding_model_id",
        ),
    ],
)
def test_differing_facts_are_named(second: dict[str, Any], fragment: str) -> None:
    found = compare(_facts(), second)
    assert any(fragment in line for line in found), found


@pytest.mark.criterion("ticketscope--e5-s9--AC-3")
def test_a_different_hostname_or_certificate_is_a_difference_when_both_carry_one() -> None:
    one = _facts(hostname="h.example", certificate="aa")
    assert compare(one, _facts(hostname="h.example", certificate="aa")) == []
    assert compare(one, _facts(hostname="h.example", certificate="bb"))
    assert compare(one, _facts(hostname="other.example", certificate="aa"))
    assert compare(one, _facts()) == []


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        {},
        {"corpus_meta": {}, "issues": 1, "digest": "d"},
        {"corpus_meta": META, "issues": "1", "digest": "d"},
        {"corpus_meta": META, "issues": True, "digest": "d"},
        {"corpus_meta": META, "issues": 1},
    ],
)
def test_untrustworthy_facts_raise_and_never_match(bad: Any) -> None:
    with pytest.raises(ValueError):
        compare(bad, _facts())
    with pytest.raises(ValueError):
        compare(_facts(), bad)


@pytest.mark.criterion("ticketscope--e5-s9--AC-4")
def test_an_unchanged_first_prefix_has_no_difference() -> None:
    assert archive_diff(_listing(*BASE), _listing(*reversed(BASE))) == []


@pytest.mark.criterion("ticketscope--e5-s9--AC-4")
def test_a_changed_first_prefix_is_named() -> None:
    added = archive_diff(_listing(*BASE), _listing(*BASE, ("backups/a/wals/0/2.gz", 1, '"e3"')))
    assert added == ["added: backups/a/wals/0/2.gz"]
    removed = archive_diff(_listing(*BASE), _listing(BASE[0]))
    assert removed == ["removed: backups/a/wals/0/1.gz"]
    changed = archive_diff(_listing(*BASE), _listing(BASE[0], (BASE[1][0], 5, '"other"')))
    assert len(changed) == 1 and changed[0].startswith("changed: backups/a/wals/0/1.gz")
    resized = archive_diff(_listing(*BASE), _listing(BASE[0], (BASE[1][0], 6, '"e2"')))
    assert len(resized) == 1 and resized[0].startswith("changed:")


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        {"Contents": None},
        {"Contents": []},
        {"Contents": [1]},
        {"Contents": [{"Key": "k", "Size": 1}]},
        {"Contents": [{"Key": "k", "Size": "1", "ETag": "e"}]},
    ],
)
def test_an_empty_or_malformed_listing_is_an_error_never_identical(bad: Any) -> None:
    with pytest.raises(ValueError):
        archive_diff(bad, bad)
    with pytest.raises(ValueError):
        archive_diff(_listing(*BASE), bad)


def _result(**over: Any) -> dict[str, Any]:
    return {
        "verdict": "OK",
        "runs": [{"step": "env-up first", "run": "1", "result": "success"}],
        "first": _facts(),
        "second": _facts(),
        "differences": [],
        "archive_differences": [],
        "notes": ["the control run was not run"],
        **over,
    }


@pytest.mark.criterion("ticketscope--e5-s9--AC-2")
def test_the_record_holds_runs_facts_and_notes_masked() -> None:
    log = f"+ aws s3api list-objects-v2\nbucket ticketscope-{ACCOUNT}\nAKIAABCDEFGHIJKLMNOP\n"
    record = render_record(_result(), log)
    assert "Result: OK" in record and "| env-up first | 1 | success |" in record
    assert "the control run was not run" in record and "loaded_at" in record
    assert ACCOUNT not in record and "AKIA" not in record
    assert "<account>" in record and "<access-key-id>" in record


def test_differences_appear_in_the_record() -> None:
    record = render_record(
        _result(
            verdict="FAILED",
            differences=["issues: first 1, second 2"],
            archive_differences=["added: k"],
        ),
        "",
    )
    assert "Result: FAILED" in record
    assert "issues: first 1, second 2" in record and "added: k" in record


def test_committed_drill_records_hold_no_account_id_or_credential() -> None:
    records = sorted((REPO / "docs" / "drills").glob("*.md"))
    assert records
    for path in records:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\b\d{12}\b", text), path.name
        assert not re.search(r"\b(AKIA|ASIA)[A-Z0-9]{16}\b", text), path.name
        assert not re.search(r"(?i)aws_secret_access_key|aws_session_token|BEGIN [A-Z ]*KEY", text)
        assert not re.search(r"arn:aws:[a-z0-9-]+:[a-z0-9-]*:\d+:", text), path.name
        assert "amazonaws.com" not in text.replace("sts.amazonaws.com", ""), path.name


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(PY), *args], capture_output=True, text=True, check=False
    )


def test_cli_exit_codes_and_record(tmp_path: Path) -> None:
    def write(name: str, body: Any) -> str:
        path = tmp_path / name
        path.write_text(json.dumps(body), encoding="utf-8")
        return str(path)

    one, two = write("1.json", _facts()), write("2.json", _facts())
    assert _run(["compare", one, two]).returncode == 0
    assert _run(["compare", one, write("3.json", _facts(issues=2))]).returncode == 1
    assert _run(["compare", one, str(tmp_path / "none.json")]).returncode == 2
    before, after = write("b.json", _listing(*BASE)), write("a.json", _listing(*BASE))
    assert _run(["archive-diff", before, after]).returncode == 0
    assert _run(["archive-diff", before, write("e.json", {"Contents": []})]).returncode == 2
    assert _run(["archive-diff", before, write("c.json", _listing(BASE[0]))]).returncode == 1
    log = tmp_path / "log.txt"
    log.write_text(f"account {ACCOUNT}\n", encoding="utf-8")
    out = tmp_path / "out.md"
    args = ["record", "--result", write("r.json", _result()), "--log", str(log), "--out", str(out)]
    assert _run(args).returncode == 0
    assert ACCOUNT not in out.read_text(encoding="utf-8")
