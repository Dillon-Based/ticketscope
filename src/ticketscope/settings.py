"""The only source of configuration: `TICKETSCOPE_*` environment variables.

Chart values map to these variables; secrets reach them from CNPG or chart Secrets.
"""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TICKETSCOPE_", extra="ignore")

    # Database. `api` gets ticketscope_ro; `migrate` and `load` get the app owner (AD-7).
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "app"
    db_user: str = "app"
    db_password: SecretStr = SecretStr("")
    db_connect_timeout_seconds: int = 5

    # Retrieval (AD-25: the chart's values.yaml sets the real default).
    default_mode: str = "keyword"

    # api
    http_host: str = "0.0.0.0"
    http_port: int = 8080

    # migrate
    migrations_dir: Path = Path("migrations")
    ro_role: str = "ticketscope_ro"
    db_wait_timeout_seconds: int = 900

    # load
    snapshot_version: str = "fixture"
    snapshot_dir: Path = Path("snapshots")

    def conninfo(self) -> str:
        """A libpq keyword/value connection string."""
        parts = {
            "host": self.db_host,
            "port": str(self.db_port),
            "dbname": self.db_name,
            "user": self.db_user,
            "password": self.db_password.get_secret_value(),
            "connect_timeout": str(self.db_connect_timeout_seconds),
            "application_name": "ticketscope",
        }
        return " ".join(f"{key}={_quote(value)}" for key, value in parts.items())


def _quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"
