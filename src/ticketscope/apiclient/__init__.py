"""The client for `/v1`, for processes that reach `api` over HTTP only (`mcp`).

It builds the request body as a plain dict and sends `mode` exactly as given, so a mode the
API does not know reaches the API's own validation instead of being rejected here
(`SearchRequest`'s Literal would reject it in this process; R-005). The response is the
`/v1/search` body, validated as `SearchResponse` with unknown fields passed through (AD-20).
"""

from collections.abc import Awaitable
from typing import Any, cast
from urllib.parse import quote

import httpx2
from pydantic import BaseModel, ValidationError

from ticketscope.contract.search import IssueResponse, SearchResponse

PROBLEM_JSON = "application/problem+json"


class ApiClientError(Exception):
    """A failed call to `/v1`; `message` is the exact text the MCP client reads."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ApiError(ApiClientError):
    """A non-2xx problem+json answer from `/v1`: its status; the message is its `detail`."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


class ApiBadResponse(ApiClientError):
    """An answer that is not a usable problem or search body; never carries the body."""

    def __init__(self, status: int, reason: str) -> None:
        super().__init__(f"ticketscope API returned HTTP {status}: {reason}")
        self.status = status
        self.reason = reason


class ApiUnreachable(ApiClientError):
    """The API could not be reached or the connection broke before a full answer."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"ticketscope API unreachable: {reason}")
        self.reason = reason


def _problem_detail(response: httpx2.Response) -> str | None:
    """The `detail` of a problem+json body, or None when the response is not one."""
    media_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != PROBLEM_JSON:
        return None
    try:
        body: Any = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        detail = cast(dict[str, Any], body).get("detail")
        if isinstance(detail, str) and detail:
            return detail
    return None


class ApiClient:
    def __init__(
        self,
        base_url: str,
        timeout: float,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        self._timeout = timeout
        self._http = httpx2.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=timeout, transport=transport
        )

    async def _send(self, request: Awaitable[httpx2.Response]) -> httpx2.Response:
        try:
            return await request
        except httpx2.ConnectError as error:
            raise ApiUnreachable("connection refused") from error
        except httpx2.TimeoutException as error:
            raise ApiUnreachable(f"timed out after {self._timeout:g}s") from error
        except httpx2.RequestError as error:
            raise ApiUnreachable("connection lost") from error

    @staticmethod
    def _validated[M: BaseModel](model: type[M], response: httpx2.Response) -> M:
        if response.is_success:
            try:
                return model.model_validate(response.json())
            except (ValueError, ValidationError) as error:
                raise ApiBadResponse(
                    response.status_code, "response did not match the contract"
                ) from error
        detail = _problem_detail(response)
        if detail is None:
            raise ApiBadResponse(response.status_code, "the API did not return a problem detail")
        raise ApiError(response.status_code, detail)

    async def search(self, query: str, mode: str | None, k: int | None) -> SearchResponse:
        body: dict[str, Any] = {"query": query}
        if mode is not None:
            body["mode"] = mode
        if k is not None:
            body["k"] = k
        response = await self._send(self._http.post("/v1/search", json=body))
        return self._validated(SearchResponse, response)

    async def get_issue(self, key: str) -> IssueResponse:
        """`GET /v1/issues/by-key/{key}`, with `key` as exactly one path segment.

        It is not validated here: the API 404s anything that is not a key (C-4).
        """
        # `quote` keeps `.`, so a bare `.` or `..` is encoded by hand: it would otherwise be
        # a dot segment that the HTTP client resolves away.
        segment = (
            quote(key, safe="").replace(".", "%2E") if set(key) == {"."} else quote(key, safe="")
        )
        response = await self._send(self._http.get(f"/v1/issues/by-key/{segment}"))
        return self._validated(IssueResponse, response)

    async def aclose(self) -> None:
        await self._http.aclose()
