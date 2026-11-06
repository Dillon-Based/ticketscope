import pytest

from ticketscope.settings import Settings


def test_settings_read_ticketscope_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TICKETSCOPE_DB_USER", "ticketscope_ro")
    monkeypatch.setenv("TICKETSCOPE_DB_PASSWORD", "p'w\\d")
    monkeypatch.setenv("TICKETSCOPE_DEFAULT_MODE", "keyword")
    settings = Settings()
    assert settings.db_user == "ticketscope_ro"
    conninfo = settings.conninfo()
    assert "user='ticketscope_ro'" in conninfo
    assert "password='p\\'w\\\\d'" in conninfo
