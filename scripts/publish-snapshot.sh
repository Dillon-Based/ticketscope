#!/usr/bin/env bash
# Publishes the next corpus snapshot as a `snapshot-YYYY.MM.N` Release (AD-6, AD-12).
# A person runs it; no workflow ingests or publishes (AD-17).
#
#   scripts/publish-snapshot.sh
#
# Needs, on this machine:
#   - The Public Jira Dataset v7 restored into a MongoDB, e.g.
#       docker run -d --name jira-mongo -p 127.0.0.1:27017:27017 mongo
#       mongorestore --uri mongodb://127.0.0.1:27017 <dump dir>
#   - `gh auth login` with write access to this repository, Docker, and uv.
#
# Steps: refuse unless this is a clean checkout of `main` equal to `origin/main`; take
# the next free version; ingest; check the checksum; validate every line against schema
# v2 and the model; time a load into the in-repo Postgres image (must be <= 600 s);
# re-check the version is still free; render the notes; create the Release targeting
# HEAD. It never deletes a Release and never overwrites one (no --clobber).
#
# Env overrides:
#   MONGO_URI       (default mongodb://127.0.0.1:27017)
#   MONGO_DATABASE  (default JiraReposAnon)
#   OUT_DIR         where ingest writes (default: a new temporary directory)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MONGO_URI="${MONGO_URI:-mongodb://127.0.0.1:27017}"
MONGO_DATABASE="${MONGO_DATABASE:-JiraReposAnon}"
BUDGET_SECONDS=600

log() { echo "[publish-snapshot] $*" >&2; }
die() { echo "[publish-snapshot] error: $*" >&2; exit 1; }

# --- guards: before anything is ingested ---------------------------------------------

branch="$(git rev-parse --abbrev-ref HEAD)"
[[ "$branch" == "main" ]] || die "publish only from main, not ${branch}"
[[ -z "$(git status --porcelain)" ]] || die "the checkout is not clean; commit or remove changes"
git fetch --quiet origin main || die "cannot fetch origin/main"
COMMIT="$(git rev-parse HEAD)"
[[ "$COMMIT" == "$(git rev-parse origin/main)" ]] || die "HEAD is not origin/main; pull or push first"

command -v gh >/dev/null || die "gh is not installed"
gh auth status >/dev/null 2>&1 || die "gh is not authenticated; run gh auth login"
docker info >/dev/null 2>&1 || die "Docker is not running"
REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"

taken_tags() {
  gh api --paginate "repos/${REPO}/git/matching-refs/tags/snapshot-" --jq '.[].ref'
  gh release list --repo "$REPO" --limit 1000 --json tagName --jq '.[].tagName'
}

RUN=(uv run --locked --group ingest)

# --- version ----------------------------------------------------------------------------

MONTH="$(date -u +%Y.%m)"
VERSION="$(taken_tags | "${RUN[@]}" python -m ticketscope.jobs.ingest.version --month "$MONTH")"
log "planned version ${VERSION} (commit ${COMMIT})"

OUT_DIR="${OUT_DIR:-$(mktemp -d)}"
mkdir -p "$OUT_DIR"
ASSET="${VERSION}.jsonl.gz"

# --- ingest, checksum, schema -----------------------------------------------------------

"${RUN[@]}" ticketscope-ingest --version "$VERSION" --out-dir "$OUT_DIR" \
  --mongo-uri "$MONGO_URI" --database "$MONGO_DATABASE" --exclusions snapshot/exclusions.txt

if command -v sha256sum >/dev/null; then
  (cd "$OUT_DIR" && sha256sum -c "${ASSET}.sha256") >&2 || die "checksum mismatch"
else
  (cd "$OUT_DIR" && shasum -a 256 -c "${ASSET}.sha256") >&2 || die "checksum mismatch"
fi

"${RUN[@]}" python -m ticketscope.jobs.ingest.schema --check "${OUT_DIR}/${ASSET}" >&2 \
  || die "the snapshot does not validate against schema v2"

# --- timed load -------------------------------------------------------------------------

if ! seconds="$(scripts/time-load.sh "$OUT_DIR" "$VERSION" | tail -n1)" \
    || ! [[ "$seconds" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
  die "timed load failed (migrate or load exited non-zero, or no time printed)"
fi
log "timed load: ${seconds} s (budget ${BUDGET_SECONDS} s)"
python3 -c "import sys; sys.exit(0 if float('${seconds}') <= ${BUDGET_SECONDS} else 1)" \
  || die "load took ${seconds} s, over the ${BUDGET_SECONDS} s budget"

# --- publish ----------------------------------------------------------------------------

next="$(taken_tags | "${RUN[@]}" python -m ticketscope.jobs.ingest.version --month "${VERSION%.*}")"
[[ "$next" == "$VERSION" ]] || die "planned ${VERSION}, but the next free version is now ${next}"
if taken_tags | grep -qx -e "snapshot-${VERSION}" -e "refs/tags/snapshot-${VERSION}"; then
  die "tag snapshot-${VERSION} already exists"
fi

NOTES="${OUT_DIR}/notes.md"
"${RUN[@]}" python -m ticketscope.jobs.ingest.notes --report "${OUT_DIR}/report.json" \
  --load-seconds "$seconds" --commit "$COMMIT" --repo "$REPO" > "$NOTES" \
  || die "could not render the Release notes"
cat "$NOTES" >&2

# No --clobber: creation fails rather than touch an existing Release.
# The kinds sidecar and report stay unpublished.
gh release create "snapshot-${VERSION}" --repo "$REPO" \
  "${OUT_DIR}/${ASSET}" "${OUT_DIR}/${ASSET}.sha256" \
  --target "$COMMIT" \
  --title "Corpus snapshot ${VERSION}" \
  --notes-file "$NOTES"
log "published snapshot-${VERSION}"
