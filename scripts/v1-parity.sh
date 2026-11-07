#!/usr/bin/env bash
# Before/after /v1 parity on the local kind cluster (stories 6, 7 and 10, AC-3 each).
#
#   scripts/v1-parity.sh <before-rev> <after-rev> <out-dir>
#
# Deploys each revision in turn onto the existing kind cluster with that revision's own
# scripts/kind-up.sh (from a `git archive` export, image tag = its full SHA), captures
# the same POST /v1/search requests through the Gateway, and compares the bodies.
# Both revisions must pin the same snapshot. Leaves the cluster on <after-rev>: rerun
# scripts/kind-up.sh from your checkout afterwards. Writes <rev>.json files and the
# comparison to <out-dir>.
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <before-rev> <after-rev> <out-dir>" >&2
  exit 2
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$(mkdir -p "$3" && cd "$3" && pwd)"
WORK="$(mktemp -d)"
PF=""
cleanup() {
  [[ -n "$PF" ]] && kill "$PF" 2>/dev/null || true
  rm -rf "$WORK"
}
trap cleanup EXIT

log() { echo "[v1-parity] $*" >&2; }

pin() { git -C "$ROOT" show "$1:deploy/charts/ticketscope/values.yaml" | grep -A2 '^snapshot:' | tr -d ' '; }
[[ "$(pin "$1")" == "$(pin "$2")" ]] || { log "revisions pin different snapshots"; exit 2; }

deploy_and_capture() {  # <rev> <label>
  local sha dir svc host port
  sha="$(git -C "$ROOT" rev-parse "$1^{commit}")"
  dir="$WORK/$sha"
  mkdir -p "$dir"
  git -C "$ROOT" archive "$sha" | tar -x -C "$dir"
  log "deploying $2 ($sha)"
  (cd "$dir" && TAG="$sha" scripts/kind-up.sh) >"$OUT/kind-up-$2.log" 2>&1 \
    || { log "kind-up failed for $2; see $OUT/kind-up-$2.log"; exit 1; }
  svc="$(kubectl -n platform get svc -o name | grep envoy-platform-ticketscope | head -1)"
  host="$(kubectl -n ticketscope get httproute -o 'jsonpath={.items[0].spec.hostnames[0]}')"
  port=18090
  [[ -n "$PF" ]] && kill "$PF" 2>/dev/null || true
  kubectl -n platform port-forward "$svc" "$port:80" >/dev/null 2>&1 &
  PF=$!
  for _ in $(seq 1 30); do
    curl -s -o /dev/null -H "Host: $host" "http://127.0.0.1:$port/readyz" && break
    sleep 1
  done
  python3 "$ROOT/scripts/v1_parity.py" capture --url "http://127.0.0.1:$port" --host "$host" \
    --out "$OUT/$2.json" --label "$2 ($sha)"
}

deploy_and_capture "$1" before
deploy_and_capture "$2" after
python3 "$ROOT/scripts/v1_parity.py" compare "$OUT/before.json" "$OUT/after.json" | tee "$OUT/compare.txt"
