"""Composition root for `ticketscope-mcp`: settings, telemetry, the API client, uvicorn.

Telemetry is set up as `ticketscope-mcp` without psycopg instrumentation: this process
holds no database connection (AD-3). The MCP SDK emits the tool span on the global provider.
"""

import sys

import uvicorn

from ticketscope import telemetry
from ticketscope.apiclient import ApiClient
from ticketscope.mcp.server import build_app
from ticketscope.settings import Settings


def main() -> None:
    settings = Settings()
    if not settings.api_base_url.strip():
        sys.exit("TICKETSCOPE_API_BASE_URL is required")
    telemetry.setup(telemetry.SERVICE_MCP, settings.otlp_endpoint, instrument_db=False)
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    app = build_app(settings, client)
    uvicorn.run(app, host=settings.http_host, port=settings.http_port, log_config=None)
