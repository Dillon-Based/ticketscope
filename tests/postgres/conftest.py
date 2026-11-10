"""A throwaway Postgres from the repo's image (pgvector, pg_textsearch), migrated.

Skipped unless `TICKETSCOPE_TEST_PG_IMAGE` names a built `images/postgres.Dockerfile` image
(e.g. `ticketscope-postgres:18-<sha>`) and docker is available. ci.yml's `containers` job
sets it and `TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1`, which turns that skip into a failure.
CNPG's image has no entrypoint script, so the container runs initdb itself.
"""

import os
import shutil
import subprocess
import uuid
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

from tests.target import REPO
from tests.waiting import eventually
from ticketscope.adapters.postgres import apply_migrations

IMAGE = os.environ.get("TICKETSCOPE_TEST_PG_IMAGE", "")

_START = (
    "B=/usr/lib/postgresql/18/bin; $B/initdb -D /tmp/pg --auth=trust -U postgres"
    " -E UTF8 --locale=C >/dev/null"
    ' && echo "host all all all trust" >> /tmp/pg/pg_hba.conf'
    " && exec $B/postgres -D /tmp/pg -c shared_preload_libraries=pg_textsearch"
    " -c listen_addresses=*"
)


def _docker(*args: str) -> str:
    return subprocess.run(
        ["docker", *args], capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.fixture(scope="session")
def pg_conninfo() -> Iterator[str]:
    if not IMAGE or shutil.which("docker") is None:
        # ci.yml's `containers` job sets this, so CI fails rather than silently skipping
        # the only real-SQL tests (epic 3 retro, F2).
        if os.environ.get("TICKETSCOPE_REQUIRE_CONTAINER_TESTS") == "1":
            pytest.fail("TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1 but no Postgres image or docker")
        pytest.skip("needs docker and TICKETSCOPE_TEST_PG_IMAGE")
    name = f"ticketscope-test-pg-{uuid.uuid4().hex[:8]}"
    _docker("run", "-d", "--rm", "--name", name, "-p", "127.0.0.1::5432", "--entrypoint", "bash",
            IMAGE, "-c", _START)  # fmt: skip
    try:
        port = _docker("port", name, "5432/tcp").splitlines()[0].rsplit(":", 1)[1]
        conninfo = f"host=127.0.0.1 port={port} user=postgres dbname=postgres"

        def accepts_connections() -> None:
            try:
                psycopg.connect(conninfo, autocommit=True).close()
            except psycopg.OperationalError as exc:
                raise AssertionError(f"postgres not up: {exc}") from exc

        eventually(accepts_connections, timeout=60, interval=0.5)
        with psycopg.connect(conninfo, autocommit=True) as conn:
            conn.execute("CREATE ROLE ticketscope_ro")
        apply_migrations(conninfo, Path(REPO / "migrations"))
        yield conninfo
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)
