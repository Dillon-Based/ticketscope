"""The client for `/v1`, for processes that reach `api` over HTTP only (`mcp`).

It builds the request body as a plain dict and sends `mode` exactly as given, so a mode the
API does not know reaches the API's own validation instead of being rejected here
(`SearchRequest`'s Literal would reject it in this process; R-005). The response is the
`/v1/search` body, validated as `SearchResponse` with unknown fields passed through (AD-20).
"""

from typing import Any, cast

import httpx2

from ticketscope.contract.search import SearchResponse


class ApiError(Exception):
    """A non-2xx answer from `/v1`: its status and the problem `detail`, when it has one."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(f"api returned {status}: {detail}")
        self.status = status
        self.detail = detail


def _detail(response: httpx2.Response) -> str:
    try:
        body: Any = response.json()
    except ValueError:
        return response.reason_phrase
    if isinstance(body, dict):
        detail = cast(dict[str, Any], body).get("detail")
        if isinstance(detail, str) and detail:
            return detail
    return response.reason_phrase


class ApiClient:
    def __init__(
        self,
        base_url: str,
        timeout: float,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        self._http = httpx2.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=timeout, transport=transport
        )

    async def search(self, query: str, mode: str | None, k: int | None) -> SearchResponse:
        body: dict[str, Any] = {"query": query}
        if mode is not None:
            body["mode"] = mode
        if k is not None:
            body["k"] = k
        response = await self._http.post("/v1/search", json=body)
        if response.is_success:
            return SearchResponse.model_validate(response.json())
        raise ApiError(response.status_code, _detail(response))

    async def aclose(self) -> None:
        await self._http.aclose()
