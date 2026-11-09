"""The project's bmad-loop plugins (.bmad-loop/plugins/): the PR-per-story flow and
the TEA plugin's retro gate-report commit.

bmad-loop is not installed in this project's environment, so a minimal stand-in for
`bmad_loop.plugins.model` is put in `sys.modules` before each plugin module loads.
Every git, gh and tickets.py call goes through a scripted fake runner.
"""

import importlib.util
import json
import sys
import types
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import pytest

from tests.target import REPO

PLUGINS = REPO / ".bmad-loop" / "plugins"

type Reply = tuple[int, str]
type Handler = Callable[[tuple[str, ...]], Reply | None]


class FakeRunner:
    """Answers each command from the first handler that returns a reply; logs every call."""

    def __init__(self, *handlers: Handler) -> None:
        self.handlers = list(handlers)
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, args: Sequence[str], cwd: Path, timeout_s: int = 0) -> Reply:
        call = tuple(args)
        self.calls.append(call)
        for handler in self.handlers:
            reply = handler(call)
            if reply is not None:
                return reply
        raise AssertionError(f"unexpected command: {call}")

    def ran(self, *prefix: str) -> bool:
        return any(call[: len(prefix)] == prefix for call in self.calls)


def answer(prefix: tuple[str, ...], *replies: Reply) -> Handler:
    """Reply to commands starting with `prefix`, in order; the last reply repeats."""
    queue = list(replies)

    def handler(call: tuple[str, ...]) -> Reply | None:
        if call[: len(prefix)] != prefix:
            return None
        return queue.pop(0) if len(queue) > 1 else queue[0]

    return handler


class FakeContext:
    def __init__(self, story_key: str, role: str | None = None, run_dir: str | None = None):
        self.story_key = story_key
        self.role = role
        self.worktree: str | None = None
        self.repo_root = "/repo"
        self.run_dir = run_dir
        self.shared: dict[str, Any] = {}
        self.vetoes: list[tuple[str, str]] = []

    def veto(self, action: str, reason: str = "") -> None:
        self.vetoes.append((action, reason))


def _stub_bmad_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    class Plugin:
        def __init__(self, manifest: object = None, settings: dict[str, Any] | None = None):
            self.settings = settings or {}

    class PluginError(Exception):
        pass

    model = types.ModuleType("bmad_loop.plugins.model")
    model.Plugin = Plugin  # type: ignore[attr-defined]
    model.PluginError = PluginError  # type: ignore[attr-defined]
    for name in ("bmad_loop", "bmad_loop.plugins"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setitem(sys.modules, "bmad_loop.plugins.model", model)


def _load(monkeypatch: pytest.MonkeyPatch, name: str, file: str) -> Any:
    _stub_bmad_loop(monkeypatch)
    spec = importlib.util.spec_from_file_location(f"loop_plugin_{name}", PLUGINS / name / file)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def pr(monkeypatch: pytest.MonkeyPatch) -> Any:
    return _load(monkeypatch, "pr", "pr_plugin.py")


@pytest.fixture
def tea(monkeypatch: pytest.MonkeyPatch) -> Any:
    return _load(monkeypatch, "tea", "tea_plugin.py")


# ------------------------------------------------------------------ PR plugin

OK: Reply = (0, "")


def ticket(status: str) -> Handler:
    return answer(("uv", "run"), (0, json.dumps({"ref": "2.2", "status": status})))


def on_branch(name: str) -> Handler:
    return answer(("git", "rev-parse", "--abbrev-ref"), (0, f"{name}\n"))


def checks(*buckets: str) -> Reply:
    return (0, json.dumps([{"name": f"job{i}", "bucket": b} for i, b in enumerate(buckets)]))


def flow(pr: Any, runner: FakeRunner, **settings: Any) -> Any:
    clock = iter(range(0, 100_000, 30))
    return pr.PrFlow(
        Path("/repo"), settings, runner, sleep=lambda _s: None, clock=lambda: next(clock)
    )


def test_branch_name_turns_dots_into_dashes(pr: Any) -> None:
    assert flow(pr, FakeRunner()).branch_for("2.2") == "story-2-2"


def test_prepare_updates_main_and_creates_the_story_branch(pr: Any) -> None:
    runner = FakeRunner(
        ticket("planned"),
        answer(("git", "status"), OK),
        on_branch("main"),
        answer(("git", "rev-parse", "--verify"), (1, "")),
        answer(("git",), OK),
    )
    flow(pr, runner).prepare("2.2")
    assert ("git", "switch", "main") in runner.calls
    assert ("git", "pull", "--ff-only") in runner.calls
    assert runner.calls[-1] == ("git", "switch", "-c", "story-2-2")


def test_prepare_reuses_an_existing_story_branch(pr: Any) -> None:
    runner = FakeRunner(
        ticket("planned"),
        answer(("git", "status"), OK),
        on_branch("main"),
        answer(("git", "rev-parse", "--verify"), OK),
        answer(("git",), OK),
    )
    flow(pr, runner).prepare("2.2")
    assert runner.calls[-1] == ("git", "switch", "story-2-2")


def test_prepare_on_its_own_branch_changes_nothing(pr: Any) -> None:
    runner = FakeRunner(answer(("git", "status"), (0, " M src/x.py\n")), on_branch("story-2-2"))
    flow(pr, runner).prepare("2.2")
    assert not runner.ran("git", "switch")


def test_prepare_refuses_tracked_changes(pr: Any) -> None:
    runner = FakeRunner(answer(("git", "status"), (0, " M src/x.py\n")), on_branch("main"))
    with pytest.raises(pr.FlowError, match="tracked changes"):
        flow(pr, runner).prepare("2.2")
    assert not runner.ran("git", "switch")


def tickets_table(rows: dict[str, dict[str, Any]]) -> Handler:
    """Answer `tickets.py find <ref>` from a table of rows; an unknown ref is an error."""

    def handler(call: tuple[str, ...]) -> Reply | None:
        if call[:2] != ("uv", "run"):
            return None
        row = rows.get(call[-1])
        return (0, json.dumps(row)) if row else (1, json.dumps({"error": "not found"}))

    return handler


def test_prepare_waits_for_an_unmerged_prerequisite_and_makes_no_branch(pr: Any) -> None:
    runner = FakeRunner(
        tickets_table({"3.2": {"after": [1]}, "3.1": {"state": "review"}}),
        answer(("git", "status"), OK),
        on_branch("main"),
        answer(("git",), OK),
    )
    with pytest.raises(pr.FlowError, match=r"3\.1 \(review\).*merged into main"):
        flow(pr, runner).prepare("3.2")
    assert ("git", "switch", "-c", "story-3-2") not in runner.calls


def test_prepare_starts_once_prerequisites_are_done_or_dropped(pr: Any) -> None:
    rows = {
        "3.2": {"after": [1, "1.5", 3, "epic-search-baseline"]},
        "3.1": {"state": "done"},
        "1.5": {"state": "done"},
        "3.3": {"state": "dropped"},
    }
    runner = FakeRunner(
        tickets_table(rows),
        answer(("git", "status"), OK),
        on_branch("main"),
        answer(("git", "rev-parse", "--verify"), (1, "")),
        answer(("git",), OK),
    )
    flow(pr, runner).prepare("3.2")
    assert runner.calls[-1] == ("git", "switch", "-c", "story-3-2")


def test_prepare_on_its_own_branch_does_not_recheck_prerequisites(pr: Any) -> None:
    runner = FakeRunner(answer(("git", "status"), OK), on_branch("story-3-2"), tickets_table({}))
    flow(pr, runner).prepare("3.2")
    assert not runner.ran("uv")


def land_runner(status: str, *check_replies: Reply, pr_view: Reply | None = None) -> FakeRunner:
    view = pr_view or (0, json.dumps({"url": "https://example/pull/9", "state": "OPEN"}))
    return FakeRunner(
        ticket(status),
        on_branch("story-2-2"),
        answer(("git", "rev-list"), (0, "1\n")),
        answer(("gh", "pr", "view"), view),
        answer(("gh", "pr", "checks"), *(check_replies or (checks("pass"),))),
        answer(("gh",), OK),
        answer(("git",), OK),
    )


def test_land_skips_a_ticket_that_is_not_built(pr: Any) -> None:
    runner = land_runner("in-progress")
    record = flow(pr, runner).land("2.2")
    assert record["status"] == "skipped"
    assert not runner.ran("git", "push")


def test_land_pushes_waits_for_green_checks_and_merges(pr: Any) -> None:
    runner = land_runner("built", checks("pending", "pass"), checks("pass", "skipping"))
    record = flow(pr, runner).land("2.2")
    assert record == {
        "ref": "2.2",
        "branch": "story-2-2",
        "url": "https://example/pull/9",
        "status": "merged",
    }
    assert runner.ran("git", "push", "-u", "origin", "story-2-2")
    assert ("gh", "pr", "merge", "story-2-2", "--squash", "--delete-branch") in runner.calls
    assert runner.calls[-2:] == [("git", "switch", "main"), ("git", "pull", "--ff-only")]


def test_land_opens_a_pr_when_none_is_open(pr: Any) -> None:
    runner = land_runner("done", pr_view=(1, "no pull requests found"))
    flow(pr, runner).land("2.2")
    assert runner.ran("gh", "pr", "create", "--base", "main", "--head", "story-2-2")


def test_land_reports_failing_checks_and_does_not_merge(pr: Any) -> None:
    runner = land_runner("built", checks("pass", "fail"))
    record = flow(pr, runner).land("2.2")
    assert record["status"] == "failed"
    assert record["reason"] == "checks failed: job1"
    assert not runner.ran("gh", "pr", "merge")


def test_land_with_merge_off_leaves_a_green_pr_open(pr: Any) -> None:
    runner = land_runner("built")
    record = flow(pr, runner, merge=False).land("2.2")
    assert record["status"] == "open"
    assert not runner.ran("gh", "pr", "merge")


def test_land_times_out_on_checks_that_never_finish(pr: Any) -> None:
    runner = land_runner("built", checks("pending"))
    with pytest.raises(pr.FlowError, match="still running"):
        flow(pr, runner, ci_timeout_minutes=1).land("2.2")


def test_land_refuses_a_branch_with_no_commit(pr: Any) -> None:
    runner = FakeRunner(ticket("built"), on_branch("story-2-2"), answer(("git",), (0, "0\n")))
    with pytest.raises(pr.FlowError, match="no commit"):
        flow(pr, runner).land("2.2")


def test_a_merged_pending_pr_clears_and_updates_main(pr: Any) -> None:
    runner = FakeRunner(
        answer(("gh", "pr", "view"), (0, json.dumps({"url": "u", "state": "MERGED"}))),
        answer(("git",), OK),
    )
    pending = {"ref": "2.2", "branch": "story-2-2", "reason": "checks failed: x"}
    assert flow(pr, runner).resolve_pending(pending) is None
    assert ("git", "switch", "main") in runner.calls


def test_an_unmerged_pending_pr_names_the_story_and_pr(pr: Any) -> None:
    runner = FakeRunner(
        answer(("gh", "pr", "view"), (0, json.dumps({"url": "https://x/9", "state": "OPEN"})))
    )
    pending = {"ref": "2.2", "branch": "story-2-2", "url": "https://x/9", "reason": "red"}
    reason = flow(pr, runner).resolve_pending(pending)
    assert reason is not None and "2.2" in reason and "https://x/9" in reason


def plugin(pr: Any, runner: FakeRunner) -> Any:
    instance = pr.PrPlugin(None, {})
    instance.runner = runner
    return instance


def test_pre_story_pauses_while_the_last_story_has_not_landed(pr: Any) -> None:
    runner = FakeRunner(answer(("gh", "pr", "view"), (0, json.dumps({"state": "OPEN"}))))
    ctx = FakeContext("2.3")
    ctx.shared["pr_pending"] = {"ref": "2.2", "branch": "story-2-2", "reason": "red"}
    plugin(pr, runner).on_pre_story(ctx)
    assert [action for action, _ in ctx.vetoes] == ["pause"]
    assert "pr_pending" in ctx.shared


def test_pre_story_turns_any_error_into_a_pause_instead_of_raising(pr: Any) -> None:
    def boom(_call: tuple[str, ...]) -> Reply:
        raise OSError("git missing")

    ctx = FakeContext("2.2")
    plugin(pr, FakeRunner(boom)).on_pre_story(ctx)
    assert ctx.vetoes and ctx.vetoes[0][0] == "pause"


def test_hooks_ignore_units_that_are_not_tickets(pr: Any) -> None:
    runner = FakeRunner()
    ctx = FakeContext("epic-eval-gate-retrospective")
    instance = plugin(pr, runner)
    instance.on_pre_story(ctx)
    instance.on_post_story(ctx)
    assert runner.calls == [] and ctx.vetoes == [] and ctx.shared == {}


def test_post_story_records_a_failure_for_the_next_story_and_in_attention(
    pr: Any, tmp_path: Path
) -> None:
    ctx = FakeContext("2.2", run_dir=str(tmp_path))
    plugin(pr, land_runner("built", checks("fail"))).on_post_story(ctx)
    assert ctx.shared["pr_pending"]["status"] == "failed"
    assert "story 2.2 did not land" in (tmp_path / "ATTENTION").read_text()


def test_post_story_says_when_a_story_was_not_pushed_and_when_it_merged(
    pr: Any, tmp_path: Path
) -> None:
    skipped = FakeContext("2.2", run_dir=str(tmp_path))
    plugin(pr, land_runner("in-progress")).on_post_story(skipped)
    assert "pr_pending" not in skipped.shared
    assert "story 2.2 was not pushed" in (tmp_path / "ATTENTION").read_text()
    merged = FakeContext("2.2", run_dir=str(tmp_path))
    plugin(pr, land_runner("built", checks("pass"))).on_post_story(merged)
    assert "story 2.2 merged" in (tmp_path / "ATTENTION").read_text()


def test_post_story_never_raises(pr: Any, tmp_path: Path) -> None:
    def boom(_call: tuple[str, ...]) -> Reply:
        raise RuntimeError("network down")

    ctx = FakeContext("2.2", run_dir=str(tmp_path))
    plugin(pr, FakeRunner(boom)).on_post_story(ctx)
    assert ctx.shared["pr_pending"]["status"] == "failed"
    assert "network down" in ctx.shared["pr_pending"]["reason"]


# ----------------------------------------------------------------- TEA plugin

ARTIFACTS = Path("/repo/_bmad-output/test-artifacts")


def test_gate_reports_already_committed_need_no_commit(tea: Any) -> None:
    runner = FakeRunner(answer(("git", "status"), OK))
    record = tea.commit_gate_reports(Path("/repo"), ARTIFACTS, "epic-eval-gate", runner)
    assert record == {"status": "clean"}
    assert not runner.ran("git", "commit")


def test_dirty_gate_reports_are_committed_and_nothing_else(tea: Any) -> None:
    status = " M _bmad-output/test-artifacts/trace/matrix.md\n?? _bmad-output/test-artifacts/r.md\n"
    runner = FakeRunner(answer(("git", "status"), (0, status)), answer(("git",), OK))
    record = tea.commit_gate_reports(Path("/repo"), ARTIFACTS, "epic-eval-gate", runner)
    assert record["status"] == "committed"
    assert record["paths"] == [
        "_bmad-output/test-artifacts/trace/matrix.md",
        "_bmad-output/test-artifacts/r.md",
    ]
    spec = "_bmad-output/test-artifacts"
    assert ("git", "add", "--all", "--", spec) in runner.calls
    message = "test(tea): epic-eval-gate release gate"
    assert runner.calls[-1] == ("git", "commit", "--only", "-m", message, "--", spec)


def test_a_failed_commit_is_reported(tea: Any) -> None:
    runner = FakeRunner(
        answer(("git", "status"), (0, "?? _bmad-output/test-artifacts/r.md\n")),
        answer(("git", "commit"), (1, "hook rejected")),
        answer(("git",), OK),
    )
    record = tea.commit_gate_reports(Path("/repo"), ARTIFACTS, "e", runner)
    assert record["status"] == "error" and record["step"] == "commit"


def test_artifacts_outside_the_repo_are_never_committed(tea: Any) -> None:
    runner = FakeRunner()
    record = tea.commit_gate_reports(Path("/repo"), Path("/elsewhere"), "e", runner)
    assert record["status"] == "skipped" and runner.calls == []


def tea_plugin(tea: Any, runner: FakeRunner, artifacts: str | None) -> Any:
    instance = tea.TeaPlugin(None, {})
    instance.runner = runner
    instance._resolve_config = lambda _root, _key: artifacts
    return instance


def test_post_session_commits_after_the_epic_retrospective_only(tea: Any) -> None:
    runner = FakeRunner(answer(("git", "status"), OK))
    instance = tea_plugin(tea, runner, str(ARTIFACTS))
    instance.on_post_session(FakeContext("2.2", role="dev"))
    assert runner.calls == []
    ctx = FakeContext("epic-eval-gate-retrospective", role="retro")
    instance.on_post_session(ctx)
    assert ctx.shared["tea_gate_commits"]["epic-eval-gate"] == {"status": "clean"}


def test_post_session_never_raises(tea: Any) -> None:
    def boom(_call: tuple[str, ...]) -> Reply:
        raise RuntimeError("git exploded")

    ctx = FakeContext("epic-eval-gate-retrospective", role="retro")
    tea_plugin(tea, FakeRunner(boom), str(ARTIFACTS)).on_post_session(ctx)
    record = ctx.shared["tea_gate_commits"]["epic-eval-gate"]
    assert record["status"] == "error" and "git exploded" in record["output"]
