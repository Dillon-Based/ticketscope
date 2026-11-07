"""ingest over a recorded, synthetic slice of The Public Jira Dataset v7 (story 13).

One test per I/O-matrix row and per test-design case. The slice (`ingest/slice.json`) is
dump-shaped but synthetic: no real document is committed. No MongoDB is needed: the
adapter is exercised against a fake collection.
"""

import gzip
import hashlib
import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from tests.target import SNAPSHOT_DIR
from ticketscope.adapters import jira_dump
from ticketscope.core.derive import derive_kind, derive_outcome, duplicate_target
from ticketscope.core.snapshot import SnapshotIssueV2
from ticketscope.jobs.ingest import jira
from ticketscope.jobs.ingest import main as ingest
from ticketscope.jobs.ingest.mask import EMAIL_MARKER, JIRA_USER_MARKER, SECRET_MARKER, mask_jira
from ticketscope.jobs.load.main import build_rows, read_kinds, read_snapshot

SLICE = Path(__file__).parent / "ingest" / "slice.json"
VERSION = "2026.11.1"
EXCLUDED = frozenset({"MCL-40", "REALMS-10"})
IDENTITIES = (
    "a1f0c3e2-1111-4a4a-9b9b-000000000001",  # reporter
    "b2e1d4f3-2222-4b4b-8c8c-000000000002",  # comment author
    "c3d2e5a4-3333-4c4c-9d9d-000000000003",  # assignee
    "d4e3f6b5-4444-4d4d-8e8e-000000000004",  # creator
    "e5f4a7c6-5555-4e4e-9f9f-000000000005",  # comment author (accountId)
)
PLANTED = (
    "jane.doe@example.com",
    "bob@example.org",
    "ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
    "AKIAIOSFODNN7EXAMPLE",
    "[~alice]",
    "accountid:5b10ac8d82e05b22cc7d4ef5",
)


def _docs() -> list[dict[str, Any]]:
    return json.loads(SLICE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def selection() -> jira.Selection:
    return jira.select(_docs(), exclusions=EXCLUDED)


@pytest.fixture(scope="module")
def by_key(selection: jira.Selection) -> dict[str, SnapshotIssueV2]:
    return {issue.key: issue for issue in selection.issues}


@pytest.fixture
def written(tmp_path: Path, selection: jira.Selection) -> tuple[Path, dict[str, Any]]:
    report = ingest.write_outputs(tmp_path, VERSION, selection)
    return tmp_path, report


def _gz_text(out: Path) -> str:
    return gzip.decompress((out / f"{VERSION}.jsonl.gz").read_bytes()).decode("utf-8")


# --- valid Jira snapshot (test design P2, cases 1-8) -----------------------------------


def test_output_validates_against_schema_v2_and_the_model(
    written: tuple[Path, dict[str, Any]],
) -> None:
    out, _ = written
    schema = json.loads((SNAPSHOT_DIR / "schema-v2.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    lines = _gz_text(out).splitlines()
    assert lines
    for line in lines:
        record = json.loads(line)
        errors = list(validator.iter_errors(record))
        assert not errors, f"{record.get('key')}: {errors[0].message}"
        SnapshotIssueV2.model_validate(record)


def test_schema_v2_and_the_model_name_the_same_fields() -> None:
    schema = json.loads((SNAPSHOT_DIR / "schema-v2.json").read_text(encoding="utf-8"))
    assert set(schema["properties"]) == set(SnapshotIssueV2.model_fields)
    assert set(schema["required"]) == set(SnapshotIssueV2.model_fields)


def test_checksum_matches_and_load_reads_the_output(written: tuple[Path, dict[str, Any]]) -> None:
    out, report = written
    asset = out / f"{VERSION}.jsonl.gz"
    digest, name = (out / f"{VERSION}.jsonl.gz.sha256").read_text().split()
    assert name == asset.name
    assert digest == hashlib.sha256(asset.read_bytes()).hexdigest() == report["sha256"]
    rows = list(build_rows(read_snapshot(asset), read_kinds(out / f"{VERSION}-kinds.json")))
    assert len(rows) == report["count"]


def test_lines_are_sorted_by_number(written: tuple[Path, dict[str, Any]]) -> None:
    out, _ = written
    numbers = [json.loads(line)["number"] for line in _gz_text(out).splitlines()]
    assert numbers == sorted(numbers)


def test_rerun_is_byte_identical(tmp_path: Path) -> None:
    first = ingest.write_outputs(tmp_path / "a", VERSION, jira.select(_docs(), exclusions=EXCLUDED))
    second = ingest.write_outputs(
        tmp_path / "b", VERSION, jira.select(_docs(), exclusions=EXCLUDED)
    )
    assert first == second
    for name in (f"{VERSION}.jsonl.gz", f"{VERSION}-kinds.json", "report.json"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()


def test_resolved_in_scope_issue_is_one_valid_record(by_key: dict[str, SnapshotIssueV2]) -> None:
    issue = by_key["MCL-1"]
    assert issue.state == "closed"
    assert issue.resolution == "Fixed"
    assert issue.issue_type == "Bug"
    assert issue.created_at.isoformat() == "2021-03-01T09:00:00+00:00"
    assert issue.resolved_at is not None
    assert issue.resolved_at.isoformat() == "2021-03-10T12:00:00+00:00"


def test_record_carries_id_key_url_and_duplicate_link(by_key: dict[str, SnapshotIssueV2]) -> None:
    issue = by_key["MCD-3"]
    assert issue.number == 30003
    assert issue.key == "MCD-3"
    assert issue.url == "https://bugs.mojang.com/browse/MCD-3"
    target = duplicate_target(issue)
    assert target is not None
    # The link side had no id: it comes from the dump's id for that key.
    assert (target.target_number, target.target_key, target.direction) == (
        10001,
        "MCL-1",
        "duplicates",
    )
    assert derive_outcome(issue).ref == "https://bugs.mojang.com/browse/MCL-1"


def test_out_of_scope_issues_are_absent(by_key: dict[str, SnapshotIssueV2]) -> None:
    assert "MC-1" not in by_key  # resolved, another project
    assert "MCL-20" not in by_key  # unresolved, no duplicate points to it


def test_open_target_is_written_open(
    selection: jira.Selection, by_key: dict[str, SnapshotIssueV2]
) -> None:
    target = by_key["REALMS-9"]
    assert target.state == "open"
    assert target.resolution is None
    assert target.resolved_at is None
    assert selection.open_targets == 1
    assert {i.key for i in selection.issues if i.state == "open"} == {"REALMS-9"}


def test_written_set_is_exactly_the_subset(by_key: dict[str, SnapshotIssueV2]) -> None:
    assert set(by_key) == {
        "MCL-1",
        "MCL-5",
        "MCD-3",
        "MCD-4",
        "MCL-30",
        "REALMS-9",
        "MCL-10",
        "MCL-11",
        "MCL-12",
        "MCL-41",
        "MCD-6",
        "MCD-7",
    }


def test_repeated_key_keeps_the_first_document(
    selection: jira.Selection, by_key: dict[str, SnapshotIssueV2]
) -> None:
    assert by_key["MCL-5"].title == "Repeated key, first document"
    assert [i.key for i in selection.issues].count("MCL-5") == 1
    assert selection.repeated_keys_dropped == 1


def test_non_duplicate_and_self_links_are_left_out(by_key: dict[str, SnapshotIssueV2]) -> None:
    links = by_key["MCL-1"].duplicate_links
    assert [(link.target_key, link.direction, link.link_type) for link in links] == [
        ("MCD-3", "duplicated_by", "Duplicate")
    ]
    assert [link.target_key for link in by_key["MCD-4"].duplicate_links] == ["MC-1"]


def test_link_with_an_unknown_target_id_is_dropped_and_counted(
    selection: jira.Selection, by_key: dict[str, SnapshotIssueV2]
) -> None:
    assert by_key["MCD-7"].duplicate_links == []
    assert selection.links_dropped == 1


def test_comment_flags_and_the_answered_rule(by_key: dict[str, SnapshotIssueV2]) -> None:
    answered = by_key["MCL-10"]
    assert [c.from_reporter for c in answered.comments] == [True, False, False]
    # (6) someone other than the reporter commented at or before the resolution
    assert derive_outcome(answered).status == "answered"
    # (7) only the reporter commented
    only_reporter = by_key["MCL-11"]
    assert [c.from_reporter for c in only_reporter.comments] == [True]
    assert derive_outcome(only_reporter).status == "fixed"
    # (8) the only non-reporter comment came after the resolution
    late = by_key["MCL-12"]
    assert [c.from_reporter for c in late.comments] == [False]
    assert derive_outcome(late).status == "fixed"


def test_comment_without_a_parseable_time_is_dropped(by_key: dict[str, SnapshotIssueV2]) -> None:
    assert [c.body for c in by_key["MCD-7"].comments] == ["Kept."]


def test_bad_created_time_skips_the_issue_and_the_run_continues(
    selection: jira.Selection, by_key: dict[str, SnapshotIssueV2]
) -> None:
    assert "MCL-50" not in by_key
    assert selection.bad_time == 1


def test_resolved_without_a_date_is_written_and_counted(
    selection: jira.Selection, by_key: dict[str, SnapshotIssueV2]
) -> None:
    issue = by_key["MCD-6"]
    assert issue.state == "closed"
    assert issue.resolved_at is None
    assert selection.resolved_without_date == 1


def test_times_are_utc() -> None:
    parsed = jira.parse_time("2021-12-28T20:34:52.000+0200")
    assert parsed is not None
    assert parsed.isoformat() == "2021-12-28T18:34:52+00:00"
    with pytest.raises(jira.BadTime):
        jira.parse_time("28/12/2021")


# --- no identities, terms (test design P2, cases 1-4) ----------------------------------


def test_no_identity_appears_in_the_output(written: tuple[Path, dict[str, Any]]) -> None:
    out, _ = written
    text = "".join(
        (out / name).read_text(encoding="utf-8")
        for name in (f"{VERSION}-kinds.json", "report.json")
    ) + _gz_text(out)
    for identity in IDENTITIES:
        assert identity not in text
    keys: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():  # pyright: ignore[reportUnknownVariableType]
                keys.add(str(key))  # pyright: ignore[reportUnknownArgumentType]
                walk(item)
        elif isinstance(value, list):
            for item in value:  # pyright: ignore[reportUnknownVariableType]
                walk(item)

    for line in _gz_text(out).splitlines():
        walk(json.loads(line))
    assert not {k for k in keys if any(w in k for w in ("reporter", "assignee", "creator"))} - {
        "from_reporter"
    }
    assert not {k for k in keys if "author" in k or "account" in k}


def test_planted_emails_and_secrets_are_masked(written: tuple[Path, dict[str, Any]]) -> None:
    out, _ = written
    text = _gz_text(out)
    for planted in PLANTED:
        assert planted not in text
    assert EMAIL_MARKER in text
    assert SECRET_MARKER in text


def test_jira_mentions_are_masked(by_key: dict[str, SnapshotIssueV2]) -> None:
    issue = by_key["MCL-1"]
    assert issue.title == f"Launcher crash reported by {JIRA_USER_MARKER} and {JIRA_USER_MARKER}"
    assert issue.body is not None
    assert f"Ping {JIRA_USER_MARKER}." in issue.body
    assert issue.comments[0].body.startswith(f"Also cc {JIRA_USER_MARKER}, {SECRET_MARKER}")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("[~alice] said", "[~user] said"),
        ("see [~accountid:5b10ac8d82e05b22cc7d4ef5]", "see [~user]"),
        ("mail a@example.com", "mail [email masked]"),
        ("[~user] stays", "[~user] stays"),
        ("ask [~jane@example.com] now", "ask [~user] now"),
        ("[not a mention]", "[not a mention]"),
    ],
)
def test_mask_jira(text: str, expected: str) -> None:
    assert mask_jira(text) == expected


def test_excluded_issue_is_absent_and_never_an_open_target(
    selection: jira.Selection, by_key: dict[str, SnapshotIssueV2]
) -> None:
    assert "MCL-40" not in by_key
    assert "REALMS-10" not in by_key  # an excluded open target
    assert "MCL-41" in by_key  # the duplicate pointing at it is still written
    assert selection.excluded == 2


def test_exclusions_file_holds_keys(tmp_path: Path) -> None:
    path = tmp_path / "exclusions.txt"
    path.write_text("# header\nMCL-40  # 2026-11-06 request\n\nREALMS-10\n")
    assert ingest.read_exclusions(path) == frozenset({"MCL-40", "REALMS-10"})


@pytest.mark.parametrize("junk", ["40", "mcl-40", "MCL-0", "MCL 40", "MCL-4x"])
def test_malformed_exclusion_line_is_refused_with_its_line(tmp_path: Path, junk: str) -> None:
    path = tmp_path / "exclusions.txt"
    path.write_text(f"MCL-1\n{junk}\n")
    with pytest.raises(ValueError, match=r"exclusions.txt:2"):
        ingest.read_exclusions(path)


def test_committed_exclusions_file_parses() -> None:
    ingest.read_exclusions(SNAPSHOT_DIR / "exclusions.txt")


# --- report (test design P2 "Release notes report", case 1) ----------------------------


def test_report_counts(written: tuple[Path, dict[str, Any]]) -> None:
    out, report = written
    assert json.loads((out / "report.json").read_text()) == report
    assert report["version"] == VERSION
    assert report["schema_version"] == 2
    assert report["subset"]["instance"] == "Mojang"
    assert report["subset"]["projects"] == ["MCL", "REALMS", "MCD"]
    assert report["count"] == 12
    assert report["open_targets"] == 1
    assert report["repeated_keys_dropped"] == 1
    assert report["excluded"] == 2
    assert report["bad_time_skipped"] == 1
    assert report["resolved_without_date"] == 1
    assert report["kinds"] == {"short": 10, "log_heavy": 2}


def test_in_subset_pairs_by_kind_equal_a_hand_count(
    written: tuple[Path, dict[str, Any]], by_key: dict[str, SnapshotIssueV2]
) -> None:
    _, report = written
    # By hand: MCD-3 -> MCL-1 (log-heavy) and MCL-30 -> REALMS-9 (short) are in the
    # snapshot; MCD-4 -> MC-1 (other project) and MCL-41 -> REALMS-10 (excluded) are not.
    assert derive_kind(by_key["MCD-3"]) == "log_heavy"
    assert derive_kind(by_key["MCL-30"]) == "short"
    assert report["pairs"] == {"total": 2, "short": 1, "log_heavy": 1}


def test_kinds_sidecar_matches_core(written: tuple[Path, dict[str, Any]]) -> None:
    out, _ = written
    kinds = read_kinds(out / f"{VERSION}-kinds.json")
    issues = list(read_snapshot(out / f"{VERSION}.jsonl.gz"))
    assert kinds == {issue.number: derive_kind(issue) for issue in issues}


# --- main and the adapter --------------------------------------------------------------


def test_run_reads_exclusions_and_writes(tmp_path: Path) -> None:
    exclusions = tmp_path / "exclusions.txt"
    exclusions.write_text("MCL-40\nREALMS-10\n")
    options = ingest.Options(version=VERSION, out_dir=tmp_path / "out", exclusions=exclusions)
    report = ingest.run(options, iter(_docs()))
    assert report["count"] == 12
    assert (tmp_path / "out" / f"{VERSION}.jsonl.gz").exists()


def test_run_refuses_an_empty_selection(tmp_path: Path) -> None:
    exclusions = tmp_path / "exclusions.txt"
    exclusions.write_text("")
    options = ingest.Options(version=VERSION, out_dir=tmp_path / "out", exclusions=exclusions)
    with pytest.raises(ValueError, match="no issues"):
        ingest.run(options, iter([]))


def test_main_refuses_a_bad_version() -> None:
    assert ingest.main(["--version", "latest"]) == ingest.EXIT_USAGE


class _FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs
        self.sorted_by: tuple[str, int] | None = None
        self.closed = False

    def sort(self, key: str, direction: int) -> _FakeCursor:
        self.sorted_by = (key, direction)
        self.docs = sorted(self.docs, key=lambda d: d[key], reverse=direction < 0)
        return self

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.docs)

    def close(self) -> None:
        self.closed = True


class _FakeCollection:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self.docs = docs
        self.calls: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
        self.cursor: _FakeCursor | None = None

    def find(
        self, filter: Mapping[str, Any], projection: Mapping[str, Any], *, no_cursor_timeout: bool
    ) -> _FakeCursor:
        self.calls.append((filter, projection))
        wanted = set(filter["fields.project.key"]["$in"])
        self.cursor = _FakeCursor([d for d in self.docs if jira.project_of(d) in wanted])
        return self.cursor


def test_adapter_reads_in_scope_projects_in_id_order() -> None:
    shuffled = list(reversed(_docs()))
    collection = _FakeCollection(shuffled)
    docs = list(jira_dump.read_issues(collection, jira.PROJECTS))
    ((query, projection),) = collection.calls
    assert query == {"fields.project.key": {"$in": ["MCD", "MCL", "REALMS"]}}
    assert collection.cursor is not None
    assert collection.cursor.sorted_by == ("_id", 1)
    assert collection.cursor.closed
    assert [d["_id"] for d in docs] == sorted(d["_id"] for d in docs)
    assert "MC-1" not in {d["key"] for d in docs}
    # Identities beyond the reporter/author ids needed for `from_reporter` are never read.
    assert not any(k.startswith(("fields.assignee", "fields.creator")) for k in projection)
    assert "fields.issuelinks.outwardIssue.id" in projection
    # Through the adapter, the first MCL-5 by `_id` still wins.
    selection = jira.select(docs, exclusions=EXCLUDED)
    assert {i.key: i.title for i in selection.issues}["MCL-5"] == "Repeated key, first document"


def test_linktype_mapping_is_package_data() -> None:
    linkmap = jira.load_linktypes()
    assert jira.is_duplicate_linktype("Duplicate", linkmap)
    assert jira.is_duplicate_linktype("3 - Duplicate", linkmap)
    assert not jira.is_duplicate_linktype("Relates", linkmap)
    assert not jira.is_duplicate_linktype(None, linkmap)
