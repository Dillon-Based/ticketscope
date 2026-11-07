"""Suite-wide hooks.

`@pytest.mark.criterion("<story key>--AC-<n>", ...)` names the acceptance criteria a test
establishes. Each id is written to the JUnit report as a `criterion` property, so
`scripts/live_results.py` can turn a CI run into trace live-verification results without
a hand-kept test-to-criterion table.
"""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        for marker in item.iter_markers("criterion"):
            for criterion in marker.args:
                item.user_properties.append(("criterion", str(criterion)))
