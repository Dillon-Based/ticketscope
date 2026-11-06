"""ingest over recorded GitHub responses: one test per I/O-matrix row, plus the outputs.

No live GitHub calls: every request goes to `Replay`, which fails on anything unrecorded.
"""

import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from tests.target import SNAPSHOT_DIR
from tests.unit.ingest.replay import FakeClock, Replay
from ticketscope.core.derive import derive_outcome
from ticketscope.core.snapshot import SnapshotIssue
from ticketscope.jobs.ingest import main as ingest
from ticketscope.jobs.ingest.mask import EMAIL_MARKER, SECRET_MARKER, USER_MARKER
from ticketscope.jobs.ingest.select import enrich, select_issues
from ticketscope.jobs.load.main import read_kinds, read_snapshot

VERSION = "2026.11.1"
EXCLUDED = 130004
PLANTED_SECRETS = (
    "jane.doe@example.com",
    "someone@example.com",
    "ops+k8s@corp.example.org",
    "ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
    "github_pat_11ABCDEFG0123456789_abcdefghijklmnopqrstuvwxyz",
    "AKIAIOSFODNN7EXAMPLE",
    "ASIAQ3EGT5EXAMPLE123",
    "xoxb-123456789012-abcdefABCDEF",
    "AIzaSyA1234567890abcdefghijklmnopqrstuv",
    "BEGIN RSA PRIVATE KEY",
    "MIIEowIBAAKCAQEAplantedplantedplanted",
)


def _options(tmp_path: Path, *, cap: int = 20_000) -> ingest.Options:
    exclusions = tmp_path / "exclusions.txt"
    exclusions.write_text(f"# takedowns\n{EXCLUDED}  # requested 2026-11-01\n")
    return ingest.Options(
        version=VERSION,
        work_dir=tmp_path / "work",
        out_dir=tmp_path / "out",
        exclusions=exclusions,
        cap=cap,
    )


def _run(
    tmp_path: Path, *, rate_limits: bool = True, cap: int = 20_000
) -> tuple[int, Replay, FakeClock]:
    clock = FakeClock()
    replay = Replay(clock, rate_limits=rate_limits)
    code = ingest.run(_options(tmp_path, cap=cap), replay.client(), clock)
    return code, replay, clock


def _asset(tmp_path: Path) -> Path:
    return tmp_path / "out" / f"{VERSION}.jsonl.gz"


def _issues(tmp_path: Path) -> dict[int, SnapshotIssue]:
    return {issue.number: issue for issue in read_snapshot(_asset(tmp_path))}


def _text(tmp_path: Path) -> str:
    return gzip.decompress(_asset(tmp_path).read_bytes()).decode("utf-8")


@pytest.fixture
def completed(tmp_path: Path) -> tuple[Path, Replay, FakeClock]:
    code, replay, clock = _run(tmp_path)
    assert code == ingest.EXIT_OK
    return tmp_path, replay, clock


# --- outputs and corpus terms -------------------------------------------------------------


def test_output_validates_against_the_schema(completed: tuple[Path, Replay, FakeClock]) -> None:
    tmp_path, _, _ = completed
    schema = json.loads((SNAPSHOT_DIR / "schema-v1.json").read_text())
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    lines = [json.loads(line) for line in _text(tmp_path).splitlines()]
    assert lines
    for line in lines:
        errors = list(validator.iter_errors(line))
        assert not errors, f"issue {line['number']}: {errors[0].message}"
        SnapshotIssue.model_validate(line)
        assert line["url"] == f"https://github.com/kubernetes/kubernetes/issues/{line['number']}"


def test_outputs_are_listed_with_a_matching_checksum(
    completed: tuple[Path, Replay, FakeClock],
) -> None:
    tmp_path, _, _ = completed
    out = tmp_path / "out"
    assert sorted(p.name for p in out.iterdir()) == sorted(
        [
            f"{VERSION}.jsonl.gz",
            f"{VERSION}.jsonl.gz.sha256",
            f"{VERSION}-kinds.json",
            "report.json",
        ]
    )
    # `sha256sum -c` format: "<hex>  <file name>".
    digest, name = (out / f"{VERSION}.jsonl.gz.sha256").read_text().rstrip("\n").split("  ")
    assert name == f"{VERSION}.jsonl.gz"
    assert digest == hashlib.sha256((out / name).read_bytes()).hexdigest()


def test_load_reads_the_output_unchanged(completed: tuple[Path, Replay, FakeClock]) -> None:
    tmp_path, _, _ = completed
    kinds = read_kinds(tmp_path / "out" / f"{VERSION}-kinds.json")
    assert set(kinds) == set(_issues(tmp_path))
    assert set(kinds.values()) == {"short", "log_heavy"}


def test_report_holds_window_count_and_kind_split(
    completed: tuple[Path, Replay, FakeClock],
) -> None:
    tmp_path, _, _ = completed
    report: dict[str, Any] = json.loads((tmp_path / "out" / "report.json").read_text())
    assert report["window"] == {
        "start": "2023-11-07T00:00:00Z",
        "end": "2026-11-06T00:00:00Z",
        "days": 1095,
    }
    assert report["count"] == 4
    assert report["kinds"] == {"short": 3, "log_heavy": 1}
    assert report["kind_threshold"] == 3
    assert report["excluded"] == 1
    assert report["version"] == VERSION


def test_only_get_requests_and_no_graphql(completed: tuple[Path, Replay, FakeClock]) -> None:
    _, replay, _ = completed
    assert replay.requests
    assert {request.method for request in replay.requests} == {"GET"}
    assert {request.url.host for request in replay.requests} == {"api.github.com"}
    assert not any("graphql" in request.url.path for request in replay.requests)


def test_no_recorded_login_appears_in_the_output(
    completed: tuple[Path, Replay, FakeClock],
) -> None:
    tmp_path, replay, _ = completed
    text = _text(tmp_path)
    assert len(replay.logins) >= 10
    leaked = sorted(login for login in replay.logins if login in text)
    assert not leaked
    assert '"login"' not in text
    assert '"user"' not in text


# --- matrix rows ---------------------------------------------------------------------------


def test_normal_issue(completed: tuple[Path, Replay, FakeClock]) -> None:
    tmp_path, _, _ = completed
    issue = _issues(tmp_path)[130001]
    assert issue.state_reason == "duplicate"
    assert [label.name for label in issue.labels] == ["kind/bug", "sig/node", "triage/duplicate"]
    assert [(c.author_association, c.created_at.isoformat()) for c in issue.comments] == [
        ("MEMBER", "2026-09-02T00:00:00+00:00"),
        ("CONTRIBUTOR", "2026-09-03T00:00:00+00:00"),
    ]
    assert issue.comments[1].body.startswith("Mail me at")
    # `labeled` and `subscribed` are dropped.
    assert [event.event for event in issue.timeline] == [
        "cross-referenced",
        "marked_as_duplicate",
        "closed",
    ]
    pr = issue.timeline[0]
    assert pr.source_number == 130002
    assert pr.source_url == "https://github.com/kubernetes/kubernetes/pull/130002"
    assert pr.source_is_pull_request is True
    assert pr.source_merged is True
    assert derive_outcome(issue).status == "duplicate"


def test_cross_references_keep_pr_and_merge_state(
    completed: tuple[Path, Replay, FakeClock],
) -> None:
    tmp_path, _, _ = completed
    refs = [e for e in _issues(tmp_path)[130005].timeline if e.event == "cross-referenced"]
    assert [(e.source_number, e.source_is_pull_request, e.source_merged) for e in refs] == [
        (129900, False, None),
        (129901, True, False),
    ]


def test_pr_in_listing_is_skipped(completed: tuple[Path, Replay, FakeClock]) -> None:
    tmp_path, replay, _ = completed
    assert 130002 not in _issues(tmp_path)
    assert 130002 not in replay.timeline_numbers()


def test_issue_closed_before_the_window_is_skipped(
    completed: tuple[Path, Replay, FakeClock],
) -> None:
    tmp_path, replay, _ = completed
    assert 130006 not in _issues(tmp_path)
    assert 130006 not in replay.timeline_numbers()


def test_order_is_most_recently_closed_first_and_capped(tmp_path: Path) -> None:
    code, replay, _ = _run(tmp_path, cap=2)
    assert code == ingest.EXIT_OK
    # 130007 and 130001 share closed_at; the higher number comes first.
    assert [issue.number for issue in read_snapshot(_asset(tmp_path))] == [130007, 130001]
    assert sorted(set(replay.timeline_numbers())) == [130001, 130007]


def test_full_order(completed: tuple[Path, Replay, FakeClock]) -> None:
    tmp_path, _, _ = completed
    assert list(_issues(tmp_path)) == [130007, 130001, 130003, 130005]


def test_more_than_100_comments_are_paged_in_full(
    completed: tuple[Path, Replay, FakeClock],
) -> None:
    tmp_path, replay, _ = completed
    issue = _issues(tmp_path)[130003]
    assert len(issue.comments) == 120
    assert [c.body.split(":")[0] for c in issue.comments] == [f"Comment {k}" for k in range(1, 121)]
    assert [e.event for e in issue.timeline] == ["closed"]
    pages = [r.url.params.get("page") for r in replay.requests if "130003" in r.url.path]
    assert pages[-2:] == [None, "2"]


def test_rate_limit_waits_for_reset_and_retries(tmp_path: Path) -> None:
    limited, unlimited = tmp_path / "limited", tmp_path / "unlimited"
    limited.mkdir()
    unlimited.mkdir()
    code, replay, clock = _run(limited)
    assert code == ingest.EXIT_OK
    code_free, _, clock_free = _run(unlimited, rate_limits=False)
    assert code_free == ingest.EXIT_OK
    assert not clock_free.slept
    # 403 with x-ratelimit-remaining: 0 waits until the reset (+1 s); 429 honours retry-after.
    assert len(clock.slept) == 2
    assert 50 < clock.slept[0] <= 61
    assert clock.slept[1] == 5
    # The same URL is retried after each wait.
    keys = [r.url.path for r in replay.requests]
    assert keys.count("/repos/kubernetes/kubernetes/issues/130003/timeline") == 2
    assert keys.count("/repos/kubernetes/kubernetes/issues/130005/timeline") == 2
    assert _asset(limited).read_bytes() == _asset(unlimited).read_bytes()


def test_deadline_mid_run_checkpoints_and_resumes(tmp_path: Path) -> None:
    reference = tmp_path / "reference"
    reference.mkdir()
    assert _run(reference, rate_limits=False)[0] == ingest.EXIT_OK

    work = tmp_path / "resumed"
    work.mkdir()
    options = _options(work)
    clock = FakeClock()
    first = Replay(clock, rate_limits=False)
    # Listing (2 requests) plus two timelines fit; the third timeline does not.
    code = ingest.run(options, first.client(deadline=clock.now + 5), clock)
    assert code == ingest.EXIT_DEADLINE
    assert not (work / "out").exists()
    done = [json.loads(line)["number"] for line in (work / "work" / "fetched.jsonl").open()]
    assert done == [130007, 130001]

    clock2 = FakeClock(now=clock.now + 3600)
    second = Replay(clock2, rate_limits=False)
    assert ingest.run(options, second.client(), clock2) == ingest.EXIT_OK
    # Nothing finished is refetched, and the listing is not repeated.
    assert second.timeline_numbers() == [130003, 130003, 130005]
    assert not any(r.url.path.endswith("/issues") for r in second.requests)
    assert _asset(work).read_bytes() == _asset(reference).read_bytes()
    # The window is the first pass's, not the resume's.
    report = json.loads((work / "out" / "report.json").read_text())
    assert report["window"]["end"] == "2026-11-06T00:00:00Z"


def test_corrupt_trailing_checkpoint_line_is_dropped(tmp_path: Path) -> None:
    reference = tmp_path / "reference"
    reference.mkdir()
    assert _run(reference, rate_limits=False)[0] == ingest.EXIT_OK

    work = tmp_path / "resumed"
    work.mkdir()
    options = _options(work)
    clock = FakeClock()
    first = Replay(clock, rate_limits=False)
    assert ingest.run(options, first.client(deadline=clock.now + 5), clock) == 3
    fetched = work / "work" / "fetched.jsonl"
    lines = fetched.read_text().splitlines(keepends=True)
    # The second record was cut short mid-write.
    fetched.write_text(lines[0] + lines[1][:40])

    clock2 = FakeClock()
    second = Replay(clock2, rate_limits=False)
    assert ingest.run(options, second.client(), clock2) == ingest.EXIT_OK
    assert second.timeline_numbers() == [130001, 130003, 130003, 130005]
    assert _asset(work).read_bytes() == _asset(reference).read_bytes()


def test_corrupt_line_before_the_end_fails(tmp_path: Path) -> None:
    path = tmp_path / "fetched.jsonl"
    path.write_text("not json\n{}\n")
    with pytest.raises(ValueError, match="corrupt checkpoint line"):
        ingest.load_fetched(path)


def test_planted_secrets_are_masked(completed: tuple[Path, Replay, FakeClock]) -> None:
    tmp_path, _, _ = completed
    text = _text(tmp_path)
    for secret in PLANTED_SECRETS:
        assert secret not in text, secret
    issues = _issues(tmp_path)
    body = issues[130001].body or ""
    assert EMAIL_MARKER in body
    assert SECRET_MARKER in body
    comment = issues[130005].comments[0].body
    assert comment.count(SECRET_MARKER) == 4  # AKIA, ASIA, Slack, PEM block
    assert comment.endswith("thanks")


def test_mentions_are_masked_and_teams_kept(completed: tuple[Path, Replay, FakeClock]) -> None:
    tmp_path, _, _ = completed
    issues = _issues(tmp_path)
    assert issues[130001].title == f"Kubelet drops status for {USER_MARKER}'s pods"
    assert "@kubernetes/sig-node-bugs" in (issues[130001].body or "")
    bot = issues[130005].comments[1].body
    assert bot.startswith(f"{USER_MARKER}: Thanks")
    assert "@kubernetes/sig-node-bugs" in bot
    assert "github.com/kubernetes/website/@main/x" in issues[130005].comments[2].body


def test_checkpoint_is_masked(tmp_path: Path) -> None:
    clock = FakeClock()
    replay = Replay(clock, rate_limits=False)
    options = _options(tmp_path)
    assert ingest.run(options, replay.client(deadline=clock.now + 5), clock) == 3
    stored = (tmp_path / "work" / "selected.json").read_text()
    stored += (tmp_path / "work" / "fetched.jsonl").read_text()
    for secret in PLANTED_SECRETS:
        assert secret not in stored, secret
    assert not any(login in stored for login in replay.logins)


def test_excluded_issue_is_never_fetched_or_written(
    completed: tuple[Path, Replay, FakeClock],
) -> None:
    tmp_path, replay, _ = completed
    assert EXCLUDED not in _issues(tmp_path)
    assert EXCLUDED not in replay.timeline_numbers()
    assert str(EXCLUDED) not in _text(tmp_path)


def test_exclusions_file_rejects_junk(tmp_path: Path) -> None:
    path = tmp_path / "exclusions.txt"
    path.write_text("# ok\n\n12  # note\nabc\n")
    with pytest.raises(ValueError, match=r"exclusions.txt:4"):
        ingest.read_exclusions(path)


def test_committed_exclusions_file_parses() -> None:
    assert isinstance(ingest.read_exclusions(SNAPSHOT_DIR / "exclusions.txt"), frozenset)


def test_main_refuses_without_a_token(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TICKETSCOPE_INGEST_GITHUB_TOKEN", raising=False)
    assert ingest.main(["--version", VERSION, "--work-dir", str(tmp_path)]) == ingest.EXIT_USAGE


def test_issue_gone_before_its_timeline_is_left_out_for_good(tmp_path: Path) -> None:
    gone_key = "/repos/kubernetes/kubernetes/issues/130003/timeline?per_page=100"
    options = _options(tmp_path)
    clock = FakeClock()
    first = Replay(clock, rate_limits=False)
    first.replace(gone_key, 404, {"message": "Not Found"})
    assert ingest.run(options, first.client(), clock) == ingest.EXIT_OK
    assert list(_issues(tmp_path)) == [130007, 130001, 130005]
    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert (report["count"], report["gone"]) == (3, 1)
    assert (tmp_path / "work" / "gone.txt").read_text() == "130003\n"

    # A resumed pass (fetched.jsonl cut back) skips the gone issue without a request.
    fetched = tmp_path / "work" / "fetched.jsonl"
    fetched.write_text(fetched.read_text().splitlines(keepends=True)[0])
    clock2 = FakeClock()
    second = Replay(clock2, rate_limits=False)
    assert ingest.run(options, second.client(), clock2) == ingest.EXIT_OK
    assert second.timeline_numbers() == [130001, 130005]
    assert 130003 not in _issues(tmp_path)


def test_exclusions_added_after_selection_are_counted(tmp_path: Path) -> None:
    options = _options(tmp_path)
    clock = FakeClock()
    first = Replay(clock, rate_limits=False)
    assert ingest.run(options, first.client(deadline=clock.now + 5), clock) == 3
    options.exclusions.write_text(f"{EXCLUDED}\n130005\n")
    clock2 = FakeClock()
    second = Replay(clock2, rate_limits=False)
    assert ingest.run(options, second.client(), clock2) == ingest.EXIT_OK
    assert 130005 not in _issues(tmp_path)
    report = json.loads((tmp_path / "out" / "report.json").read_text())
    assert (report["count"], report["excluded"], report["gone"]) == (3, 2, 0)


def test_nul_characters_never_reach_a_record() -> None:
    # The first real snapshot failed its timed load: Postgres text cannot hold NUL.
    listed: dict[str, Any] = {
        "number": 1,
        "title": "crash\x00",
        "body": "log line\x00 here",
        "state": "closed",
        "state_reason": "completed",
        "created_at": "2026-01-01T00:00:00Z",
        "closed_at": "2026-01-02T00:00:00Z",
        "labels": [],
    }
    [base], _ = select_issues(
        [listed],
        repo="kubernetes/kubernetes",
        window_start=datetime(2025, 1, 1, tzinfo=UTC),
        cap=10,
        exclusions=frozenset(),
    )
    comment: dict[str, Any] = {
        "event": "commented",
        "created_at": "2026-01-01T12:00:00Z",
        "author_association": "MEMBER",
        "body": "\x00same\x00",
    }
    issue = enrich(base, [comment])
    assert (issue.title, issue.body, issue.comments[0].body) == ("crash", "log line here", "same")
    assert "\\u0000" not in issue.model_dump_json()
