"""Story 4.4: `issue.key`, `GET /v1/issues/by-key/{key}` and the `get_issue` tool (R-007).

The expected keys come from `tests.key_oracle` and the snapshot's own `key` field, never from
the url parser under test.
"""

import asyncio
import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx2
import jsonschema
import pytest
from fastapi.testclient import TestClient

from tests import key_oracle as oracle
from tests.target import SNAPSHOT_DIR
from ticketscope.apiclient import ApiClient, ApiError
from ticketscope.contract.search import IssueResponse, SearchResponse
from ticketscope.core.derive import key_from_url
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueDetail, IssueRecord
from ticketscope.http.app import create_app
from ticketscope.mcp.server import build_app
from ticketscope.settings import Settings

HOST = "ticketscope.test"
HEADERS = {"content-type": "application/json", "accept": "application/json, text/event-stream"}
KNOWN = "MCL-9001"
KNOWN_NUMBER = 900001
PARITY = Path(__file__).resolve().parents[2] / "scripts" / "v1_parity.py"


class _SpyStore(InMemoryCorpusStore):
    """Records every number fetched, so a hostile key can be shown never to reach one."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.numbers: list[int] = []

    def get_issue(self, number: int) -> IssueDetail | None:
        self.numbers.append(number)
        return super().get_issue(number)


@pytest.fixture
def spy_store(fixture_store: InMemoryCorpusStore) -> _SpyStore:
    store = _SpyStore(corpus_version="v1")
    store.__dict__.update({k: v for k, v in fixture_store.__dict__.items() if k != "numbers"})
    store.numbers = []
    # The oracle's forbidden issue exists, so reaching it would be visible.
    forbidden = IssueRecord(
        number=oracle.FORBIDDEN_NUMBER,
        title="forbidden",
        url="https://bugs.mojang.com/browse/MCL-6629",
        kind="short",
        state="closed",
    )
    store._docs.append((forbidden, Counter()))  # pyright: ignore[reportPrivateUsage, reportArgumentType]
    return store


def _issue_line(key: str, number: int, url: str | None = None) -> dict[str, Any]:
    return {
        "issue": {
            "number": number,
            "title": "t",
            "url": url or f"https://bugs.mojang.com/browse/{key}",
            "kind": "short",
            "state": "closed",
            "key": key,
            "body": None,
        },
        "outcome": {"status": "unknown", "summary": None, "source": None, "ref": None},
    }


# --- key derivation --------------------------------------------------------------------------


@pytest.mark.parametrize(("url", "_snapshot", "expected"), oracle.URL_TO_KEY)
def test_the_url_to_key_oracle(url: str, _snapshot: str | None, expected: str | None) -> None:
    assert key_from_url(url) == expected


def test_every_fixture_issue_url_derives_its_snapshot_key() -> None:
    lines = (SNAPSHOT_DIR / "fixture.jsonl").read_text().splitlines()
    issues = [json.loads(line) for line in lines]
    assert issues
    for issue in issues:
        assert key_from_url(issue["url"]) == issue["key"]


def test_search_and_issue_bodies_carry_the_key(spy_store: _SpyStore) -> None:
    client = TestClient(create_app(store=spy_store, settings=Settings(default_mode="keyword")))
    found = client.post("/v1/search", json={"query": "widget", "mode": "keyword", "k": 50})
    results = SearchResponse.model_validate(found.json()).results
    assert results
    snapshot = {
        json.loads(line)["number"]: json.loads(line)["key"]
        for line in (SNAPSHOT_DIR / "fixture.jsonl").read_text().splitlines()
    }
    for result in results:
        assert result.issue.key == snapshot[result.issue.number]
    by_number = client.get(f"/v1/issues/{KNOWN_NUMBER}")
    assert by_number.json()["issue"]["key"] == KNOWN


def test_a_non_browse_url_gives_a_null_key() -> None:
    record = IssueRecord(
        number=7, title="x", url="https://github.com/o/r/issues/7", kind="short", state="open"
    )
    store = InMemoryCorpusStore([(record, "x")], corpus_version="v")
    client = TestClient(create_app(store=store, settings=Settings(default_mode="keyword")))
    assert client.get("/v1/issues/7").json()["issue"]["key"] is None
    assert (
        client.post("/v1/search", json={"query": "x", "mode": "keyword"}).json()["results"][0][
            "issue"
        ]["key"]
        is None
    )


def test_a_body_without_key_still_validates() -> None:
    body = _issue_line(KNOWN, 1)
    del body["issue"]["key"]
    assert IssueResponse.model_validate(body).issue.key is None


# --- the by-key route ------------------------------------------------------------------------


def test_by_key_equals_by_number(spy_store: _SpyStore) -> None:
    client = TestClient(create_app(store=spy_store, settings=Settings(default_mode="keyword")))
    by_key = client.get(f"/v1/issues/by-key/{KNOWN}")
    assert by_key.status_code == 200
    assert by_key.json() == client.get(f"/v1/issues/{KNOWN_NUMBER}").json()


def test_an_unknown_well_formed_key_is_a_404_problem(spy_store: _SpyStore) -> None:
    client = TestClient(create_app(store=spy_store, settings=Settings(default_mode="keyword")))
    response = client.get("/v1/issues/by-key/MCL-1")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


@pytest.mark.parametrize("key", [k for k in oracle.HOSTILE_KEYS if k])
def test_a_hostile_key_is_a_404_and_fetches_no_number(spy_store: _SpyStore, key: str) -> None:
    client = TestClient(create_app(store=spy_store, settings=Settings(default_mode="keyword")))
    response = client.get(f"/v1/issues/by-key/{quote(key, safe='')}")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert oracle.FORBIDDEN_NUMBER not in spy_store.numbers


def test_the_fake_store_looks_up_by_exact_url(spy_store: _SpyStore) -> None:
    found = spy_store.get_issue_by_key(KNOWN)
    assert found is not None
    assert found.issue.number == KNOWN_NUMBER
    assert spy_store.get_issue_by_key("MCL-9001 ") is None
    assert spy_store.get_issue_by_key("mcl-9001") is None


# --- the apiclient and the tool, in process --------------------------------------------------


def _tool_run(
    store: InMemoryCorpusStore,
    arguments: dict[str, Any],
    paths: list[str] | None = None,
    api: Callable[[httpx2.Request], httpx2.Response] | None = None,
) -> dict[str, Any]:
    """Call `get_issue` through the MCP app and `apiclient`, over `create_app` or a fake."""
    if api is None:
        asgi = httpx2.ASGITransport(
            app=create_app(store=store, settings=Settings(default_mode="keyword"))
        )

        transport: httpx2.AsyncBaseTransport = _Spy(asgi, paths)
    else:
        transport = _Spy(httpx2.MockTransport(api), paths)
    client = ApiClient("http://api", 5, transport=transport)
    app = build_app(Settings(mcp_allowed_hosts=HOST, api_base_url="http://api"), client)  # pyright: ignore[reportArgumentType]
    rpc = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "get_issue", "arguments": arguments},
    }

    async def main() -> dict[str, Any]:
        async with app.router.lifespan_context(app):
            asgi_mcp = httpx2.ASGITransport(app=app)
            async with httpx2.AsyncClient(transport=asgi_mcp, base_url=f"http://{HOST}") as http:
                response = await http.post("/mcp", headers=HEADERS, json=rpc)
        data = next(line for line in response.text.splitlines() if line.startswith("data: "))
        return json.loads(data.removeprefix("data: "))["result"]

    return asyncio.run(main())


class _Spy(httpx2.AsyncBaseTransport):
    def __init__(self, inner: httpx2.AsyncBaseTransport, paths: list[str] | None) -> None:
        self._inner = inner
        self._paths = paths if paths is not None else []

    async def handle_async_request(self, request: httpx2.Request) -> httpx2.Response:
        self._paths.append(request.url.raw_path.decode())
        return await self._inner.handle_async_request(request)


def test_get_issue_returns_the_issue_valid_against_the_schema(spy_store: _SpyStore) -> None:
    result = _tool_run(spy_store, {"key": KNOWN})
    assert result["isError"] is False
    body = result["structuredContent"]
    assert body["issue"]["key"] == KNOWN
    assert body["issue"]["number"] == KNOWN_NUMBER
    assert "outcome" in body
    jsonschema.validate(body, IssueResponse.model_json_schema())


def test_an_unknown_key_is_a_tool_error_with_the_api_detail(spy_store: _SpyStore) -> None:
    result = _tool_run(spy_store, {"key": "MCL-1"})
    assert result["isError"] is True
    assert result["content"][0]["text"] == "issue MCL-1 not found"


@pytest.mark.parametrize("key", oracle.HOSTILE_KEYS)
def test_a_hostile_key_is_a_tool_error_and_no_other_issue_is_fetched(
    spy_store: _SpyStore, key: str
) -> None:
    result = _tool_run(spy_store, {"key": key})
    assert result["isError"] is True
    assert "structuredContent" not in result or not result["structuredContent"]
    assert oracle.FORBIDDEN_NUMBER not in spy_store.numbers


@pytest.mark.parametrize("key", [*oracle.DOT_SEGMENT_KEYS, "..", "."])
def test_a_dot_segment_key_stays_under_by_key(spy_store: _SpyStore, key: str) -> None:
    paths: list[str] = []
    result = _tool_run(spy_store, {"key": key}, paths)
    assert result["isError"] is True
    [path] = paths
    assert path.startswith("/v1/issues/by-key/"), path
    assert path.count("/") == 4, path
    assert oracle.FORBIDDEN_NUMBER not in spy_store.numbers


def test_a_returned_key_that_differs_is_a_tool_error() -> None:
    def api(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json=_issue_line("MCL-1", 1))

    result = _tool_run(InMemoryCorpusStore(), {"key": "MCL-2"}, api=api)
    assert result["isError"] is True
    assert "structuredContent" not in result or not result["structuredContent"]


def test_a_body_with_no_key_is_a_tool_error() -> None:
    def api(request: httpx2.Request) -> httpx2.Response:
        body = _issue_line("MCL-2", 1)
        del body["issue"]["key"]
        return httpx2.Response(200, json=body)

    assert _tool_run(InMemoryCorpusStore(), {"key": "MCL-2"}, api=api)["isError"] is True


def test_apiclient_encodes_the_key_as_one_segment() -> None:
    seen: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request.url.raw_path.decode())
        return httpx2.Response(
            404, json={"detail": "x"}, headers={"content-type": "application/problem+json"}
        )

    client = ApiClient("http://api", 5, transport=httpx2.MockTransport(handler))
    with pytest.raises(ApiError):
        asyncio.run(client.get_issue("MCL-1?x=1#a/b"))
    assert seen == ["/v1/issues/by-key/MCL-1%3Fx%3D1%23a%2Fb"]


# --- the parity script's drop option ---------------------------------------------------------


def _capture(path: Path, body: dict[str, Any]) -> None:
    saved = {
        "label": path.name,
        "responses": [{"id": "q", "request": {}, "status": 200, "body": json.dumps(body)}],
    }
    path.write_text(json.dumps(saved))


def _search_body(key: str | None, title: str = "t") -> dict[str, Any]:
    issue: dict[str, Any] = {"number": 1, "title": title, "url": "u", "kind": "short"}
    if key is not None:
        issue["key"] = key
    return {"mode": "keyword", "results": [{"rank": 1, "issue": issue}]}


def _compare(tmp_path: Path, before: dict[str, Any], after: dict[str, Any], *opts: str) -> int:
    import importlib.util

    spec = importlib.util.spec_from_file_location("v1_parity", PARITY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _capture(tmp_path / "a.json", before)
    _capture(tmp_path / "b.json", after)
    return module.main(["compare", *opts, str(tmp_path / "a.json"), str(tmp_path / "b.json")])


def test_parity_passes_when_only_issue_key_differs(tmp_path: Path) -> None:
    before, after = _search_body(None), _search_body("MCL-1")
    assert _compare(tmp_path, before, after) == 1
    assert _compare(tmp_path, before, after, "--drop-issue-key") == 0


def test_parity_still_fails_on_any_other_difference(tmp_path: Path) -> None:
    before, after = _search_body(None), _search_body("MCL-1", title="changed")
    assert _compare(tmp_path, before, after, "--drop-issue-key") == 1
