"""The client for `/v1`, for processes that reach `api` over HTTP only (`mcp`).

It builds the request body as a plain dict and sends `mode` exactly as given, so a mode the
API does not know reaches the API's own validation instead of being rejected here
(`SearchRequest`'s Literal would reject it in this process; R-005). The response is the
`/v1/search` body, validated as `SearchResponse` with unknown fields passed through (AD-20).
"""

from typing import Any, cast

import httpx2
from pydantic import ValidationError

from ticketscope.contract.search import SearchResponse

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

    async def search(self, query: str, mode: str | None, k: int | None) -> SearchResponse:
        body: dict[str, Any] = {"query": query}
        if mode is not None:
            body["mode"] = mode
        if k is not None:
            body["k"] = k
        try:
            response = await self._http.post("/v1/search", json=body)
        except httpx2.ConnectError as error:
            raise ApiUnreachable("connection refused") from error
        except httpx2.TimeoutException as error:
            raise ApiUnreachable(f"timed out after {self._timeout:g}s") from error
        except httpx2.RequestError as error:
            raise ApiUnreachable("connection lost") from error
        if response.is_success:
            try:
                return SearchResponse.model_validate(response.json())
            except (ValueError, ValidationError) as error:
                raise ApiBadResponse(
                    response.status_code, "response did not match the contract"
                ) from error
        detail = _problem_detail(response)
        if detail is None:
            raise ApiBadResponse(response.status_code, "the API did not return a problem detail")
        raise ApiError(response.status_code, detail)

    async def aclose(self) -> None:
        await self._http.aclose()
