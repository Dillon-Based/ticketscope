"""The replica check must observe calls from this run, even on a reused cluster."""

from collections.abc import Callable
from typing import Any

import pytest

from tests.mcp import test_search_tool as suite


@pytest.mark.parametrize("new_calls_on_both", [False, True])
def test_historical_logs_cannot_satisfy_the_replica_check(
    monkeypatch: pytest.MonkeyPatch, new_calls_on_both: bool
) -> None:
    counts = {"pod-a": 3, "pod-b": 4}
    calls = 0

    async def search(arguments: dict[str, Any]) -> dict[str, Any]:
        nonlocal calls
        pod = "pod-b" if new_calls_on_both and calls % 2 else "pod-a"
        counts[pod] += 1
        calls += 1
        return {"mode": "keyword"}

    def check_once(check: Callable[[], None], **kwargs: Any) -> None:
        check()

    monkeypatch.setattr(suite, "_mcp_pods", lambda: list(counts))
    monkeypatch.setattr(suite, "_pod_log", lambda pod: f"tool call {suite.TOOL}\n" * counts[pod])
    monkeypatch.setattr(suite, "_search", search)
    monkeypatch.setattr(suite, "eventually", check_once)

    if new_calls_on_both:
        suite.test_fresh_connections_are_served_by_both_replicas()
    else:
        with pytest.raises(AssertionError, match="no new tool call logged by pod-b"):
            suite.test_fresh_connections_are_served_by_both_replicas()
    assert calls == 20
