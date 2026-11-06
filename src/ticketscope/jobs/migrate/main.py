"""migrate: apply `migrations/*.sql` in order, as the app owner (AD-7, AD-22).

It runs as a post-install/pre-upgrade hook, so it first waits for the Cluster to
accept connections and for CNPG to create the `ticketscope_ro` role, which
migration 0001's default grants name.
"""

import logging
import sys

from ticketscope.adapters.postgres import apply_migrations, wait_for_database
from ticketscope.settings import Settings

log = logging.getLogger("ticketscope.migrate")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings()
    conninfo = settings.conninfo()
    try:
        wait_for_database(
            conninfo, role=settings.ro_role, timeout_s=settings.db_wait_timeout_seconds
        )
        applied = apply_migrations(conninfo, settings.migrations_dir)
    except Exception:
        log.exception("migrate failed")
        return 1
    log.info("migrate done; applied %d: %s", len(applied), ", ".join(applied) or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
