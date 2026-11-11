"""Composition root for `ticketscope-mcp`: settings, JSON logs, the API client, uvicorn.

It does not call `telemetry.setup`, which instruments psycopg; tracing is story 4.5.
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
    telemetry.configure_logging()
    client = ApiClient(settings.api_base_url, settings.api_timeout_seconds)
    app = build_app(settings, client)
    uvicorn.run(app, host=settings.http_host, port=settings.http_port, log_config=None)
