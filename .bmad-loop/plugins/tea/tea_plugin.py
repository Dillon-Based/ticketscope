"""In-process half of the project-local v7 TEA plugin (see plugin.toml).

* ``validate``: TEA must be configured the v7 way, and an enabled epic gate
  needs ``[gates] retrospective = "auto"`` — without it the loop launches no
  session at the epic boundary and the gate would silently never run.
* ``on_pre_session``: when the session is bmad-loop's auto retrospective for a
  ticket-tree epic (task ``<epic-slug>-retrospective``, role ``retro``), prepend
  the TEA release gate for that epic to its prompt.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from bmad_loop.plugins.model import Plugin, PluginError

if TYPE_CHECKING:
    from bmad_loop.plugins.context import HookContext

RETRO_SUFFIX = "-retrospective"
SUBPROCESS_TIMEOUT_S = 60

# TEA's release-gate order: test review, NFR, then trace (the gate decision).
EPIC_GATES = (
    (
        "epic_review_enabled",
        "`bmad-tea-test-review` with `headless: true`: review the quality of the "
        "tests covering the epic's tickets and save the report.",
    ),
    (
        "epic_nfr_enabled",
        "`bmad-tea-nfr`: audit the NFR evidence for the epic and record its gate status.",
    ),
    (
        "epic_trace_enabled",
        "`bmad-tea-trace` with gate type `epic`: map the epic's requirements and "
        "its tickets' criteria to tests, and write the traceability matrix and "
        "`trace/gate-decision-epic-<epic_key>.json`.",
    ),
)


def epic_gate_prompt(
    slug: str,
    epic_file: str | None,
    test_artifacts: str,
    steps: list[str],
    bound_verdict: bool,
    trace_on: bool,
) -> str:
    target = f"epic `{slug}`" + (f" (epic file `{epic_file}`)" if epic_file else "")
    lines = [
        f"Before the retrospective, run the Test Architect release gate for {target}. "
        "Run each workflow below in Create mode, autonomously (no questions), "
        f"scoped to {target}, in this order:",
        "",
    ]
    lines += [f"{i}. {step}" for i, step in enumerate(steps, 1)]
    lines += [
        "",
        "Do not modify tests or production code, and never change any ticket's or "
        "epic's status. A workflow that halts or fails: note why, and go on to the next.",
        "",
        f"Then commit only the files those workflows wrote under `{test_artifacts}`, "
        f"in one commit with the message `test(tea): {slug} release gate`. Commit "
        "nothing else; leave every other file as it is.",
        "",
        "Then run the retrospective below. Cite the gate reports as evidence.",
    ]
    if bound_verdict and trace_on:
        lines += [
            "The trace gate decision bounds the retrospective's acceptance verdict: "
            "FAIL means the verdict is `rejected`; CONCERNS means at most "
            "`accepted-with-open-items`, with each concern as an action item; PASS or "
            "WAIVED sets no bound. If trace wrote no gate decision, say so and use at "
            "most `accepted-with-open-items`.",
        ]
    lines += ["", "---", ""]
    return "\n".join(lines)


class TeaPlugin(Plugin):
    fail_closed = False

    # ------------------------------------------------------------ readiness

    def validate(self, policy: Any) -> None:
        root = Path.cwd()
        if bool(self.settings.get("require_tea", True)):
            problems = []
            if not (root / "_bmad" / "tea").is_dir():
                problems.append(f"missing {root / '_bmad' / 'tea'}")
            if not self._resolve_config(root, "modules.tea.test_artifacts"):
                problems.append("_bmad/config.toml has no modules.tea.test_artifacts")
            if problems:
                raise PluginError(
                    "plugin 'tea' (v7): TEA is not configured in this project ("
                    + "; ".join(problems)
                    + "). Run `bmad setup tea`, or set require_tea = false under "
                    "[plugins.tea] in .bmad-loop/policy.toml."
                )
        retro = getattr(getattr(policy, "gates", None), "retrospective", None)
        if self._epic_steps() and retro is not None and retro != "auto":
            raise PluginError(
                "plugin 'tea' (v7): the epic release gate runs inside bmad-loop's auto "
                f"retrospective, but [gates] retrospective = {retro!r}. Set it to "
                '"auto" in .bmad-loop/policy.toml, or turn the epic_*_enabled '
                "settings off under [plugins.tea]."
            )

    # -------------------------------------------------------- epic gate

    def on_pre_session(self, ctx: HookContext) -> None:
        key = ctx.story_key or ""
        if ctx.role != "retro" or not key.endswith(RETRO_SUFFIX):
            return
        steps = self._epic_steps()
        if not steps or ctx.proposed_prompt is None:
            return
        slug = key[: -len(RETRO_SUFFIX)]
        root = Path(ctx.worktree or ctx.repo_root or Path.cwd())
        cfg = self._resolve_config_many(
            root, ["modules.tea.test_artifacts", "core.output_folder", "core.active_initiative"]
        )
        test_artifacts = self._expand(cfg.get("modules.tea.test_artifacts"), root) or (
            "TEA's configured test_artifacts folder"
        )
        epic_file = None
        out = self._expand(cfg.get("core.output_folder"), root)
        initiative = cfg.get("core.active_initiative")
        if out:
            pattern = f"{initiative or 'initiative-*'}/tickets/{slug}/{slug}.md"
            found = sorted(Path(out).glob(pattern))
            if len(found) == 1:  # ambiguous across initiatives: let TEA resolve the slug
                path = found[0]
                epic_file = str(path.relative_to(root) if path.is_relative_to(root) else path)
        prefix = epic_gate_prompt(
            slug,
            epic_file,
            test_artifacts,
            steps,
            bool(self.settings.get("trace_bounds_verdict", True)),
            bool(self.settings.get("epic_trace_enabled", True)),
        )
        ctx.proposed_prompt = prefix + ctx.proposed_prompt
        ctx.shared.setdefault("tea_epic_gates", {})[slug] = {
            "steps": [s.split("`")[1] for s in steps],
        }

    # --------------------------------------------------------------- helpers

    def _epic_steps(self) -> list[str]:
        return [text for key, text in EPIC_GATES if bool(self.settings.get(key, True))]

    @staticmethod
    def _expand(value: Any, root: Path) -> str | None:
        if not isinstance(value, str) or not value:
            return None
        value = value.replace("{project-root}", str(root))
        path = Path(value)
        return str(path if path.is_absolute() else root / path)

    def _resolve_config(self, root: Path, key: str) -> str | None:
        value = self._resolve_config_many(root, [key]).get(key)
        return value if isinstance(value, str) and value else None

    def _resolve_config_many(self, root: Path, keys: list[str]) -> dict[str, Any]:
        script = root / "_bmad" / "scripts" / "resolve_config.py"
        if not script.is_file():
            return {}
        cmd = ["uv", "run", str(script), "--project-root", str(root)]
        for key in keys:
            cmd += ["--key", key]
        # One exception type per clause: ruff format (project target 3.14) would
        # rewrite a tuple clause to PEP 758 syntax, which bmad-loop's 3.13 can't parse.
        try:
            proc = subprocess.run(
                cmd, cwd=root, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT_S
            )
        except OSError:
            return {}
        except subprocess.TimeoutExpired:
            return {}
        if proc.returncode != 0:
            return {}
        try:
            data = json.loads(proc.stdout)
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}
