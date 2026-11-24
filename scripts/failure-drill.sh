#!/usr/bin/env bash
# The failure drill (story 5.8, R10): terminates the node holding the primary of a live
# two-instance environment while a probe searches through the public hostname every second, and
# records when a standby took over, when the probe next succeeded and how many requests failed.
# Run by a person with admin AWS credentials and the admin kubeconfig, last in the live window.
#
#   scripts/failure-drill.sh --kubeconfig <file> --url https://<hostname> --out <dir>
#
# Refuses to terminate anything unless the Cluster's instances are on different nodes. Writes the
# log, the probe log, the events, the result and the masked record to <out-dir>.
# Exit 0 only when failure_drill.py says OK; 1 on a failed drill or a precondition that does not
# hold; 2 on usage or an input that cannot be trusted.
#
# Env overrides:
#   PROMOTE_TIMEOUT  seconds to wait for a new primary (default 600)
#   RECOVER_TIMEOUT  seconds to wait for the probe to succeed again (default 600)
#   ARCHIVE_TIMEOUT  seconds to wait for a WAL to archive after a switch (default 180)
#   SETTLE_SECONDS   seconds of probing before the failure and after recovery (default 15)
set -euo pipefail

usage() {
  echo "usage: scripts/failure-drill.sh --kubeconfig <file> --url https://<hostname> --out <dir>" >&2
  exit 2
}

KUBECONFIG_FILE=""
URL=""
OUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) [[ $# -ge 2 ]] || usage; KUBECONFIG_FILE="$2"; shift 2 ;;
    --url) [[ $# -ge 2 ]] || usage; URL="$2"; shift 2 ;;
    --out) [[ $# -ge 2 ]] || usage; OUT="$2"; shift 2 ;;
    -h | --help) usage ;;
    *) echo "failure-drill: unknown argument $1" >&2; usage ;;
  esac
done
[[ -n "$KUBECONFIG_FILE" && -n "$URL" && -n "$OUT" ]] || usage
[[ "$URL" == https://* ]] || { echo "failure-drill: --url must be https://<hostname>" >&2; usage; }
[[ -f "$KUBECONFIG_FILE" ]] || { echo "failure-drill: kubeconfig $KUBECONFIG_FILE not found" >&2; usage; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
for tool in kubectl aws curl jq python3; do
  command -v "$tool" >/dev/null || { echo "failure-drill: $tool is required" >&2; exit 2; }
done

mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
LOG="$OUT/failure-drill.log"
PROBE="$OUT/probe.log"
: >"$LOG"
: >"$PROBE"
exec > >(tee -a "$LOG") 2>&1

export KUBECONFIG="$KUBECONFIG_FILE"
export AWS_REGION="${AWS_REGION:-us-east-1}"
NS=ticketscope
CLUSTER=ticketscope-db
PROMOTE_TIMEOUT="${PROMOTE_TIMEOUT:-600}"
RECOVER_TIMEOUT="${RECOVER_TIMEOUT:-600}"
ARCHIVE_TIMEOUT="${ARCHIVE_TIMEOUT:-180}"
SETTLE_SECONDS="${SETTLE_SECONDS:-15}"
PY="scripts/failure_drill.py"

# x <command...>: echoes the command (the record keeps the commands) and runs it.
x() { printf '+ %s\n' "$*" >&2; "$@"; }

PROBE_PID=""
# shellcheck disable=SC2317,SC2329  # called by the EXIT trap (SC2317 on shellcheck < 0.11)
cleanup() {
  if [[ -n "$PROBE_PID" ]]; then kill "$PROBE_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT

cluster_json() { kubectl -n "$NS" get cluster.postgresql.cnpg.io "$CLUSTER" -o json; }
primary_pod() { kubectl -n "$NS" get cluster.postgresql.cnpg.io "$CLUSTER" -o 'jsonpath={.status.currentPrimary}'; }

echo "stage: placement"
# Instance pods only (not the initdb or join job pods), each scheduled and Ready.
PODS_JSON="$(x kubectl -n "$NS" get pod -l "cnpg.io/cluster=$CLUSTER,cnpg.io/podRole=instance" -o json)"
NODES_JSON="$(jq -c '[.items[] | .spec.nodeName // empty]' <<<"$PODS_JSON")"
READY="$(jq '[.items[] | select(any(.status.conditions[]?; .type == "Ready" and .status == "True"))] | length' <<<"$PODS_JSON")"
[[ "$(jq 'length' <<<"$NODES_JSON")" -ge 2 && "$READY" -eq "$(jq '.items | length' <<<"$PODS_JSON")" ]] \
  || { echo "failure-drill: fewer than two instances are scheduled and Ready" >&2; exit 1; }
if [[ "$(jq 'unique | length' <<<"$NODES_JSON")" -ne "$(jq 'length' <<<"$NODES_JSON")" ]]; then
  echo "failure-drill: the instances share a node ($NODES_JSON); refusing to terminate" >&2
  exit 1
fi
echo "instances on different nodes: $NODES_JSON"

OLD_PRIMARY="$(primary_pod)"
[[ -n "$OLD_PRIMARY" ]] || { echo "failure-drill: the Cluster reports no primary" >&2; exit 2; }
NODE="$(kubectl -n "$NS" get pod "$OLD_PRIMARY" -o 'jsonpath={.spec.nodeName}')"
PROVIDER_ID="$(kubectl get node "$NODE" -o 'jsonpath={.spec.providerID}')"
INSTANCE_ID="${PROVIDER_ID##*/}"
[[ "$INSTANCE_ID" == i-* ]] || { echo "failure-drill: no EC2 instance id for node $NODE" >&2; exit 2; }
BEFORE_JSON="$(cluster_json)"
SERVER_BEFORE="$(jq -r '[.spec.plugins[]? | select(.name == "barman-cloud.cloudnative-pg.io") | .parameters.serverName // empty][0] // empty' <<<"$BEFORE_JSON")"
[[ -n "$SERVER_BEFORE" ]] || { echo "failure-drill: the Cluster has no barman plugin serverName; nothing terminated" >&2; exit 2; }
if [[ "$(jq -r '[.status.conditions[]? | select(.type == "ContinuousArchiving") | .status][0] // "missing"' <<<"$BEFORE_JSON")" != True ]]; then
  echo "failure-drill: the Cluster is not archiving before the failure; nothing terminated" >&2
  exit 1
fi
ARCHIVED_BEFORE=""
echo "the primary is $OLD_PRIMARY on $NODE ($INSTANCE_ID); serverName $SERVER_BEFORE"

probe() {
  while :; do
    code="$(curl -s -o /dev/null -m 5 -w '%{http_code}' --data-urlencode 'q=launcher crash' "$URL/" || true)"
    printf '%s %s\n' "$(date +%s)" "${code:-000}" >>"$PROBE"
    sleep 1
  done
}
echo "stage: probe"
probe &
PROBE_PID=$!
sleep "$SETTLE_SECONDS"
if ! tail -n 1 "$PROBE" | grep -q ' 200$'; then
  echo "failure-drill: the public search probe does not succeed before the failure" >&2
  exit 1
fi

echo "stage: terminate"
TERMINATED_AT=$(date +%s)
x aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --query 'TerminatingInstances[].CurrentState.Name' --output text \
  || { echo "failure-drill: terminate-instances failed; nothing was proven" >&2; exit 2; }

echo "stage: promote"
PROMOTED_AT=null
deadline=$((TERMINATED_AT + PROMOTE_TIMEOUT))
while (($(date +%s) <= deadline)); do
  now_primary="$(primary_pod 2>/dev/null || true)"
  if [[ -n "$now_primary" && "$now_primary" != "$OLD_PRIMARY" ]]; then
    PROMOTED_AT=$(date +%s)
    echo "promoted: $now_primary is the primary"
    break
  fi
  sleep 1
done

echo "stage: recover"
# Recovered: the newest probe succeeded, and either a probe has failed since the termination or a
# minute has passed without one (the failure may be too short to see).
recovered() {
  local failed_since last
  failed_since="$(awk -v t="$TERMINATED_AT" '$1 >= t && $2 != 200 {n++} END {print n+0}' "$PROBE")"
  last="$(tail -n 1 "$PROBE")"
  [[ "$last" == *" 200" ]] || return 1
  ((failed_since > 0 || $(date +%s) - TERMINATED_AT > 60))
}
deadline=$(($(date +%s) + RECOVER_TIMEOUT))
until recovered; do
  if (($(date +%s) > deadline)); then
    echo "failure-drill: the probe did not recover within ${RECOVER_TIMEOUT}s" >&2
    break
  fi
  sleep 1
done
sleep "$SETTLE_SECONDS"

echo "stage: archive"
ARCHIVED_AFTER=""
if [[ "$PROMOTED_AT" != null ]]; then
  NEW_PRIMARY="$(primary_pod)"
  kubectl -n "$NS" wait --for=condition=Ready "pod/$NEW_PRIMARY" --timeout="${ARCHIVE_TIMEOUT}s" || true
  # Read after promotion, so the new timeline's .history file is not mistaken for the switch.
  ARCHIVED_BEFORE="$(cluster_json 2>/dev/null | jq -r '.status.lastArchivedWAL // empty' || true)"
  x kubectl -n "$NS" exec "$NEW_PRIMARY" -c postgres -- psql -d app -tAc 'select pg_switch_wal()' || true
  deadline=$(($(date +%s) + ARCHIVE_TIMEOUT))
  while (($(date +%s) <= deadline)); do
    ARCHIVED_AFTER="$(cluster_json 2>/dev/null | jq -r '.status.lastArchivedWAL // empty' || true)"
    [[ "$ARCHIVED_AFTER" =~ ^[0-9A-F]{24}$ && "$ARCHIVED_AFTER" != "$ARCHIVED_BEFORE" ]] && break
    sleep 5
  done
fi
kill "$PROBE_PID" 2>/dev/null || true
PROBE_PID=""

FINAL="$(cluster_json || true)"
[[ -n "$FINAL" ]] || { echo "failure-drill: cannot read the Cluster after the failure" >&2; exit 2; }
jq -n --argjson terminated "$TERMINATED_AT" --argjson promoted "$PROMOTED_AT" \
  --arg before "$ARCHIVED_BEFORE" --arg after "$ARCHIVED_AFTER" --arg server_before "$SERVER_BEFORE" \
  --argjson final "$FINAL" \
  '{terminated_at: $terminated, promoted_at: $promoted,
    archive: {
      continuous_archiving: ([$final.status.conditions[]? | select(.type == "ContinuousArchiving") | .status][0] // "missing"),
      last_archived_before: $before,
      last_archived_after: $after,
      last_failed: ($final.status.lastFailedWAL // ""),
      server_before: $server_before,
      server_after: ($final.spec.plugins[0].parameters.serverName // "")}}' >"$OUT/events.json"

rc=0
uv run python "$PY" analyze --probe "$PROBE" --events "$OUT/events.json" >"$OUT/analysis.json" || rc=$?
if [[ "$rc" -eq 2 ]]; then echo "failure-drill: an input could not be read" >&2; exit 2; fi
jq --argjson nodes "$NODES_JSON" '. + {placement: $nodes}' "$OUT/analysis.json" >"$OUT/result.json"
sleep 1 # let the tee behind the log catch up before the record reads it
uv run python "$PY" record --result "$OUT/result.json" --log "$LOG" --out "$OUT/failure-drill.md"
verdict="$(jq -r '.verdict' "$OUT/result.json")"
echo "failure drill: $verdict; the masked record is $OUT/failure-drill.md (copy it to docs/drills/)"
exit "$rc"
