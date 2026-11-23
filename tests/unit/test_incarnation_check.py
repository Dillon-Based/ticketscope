"""The incarnation check (story 5.9, R11): refuses a prefix that exists, or a restore source with
no base backup, before `terraform apply`. No AWS call; the listings are files."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.incarnation_check import NAME, ListingError, check, folders
from tests.target import REPO

PY = REPO / "scripts" / "incarnation_check.py"


def _listing(*names: str, parent: str = "backups/") -> dict[str, Any]:
    return {"CommonPrefixes": [{"Prefix": f"{parent}{n}/"} for n in names] or None}


def _run(tmp_path: Path, args: list[str], **files: Any) -> subprocess.CompletedProcess[str]:
    for name, body in files.items():
        text = body if isinstance(body, str) else json.dumps(body)
        (tmp_path / name).write_text(text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-I", str(PY), *args], capture_output=True, text=True, check=False
    )


@pytest.mark.criterion("ticketscope--e5-s9--AC-1")
def test_fresh_incarnation_with_no_restore_passes() -> None:
    assert check("inc-2-1", "", {"inc-1-1"}) == []
    assert check("inc-2-1", "", set()) == []


@pytest.mark.criterion("ticketscope--e5-s9--AC-1")
def test_an_incarnation_whose_prefix_exists_is_refused_and_named() -> None:
    (problem,) = check("inc-1-1", "", {"inc-1-1"})
    assert "backups/inc-1-1/" in problem and "already exists" in problem


def test_a_rerun_attempt_is_a_new_incarnation() -> None:
    assert check("inc-1-2", "", {"inc-1-1"}) == []


def test_recreate_passes_when_the_source_has_a_base_backup() -> None:
    assert check("inc-2-1", "inc-1-1", {"inc-1-1"}, {"20261123T170000"}) == []


@pytest.mark.parametrize(
    ("restore_from", "prefixes", "base", "fragment"),
    [
        ("inc-9-9", {"inc-1-1"}, {"b"}, "not in the bucket"),
        ("inc-1-1", {"inc-1-1"}, set(), "no base backup"),
        ("inc-1-1", {"inc-1-1"}, None, "not listed"),
        ("inc-2-1", {"inc-2-1"}, {"b"}, "equals the incarnation"),
    ],
)
def test_an_unusable_restore_source_is_refused(
    restore_from: str, prefixes: set[str], base: set[str] | None, fragment: str
) -> None:
    problems = check("inc-2-1", restore_from, prefixes, base)
    assert any(fragment in p for p in problems), problems


@pytest.mark.parametrize("bad", ["", "Inc-1", "-a", "a_b", "a/b", "a" * 64, "a b", "../x"])
def test_names_outside_the_pattern_are_refused(bad: str) -> None:
    assert NAME.pattern == r"^[a-z0-9][a-z0-9-]{0,62}$"
    assert check(bad, "", set())
    if bad:
        assert check("inc-2-1", bad, {"x"}, {"b"})


def test_the_longest_allowed_name_passes() -> None:
    assert check("a" * 63, "", set()) == []


def test_folders_read_the_prefixes_under_the_parent(tmp_path: Path) -> None:
    path = tmp_path / "l.json"
    path.write_text(json.dumps(_listing("a", "b")), encoding="utf-8")
    assert folders(path, "backups/") == {"a", "b"}
    path.write_text(json.dumps({"CommonPrefixes": None}), encoding="utf-8")
    assert folders(path, "backups/") == set()


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not json",
        "[]",
        "{}",
        '{"Contents": []}',
        '{"CommonPrefixes": "x"}',
        '{"CommonPrefixes": [{"Prefix": "other/a/"}]}',
        '{"CommonPrefixes": [{"Prefix": "backups/a/b/"}]}',
        '{"CommonPrefixes": [{"Prefix": "backups//"}]}',
        '{"CommonPrefixes": [{"Nope": 1}]}',
    ],
)
def test_an_unreadable_listing_is_an_error_never_absent(tmp_path: Path, text: str) -> None:
    path = tmp_path / "l.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ListingError):
        folders(path, "backups/")
    result = _run(tmp_path, ["--incarnation", "inc-2-1", "--listing", str(path)])
    assert result.returncode == 2 and "FAIL" in result.stderr


def test_a_missing_listing_file_is_an_error(tmp_path: Path) -> None:
    result = _run(tmp_path, ["--incarnation", "inc-2-1", "--listing", str(tmp_path / "none.json")])
    assert result.returncode == 2


def test_cli_exit_codes(tmp_path: Path) -> None:
    listing = tmp_path / "l.json"
    base = tmp_path / "b.json"
    fresh = ["--incarnation", "inc-2-1", "--listing", str(listing)]
    ok = _run(tmp_path, fresh, **{"l.json": _listing()})
    assert ok.returncode == 0 and "starts fresh" in ok.stdout
    taken = _run(
        tmp_path,
        ["--incarnation", "inc-1-1", "--listing", str(listing)],
        **{"l.json": _listing("inc-1-1")},
    )
    assert taken.returncode == 1 and "backups/inc-1-1/" in taken.stderr
    restore = [
        *["--incarnation", "inc-2-1", "--restore-from", "inc-1-1"],
        *["--listing", str(listing), "--base-listing", str(base)],
    ]
    bases = _listing("20261123T1", parent="backups/inc-1-1/base/")
    good = _run(tmp_path, restore, **{"l.json": _listing("inc-1-1"), "b.json": bases})
    assert good.returncode == 0 and "restores from inc-1-1" in good.stdout
    empty = _run(tmp_path, restore, **{"b.json": _listing()})
    assert empty.returncode == 1 and "no base backup" in empty.stderr
    unlisted = _run(tmp_path, restore[:6])
    assert unlisted.returncode == 1 and "not listed" in unlisted.stderr
    broken = _run(tmp_path, restore, **{"b.json": ""})
    assert broken.returncode == 2


def test_the_check_makes_no_aws_call() -> None:
    text = PY.read_text(encoding="utf-8")
    assert "subprocess" not in text and "boto" not in text
