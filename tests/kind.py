"""Where the kind cluster's Gateway is, for the `-m kind` tests in `tests/smoke` and `tests/mcp`."""

import os

import pytest


def gateway() -> tuple[str, str]:
    """The Gateway's URL and the route hostname to send as `Host`."""
    url = os.environ.get("TICKETSCOPE_GATEWAY_URL")
    host = os.environ.get("TICKETSCOPE_GATEWAY_HOST")
    if not url or not host:
        pytest.fail("TICKETSCOPE_GATEWAY_URL and TICKETSCOPE_GATEWAY_HOST must be set")
    return url.rstrip("/"), host
