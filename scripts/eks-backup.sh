#!/usr/bin/env bash
# One on-demand backup on an up EKS environment (story 5.6, R8): creates a plugin Backup, waits
# for it to complete, and prints what the archive and the Backup recorded. Run by env-up after the
# smoke check, outside the 30-minute clock.
#
#   scripts/eks-backup.sh --kubeconfig <file> --incarnation <id>
#
# Env overrides:
#   BACKUP_TIMEOUT  seconds to wait for the Backup to complete (default 900)
set -euo pipefail

usage() {
  echo "usage: scripts/eks-backup.sh --kubeconfig <file> --incarnation <id>" >&2
  exit 2
}

KUBECONFIG_FILE=""
INCARNATION=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) [[ $# -ge 2 ]] || usage; KUBECONFIG_FILE="$2"; shift 2 ;;
    --incarnation) [[ $# -ge 2 ]] || usage; INCARNATION="$2"; shift 2 ;;
    -h | --help) usage ;;
    *) echo "eks-backup: unknown argument $1" >&2; usage ;;
  esac
done
[[ -n "$KUBECONFIG_FILE" && -n "$INCARNATION" ]] || usage
[[ -f "$KUBECONFIG_FILE" ]] || { echo "eks-backup: kubeconfig $KUBECONFIG_FILE not found" >&2; usage; }

export KUBECONFIG="$KUBECONFIG_FILE"
NS=ticketscope
CLUSTER=ticketscope-db
NAME="${CLUSTER}-ondemand-${INCARNATION}"
BACKUP_TIMEOUT="${BACKUP_TIMEOUT:-900}"

kubectl -n "$NS" apply -f - <<EOF
apiVersion: postgresql.cnpg.io/v1
kind: Backup
metadata:
  name: ${NAME}
  namespace: ${NS}
spec:
  method: plugin
  cluster:
    name: ${CLUSTER}
  pluginConfiguration:
    name: barman-cloud.cloudnative-pg.io
EOF

deadline=$(($(date +%s) + BACKUP_TIMEOUT))
phase=""
while :; do
  phase="$(kubectl -n "$NS" get backup.postgresql.cnpg.io "$NAME" -o jsonpath='{.status.phase}' 2>/dev/null || true)"
  case "$phase" in
    completed) break ;;
    failed)
      echo "eks-backup: backup $NAME failed" >&2
      kubectl -n "$NS" get backup.postgresql.cnpg.io "$NAME" -o jsonpath='{.status.error}' >&2 || true
      exit 1
      ;;
  esac
  if (($(date +%s) > deadline)); then
    echo "eks-backup: backup $NAME is '${phase:-pending}' after ${BACKUP_TIMEOUT}s" >&2
    exit 1
  fi
  sleep 10
done

echo "backup ${NAME}: ${phase}"
kubectl -n "$NS" get backup.postgresql.cnpg.io "$NAME" \
  -o jsonpath='{"pluginMetadata: "}{.status.pluginMetadata}{"\nbeginWal: "}{.status.beginWal}{"\nendWal: "}{.status.endWal}{"\n"}'
echo "objects: backups/${INCARNATION}/"
