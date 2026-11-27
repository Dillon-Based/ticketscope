"""Composition root for `ticketscope-mcp`: settings, telemetry, the API client, uvicorn.

Telemetry is set up as `ticketscope-mcp` without psycopg instrumentation: this process
holds no database connection (AD-3). The MCP SDK emits the tool span on the global provider.
"""

import sys
from urllib.parse import urlsplit

import httpx2
import uvicorn

from ticketscope import telemetry
from ticketscope.apiclient import ApiClient
from ticketscope.mcp.auth import FETCH_TIMEOUT_SECONDS, AuthConfig
from ticketscope.mcp.server import build_app
from ticketscope.settings import Settings


def _auth_config(settings: Settings) -> AuthConfig | None:
    """The one place auth settings are read; auth half-configured never starts."""
    if not settings.mcp_auth_enabled:
        return None
    issuer = settings.mcp_auth_issuer.strip()
    audience = settings.mcp_auth_audience.strip()
    if not issuer:
        sys.exit("TICKETSCOPE_MCP_AUTH_ISSUER is required when TICKETSCOPE_MCP_AUTH_ENABLED is set")
    if not _is_absolute_http_url(issuer):
        sys.exit("TICKETSCOPE_MCP_AUTH_ISSUER must be an absolute http(s) URL")
    if issuer.endswith("/"):
        # Tokens carry `iss` without the slash, so a trailing one refuses every token.
        sys.exit("TICKETSCOPE_MCP_AUTH_ISSUER must not end with a slash")
    if not audience:
        sys.exit(
            "TICKETSCOPE_MCP_AUTH_AUDIENCE is required when TICKETSCOPE_MCP_AUTH_ENABLED is set"
        )
    if not _is_absolute_http_url(audience):
        sys.exit("TICKETSCOPE_MCP_AUTH_AUDIENCE must be an absolute http(s) URL")
    return AuthConfig(issuer=issuer, audience=audience)


def _is_absolute_http_url(value: str) -> bool:
    # http is allowed for the kind stub issuer; the EKS values use https.
    parts = urlsplit(value)
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def main() -> None:
    settings = Settings()
    if not settings.api_base_url.strip():
        sys.exit("TICKETSCOPE_API_BASE_URL is required")
    auth = _auth_config(settings)
    telemetry.setup(telemetry.SERVICE_MCP, settings.otlp_endpoint, instrument_db=False)
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    key_client = httpx2.AsyncClient(timeout=FETCH_TIMEOUT_SECONDS) if auth is not None else None
    app = build_app(settings, client, auth, key_client=key_client)
    uvicorn.run(app, host=settings.http_host, port=settings.http_port, log_config=None)
