"""`ApiClient` against a fake `/v1` (story 4.1, R-005): the body is a plain dict, `mode` is
sent exactly as given, and a non-2xx answer carries the problem detail."""

import asyncio
import json
from typing import Any

import httpx2
import pytest

from ticketscope.apiclient import ApiClient, ApiError

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


def test_a_problem_body_gives_its_detail() -> None:
    problem = {"type": "t", "title": "Unprocessable", "status": 422, "detail": "bad mode"}
    with pytest.raises(ApiError) as caught:
        asyncio.run(_client([], 422, problem).search("q", "bogus", None))
    assert caught.value.status == 422
    assert caught.value.detail == "bad mode"


def test_a_non_json_error_still_raises_api_error() -> None:
    with pytest.raises(ApiError) as caught:
        asyncio.run(_client([], 502, text="<html>").search("q", None, None))
    assert caught.value.status == 502
