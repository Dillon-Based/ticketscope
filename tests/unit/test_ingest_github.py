"""The read-only GitHub client: paging, retries, rate limits and the deadline."""

from typing import Any

import httpx2
import pytest

from tests.unit.ingest.replay import FakeClock
from ticketscope.adapters.github import DeadlineReached, GitHubClient, GitHubError


def _client(handler: httpx2.MockTransport, clock: FakeClock, **kwargs: Any) -> GitHubClient:
    return GitHubClient("t", transport=handler, sleep=clock.sleep, clock=clock, **kwargs)


def test_sends_token_and_api_headers() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=[])

    clock = FakeClock()
    assert list(_client(httpx2.MockTransport(handler), clock).get_pages("/x")) == [[]]
    assert seen[0].headers["authorization"] == "Bearer t"
    assert seen[0].headers["x-github-api-version"] == "2022-11-28"


def test_5xx_is_retried_then_succeeds() -> None:
    statuses = iter([502, 503, 200])

    def handler(request: httpx2.Request) -> httpx2.Response:
        status = next(statuses)
        return httpx2.Response(status, json=[{"n": 1}] if status == 200 else {})

    clock = FakeClock()
    pages = list(_client(httpx2.MockTransport(handler), clock).get_pages("/x"))
    assert pages == [[{"n": 1}]]
    assert clock.slept == [2.0, 4.0]


def test_5xx_gives_up_after_bounded_retries() -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(500, json={})

    clock = FakeClock()
    client = _client(httpx2.MockTransport(handler), clock, max_retries=3)
    with pytest.raises(GitHubError, match="giving up"):
        list(client.get_pages("/x"))
    assert calls == 4


def test_non_rate_limit_403_fails_at_once() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(403, json={"message": "Resource not accessible by token"})

    clock = FakeClock()
    with pytest.raises(GitHubError, match="403"):
        list(_client(httpx2.MockTransport(handler), clock).get_pages("/x"))
    assert not clock.slept


def test_rate_limit_wait_past_the_deadline_stops_without_sleeping() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(clock.now) + 3600)}
        return httpx2.Response(403, headers=headers, json={"message": "API rate limit exceeded"})

    clock = FakeClock()
    client = _client(httpx2.MockTransport(handler), clock, deadline=clock.now + 600)
    with pytest.raises(DeadlineReached):
        list(client.get_pages("/x"))
    assert not clock.slept


def test_next_link_off_the_api_is_refused() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200, headers={"link": '<https://evil.example/x?page=2>; rel="next"'}, json=[]
        )

    clock = FakeClock()
    with pytest.raises(GitHubError, match="refusing"):
        list(_client(httpx2.MockTransport(handler), clock).get_pages("/x"))


def test_client_has_no_write_methods() -> None:
    public = {name for name in dir(GitHubClient) if not name.startswith("_")}
    assert public == {"get_pages", "close"}
