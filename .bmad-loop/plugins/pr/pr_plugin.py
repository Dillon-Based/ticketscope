"""In-process half of the project-local PR-per-story plugin (see plugin.toml).

Lands every ticket bmad-loop builds through its own branch and pull request, so
CI gates each merge, the way ``scripts/loop-story-pr.sh`` does for one story:

* ``on_pre_story``: refuse to start on tracked changes; if the previous story's
  PR is still open or failed, pause until it is merged; otherwise update the
  base branch and switch to ``<prefix><ref>`` (reused when a paused story
  resumes).
* ``on_post_story``: when the ticket ended ``built`` or ``done``, push the branch,
  open (or reuse) its PR, wait for every check, squash-merge, and return to an
  updated base branch. A red check, a timeout or any error is recorded in
  ``ctx.shared`` and in the run's ATTENTION file; the next ``on_pre_story`` then
  pauses the run. ``post_story`` itself cannot veto in bmad-loop.

Hooks never raise: bmad-loop disables a plugin whose hook raises for the rest of
the run. Everything external goes through ``runner`` so tests can fake it.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bmad_loop.plugins.model import Plugin, PluginError

if TYPE_CHECKING:
    from bmad_loop.plugins.context import HookContext

SHARED_PENDING = "pr_pending"
SHARED_HISTORY = "pr_history"
# A ticket-tree ref: `<epic id>.<entry id>`, the entry id possibly carrying letters.
TICKET_REF = re.compile(r"^\d+\.[0-9A-Za-z]+$")
LANDED = frozenset({"built", "done"})
COMMAND_TIMEOUT_S = 300
FAILING_BUCKETS = frozenset({"fail", "cancel"})

# (args, cwd, timeout seconds) -> (returncode, stdout + stderr); injectable for tests.
Runner = Callable[[Sequence[str], Path, int], tuple[int, str]]


def run_command(
    args: Sequence[str], cwd: Path, timeout_s: int = COMMAND_TIMEOUT_S
) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            list(args), cwd=cwd, capture_output=True, text=True, timeout=timeout_s
        )
    except OSError as e:
        return 127, str(e)
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout_s}s: {' '.join(args)}"
    return proc.returncode, proc.stdout + proc.stderr


class FlowError(Exception):
    """A step failed; the message says which and why."""


class PrFlow:
    """The branch / PR / CI / merge steps for one project, over an injectable runner."""

    def __init__(
        self,
        root: Path,
        settings: Mapping[str, Any],
        run: Runner = run_command,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.root = root
        self.base = str(settings.get("base_branch") or "main")
        self.prefix = str(settings.get("branch_prefix") or "story-")
        self.merge = bool(settings.get("merge", True))
        self.method = str(settings.get("merge_method") or "squash")
        self.ci_timeout_s = int(settings.get("ci_timeout_minutes", 90)) * 60
        self.poll_s = int(settings.get("poll_seconds", 30))
        self.register_timeout_s = int(settings.get("checks_register_seconds", 180))
        self._run = run
        self._sleep = sleep
        self._clock = clock

    # ------------------------------------------------------------- helpers

    def branch_for(self, ref: str) -> str:
        return self.prefix + ref.replace(".", "-")

    def _ok(self, step: str, args: Sequence[str], timeout_s: int = COMMAND_TIMEOUT_S) -> str:
        rc, out = self._run(args, self.root, timeout_s)
        if rc != 0:
            raise FlowError(f"{step} failed ({' '.join(args)}): {out.strip()[-400:]}")
        return out

    def current_branch(self) -> str:
        return self._ok("read branch", ["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()

    def ticket_status(self, ref: str) -> str:
        out = self._ok(
            "find ticket",
            [
                "uv",
                "run",
                "--quiet",
                "_bmad/method/scripts/tickets.py",
                "--project-root",
                str(self.root),
                "find",
                ref,
            ],
        )
        try:
            data = json.loads(out)
        except ValueError as e:
            raise FlowError(f"find ticket {ref}: not JSON: {out.strip()[-200:]}") from e
        if not isinstance(data, dict) or "error" in data:
            raise FlowError(f"find ticket {ref}: {data}")
        return str(data.get("status") or "")

    def pr_state(self, branch: str) -> dict[str, Any] | None:
        rc, out = self._run(
            ["gh", "pr", "view", branch, "--json", "url,state"], self.root, COMMAND_TIMEOUT_S
        )
        if rc != 0:
            return None
        try:
            data = json.loads(out)
        except ValueError:
            return None
        return data if isinstance(data, dict) else None

    def update_base(self) -> None:
        self._ok("switch to base", ["git", "switch", self.base])
        self._ok("pull base", ["git", "pull", "--ff-only"])

    # ------------------------------------------------------------- pre_story

    def resolve_pending(self, pending: Mapping[str, Any]) -> str | None:
        """None when the earlier story's PR has merged (base updated); else why to pause."""
        branch = str(pending.get("branch", ""))
        state = self.pr_state(branch) if branch else None
        if state is not None and state.get("state") == "MERGED":
            self.update_base()
            return None
        where = pending.get("url") or branch or "its branch"
        return (
            f"story {pending.get('ref')} did not land: {pending.get('reason')}. "
            f"Fix and merge {where}, then `bmad-loop resume`."
        )

    def prepare(self, ref: str) -> None:
        dirty = self._ok("read status", ["git", "status", "--porcelain", "--untracked-files=no"])
        branch = self.branch_for(ref)
        if self.current_branch() == branch:
            return  # the same story resuming on its own branch
        if dirty.strip():
            raise FlowError(
                f"tracked changes in {self.root}; commit or stash them before story {ref}"
            )
        self.update_base()
        rc, _ = self._run(
            ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
            self.root,
            COMMAND_TIMEOUT_S,
        )
        if rc == 0:
            self._ok("switch to story branch", ["git", "switch", branch])
        else:
            self._ok("create story branch", ["git", "switch", "-c", branch])

    # ------------------------------------------------------------ post_story

    def wait_for_checks(self, branch: str) -> list[dict[str, Any]]:
        """Every check's final state, or FlowError on timeout."""
        started = self._clock()
        while True:
            args = ["gh", "pr", "checks", branch, "--json", "name,bucket"]
            rc, out = self._run(args, self.root, COMMAND_TIMEOUT_S)
            checks: list[dict[str, Any]] = []
            if out.strip():
                try:
                    parsed = json.loads(out)
                except ValueError:
                    parsed = []
                if isinstance(parsed, list):
                    checks = [c for c in parsed if isinstance(c, dict)]
            elapsed = self._clock() - started
            if checks and all(c.get("bucket") != "pending" for c in checks):
                return checks
            if not checks and rc != 0 and elapsed > self.register_timeout_s:
                raise FlowError(f"no checks registered on {branch} after {int(elapsed)}s")
            if elapsed > self.ci_timeout_s:
                raise FlowError(f"checks still running on {branch} after {int(elapsed)}s")
            self._sleep(self.poll_s)

    def land(self, ref: str) -> dict[str, Any]:
        branch = self.branch_for(ref)
        record: dict[str, Any] = {"ref": ref, "branch": branch}
        status = self.ticket_status(ref)
        if status not in LANDED:
            return {**record, "status": "skipped", "reason": f"ticket is {status or 'unset'!r}"}
        if self.current_branch() != branch:
            raise FlowError(f"expected to be on {branch}, not {self.current_branch()}")
        ahead = self._ok("count commits", ["git", "rev-list", "--count", f"{self.base}..HEAD"])
        if ahead.strip() in ("", "0"):
            raise FlowError(f"{branch} has no commit beyond {self.base}")
        self._ok("push", ["git", "push", "-u", "origin", branch])
        state = self.pr_state(branch)
        if state is None or state.get("state") != "OPEN":
            self._ok(
                "open PR",
                ["gh", "pr", "create", "--base", self.base, "--head", branch, "--fill"],
            )
            state = self.pr_state(branch) or {}
        record["url"] = state.get("url", "")
        checks = self.wait_for_checks(branch)
        failing = sorted(str(c.get("name")) for c in checks if c.get("bucket") in FAILING_BUCKETS)
        if failing:
            reason = f"checks failed: {', '.join(failing)}"
            return {**record, "status": "failed", "reason": reason}
        if not self.merge:
            reason = "CI green; merge is off, merge it by hand"
            return {**record, "status": "open", "reason": reason}
        self._ok("merge", ["gh", "pr", "merge", branch, f"--{self.method}", "--delete-branch"])
        self.update_base()
        return {**record, "status": "merged"}


def note_attention(run_dir: str | None, message: str) -> None:
    if not run_dir:
        return
    try:
        with (Path(run_dir) / "ATTENTION").open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] pr plugin: {message}\n")
    except OSError:
        pass


class PrPlugin(Plugin):
    fail_closed = False
    runner: Runner = staticmethod(run_command)

    def validate(self, policy: Any) -> None:
        isolation = getattr(getattr(policy, "scm", None), "isolation", None)
        if isolation is not None and isolation != "none":
            raise PluginError(
                "plugin 'pr': it puts each story on its own branch in the main checkout, "
                f'so it needs [scm] isolation = "none", not {isolation!r}.'
            )
        if shutil.which("gh") is None:
            raise PluginError("plugin 'pr': the GitHub CLI `gh` is not on PATH.")

    def _flow(self, ctx: HookContext) -> PrFlow:
        root = Path(ctx.worktree or ctx.repo_root or Path.cwd())
        return PrFlow(root, self.settings, self.runner)

    def on_pre_story(self, ctx: HookContext) -> None:
        ref = ctx.story_key or ""
        if not TICKET_REF.match(ref):
            return
        try:
            flow = self._flow(ctx)
            pending = ctx.shared.get(SHARED_PENDING)
            if isinstance(pending, dict):
                reason = flow.resolve_pending(pending)
                if reason is not None:
                    ctx.veto("pause", reason)
                    return
                ctx.shared.pop(SHARED_PENDING, None)
            flow.prepare(ref)
        except Exception as e:  # never raise: a raising hook disables the plugin
            ctx.veto("pause", f"pr plugin could not prepare story {ref}: {e}")

    def on_post_story(self, ctx: HookContext) -> None:
        ref = ctx.story_key or ""
        if not TICKET_REF.match(ref):
            return
        try:
            record = self._flow(ctx).land(ref)
        except Exception as e:  # never raise: a raising hook disables the plugin
            record = {"ref": ref, "status": "failed", "reason": str(e)}
        history = ctx.shared.setdefault(SHARED_HISTORY, [])
        if isinstance(history, list):
            history.append(record)
        if record.get("status") in ("failed", "open"):
            ctx.shared[SHARED_PENDING] = record
            where = record.get("url") or record.get("branch", "")
            note_attention(
                ctx.run_dir,
                f"story {ref} did not land ({record.get('reason')}): {where}. "
                "The next story pauses until it is merged.",
            )
