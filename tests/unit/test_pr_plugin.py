"""The project-local `pr` bmad-loop plugin: a story waits for its prerequisites to be merged.

Skipped where bmad-loop is not installed (the plugin imports its base classes).
"""

import importlib.util
import json
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

pytest.importorskip("bmad_loop")

PLUGIN = Path(__file__).resolve().parents[2] / ".bmad-loop" / "plugins" / "pr" / "pr_plugin.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("pr_plugin_under_test", PLUGIN)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pr = _load()


class FakeRunner:
    """Answers git and `tickets.py find` from a table of ticket rows."""

    def __init__(self, tickets: dict[str, dict[str, Any]], branch: str = "main") -> None:
        self.tickets = tickets
        self.branch = branch
        self.calls: list[list[str]] = []

    def __call__(self, args: Sequence[str], cwd: Path, timeout_s: int) -> tuple[int, str]:
        argv = list(args)
        self.calls.append(argv)
        if argv[:3] == ["git", "rev-parse", "--abbrev-ref"]:
            return 0, self.branch + "\n"
        if argv[:2] == ["git", "status"]:
            return 0, ""
        if argv[:2] == ["git", "rev-parse"]:  # --verify the story branch: absent
            return 1, ""
        if argv[:2] == ["git", "switch"]:
            self.branch = argv[-1]
            return 0, ""
        if argv[:2] == ["git", "pull"]:
            return 0, ""
        if "find" in argv:
            row = self.tickets.get(argv[-1])
            return (0, json.dumps(row)) if row else (1, json.dumps({"error": "not found"}))
        raise AssertionError(f"unexpected command {argv}")


def _flow(tickets: dict[str, dict[str, Any]], runner: FakeRunner | None = None) -> Any:
    return pr.PrFlow(Path("."), {}, runner or FakeRunner(tickets))


def test_a_story_waits_for_an_unmerged_prerequisite() -> None:
    tickets = {
        "3.2": {"after": [1], "state": "planned"},
        "3.1": {"after": [], "state": "review"},
    }
    runner = FakeRunner(tickets)
    with pytest.raises(pr.FlowError, match=r"3\.1 \(review\).*merged into main"):
        _flow(tickets, runner).prepare("3.2")
    assert ["git", "switch", "-c", "story-3-2"] not in runner.calls


def test_a_story_starts_once_its_prerequisites_are_done() -> None:
    tickets = {
        "3.2": {"after": [1, "1.5", "epic-search-baseline"], "state": "planned"},
        "3.1": {"after": [], "state": "done"},
        "1.5": {"after": [], "state": "done"},
    }
    runner = FakeRunner(tickets)
    _flow(tickets, runner).prepare("3.2")
    assert runner.branch == "story-3-2"


def test_a_dropped_prerequisite_does_not_block() -> None:
    tickets = {"3.2": {"after": [1], "state": "planned"}, "3.1": {"after": [], "state": "dropped"}}
    assert _flow(tickets).unmet_prerequisites("3.2") == []


def test_a_resuming_story_is_not_rechecked() -> None:
    tickets = {"3.2": {"after": [1], "state": "planned"}, "3.1": {"state": "review"}}
    runner = FakeRunner(tickets, branch="story-3-2")
    _flow(tickets, runner).prepare("3.2")
    assert not any("find" in call for call in runner.calls)


def test_whole_epic_prerequisites_are_not_judged() -> None:
    tickets = {"3.2": {"after": ["epic-search-baseline"], "state": "planned"}}
    assert _flow(tickets).unmet_prerequisites("3.2") == []
