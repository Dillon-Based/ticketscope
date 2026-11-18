"""The runbooks are pasted into a shell by a person, so a command in a code fence must run as
written. A `<placeholder>` in a fence does not: the shell reads `<` as a redirect and zsh stops with
a parse error. Fill such values from the environment (`eks-env.sh` exports them) instead."""

import re
from pathlib import Path

import pytest

from tests.target import REPO

RUNBOOKS = sorted((REPO / "docs" / "runbooks").glob("*.md"))
SHELL_FENCES = {"sh", "bash", "zsh", "shell"}
PLACEHOLDER = re.compile(r"(?<![<\w])<[A-Za-z][A-Za-z0-9 _.-]*>")


def _shell_lines(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            fence = None if fence is not None else stripped.removeprefix("```").strip() or "plain"
            continue
        if fence in SHELL_FENCES and not stripped.startswith("#"):
            found.append((number, line))
    return found


def test_there_are_runbooks_to_check() -> None:
    assert RUNBOOKS, "docs/runbooks has no runbook; the glob is stale"


@pytest.mark.criterion("ticketscope--e5-s3--AC-9")
@pytest.mark.parametrize("runbook", RUNBOOKS, ids=lambda p: p.name)
def test_no_shell_command_holds_a_placeholder_in_angle_brackets(runbook: Path) -> None:
    bad = [
        f"{runbook.name}:{number}: {line.strip()}"
        for number, line in _shell_lines(runbook.read_text(encoding="utf-8"))
        if PLACEHOLDER.search(line)
    ]
    assert not bad, "angle-bracket placeholder in a shell fence:\n" + "\n".join(bad)


def test_the_check_would_catch_the_placeholder_that_broke_zsh() -> None:
    text = '```sh\neval "$(scripts/eks-env.sh <fixed hostname>)"\n```\n'
    assert _shell_lines(text) and PLACEHOLDER.search(_shell_lines(text)[0][1])
