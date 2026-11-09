#!/usr/bin/env bash
# Publishes the next corpus snapshot as a `snapshot-YYYY.MM.N` Release (AD-6, AD-12).
# A person runs it; no workflow ingests or publishes (AD-17).
#
#   scripts/publish-snapshot.sh                         publish the next snapshot, then its embeddings
#   scripts/publish-snapshot.sh --embeddings-only 2026.11.1
#                                                       embed an already published snapshot
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
# HEAD. Then the embedding phase: embed the checksum-verified snapshot (never the raw
# dump) with the model in values.yaml, write the manifest, time a load of the asset
# (download, checksum and bulk load, <= 600 s), and create the asset's own Release
# `embeddings-<version>-<model>-<preprocessing>` targeting HEAD. No published Release is
# touched. It never deletes a Release and never overwrites one (no --clobber); an
# embeddings tag that exists stops the run before anything is embedded or uploaded.
# A person then merges `embeddings.assetVersion` and `embeddings.sha256` into values.yaml.
#
# Env overrides:
#   MONGO_URI       (default mongodb://127.0.0.1:27017)
#   MONGO_DATABASE  (default JiraReposAnon)
#   OUT_DIR         where ingest writes (default: a new temporary directory)
#   EMBEDDING_CACHE_DIR  where the model is downloaded (default ~/.cache/ticketscope-models)
#   SNAPSHOT_SHA256 with --embeddings-only for a version other than the pinned one: the
#                   published snapshot's SHA-256
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MONGO_URI="${MONGO_URI:-mongodb://127.0.0.1:27017}"
MONGO_DATABASE="${MONGO_DATABASE:-JiraReposAnon}"
BUDGET_SECONDS=600

EMBEDDINGS_ONLY=""
case "${1:-}" in
  "") ;;
  --embeddings-only)
    EMBEDDINGS_ONLY="${2:-}"
    [[ "$EMBEDDINGS_ONLY" =~ ^[0-9]{4}\.[0-9]{2}\.[1-9][0-9]*$ ]] \
      || { echo "usage: $0 [--embeddings-only YYYY.MM.N]" >&2; exit 2; }
    ;;
  *) echo "usage: $0 [--embeddings-only YYYY.MM.N]" >&2; exit 2 ;;
esac

log() { echo "[publish-snapshot] $*" >&2; }
die() { echo "[publish-snapshot] error: $*" >&2; exit 1; }

RUN=(uv run --locked --group ingest)

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

taken_embedding_tags() {
  gh api --paginate "repos/${REPO}/git/matching-refs/tags/embeddings-" --jq '.[].ref'
  gh release list --repo "$REPO" --limit 1000 --json tagName --jq '.[].tagName'
}

# Whether a tag is taken. The listing is captured first: `grep -q` closing a pipe early would
# fail the pipeline under pipefail and read as "not taken".
embedding_tag_taken() {
  local taken
  taken="$(taken_embedding_tags)" || die "cannot list the existing tags"
  grep -qx -e "$1" -e "refs/tags/$1" <<<"$taken"
}

# --- embeddings: embed the verified snapshot, time the load, attach as its own Release ---

publish_embeddings() {
  local version="$1" out_dir="$2" snapshot_sha="$3"
  local model_id cache_dir tag asset
  model_id="$("${RUN[@]}" python -c "
from pathlib import Path
from ticketscope.adapters.release import read_embeddings_pin
print(read_embeddings_pin(Path('deploy/charts/ticketscope/values.yaml'))['modelId'])")" \
    || die "cannot read embeddings.modelId from values.yaml"
  [[ -n "$model_id" ]] || die "embeddings.modelId is empty in values.yaml"
  { read -r tag; read -r asset; } < <("${RUN[@]}" python -m ticketscope.jobs.ingest.embed tag \
    --version "$version" --model-id "$model_id") || die "could not name the embedding asset"
  log "embedding asset ${tag} (model ${model_id})"

  # Refuse before the long embedding pass, and again just before the upload.
  embedding_tag_taken "$tag" \
    && die "tag ${tag} already exists; not overwriting. Bump the version, model or preprocessing"

  cache_dir="${EMBEDDING_CACHE_DIR:-${HOME}/.cache/ticketscope-models}"
  mkdir -p "$cache_dir"
  # The input is the published snapshot, verified against its SHA-256; never the raw dump.
  "${RUN[@]}" python -m ticketscope.jobs.ingest.embed build \
    --snapshot "${out_dir}/${version}.jsonl.gz" --sha256 "$snapshot_sha" \
    --version "$version" --model-id "$model_id" --out-dir "$out_dir" --cache-dir "$cache_dir" \
    || die "could not build the embedding asset"
  [[ -f "${out_dir}/${asset}" ]] || die "the embedding asset ${asset} was not written"

  local eseconds
  if ! eseconds="$(EMBEDDINGS_FILE="$asset" EMBEDDING_MODEL_ID="$model_id" \
        scripts/time-load.sh "$out_dir" "$version" | tail -n1)" \
      || ! [[ "$eseconds" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
    die "timed load with the embedding asset failed"
  fi
  log "timed load with embeddings: ${eseconds} s (budget ${BUDGET_SECONDS} s)"
  python3 -c "import sys; sys.exit(0 if float('${eseconds}') <= ${BUDGET_SECONDS} else 1)" \
    || die "load with embeddings took ${eseconds} s, over the ${BUDGET_SECONDS} s budget"

  embedding_tag_taken "$tag" && die "tag ${tag} already exists"
  local enotes="${out_dir}/embeddings-notes.md"
  "${RUN[@]}" python -m ticketscope.jobs.ingest.notes \
    --embeddings-manifest "${out_dir}/${tag}.manifest.json" \
    --load-seconds "$eseconds" --commit "$COMMIT" > "$enotes" \
    || die "could not render the embedding Release notes"
  cat "$enotes" >&2

  # No --clobber: creation fails rather than touch an existing Release.
  gh release create "$tag" --repo "$REPO" \
    "${out_dir}/${asset}" "${out_dir}/${asset}.sha256" \
    --target "$COMMIT" \
    --title "Embeddings ${version} (${model_id})" \
    --notes-file "$enotes"
  log "published ${tag}; a person merges embeddings.assetVersion ${version} and the SHA-256 into values.yaml"
}

if [[ -n "$EMBEDDINGS_ONLY" ]]; then
  OUT_DIR="${OUT_DIR:-$(mktemp -d)}"
  mkdir -p "$OUT_DIR"
  gh release download "snapshot-${EMBEDDINGS_ONLY}" --repo "$REPO" \
    --pattern "${EMBEDDINGS_ONLY}.jsonl.gz" --dir "$OUT_DIR" \
    || die "cannot download snapshot-${EMBEDDINGS_ONLY}"
  pinned="$("${RUN[@]}" python -c "
from pathlib import Path
from ticketscope.adapters.release import read_snapshot_pin
pin = read_snapshot_pin(Path('deploy/charts/ticketscope/values.yaml'))
print(pin['version'], pin['sha256'])")"
  if [[ "${pinned%% *}" == "$EMBEDDINGS_ONLY" ]]; then
    SNAPSHOT_SHA="${pinned##* }"
  else
    SNAPSHOT_SHA="${SNAPSHOT_SHA256:-}"
    [[ -n "$SNAPSHOT_SHA" ]] || die "${EMBEDDINGS_ONLY} is not the pinned snapshot; set SNAPSHOT_SHA256"
  fi
  publish_embeddings "$EMBEDDINGS_ONLY" "$OUT_DIR" "$SNAPSHOT_SHA"
  exit 0
fi

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

SNAPSHOT_SHA="$(cut -d' ' -f1 "${OUT_DIR}/${ASSET}.sha256")"
publish_embeddings "$VERSION" "$OUT_DIR" "$SNAPSHOT_SHA"
