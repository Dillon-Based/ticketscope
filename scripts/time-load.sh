#!/usr/bin/env bash
# Times a load of a snapshot into the in-repo Postgres image, through story 1's
# path: `ticketscope-migrate`, then `ticketscope-load` (initiative R10).
#
#   scripts/time-load.sh <snapshot-dir> <version>
#
# <snapshot-dir> holds <version>.jsonl.gz and <version>-kinds.json, as ingest
# writes them. Starts a throwaway container (initdb + postgres with
# pg_textsearch preloaded), creates the extensions, the app owner and the
# ticketscope_ro role as CNPG would, runs migrate, then times load.
# Logs go to stderr; the last line on stdout is the load time in seconds.
#
# Env overrides:
#   POSTGRES_IMAGE  image to run (default: ticketscope-postgres:18-local, built
#                   from images/postgres.Dockerfile if missing)
#   RUN             command prefix for the app entry points (default: "uv run")
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <snapshot-dir> <version>" >&2
  exit 2
fi
SNAPSHOT_DIR="$(cd "$1" && pwd)"
VERSION="$2"
for f in "${SNAPSHOT_DIR}/${VERSION}.jsonl.gz" "${SNAPSHOT_DIR}/${VERSION}-kinds.json"; do
  [[ -f "$f" ]] || { echo "missing $f" >&2; exit 2; }
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

POSTGRES_IMAGE="${POSTGRES_IMAGE:-ticketscope-postgres:18-local}"
RUN="${RUN:-uv run}"
CONTAINER="ticketscope-timeload-$$"
PG_BIN=/usr/lib/postgresql/18/bin

log() { echo "[time-load] $*" >&2; }
now() { python3 -c 'import time; print(f"{time.time():.3f}")'; }

if ! docker image inspect "$POSTGRES_IMAGE" >/dev/null 2>&1; then
  log "building ${POSTGRES_IMAGE}"
  docker build -f images/postgres.Dockerfile -t "$POSTGRES_IMAGE" . >&2
fi

cleanup() { docker rm -f "$CONTAINER" >/dev/null 2>&1 || true; }
trap cleanup EXIT

log "starting ${POSTGRES_IMAGE}"
# The CNPG image has no entrypoint script: init a cluster and start postgres directly.
docker run -d --name "$CONTAINER" -p 127.0.0.1::5432 --entrypoint /bin/bash \
  "$POSTGRES_IMAGE" -c "
    set -e
    export PGDATA=/tmp/pgdata
    ${PG_BIN}/initdb -U postgres --auth=trust >/dev/null
    echo 'host all all 0.0.0.0/0 trust' >> \$PGDATA/pg_hba.conf
    exec ${PG_BIN}/postgres -c listen_addresses='*' \
      -c shared_preload_libraries=pg_textsearch
  " >/dev/null

for _ in $(seq 1 60); do
  if docker exec "$CONTAINER" ${PG_BIN}/pg_isready -h 127.0.0.1 -U postgres >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec "$CONTAINER" ${PG_BIN}/pg_isready -h 127.0.0.1 -U postgres >&2

psql() { docker exec -i "$CONTAINER" ${PG_BIN}/psql -h 127.0.0.1 -U postgres -v ON_ERROR_STOP=1 -q "$@"; }
psql -d postgres -c "CREATE ROLE app LOGIN" -c "CREATE ROLE ticketscope_ro LOGIN" \
  -c "CREATE DATABASE app OWNER app" >&2
psql -d app -c "CREATE EXTENSION IF NOT EXISTS vector" \
  -c "CREATE EXTENSION IF NOT EXISTS pg_textsearch" >&2

PORT="$(docker port "$CONTAINER" 5432/tcp | head -n1 | sed 's/.*://')"
export TICKETSCOPE_DB_HOST=127.0.0.1
export TICKETSCOPE_DB_PORT="$PORT"
export TICKETSCOPE_DB_NAME=app
export TICKETSCOPE_DB_USER=app
export TICKETSCOPE_DB_PASSWORD=""
export TICKETSCOPE_DB_WAIT_TIMEOUT_SECONDS=60
export TICKETSCOPE_MIGRATIONS_DIR="${ROOT}/migrations"
export TICKETSCOPE_SNAPSHOT_DIR="$SNAPSHOT_DIR"
export TICKETSCOPE_SNAPSHOT_VERSION="$VERSION"

log "migrate"
$RUN ticketscope-migrate >&2

log "load ${VERSION}"
START="$(now)"
$RUN ticketscope-load >&2
END="$(now)"
SECONDS_TAKEN="$(python3 -c "print(f'{${END} - ${START}:.1f}')")"
log "load took ${SECONDS_TAKEN} s"
echo "$SECONDS_TAKEN"
