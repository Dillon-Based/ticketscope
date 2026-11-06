"""Replays recorded GitHub REST responses for the ingest tests. No network.

A recording file holds `responses`: each a `request` key (path plus sorted query), a
`status`, `headers` and a JSON `body`. Responses for one key are served in order; the
last one repeats. A request with no recording fails the test.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx2

from ticketscope.adapters.github import GitHubClient

RECORDINGS = Path(__file__).parent / "recordings"
NOW = float(json.loads((RECORDINGS / "listing.json").read_text())["now"])


def request_key(request: httpx2.Request) -> str:
    query = urlencode(sorted(request.url.params.multi_items()))
    return request.url.path + (f"?{query}" if query else "")


@dataclass
class FakeClock:
    now: float = NOW
    tick: float = 1.0  # seconds each request takes
    slept: list[float] = field(default_factory=list[float])

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


class Replay:
    def __init__(
        self,
        clock: FakeClock,
        *,
        rate_limits: bool = True,
        files: tuple[str, ...] = ("listing.json", "timelines.json"),
    ) -> None:
        self.clock = clock
        self.requests: list[httpx2.Request] = []
        self.logins: set[str] = set()
        self._queues: dict[str, list[dict[str, Any]]] = {}
        for name in files:
            doc = json.loads((RECORDINGS / name).read_text())
            _collect_logins(doc, self.logins)
            for entry in doc["responses"]:
                if not rate_limits and entry["status"] in (403, 429):
                    continue
                self._queues.setdefault(entry["request"], []).append(entry)

    def replace(self, key: str, status: int, body: object) -> None:
        """Serve this response, and only this one, for `key`."""
        self._queues[key] = [{"request": key, "status": status, "headers": {}, "body": body}]

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        self.clock.now += self.clock.tick
        key = request_key(request)
        queue = self._queues.get(key)
        assert queue, f"no recording for {request.method} {key}"
        entry = queue.pop(0) if len(queue) > 1 else queue[0]
        return httpx2.Response(entry["status"], headers=entry["headers"], json=entry["body"])

    def client(self, *, deadline: float | None = None) -> GitHubClient:
        return GitHubClient(
            "test-token",
            transport=httpx2.MockTransport(self.handler),
            sleep=self.clock.sleep,
            clock=self.clock,
            deadline=deadline,
        )

    def timeline_numbers(self) -> list[int]:
        """Issue numbers whose timeline was requested, in request order."""
        numbers: list[int] = []
        for request in self.requests:
            parts = request.url.path.strip("/").split("/")
            if parts[-1] == "timeline":
                numbers.append(int(parts[-2]))
        return numbers


def _collect_logins(node: object, into: set[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():  # pyright: ignore[reportUnknownVariableType]
            if key == "login" and isinstance(value, str):
                into.add(value)
            else:
                _collect_logins(value, into)
    elif isinstance(node, list):
        for value in node:  # pyright: ignore[reportUnknownVariableType]
            _collect_logins(value, into)
