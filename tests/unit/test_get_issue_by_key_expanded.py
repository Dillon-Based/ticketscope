"""Story 4.4 expanded coverage: key-pattern edges, the by-key 503, apiclient failure modes,
and the parity script's drop option on non-search bodies. Complements test_get_issue_by_key.py.
"""

import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient

from ticketscope.apiclient import ApiBadResponse, ApiClient, ApiError, ApiUnreachable
from ticketscope.core.derive import MOJANG_BROWSE_URL, is_issue_key, key_from_url
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.core.model import IssueRecord
from ticketscope.http.app import create_app
from ticketscope.settings import Settings

PARITY = Path(__file__).resolve().parents[2] / "scripts" / "v1_parity.py"


@pytest.mark.parametrize("key", ["MCL-1", "A-1", "A1B2-90", "REALMS-12", "MC2-3"])
def test_well_formed_keys_match(key: str) -> None:
    assert is_issue_key(key)


@pytest.mark.parametrize(
    "key",
    [
        "MCL-0",  # number starts at 1
        "MCL-01",  # no leading zero
        "MCL-",
        "-1",
        "1MCL-1",  # prefix starts with a letter
        "mcl-1",
        "MCL-1\n",  # `$` alone would admit a trailing newline
        "\nMCL-1",
        "MCL-1 ",
        "MCL-\u0661",  # Arabic-indic digit, not [0-9]
        "MCL-1-2",
        "",
    ],
)
def test_malformed_keys_do_not_match(key: str) -> None:
    assert not is_issue_key(key)


@pytest.mark.parametrize(
    "url",
    [
        MOJANG_BROWSE_URL + "MCL-1\n",
        MOJANG_BROWSE_URL + "mcl-1",
        MOJANG_BROWSE_URL,
        MOJANG_BROWSE_URL + "MCL-1?x=1",
        "",
    ],
)
def test_key_from_url_is_none_for_a_malformed_tail(url: str) -> None:
    assert key_from_url(url) is None


def _store(version: str | None) -> InMemoryCorpusStore:
    record = IssueRecord(
        number=5, title="x", url=MOJANG_BROWSE_URL + "MCL-5", kind="short", state="open"
    )
    return InMemoryCorpusStore([(record, "x")], corpus_version=version)


def test_by_key_is_503_when_no_corpus_is_loaded() -> None:
    client = TestClient(create_app(store=_store(None), settings=Settings(default_mode="keyword")))
    response = client.get("/v1/issues/by-key/MCL-5")
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")


def test_by_key_trailing_newline_is_404_not_the_issue() -> None:
    client = TestClient(create_app(store=_store("v"), settings=Settings(default_mode="keyword")))
    assert client.get("/v1/issues/by-key/MCL-5").status_code == 200
    assert client.get("/v1/issues/by-key/MCL-5%0A").status_code == 404


def test_by_key_does_not_shadow_numeric_lookup() -> None:
    client = TestClient(create_app(store=_store("v"), settings=Settings(default_mode="keyword")))
    assert client.get("/v1/issues/5").json() == client.get("/v1/issues/by-key/MCL-5").json()


# --- apiclient failure modes for get_issue ---------------------------------------------------


def _client(handler: Any) -> ApiClient:
    return ApiClient("http://api", 5, transport=httpx2.MockTransport(handler))


def test_get_issue_connection_failure_is_api_unreachable() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("refused")

    with pytest.raises(ApiUnreachable):
        asyncio.run(_client(handler).get_issue("MCL-1"))


def test_get_issue_timeout_is_api_unreachable() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("slow")

    with pytest.raises(ApiUnreachable):
        asyncio.run(_client(handler).get_issue("MCL-1"))


def test_get_issue_non_problem_error_is_bad_response() -> None:
    with pytest.raises(ApiBadResponse):
        asyncio.run(_client(lambda r: httpx2.Response(502, text="<html>")).get_issue("MCL-1"))


def test_get_issue_200_that_is_not_the_contract_is_bad_response() -> None:
    with pytest.raises(ApiBadResponse):
        asyncio.run(_client(lambda r: httpx2.Response(200, json={"nope": 1})).get_issue("MCL-1"))


def test_get_issue_problem_detail_is_carried() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            404,
            json={"detail": "issue MCL-1 not found"},
            headers={"content-type": "application/problem+json"},
        )

    with pytest.raises(ApiError) as info:
        asyncio.run(_client(handler).get_issue("MCL-1"))
    assert info.value.status == 404
    assert info.value.detail == "issue MCL-1 not found"


@pytest.mark.parametrize(("key", "tail"), [(".", "%2E"), ("..", "%2E%2E"), ("...", "%2E%2E%2E")])
def test_get_issue_encodes_all_dot_keys(key: str, tail: str) -> None:
    seen: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request.url.raw_path.decode())
        return httpx2.Response(404, text="x")

    with pytest.raises(ApiBadResponse):
        asyncio.run(_client(handler).get_issue(key))
    assert seen == [f"/v1/issues/by-key/{tail}"]


# --- parity drop option ----------------------------------------------------------------------


def _load_parity() -> Any:
    spec = importlib.util.spec_from_file_location("v1_parity_expanded", PARITY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_drop_issue_key_touches_only_issue_key() -> None:
    module = _load_parity()
    body = json.dumps(
        {
            "key": "top",
            "results": [{"key": "result", "issue": {"key": "MCL-1", "title": "t"}}],
        }
    )
    assert json.loads(module._without_issue_key(body)) == {
        "key": "top",
        "results": [{"key": "result", "issue": {"title": "t"}}],
    }


@pytest.mark.parametrize(
    "body", ["not json", "[1, 2]", '{"detail": "x"}', '{"results": [1, null]}']
)
def test_drop_issue_key_leaves_other_bodies_alone(body: str) -> None:
    module = _load_parity()
    out = module._without_issue_key(body)
    assert out == body or json.loads(out) == json.loads(body)
