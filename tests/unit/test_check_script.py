"""scripts/check.sh mirrors the static jobs of ci.yml, and the two cannot drift: every command
the script runs appears in the workflow, and every such command in the workflow is run by it."""

import re

import pytest

from tests.target import REPO

CHECK = (REPO / "scripts" / "check.sh").read_text(encoding="utf-8")
CI = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

# What the workflow's static jobs run, by tool. A command here must be run by the script.
CI_COMMANDS = re.compile(
    r"uv run (?:ruff check \.|ruff format --check \.|pyright|lint-imports)"
    r"|python3 scripts/render_readme_table\.py --check"
    r"|terraform -chdir=\S+ (?:fmt -check|init -backend=false|validate)"
    r"|actionlint -ignore '[^']+'"
    r"|shellcheck scripts/\S+"
)


def _script_commands() -> list[str]:
    return re.findall(r"^run (.+)$", CHECK, re.MULTILINE)


@pytest.mark.criterion("ticketscope--e5-s3--AC-7")
def test_every_command_check_sh_runs_is_in_ci() -> None:
    commands = _script_commands()
    assert commands, "scripts/check.sh runs nothing"
    for command in commands:
        assert command in CI, f"scripts/check.sh runs `{command}`, which ci.yml does not"


@pytest.mark.criterion("ticketscope--e5-s3--AC-7")
def test_every_static_ci_command_is_run_by_check_sh() -> None:
    in_ci = set(CI_COMMANDS.findall(CI))
    assert in_ci, "no static commands found in ci.yml; the pattern is stale"
    commands = set(_script_commands())
    for command in in_ci:
        assert command in commands, f"ci.yml runs `{command}`, which scripts/check.sh does not"
