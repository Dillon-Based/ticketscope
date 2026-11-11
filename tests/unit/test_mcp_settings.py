"""The mcp fields of `Settings` (story 4.1, AD-25) and the entrypoint's refusals."""

import pytest

from ticketscope.mcp import main as mcp_main
from ticketscope.settings import Settings


def test_mcp_fields_read_from_ticketscope_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TICKETSCOPE_API_BASE_URL", "http://ticketscope-api.ticketscope.svc")
    monkeypatch.setenv("TICKETSCOPE_API_TIMEOUT_SECONDS", "3")
    monkeypatch.setenv("TICKETSCOPE_MCP_ALLOWED_HOSTS", "a.test, b.test:8443 ,")
    settings = Settings()
    assert settings.api_base_url == "http://ticketscope-api.ticketscope.svc"
    assert settings.api_timeout_seconds == 3
    assert settings.mcp_allowed_hosts == ["a.test", "b.test:8443"]


def test_defaults_are_empty_so_nothing_is_allowed_by_accident(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("API_BASE_URL", "API_TIMEOUT_SECONDS", "MCP_ALLOWED_HOSTS"):
        monkeypatch.delenv(f"TICKETSCOPE_{name}", raising=False)
    settings = Settings()
    assert settings.api_base_url == ""
    assert settings.api_timeout_seconds == 10
    assert settings.mcp_allowed_hosts == []


def test_main_fails_clearly_without_an_api_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TICKETSCOPE_API_BASE_URL", raising=False)
    with pytest.raises(SystemExit) as caught:
        mcp_main.main()
    assert "TICKETSCOPE_API_BASE_URL" in str(caught.value)
