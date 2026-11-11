"""The tool and the ASGI app (story 4.1).

Tool output is the `/v1/search` body unchanged. `mode` stays a plain string: this process has
no default mode and no mode list (AD-25), and the API judges what it is sent (R-005).
"""

import logging
import time
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from ticketscope.apiclient import ApiClient, ApiError
from ticketscope.contract.search import K_MAX, K_MIN, SearchResponse
from ticketscope.settings import Settings

TOOL_NAME = "search_similar_issues"

logger = logging.getLogger("ticketscope.mcp")


def check_allowed_hosts(hosts: list[str]) -> list[str]:
    """The hosts the server answers to; empty or a wildcard is refused at startup."""
    cleaned = [host.strip() for host in hosts if host.strip()]
    if not cleaned:
        raise ValueError("TICKETSCOPE_MCP_ALLOWED_HOSTS must name at least one host")
    for host in cleaned:
        if "*" in host.split(":", 1)[0]:
            raise ValueError(f"TICKETSCOPE_MCP_ALLOWED_HOSTS must not contain a wildcard: {host}")
    return cleaned


def build_server(client: ApiClient) -> MCPServer:
    server = MCPServer("ticketscope")

    @server.tool(
        name=TOOL_NAME,
        description=(
            "Find issues in the Mojang bug tracker that resemble a description, ranked by "
            "similarity. Each result carries the issue and what became of it."
        ),
    )
    async def search_similar_issues(  # pyright: ignore[reportUnusedFunction]
        query: Annotated[str, Field(description="The text to find similar issues for.")],
        mode: Annotated[
            str | None,
            Field(description="Retrieval mode; omit to use the server's default."),
        ] = None,
        k: Annotated[
            int | None,
            Field(description="How many results to return.", ge=K_MIN, le=K_MAX),
        ] = None,
    ) -> SearchResponse:
        started = time.monotonic()
        status = "ok"
        count = 0
        try:
            response = await client.search(query, mode, k)
            count = len(response.results)
            return response
        except ApiError as error:
            status = f"api_{error.status}"
            raise
        except BaseException:
            status = "error"
            raise
        finally:
            # The query text is never logged here (tracing owns that opt-in).
            logger.info(
                "tool call %s mode=%s k=%s status=%s results=%d duration_ms=%d",
                TOOL_NAME,
                mode,
                k,
                status,
                count,
                (time.monotonic() - started) * 1000,
            )

    @server.custom_route("/healthz", methods=["GET"])
    async def healthz(request: Request) -> Response:  # pyright: ignore[reportUnusedFunction]
        # The process only: it never calls api (R-009).
        return PlainTextResponse("ok")

    return server


def build_app(settings: Settings, client: ApiClient) -> Starlette:
    hosts = check_allowed_hosts(settings.mcp_allowed_hosts)
    return build_server(client).streamable_http_app(
        stateless_http=True,
        transport_security=TransportSecuritySettings(allowed_hosts=hosts),
        host=settings.http_host,
    )
