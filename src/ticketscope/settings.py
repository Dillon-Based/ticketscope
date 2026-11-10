"""The only source of configuration: `TICKETSCOPE_*` environment variables.

Chart values map to these variables; secrets reach them from CNPG or chart Secrets.
"""

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TICKETSCOPE_", extra="ignore")

    # Database. `api` and `eval` get ticketscope_ro; `migrate` and `load` get the app owner (AD-7).
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "app"
    db_user: str = "app"
    db_password: SecretStr = SecretStr("")
    db_connect_timeout_seconds: int = 5

    # Retrieval (AD-25: the chart's values.yaml sets the real default).
    default_mode: str = "keyword"

    # Embeddings (AD-21). An empty model id means no embeddings: dense is unavailable.
    # `embeddings_compute` lets `load` compute them when no asset is pinned (kind only; the
    # chart sets it).
    embedding_model_id: str = ""
    embeddings_compute: bool = False
    # Where the baked model lives; the runtime is offline (HF_HUB_OFFLINE=1).
    embedding_cache_dir: Path = Path("/models")

    # Traces (AD-10): OTLP/HTTP base URL of the in-cluster collector; empty exports nothing.
    otlp_endpoint: str = ""
    # Query text goes on the retrieval span only when this is true.
    trace_query_text: bool = False

    # api
    http_host: str = "0.0.0.0"
    http_port: int = 8080

    # migrate
    migrations_dir: Path = Path("migrations")
    ro_role: str = "ticketscope_ro"
    db_wait_timeout_seconds: int = 900

    # load: the pin (AD-6, AD-25). The chart's values.yaml sets version and checksum.
    snapshot_version: str = "fixture"
    snapshot_sha256: str = ""
    snapshot_base_url: str = "https://github.com/Dillon-Based/ticketscope/releases/download"
    snapshot_download_timeout_seconds: int = 300
    snapshot_dir: Path = Path("snapshots")

    # load: the pinned embedding asset (AD-6, AD-25). The snapshot version it was built from
    # and its checksum; both empty means no pin, and `embeddings_compute` applies instead.
    # A pinned asset always wins. It is fetched from `snapshot_base_url` into `snapshot_dir`.
    embeddings_asset_version: str = ""
    embeddings_sha256: str = ""

    # eval: the labelled pairs, one `<snapshot_version>.jsonl` per snapshot (AD-26).
    eval_pairs_dir: Path = Path("eval/pairs")

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
