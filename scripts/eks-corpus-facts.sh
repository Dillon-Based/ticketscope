#!/usr/bin/env bash
# Prints the corpus facts of the live environment as one line of JSON (story 5.9, R11): the
# `corpus_meta` row, the issue count and a digest of the ordered issue numbers, read as postgres
# on the Cluster's primary. env-up puts them in the job summary after the smoke check; the recreate
# drill compares the two incarnations' lines (scripts/recreate_drill.py compare). Equal `loaded_at`
# in both proves the second environment restored the corpus and did not load it again.
#
#   scripts/eks-corpus-facts.sh --kubeconfig <file>
#
# The same query as scripts/restore-drill.sh `gather`. Exit 0 with the JSON on stdout; 1 when the
# primary has no answer; 2 on usage. Nothing is written.
set -euo pipefail

usage() {
  echo "usage: scripts/eks-corpus-facts.sh --kubeconfig <file>" >&2
  exit 2
}

KUBECONFIG_FILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) [[ $# -ge 2 ]] || usage; KUBECONFIG_FILE="$2"; shift 2 ;;
    -h | --help) usage ;;
    *) echo "eks-corpus-facts: unknown argument $1" >&2; usage ;;
  esac
done
[[ -n "$KUBECONFIG_FILE" ]] || usage
[[ -f "$KUBECONFIG_FILE" ]] || { echo "eks-corpus-facts: kubeconfig $KUBECONFIG_FILE not found" >&2; usage; }

export KUBECONFIG="$KUBECONFIG_FILE"
NS=ticketscope
CLUSTER=ticketscope-db

pod="$(kubectl -n "$NS" get pod -l "cnpg.io/cluster=$CLUSTER,cnpg.io/instanceRole=primary" \
  -o 'jsonpath={.items[0].metadata.name}')"
[[ -n "$pod" ]] || { echo "eks-corpus-facts: no primary pod for $CLUSTER" >&2; exit 1; }
kubectl -n "$NS" exec "$pod" -c postgres -- psql -d app -tAc \
  "select json_build_object('corpus_meta', (select to_jsonb(c) from corpus_meta c), 'issues', (select count(*) from issue), 'digest', (select md5(string_agg(number::text, ',' order by number)) from issue))"
