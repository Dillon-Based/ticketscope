"""`ApiClient` against a fake `/v1` (story 4.1, R-005): the body is a plain dict, `mode` is
sent exactly as given. Failures are typed errors that carry the text for the MCP client (4.2)."""

import asyncio
import json
from typing import Any

import httpx2
import pytest

from ticketscope.apiclient import (
    ApiBadResponse,
    ApiClient,
    ApiError,
    ApiUnreachable,
)
from ticketscope.core.fakes import InMemoryCorpusStore
from ticketscope.http.app import create_app
from ticketscope.settings import Settings

BODY = {"mode": "keyword", "score_kind": "bm25", "corpus_version": "v1", "results": []}


def _client(
    seen: list[dict[str, Any]], status: int = 200, body: Any = BODY, text: str | None = None
) -> ApiClient:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/v1/search"
        seen.append(json.loads(request.content))
        if text is not None:
            return httpx2.Response(status, text=text)
        return httpx2.Response(status, json=body)

    return ApiClient("http://api/", 5, transport=httpx2.MockTransport(handler))


def test_omitted_mode_and_k_are_not_in_the_body() -> None:
    seen: list[dict[str, Any]] = []
    asyncio.run(_client(seen).search("crash", None, None))
    assert seen == [{"query": "crash"}]


@pytest.mark.parametrize("mode", ["keyword", "bogus", ""])
def test_mode_is_sent_exactly_as_given(mode: str) -> None:
    seen: list[dict[str, Any]] = []
    asyncio.run(_client(seen).search("crash", mode, 3))
    assert seen == [{"query": "crash", "mode": mode, "k": 3}]


def test_unknown_response_fields_pass_through() -> None:
    seen: list[dict[str, Any]] = []
    result = asyncio.run(_client(seen, body={**BODY, "extra": {"a": 1}}).search("q", None, None))
    assert result.model_dump()["extra"] == {"a": 1}


class _FailingStore(InMemoryCorpusStore):
    def keyword_search(self, query: str, k: int) -> list[Any]:
        raise ConnectionError("database down")


async def _record(
    store: InMemoryCorpusStore, method: str, path: str, payload: dict[str, Any] | None = None
) -> httpx2.Response:
    app = create_app(store=store, settings=Settings(default_mode="keyword"))
    transport = httpx2.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx2.AsyncClient(transport=transport, base_url="http://api") as http:
        return await http.request(method, path, json=payload)


def recorded_problems() -> dict[int, httpx2.Response]:
    """Real problem answers from the app: 422, 404, 500, 503."""
    loaded = InMemoryCorpusStore(corpus_version="v")

    async def record() -> dict[int, httpx2.Response]:
        search = {"query": "crash", "mode": "bogus"}
        return {
            422: await _record(loaded, "POST", "/v1/search", search),
            404: await _record(loaded, "GET", "/v1/issues/1"),
            500: await _record(
                _FailingStore(corpus_version="v"), "POST", "/v1/search", {"query": "crash"}
            ),
            503: await _record(InMemoryCorpusStore(), "POST", "/v1/search", {"query": "crash"}),
        }

    return asyncio.run(record())


def replay(recorded: httpx2.Response) -> ApiClient:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            recorded.status_code,
            headers={"content-type": recorded.headers["content-type"]},
            content=recorded.content,
        )

    return ApiClient("http://api", 5, transport=httpx2.MockTransport(handler))


@pytest.mark.parametrize("status", [422, 404, 500, 503])
def test_a_problem_answer_carries_its_detail_verbatim(status: int) -> None:
    recorded = recorded_problems()[status]
    detail = recorded.json()["detail"]
    assert detail
    with pytest.raises(ApiError) as caught:
        asyncio.run(replay(recorded).search("q", None, None))
    assert caught.value.status == status
    assert caught.value.message == detail == caught.value.detail


def _raising(exc: Exception, timeout: float = 5) -> ApiClient:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise exc

    return ApiClient("http://api", timeout, transport=httpx2.MockTransport(handler))


@pytest.mark.parametrize(
    ("exc", "timeout", "message"),
    [
        (httpx2.ConnectError("x"), 5, "ticketscope API unreachable: connection refused"),
        (httpx2.ReadTimeout("x"), 10, "ticketscope API unreachable: timed out after 10s"),
        (httpx2.ConnectTimeout("x"), 2.5, "ticketscope API unreachable: timed out after 2.5s"),
        (httpx2.ReadError("x"), 5, "ticketscope API unreachable: connection lost"),
        (httpx2.RemoteProtocolError("x"), 5, "ticketscope API unreachable: connection lost"),
        (httpx2.DecodingError("x"), 5, "ticketscope API unreachable: connection lost"),
    ],
)
def test_transport_failures_are_unreachable(exc: Exception, timeout: float, message: str) -> None:
    with pytest.raises(ApiUnreachable) as caught:
        asyncio.run(_raising(exc, timeout).search("q", None, None))
    assert caught.value.message == message


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(502, text="<html>secret</html>", headers={"content-type": "text/html"}),
        httpx2.Response(500, json={"detail": "not a problem"}),
        httpx2.Response(
            422, content=b'{"detail": "cut', headers={"content-type": "application/problem+json"}
        ),
        httpx2.Response(
            422, json={"detail": ""}, headers={"content-type": "application/problem+json"}
        ),
        httpx2.Response(
            422, json={"detail": 7}, headers={"content-type": "application/problem+json"}
        ),
        httpx2.Response(422, json=["x"], headers={"content-type": "application/problem+json"}),
    ],
)
def test_a_non_problem_failure_names_the_status_and_never_the_body(
    response: httpx2.Response,
) -> None:
    client = ApiClient("http://api", 5, transport=httpx2.MockTransport(lambda r: response))
    with pytest.raises(ApiBadResponse) as caught:
        asyncio.run(client.search("q", None, None))
    assert caught.value.message.startswith(
        f"ticketscope API returned HTTP {response.status_code}: "
    )
    assert "secret" not in caught.value.message
    assert "<html>" not in caught.value.message


@pytest.mark.parametrize(
    "response", [httpx2.Response(200, json={"nope": 1}), httpx2.Response(200, text="x")]
)
def test_a_200_failing_the_contract_is_a_bad_response(response: httpx2.Response) -> None:
    client = ApiClient("http://api", 5, transport=httpx2.MockTransport(lambda r: response))
    with pytest.raises(ApiBadResponse) as caught:
        asyncio.run(client.search("q", None, None))
    assert caught.value.message == (
        "ticketscope API returned HTTP 200: response did not match the contract"
    )
