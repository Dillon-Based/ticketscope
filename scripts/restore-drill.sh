#!/usr/bin/env bash
# The restore drill (story 5.7, R9): takes a backup on a live EKS environment, restores it into a
# new one-instance Cluster through the Barman Cloud Plugin, and compares the two. Run by a person
# with the admin kubeconfig (the read-only role cannot read CNPG objects), once the environment is
# up and 5.6's backup works. Writes the log, the result and the masked record to <out-dir>.
#
#   scripts/restore-drill.sh --kubeconfig <file> --out <dir>
#
# Stages (each timed): backup, restore (create the recovery Cluster and wait for Ready), compare.
# The recovery Cluster `ticketscope-restore` reads the source's serverName and does not archive
# (no WAL archiver entry), so it writes nothing to the bucket. It is deleted on exit.
# Exit 0 only when restore_drill.py compare says OK; 1 on a difference or a Cluster that never got
# Ready; 2 on usage or an input that cannot be trusted.
#
# Env overrides:
#   RESTORE_TIMEOUT  seconds to wait for the recovery Cluster to be Ready (default 1500)
#   BACKUP_TIMEOUT   passed to scripts/eks-backup.sh (default 900)
set -euo pipefail

usage() {
  echo "usage: scripts/restore-drill.sh --kubeconfig <file> --out <dir>" >&2
  exit 2
}

KUBECONFIG_FILE=""
OUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) [[ $# -ge 2 ]] || usage; KUBECONFIG_FILE="$2"; shift 2 ;;
    --out) [[ $# -ge 2 ]] || usage; OUT="$2"; shift 2 ;;
    -h | --help) usage ;;
    *) echo "restore-drill: unknown argument $1" >&2; usage ;;
  esac
done
[[ -n "$KUBECONFIG_FILE" && -n "$OUT" ]] || usage
[[ -f "$KUBECONFIG_FILE" ]] || { echo "restore-drill: kubeconfig $KUBECONFIG_FILE not found" >&2; usage; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
for tool in kubectl jq uv; do
  command -v "$tool" >/dev/null || { echo "restore-drill: $tool is required" >&2; exit 2; }
done

mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
LOG="$OUT/restore-drill.log"
: >"$LOG"
exec > >(tee -a "$LOG") 2>&1

export KUBECONFIG="$KUBECONFIG_FILE"
NS=ticketscope
SOURCE=ticketscope-db
RESTORE=ticketscope-restore
OBJECTSTORE=ticketscope-backup
RESTORE_TIMEOUT="${RESTORE_TIMEOUT:-1500}"
PY="scripts/restore_drill.py"

# x <command...>: echoes the command (the record keeps the commands) and runs it.
x() { printf '+ %s\n' "$*" >&2; "$@"; }

STAGES=()
STAGE_START=$(date +%s)
CURRENT=""
stage() {
  local now
  now=$(date +%s)
  if [[ -n "$CURRENT" ]]; then STAGES+=("$CURRENT $((now - STAGE_START))"); fi
  CURRENT="${1:-}"
  STAGE_START=$now
  if [[ -n "$CURRENT" ]]; then echo "stage: $CURRENT"; fi
}

# shellcheck disable=SC2317,SC2329  # called by the EXIT trap (SC2317 on shellcheck < 0.11)
cleanup() {
  echo "cleanup: deleting the recovery Cluster $RESTORE"
  kubectl -n "$NS" delete cluster.postgresql.cnpg.io "$RESTORE" --ignore-not-found --wait=false || true
}
trap cleanup EXIT

primary_of() {
  kubectl -n "$NS" get pod -l "cnpg.io/cluster=$1,cnpg.io/instanceRole=primary" \
    -o 'jsonpath={.items[0].metadata.name}'
}

# gather <cluster> <file>: one JSON snapshot of the cluster's corpus, read as postgres.
gather() {
  local pod
  pod="$(primary_of "$1")"
  [[ -n "$pod" ]] || { echo "restore-drill: no primary pod for $1" >&2; exit 2; }
  x kubectl -n "$NS" exec "$pod" -c postgres -- psql -d app -tAc \
    "select json_build_object('corpus_meta', (select to_jsonb(c) from corpus_meta c), 'issues', (select count(*) from issue), 'digest', (select md5(string_agg(number::text, ',' order by number)) from issue))" \
    >"$2"
}

stage "backup"
SERVER_NAME="$(kubectl -n "$NS" get cluster.postgresql.cnpg.io "$SOURCE" -o 'jsonpath={.spec.plugins[0].parameters.serverName}')"
[[ -n "$SERVER_NAME" ]] || { echo "restore-drill: the source Cluster has no plugin serverName" >&2; exit 2; }
x scripts/eks-backup.sh --kubeconfig "$KUBECONFIG_FILE" --incarnation "$SERVER_NAME" \
  --name-suffix "drill-$(date +%s)"

stage "restore"
SRC_JSON="$(kubectl -n "$NS" get cluster.postgresql.cnpg.io "$SOURCE" -o json)"
IMAGE="$(jq -r '.spec.imageName' <<<"$SRC_JSON")"
STORAGE_SIZE="$(jq -r '.spec.storage.size' <<<"$SRC_JSON")"
STORAGE_CLASS="$(jq -r '.spec.storage.storageClass // empty' <<<"$SRC_JSON")"
RESOURCES="$(jq -c '.spec.resources' <<<"$SRC_JSON")"
ROLE_ARN="$(jq -r '.spec.serviceAccountTemplate.metadata.annotations["eks.amazonaws.com/role-arn"] // empty' <<<"$SRC_JSON")"
[[ -n "$ROLE_ARN" ]] || { echo "restore-drill: the source Cluster has no IRSA role annotation" >&2; exit 2; }
echo "recovering from serverName $SERVER_NAME through ObjectStore $OBJECTSTORE"
kubectl -n "$NS" apply -f - <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: ${RESTORE}
  namespace: ${NS}
spec:
  instances: 1
  imageName: ${IMAGE}
  postgresql:
    shared_preload_libraries:
      - pg_textsearch
  serviceAccountTemplate:
    metadata:
      annotations:
        eks.amazonaws.com/role-arn: ${ROLE_ARN}
  bootstrap:
    recovery:
      source: source-cluster
      database: app
      owner: app
  externalClusters:
    - name: source-cluster
      plugin:
        name: barman-cloud.cloudnative-pg.io
        parameters:
          barmanObjectName: ${OBJECTSTORE}
          serverName: ${SERVER_NAME}
  storage:
    size: ${STORAGE_SIZE}
${STORAGE_CLASS:+    storageClass: ${STORAGE_CLASS}}
  resources: ${RESOURCES}
EOF
if ! kubectl -n "$NS" wait cluster.postgresql.cnpg.io/"$RESTORE" --for=condition=Ready --timeout="${RESTORE_TIMEOUT}s"; then
  echo "restore-drill: $RESTORE was not Ready within ${RESTORE_TIMEOUT}s" >&2
  kubectl -n "$NS" get cluster.postgresql.cnpg.io "$RESTORE" -o jsonpath='{.status.conditions}' >&2 || true
  exit 1
fi

stage "compare"
gather "$SOURCE" "$OUT/source.json"
gather "$RESTORE" "$OUT/restored.json"
EXPECTED="$(uv run python "$PY" expected-issues)"
echo "the pinned Release publishes $EXPECTED issues"
rc=0
x uv run python "$PY" compare "$OUT/source.json" "$OUT/restored.json" --expected "$EXPECTED" || rc=$?
stage ""

verdict=OK
[[ "$rc" -eq 0 ]] || verdict=FAILED
differences="$(uv run python "$PY" compare "$OUT/source.json" "$OUT/restored.json" --expected "$EXPECTED" | grep -v '^restore drill: OK$' || true)"
stages_json="$(printf '%s\n' "${STAGES[@]}" | jq -Rn '[inputs | split(" ") | {stage: .[0], seconds: (.[1] | tonumber)}]')"
jq -n --arg verdict "$verdict" --argjson expected "$EXPECTED" --argjson stages "$stages_json" \
  --slurpfile source "$OUT/source.json" --slurpfile restored "$OUT/restored.json" \
  --arg differences "$differences" \
  '{verdict: $verdict, expected: $expected, stages: $stages, source: $source[0], restored: $restored[0],
    differences: ($differences | split("\n") | map(select(. != "")))}' >"$OUT/result.json"
uv run python "$PY" record --result "$OUT/result.json" --log "$LOG" --out "$OUT/restore-drill.md"
echo "restore drill: $verdict; the masked record is $OUT/restore-drill.md (copy it to docs/drills/)"
exit "$rc"
