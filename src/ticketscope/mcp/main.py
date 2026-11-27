"""Composition root for `ticketscope-mcp`: settings, telemetry, the API client, uvicorn.

Telemetry is set up as `ticketscope-mcp` without psycopg instrumentation: this process
holds no database connection (AD-3). The MCP SDK emits the tool span on the global provider.
"""

import sys
from urllib.parse import urlsplit

import uvicorn

from ticketscope import telemetry
from ticketscope.apiclient import ApiClient
from ticketscope.mcp.auth import AuthConfig
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
    if not urlsplit(issuer).scheme or not urlsplit(issuer).netloc:
        sys.exit("TICKETSCOPE_MCP_AUTH_ISSUER must be an absolute URL")
    if not audience:
        sys.exit(
            "TICKETSCOPE_MCP_AUTH_AUDIENCE is required when TICKETSCOPE_MCP_AUTH_ENABLED is set"
        )
    if not urlsplit(audience).netloc:
        sys.exit("TICKETSCOPE_MCP_AUTH_AUDIENCE must be an absolute URL")
    return AuthConfig(issuer=issuer, audience=audience)


def main() -> None:
    settings = Settings()
    if not settings.api_base_url.strip():
        sys.exit("TICKETSCOPE_API_BASE_URL is required")
    auth = _auth_config(settings)
    telemetry.setup(telemetry.SERVICE_MCP, settings.otlp_endpoint, instrument_db=False)
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    app = build_app(settings, client, auth)
    uvicorn.run(app, host=settings.http_host, port=settings.http_port, log_config=None)
