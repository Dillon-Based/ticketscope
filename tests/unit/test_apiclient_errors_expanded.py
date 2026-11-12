"""Extra edge coverage for story 4.3: problem+json media-type matching and error-text hygiene."""

import asyncio

import httpx2
import pytest

from ticketscope.apiclient import ApiBadResponse, ApiClient, ApiError, ApiUnreachable


def _client(response: httpx2.Response) -> ApiClient:
    return ApiClient("http://api", 5, transport=httpx2.MockTransport(lambda r: response))


@pytest.mark.parametrize(
    "content_type",
    [
        "application/problem+json; charset=utf-8",
        "Application/Problem+JSON",
        "  application/problem+json ;charset=utf-8",
    ],
)
def test_a_problem_media_type_matches_with_parameters_and_any_case(content_type: str) -> None:
    response = httpx2.Response(
        422, json={"detail": "mode must be one of x"}, headers={"content-type": content_type}
    )
    with pytest.raises(ApiError) as caught:
        asyncio.run(_client(response).search("q", "bogus", None))
    assert caught.value.status == 422
    assert caught.value.message == "mode must be one of x"


@pytest.mark.parametrize(
    "content_type", ["application/json", "text/plain", "application/problem+xml"]
)
def test_a_detail_under_another_media_type_is_never_surfaced(content_type: str) -> None:
    response = httpx2.Response(
        500, json={"detail": "internal secret"}, headers={"content-type": content_type}
    )
    with pytest.raises(ApiBadResponse) as caught:
        asyncio.run(_client(response).search("q", None, None))
    assert "secret" not in caught.value.message
    assert caught.value.message.startswith("ticketscope API returned HTTP 500: ")


def test_a_non_problem_answer_without_a_content_type_is_a_bad_response() -> None:
    response = httpx2.Response(503, content=b"upstream down")
    with pytest.raises(ApiBadResponse) as caught:
        asyncio.run(_client(response).search("q", None, None))
    assert "upstream down" not in caught.value.message


def test_a_problem_detail_is_verbatim_with_no_prefix_or_status() -> None:
    response = httpx2.Response(
        404,
        json={"detail": "no such thing", "status": 404},
        headers={"content-type": "application/problem+json"},
    )
    with pytest.raises(ApiError) as caught:
        asyncio.run(_client(response).search("q", None, None))
    assert str(caught.value) == caught.value.message == "no such thing"


def test_an_unreachable_message_never_carries_exception_text() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("[Errno 61] /var/secret/path Traceback")

    client = ApiClient("http://api", 5, transport=httpx2.MockTransport(handler))
    with pytest.raises(ApiUnreachable) as caught:
        asyncio.run(client.search("q", None, None))
    assert caught.value.message == "ticketscope API unreachable: connection refused"
