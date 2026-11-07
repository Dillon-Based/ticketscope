"""[P1] AD-1 contracts reject planted imports in disposable source copies.

The real CLI builds the copied package's graph. Source files in the checkout are
never patched, and a clean control prevents a missing package or broken setup from
being mistaken for enforcement of the intended contract.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.target import REPO


@pytest.fixture
def copied_project(tmp_path: Path) -> Path:
    shutil.copytree(REPO / "src", tmp_path / "src", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(REPO / ".importlinter", tmp_path / ".importlinter")
    return tmp_path


def _lint(project: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from importlinter.cli import lint_imports_command; lint_imports_command()",
            "--config",
            str(project / ".importlinter"),
            "--no-cache",
            "--no-logo",
        ],
        cwd=project,
        env={**os.environ, "PYTHONPATH": str(project / "src")},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_clean_source_copy_keeps_all_layer_contracts(copied_project: Path) -> None:
    result = _lint(copied_project)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "Contracts: 7 kept, 0 broken." in output


@pytest.mark.parametrize(
    ("source", "forbidden", "contract"),
    [
        (
            "core/modes.py",
            "ticketscope.adapters.postgres",
            "core imports only stdlib and pydantic",
        ),
        (
            "contract/search.py",
            "ticketscope.core.model",
            "contract imports only pydantic",
        ),
    ],
    ids=["core-imports-adapter", "contract-imports-core"],
)
def test_forbidden_import_breaks_its_named_contract(
    copied_project: Path, source: str, forbidden: str, contract: str
) -> None:
    path = copied_project / "src" / "ticketscope" / source
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"\nimport {forbidden}\n")

    result = _lint(copied_project)
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert f"{contract} BROKEN" in output
    assert forbidden in output
    source_module = "ticketscope." + source.removesuffix(".py").replace("/", ".")
    assert f"{source_module} -> {forbidden}" in output
