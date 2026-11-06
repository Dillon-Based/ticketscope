"""Spike 1.12: the pure functions of measure.py and convert.py on hand-built Jira dicts.

    uv run pytest <findings>/test_spike.py

One test per row of the plan's I/O matrix, plus the pieces they rest on.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import convert
from convert import mask_jira, select, to_snapshot
from measure import (
    DupLink,
    Scope,
    SubsetSpec,
    derive_outcome,
    duplicate_target,
    extended_kind,
    hygiene_flags,
    jira_to_fences,
    load_linktype_map,
    map_resolution,
)

from ticketscope.core.derive import kind_score
from ticketscope.core.snapshot import SnapshotIssue

LINKMAP = load_linktype_map()
BASE = "https://bugs.example.org"
REPORTER = {"key": "<<|author_key|r|>>"}
OTHER = {"key": "<<|author_key|o|>>"}

LOG_BODY = "It crashes:\n{code}\njava.lang.NullPointerException\n{code}\n" + "\n".join(
    f"\tat com.example.Foo.bar(Foo.java:{n})" for n in range(5)
)


def dup_link(target: str, *, outward: bool = True, name: str = "Duplicate") -> dict[str, Any]:
    side = "outwardIssue" if outward else "inwardIssue"
    return {
        "type": {"name": name, "inward": "is duplicated by", "outward": "duplicates"},
        side: {"id": "9" + target.split("-")[1], "key": target},
    }


def issue(
    key: str,
    resolution: str | None = "Fixed",
    *,
    links: list[dict[str, Any]] | None = None,
    itype: str = "Bug",
    body: str | None = "Short report.",
    comments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    number = key.split("-")[1]
    return {
        "id": "9" + number,
        "key": key,
        "fields": {
            "summary": f"Issue {key}",
            "description": body,
            "resolution": {"name": resolution} if resolution else None,
            "resolutiondate": "2021-06-02T10:00:00.000+0200" if resolution else None,
            "created": "2021-06-01T10:00:00.000+0200",
            "issuetype": {"name": itype},
            "project": {"key": key.split("-")[0]},
            "reporter": REPORTER,
            "labels": ["crash"],
            "issuelinks": links or [],
            "comments": comments or [],
        },
    }


def scope_row(*issues: dict[str, Any]) -> dict[str, Any]:
    scope = Scope("Test")
    for i in issues:
        scope.add(i, LINKMAP)
    return scope.row()


# --- I/O matrix ----------------------------------------------------------------------------


def test_instance_measured_gives_one_row_with_every_column() -> None:
    row = scope_row(
        issue("MC-1", "Duplicate", links=[dup_link("MC-2")]),
        issue("MC-2", "Fixed", body=LOG_BODY),
        issue("MC-3", None),
    )
    assert row["issues_total"] == 3
    assert row["issues_resolved"] == 2
    assert row["pairs"] == 1 and row["pairs_short"] == 1 and row["pairs_log_heavy"] == 0
    assert row["share_duplicate"] == 0.5 and row["share_fixed"] == 0.5
    assert row["short"] == 1 and row["log_heavy"] == 1
    assert row["type_bug"] == 1.0
    assert row["hyg_wiki"] == 1  # MC-2's {code}
    assert row["unmapped_resolutions"] == ""


def test_in_subset_pair_counts_once_under_the_duplicate_kind() -> None:
    row = scope_row(
        issue("MC-1", "Duplicate", links=[dup_link("MC-2")], body=LOG_BODY),
        issue("MC-2", "Duplicate", links=[dup_link("MC-1")]),  # the same pair, seen back
    )
    assert row["pairs"] == 1
    assert row["pairs_log_heavy"] == 1 and row["pairs_short"] == 0


def test_duplicate_link_outside_the_subset_is_counted_separately() -> None:
    row = scope_row(issue("MC-1", "Duplicate", links=[dup_link("WEB-7")]), issue("MC-2"))
    assert row["pairs"] == 0
    assert row["pairs_out_of_scope"] == 1
    assert row["dup_no_target"] == 0


def test_duplicate_link_to_an_unresolved_issue_is_not_an_in_subset_pair() -> None:
    row = scope_row(issue("MC-1", "Duplicate", links=[dup_link("MC-2")]), issue("MC-2", None))
    assert row["pairs"] == 0
    assert row["pairs_target_open"] == 1
    assert row["plus_open_targets_pairs"] == 1
    assert row["plus_open_targets_issues"] == 2


def test_duplicate_with_no_link_is_a_duplicate_outcome_without_a_pair() -> None:
    dup = issue("MC-1", "Duplicate")
    assert derive_outcome(dup) == ("duplicate", None)
    row = scope_row(dup, issue("MC-2"))
    assert row["dup_no_target"] == 1
    assert row["pairs"] == 0
    assert row["share_duplicate"] == 0.5


def test_unmapped_resolution_is_unknown_and_listed() -> None:
    odd = issue("MC-1", "REMIND")
    assert derive_outcome(odd) == ("unknown", "REMIND")
    row = scope_row(odd, issue("MC-2"))
    assert row["share_unknown"] == 0.5
    assert row["unmapped_resolutions"] == "REMIND=1"


def test_converted_line_validates_and_the_sidecar_follows_the_extended_rule() -> None:
    dup = issue(
        "MC-1",
        "Duplicate",
        links=[dup_link("MC-2")],
        body=LOG_BODY + "\nmail me at someone@example.com [~jdoe]\x00",
        comments=[{"author": OTHER, "body": "Same as MC-2", "created": "2021-06-01T12:00:00Z"}],
    )
    target = issue("MC-2", "Fixed")
    ids = {"MC-1": 91, "MC-2": 92}
    line = to_snapshot(dup, BASE, LINKMAP, ids)
    parsed = SnapshotIssue.model_validate(line)
    assert parsed.number == 91
    assert parsed.url == f"{BASE}/browse/MC-1"
    assert parsed.state == "closed" and parsed.state_reason == "duplicate"
    assert line["created_at"] == "2021-06-01T08:00:00Z"
    assert line["closed_at"] == "2021-06-02T08:00:00Z"
    assert parsed.comments[0].author_association == "NONE"
    event = parsed.timeline[0]
    assert event.event == "marked_as_duplicate" and event.source_number == 92
    assert "someone@example.com" not in (parsed.body or "")
    assert "[~jdoe]" not in (parsed.body or "") and "\x00" not in (parsed.body or "")
    # The sidecar's kind is the extended rule over the converted body.
    assert extended_kind(line["body"]) == "log_heavy"
    assert SnapshotIssue.model_validate(to_snapshot(target, BASE, LINKMAP, ids)).timeline == []


# --- the pieces ----------------------------------------------------------------------------


def test_jira_blocks_become_fences_for_kind_score() -> None:
    body = "x {code:java}a.go:1{code} y\n{noformat}\nERROR one\n{noformat}"
    fenced = jira_to_fences(body)
    assert fenced is not None and "{code" not in fenced and "{noformat}" not in fenced
    # Two fence openings (code, noformat), each body line counted once as log-like.
    assert kind_score(fenced) == 4
    assert kind_score(body) == 2  # without the extension: "a.go:1" and "ERROR one" only
    assert extended_kind(body) == "log_heavy"
    assert extended_kind("Just words.") == "short"
    assert extended_kind(None) == "short"


def test_resolution_mapping_covers_each_outcome() -> None:
    assert map_resolution("Duplicate") == ("duplicate", True)
    assert map_resolution("Done") == ("fixed", True)
    assert map_resolution("Won't Fix") == ("not_planned", True)
    assert map_resolution("Awaiting Response") == ("stale", True)
    assert map_resolution("Answered") == ("answered", True)
    assert map_resolution(None) == ("unknown", True)
    assert map_resolution("Stop Dots") == ("unknown", False)


def test_answered_rule_needs_a_question_and_a_non_reporter_comment_before_resolution() -> None:
    before = {"author": OTHER, "body": "Try X", "created": "2021-06-01T12:00:00.000+0200"}
    after = {"author": OTHER, "body": "late", "created": "2021-06-03T12:00:00.000+0200"}
    own = {"author": REPORTER, "body": "me", "created": "2021-06-01T12:00:00.000+0200"}
    q = "Question"
    assert derive_outcome(issue("Q-1", "Done", itype=q, comments=[before]))[0] == "answered"
    assert derive_outcome(issue("Q-2", "Done", itype=q, comments=[after]))[0] == "fixed"
    assert derive_outcome(issue("Q-3", "Done", itype=q, comments=[own]))[0] == "fixed"
    assert derive_outcome(issue("Q-4", "Done", comments=[before]))[0] == "fixed"  # a Bug
    assert derive_outcome(issue("Q-5", "Won't Fix", itype=q, comments=[before]))[0] == (
        "not_planned"
    )


def test_duplicate_target_prefers_the_duplicates_direction() -> None:
    reverse = dup_link("MC-5", outward=False)
    forward = dup_link("MC-6")
    found = duplicate_target(issue("MC-1", "Duplicate", links=[reverse, forward]), LINKMAP)
    assert found == DupLink("MC-6", False)
    only_reverse = issue("MC-1", "Duplicate", links=[reverse])
    assert duplicate_target(only_reverse, LINKMAP) == DupLink("MC-5", True)
    relates = dup_link("MC-7", name="Relates")
    assert duplicate_target(issue("MC-1", "Duplicate", links=[relates]), LINKMAP) is None
    sakai = dup_link("MC-8", name="3 - Duplicate")
    assert duplicate_target(issue("MC-1", "Duplicate", links=[sakai]), LINKMAP) == DupLink(
        "MC-8", False
    )


def test_hygiene_flags() -> None:
    assert hygiene_flags(["h1. Title\n[docs|https://x.org]"]) == {"wiki"}
    assert hygiene_flags(["ping [~accountid:abc123] and [~bob]"]) == {"mention"}
    assert hygiene_flags(["a@b.example.com"]) == {"email"}
    assert hygiene_flags(["key AKIAABCDEFGHIJKLMNOP"]) == {"secret"}
    assert hygiene_flags(["a\x00b", None]) == {"nul"}
    assert hygiene_flags(["plain"]) == set()


def test_repeated_documents_count_once() -> None:
    row = scope_row(issue("MC-1"), issue("MC-1"), issue("MC-2"))
    assert row["issues_resolved"] == 2 and row["repeated_docs"] == 1
    assert row["type_bug"] == 1.0
    assert [i["key"] for i in select([issue("MC-1"), issue("MC-1")], LINKMAP, False)] == ["MC-1"]


def test_select_adds_open_targets_only_when_asked() -> None:
    issues = [issue("MC-1", "Duplicate", links=[dup_link("MC-2")]), issue("MC-2", None)]
    assert [i["key"] for i in select(issues, LINKMAP, False)] == ["MC-1"]
    assert [i["key"] for i in select(issues, LINKMAP, True)] == ["MC-1", "MC-2"]
    line = to_snapshot(issues[1], BASE, LINKMAP, {})
    assert line["state"] == "open" and line["state_reason"] is None
    assert line["closed_at"] is None


def test_mask_jira_masks_mentions_and_emails() -> None:
    assert mask_jira("hi [~accountid:5b10a2844c20165700ede21g] x@y.org") == (
        "hi [~user] [email masked]"
    )
    assert mask_jira(None) is None


def test_convert_writes_a_sidecar_keyed_by_number_with_the_extended_kind(
    tmp_path: Path, monkeypatch: Any
) -> None:
    issues = [
        issue("MC-1", "Duplicate", links=[dup_link("MC-2")], body=LOG_BODY),
        issue("MC-2", None, body="Short report."),
        issue("MC-3", "Fixed", body="x {code}a.go:1{code}\n{noformat}\nERROR one\n{noformat}"),
        issue("MC-4", "Fixed", body=None),
    ]
    monkeypatch.setattr(convert, "iter_issues", lambda instance, query=None: iter(issues))
    spec = SubsetSpec.parse("t", "Mojang:MC")
    report = convert.convert(spec, tmp_path, "t", with_open_targets=True)
    with gzip.open(tmp_path / "t.jsonl.gz", "rt", encoding="utf-8") as lines:
        written = [json.loads(line) for line in lines]
    kinds = json.loads((tmp_path / "t-kinds.json").read_text())
    assert sorted(kinds) == sorted(str(line["number"]) for line in written)
    assert len(written) == 4 and report["issues"] == 4
    for line in written:
        assert kinds[str(line["number"])] == extended_kind(line["body"])
    assert kinds["91"] == "log_heavy" and kinds["93"] == "log_heavy"
    assert kinds["92"] == "short" and kinds["94"] == "short"
