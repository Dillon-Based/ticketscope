#!/usr/bin/env bash
# The read-only leftover check of env-down (story 5.4, R3): lists what is still tagged for the
# environment and fails on any of it. Only list and describe calls are made.
#
#   scripts/leftover-check.sh [--list] [--dry-run] [--from-file <listing.json> ...]
#
#   (no flag)   fail (exit 1) naming each tagged resource; an `aws` error fails (exit 2) too
#   --list      print what is found and exit 0 (the positive control while the environment is up)
#   --dry-run   no AWS call: injects a tagged load balancer, which must fail and name it
#   --from-file read the given listings instead of calling AWS
#
# Env: ENVIRONMENT_TAG (default eks), CLUSTER_NAME (default ticketscope-env), AWS_REGION
# (default us-east-1). Resources tagged `stack=bootstrap`, or with another environment's tag, are
# never selected. The tagging API can omit network interfaces, so they are listed through EC2.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENVIRONMENT_TAG="${ENVIRONMENT_TAG:-eks}"
CLUSTER_NAME="${CLUSTER_NAME:-ticketscope-env}"
REGION="${AWS_REGION:-us-east-1}"

USAGE="usage: leftover-check.sh [--list] [--dry-run] [--from-file F]"
mode=()
files=()
dry=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --list) mode+=(--list); shift ;;
    --dry-run) mode+=(--dry-run); dry=1; shift ;;
    --from-file)
      [[ $# -ge 2 ]] || { echo "$USAGE" >&2; exit 2; }
      files+=("$2")
      shift 2
      ;;
    *) echo "$USAGE" >&2; exit 2 ;;
  esac
done

check() {
  python3 "$ROOT/scripts/leftover_check.py" --environment "$ENVIRONMENT_TAG" \
    --cluster "$CLUSTER_NAME" ${mode[@]+"${mode[@]}"} "$@"
}

if ((dry)); then check; exit $?; fi
if ((${#files[@]})); then check "${files[@]}"; exit $?; fi

command -v aws >/dev/null || { echo "leftover-check: FAIL, aws is required" >&2; exit 2; }
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# fetch <output file> <aws arguments...>: an error or an empty answer fails the whole check.
fetch() {
  local out="$1"
  shift
  if ! aws "$@" --region "$REGION" --output json >"$out"; then
    echo "leftover-check: FAIL, aws $1 $2 failed; the account cannot be called clean" >&2
    exit 2
  fi
  [[ -s "$out" ]] || { echo "leftover-check: FAIL, aws $1 $2 printed nothing" >&2; exit 2; }
}

fetch "$work/by-environment.json" resourcegroupstaggingapi get-resources \
  --tag-filters "Key=environment,Values=$ENVIRONMENT_TAG"
fetch "$work/by-cluster.json" resourcegroupstaggingapi get-resources \
  --tag-filters "Key=elbv2.k8s.aws/cluster,Values=$CLUSTER_NAME"
fetch "$work/enis-environment.json" ec2 describe-network-interfaces \
  --filters "Name=tag:environment,Values=$ENVIRONMENT_TAG"
fetch "$work/enis-cluster.json" ec2 describe-network-interfaces \
  --filters "Name=tag:elbv2.k8s.aws/cluster,Values=$CLUSTER_NAME"

check "$work/by-environment.json" "$work/by-cluster.json" "$work/enis-environment.json" \
  "$work/enis-cluster.json"
