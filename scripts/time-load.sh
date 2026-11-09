#!/usr/bin/env bash
# Times a load of a snapshot into the in-repo Postgres image, through story 1's
# path: `ticketscope-migrate`, then `ticketscope-load` (initiative R10).
#
#   scripts/time-load.sh <snapshot-dir> <version>
#
# <snapshot-dir> holds <version>.jsonl.gz, as ingest writes it or as downloaded
# from its Release. load verifies it against TICKETSCOPE_SNAPSHOT_SHA256, which
# this script sets to the file's own SHA-256 (the asset is the one being timed). Starts a throwaway container (initdb + postgres with
# pg_textsearch preloaded), creates the extensions, the app owner and the
# ticketscope_ro role as CNPG would, runs migrate, then times load.
# Logs go to stderr; the last line on stdout is the load time in seconds.
#
# With EMBEDDINGS_FILE (a file in <snapshot-dir> named as the embedding asset is) and
# EMBEDDING_MODEL_ID, load also takes the pinned embedding asset: it is served from
# 127.0.0.1 and downloaded by load as from a Release, so the time covers the asset
# download, its checksum, and the bulk load of the vectors (story 4).
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
ASSET="${SNAPSHOT_DIR}/${VERSION}.jsonl.gz"
[[ -f "$ASSET" ]] || { echo "missing $ASSET" >&2; exit 2; }
if command -v sha256sum >/dev/null; then
  SHA256="$(sha256sum "$ASSET" | cut -d' ' -f1)"
else
  SHA256="$(shasum -a 256 "$ASSET" | cut -d' ' -f1)"
fi

EMBEDDINGS_FILE="${EMBEDDINGS_FILE:-}"
if [[ -n "$EMBEDDINGS_FILE" ]]; then
  [[ -f "${SNAPSHOT_DIR}/${EMBEDDINGS_FILE}" ]] || { echo "missing ${EMBEDDINGS_FILE}" >&2; exit 2; }
  [[ -n "${EMBEDDING_MODEL_ID:-}" ]] || { echo "EMBEDDING_MODEL_ID is required" >&2; exit 2; }
  if command -v sha256sum >/dev/null; then
    EMB_SHA256="$(sha256sum "${SNAPSHOT_DIR}/${EMBEDDINGS_FILE}" | cut -d' ' -f1)"
  else
    EMB_SHA256="$(shasum -a 256 "${SNAPSHOT_DIR}/${EMBEDDINGS_FILE}" | cut -d' ' -f1)"
  fi
fi

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

WORK=""
SERVER_PID=""
cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  if [[ -n "$SERVER_PID" ]]; then kill "$SERVER_PID" 2>/dev/null || true; fi
  if [[ -n "$WORK" ]]; then rm -rf "$WORK"; fi
}
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
export TICKETSCOPE_SNAPSHOT_SHA256="$SHA256"

if [[ -n "$EMBEDDINGS_FILE" ]]; then
  # load finds the snapshot locally and downloads the embedding asset from a loopback
  # server laid out as a Release is: <tag>/<asset>.
  WORK="$(mktemp -d)"
  mkdir -p "${WORK}/snapshots" "${WORK}/serve/${EMBEDDINGS_FILE%.jsonl.gz}"
  cp "$ASSET" "${WORK}/snapshots/"
  ln -s "${SNAPSHOT_DIR}/${EMBEDDINGS_FILE}" "${WORK}/serve/${EMBEDDINGS_FILE%.jsonl.gz}/${EMBEDDINGS_FILE}"
  python3 -u -m http.server 0 --bind 127.0.0.1 --directory "${WORK}/serve" \
    >"${WORK}/server.log" 2>&1 &
  SERVER_PID=$!
  disown "$SERVER_PID" 2>/dev/null || true
  for _ in $(seq 1 50); do
    grep -q "port" "${WORK}/server.log" 2>/dev/null && break
    sleep 0.2
  done
  SERVE_PORT="$(sed -n 's/.*port \([0-9][0-9]*\).*/\1/p' "${WORK}/server.log" | head -n1)"
  [[ -n "$SERVE_PORT" ]] || { echo "asset server did not start" >&2; exit 1; }
  export TICKETSCOPE_SNAPSHOT_DIR="${WORK}/snapshots"
  export TICKETSCOPE_SNAPSHOT_BASE_URL="http://127.0.0.1:${SERVE_PORT}"
  export TICKETSCOPE_EMBEDDING_MODEL_ID="$EMBEDDING_MODEL_ID"
  export TICKETSCOPE_EMBEDDINGS_ASSET_VERSION="$VERSION"
  export TICKETSCOPE_EMBEDDINGS_SHA256="$EMB_SHA256"
  log "embeddings: ${EMBEDDINGS_FILE} served on 127.0.0.1:${SERVE_PORT}"
fi

log "migrate"
$RUN ticketscope-migrate >&2

log "load ${VERSION}"
START="$(now)"
$RUN ticketscope-load >&2
END="$(now)"
SECONDS_TAKEN="$(python3 -c "print(f'{${END} - ${START}:.1f}')")"
log "load took ${SECONDS_TAKEN} s"
echo "$SECONDS_TAKEN"
