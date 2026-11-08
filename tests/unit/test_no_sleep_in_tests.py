"""Keep `time.sleep` out of tests/ (epic-search-baseline test review G3).

Waiting belongs in `tests/waiting.py`, which blocks on an event with a deadline instead of
sleeping, and retries only assertion failures.
"""

import ast

from tests.target import REPO

TESTS = REPO / "tests"


def sleep_calls(source: str) -> list[int]:
    """Line numbers that use `time.sleep`, called or passed, including `from time import sleep`."""
    tree = ast.parse(source)
    time_names = {"time"}
    sleep_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            time_names |= {a.asname or a.name for a in node.names if a.name == "time"}
        elif isinstance(node, ast.ImportFrom) and node.module == "time":
            sleep_names |= {a.asname or a.name for a in node.names if a.name == "sleep"}
    lines: list[int] = []
    for node in ast.walk(tree):
        # Any reference counts, not only a call: `eventually(..., wait=time.sleep)` sleeps too.
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "sleep"
            and isinstance(node.value, ast.Name)
            and node.value.id in time_names
        ) or (isinstance(node, ast.Name) and node.id in sleep_names):
            lines.append(node.lineno)
    return lines


def test_tests_never_call_time_sleep() -> None:
    hits = [
        f"{path.relative_to(REPO)}:{line}"
        for path in sorted(TESTS.rglob("*.py"))
        for line in sleep_calls(path.read_text("utf-8"))
    ]
    assert not hits, f"time.sleep in tests (use tests.waiting.eventually): {hits}"


def test_the_detector_sees_each_spelling() -> None:
    assert sleep_calls("import time\ntime.sleep(1)\n") == [2]
    assert sleep_calls("import time as t\nt.sleep(1)\n") == [2]
    assert sleep_calls("from time import sleep\nsleep(1)\n") == [2]
    assert sleep_calls("from time import sleep as nap\nnap(1)\n") == [2]
    assert sleep_calls("import time\nwait(time.sleep)\n") == [2]
    assert sleep_calls("import time\ntime.monotonic()\nwait(1)\n") == []
