"""AD-1 allow-list: core imports only stdlib and pydantic; contract only pydantic (+ stdlib).

import-linter's contracts are deny-lists, so this closes the gap for any
third-party package they do not name.
"""

import ast
import sys
from pathlib import Path

import pytest

from tests.target import REPO

SRC = REPO / "src" / "ticketscope"


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import: stays inside the package
                continue
            modules.append(node.module or "")
    return modules


def _allowed(module: str, own: str) -> bool:
    top = module.split(".")[0]
    return (
        top in sys.stdlib_module_names
        or top == "pydantic"
        or module == own
        or module.startswith(own + ".")
    )


@pytest.mark.parametrize("package", ["core", "contract"])
def test_layer_imports_only_stdlib_pydantic_and_itself(package: str) -> None:
    own = f"ticketscope.{package}"
    files = sorted((SRC / package).rglob("*.py"))
    assert files
    bad = [
        f"{path.relative_to(REPO)}: {module}"
        for path in files
        for module in _imported_modules(path)
        if not _allowed(module, own)
    ]
    assert not bad, f"{own} imports outside its allow-list: {bad}"
