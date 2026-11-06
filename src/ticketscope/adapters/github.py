"""GitHub REST adapter, read only (AD-1, AD-6). Only `jobs.ingest` uses it.

The client sends `GET` and nothing else: it has no method that could write, and no
GraphQL. It follows `Link: rel="next"` pages, waits out rate limits and retries the
same request, retries 5xx a bounded number of times, and stops with `DeadlineReached`
when the caller's deadline would pass.
"""

import logging
import time
from collections.abc import Callable, Iterator, Mapping
from typing import Any, cast

import httpx2

log = logging.getLogger(__name__)

API_ORIGIN = "https://api.github.com"
API_VERSION = "2022-11-28"
_SECONDARY_LIMIT_WAIT_S = 60.0


class GitHubError(RuntimeError):
    """A response the client cannot recover from."""


class GitHubGone(GitHubError):
    """The resource moved (301), is hidden (404) or was deleted (410)."""


class DeadlineReached(Exception):
    """The deadline passed, or a rate-limit wait would run past it."""


class GitHubClient:
    """Read-only GitHub REST client."""

    def __init__(
        self,
        token: str,
        transport: httpx2.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
        *,
        deadline: float | None = None,
        max_retries: int = 5,
        timeout_s: float = 30.0,
    ) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "ticketscope-ingest",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._http = httpx2.Client(
            base_url=API_ORIGIN,
            headers=headers,
            transport=transport,
            timeout=timeout_s,
            follow_redirects=False,
        )
        self._sleep = sleep
        self._clock = clock
        self.deadline = deadline
        self._max_retries = max_retries

    def close(self) -> None:
        self._http.close()

    def get_pages(
        self, path: str, params: Mapping[str, str | int] | None = None
    ) -> Iterator[list[dict[str, Any]]]:
        """Yield each page of a list endpoint, following `Link: rel="next"`."""
        response = self._get(path, params)
        while True:
            yield _json_list(response)
            next_url = _next_link(response)
            if next_url is None:
                return
            if not next_url.startswith(API_ORIGIN + "/"):
                raise GitHubError(f"refusing to follow a next link off the API: {next_url}")
            response = self._get(next_url, None)

    def _get(self, url: str, params: Mapping[str, str | int] | None) -> httpx2.Response:
        failures = 0
        while True:
            self._check_deadline(0.0)
            try:
                response = self._http.get(url, params=dict(params) if params else None)
            except httpx2.TransportError as exc:
                failures += 1
                self._backoff(failures, f"{url}: {exc!r}")
                continue
            if response.status_code == 200:
                return response
            wait = _rate_limit_wait(response, self._clock())
            if wait is not None:
                self._check_deadline(wait)
                log.warning("rate limited on %s; waiting %.0f s", url, wait)
                self._sleep(wait)
                continue
            if response.status_code >= 500:
                failures += 1
                self._backoff(failures, f"{url}: HTTP {response.status_code}")
                continue
            error = GitHubGone if response.status_code in (301, 404, 410) else GitHubError
            raise error(f"GET {url}: HTTP {response.status_code}: {response.text[:300]}")

    def _backoff(self, failures: int, what: str) -> None:
        if failures > self._max_retries:
            raise GitHubError(f"giving up after {failures} failures: {what}")
        wait = float(2**failures)
        self._check_deadline(wait)
        log.warning("retry %d/%d in %.0f s: %s", failures, self._max_retries, wait, what)
        self._sleep(wait)

    def _check_deadline(self, wait: float) -> None:
        if self.deadline is not None and self._clock() + wait >= self.deadline:
            raise DeadlineReached


def _rate_limit_wait(response: httpx2.Response, now: float) -> float | None:
    """Seconds to wait before retrying, or None when this is not a rate-limit response."""
    if response.status_code not in (403, 429):
        return None
    headers = response.headers
    retry_after = headers.get("retry-after")
    if retry_after is not None:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            return _SECONDARY_LIMIT_WAIT_S
    if headers.get("x-ratelimit-remaining") == "0":
        reset = headers.get("x-ratelimit-reset")
        try:
            return max(0.0, float(reset) - now) + 1.0 if reset else _SECONDARY_LIMIT_WAIT_S
        except ValueError:
            return _SECONDARY_LIMIT_WAIT_S
    if response.status_code == 429 or "rate limit" in response.text.lower():
        return _SECONDARY_LIMIT_WAIT_S
    return None


def _next_link(response: httpx2.Response) -> str | None:
    links = cast(dict[str, dict[str, str]], response.links)
    url = links.get("next", {}).get("url")
    return url or None


def _json_list(response: httpx2.Response) -> list[dict[str, Any]]:
    data: object = response.json()
    if not isinstance(data, list):
        raise GitHubError(f"GET {response.request.url}: expected a JSON list")
    items = cast(list[object], data)
    if not all(isinstance(item, dict) for item in items):
        raise GitHubError(f"GET {response.request.url}: expected a list of objects")
    return cast(list[dict[str, Any]], items)
