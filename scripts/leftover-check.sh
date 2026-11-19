#!/usr/bin/env bash
# The read-only leftover check of env-down (story 5.4, R3): lists what is still tagged for the
# environment and fails on any of it. Only list and describe calls are made.
#
#   scripts/leftover-check.sh [--list] [--dry-run] [--from-file <listing.json> ...]
#
#   (no flag)   fail (exit 1) naming each tagged resource; an `aws` error fails (exit 2) too
#   --list      print what is found and exit 0 (the positive control while the environment is up);
#               nothing is confirmed or dropped
#   --dry-run   no AWS call: injects a tagged load balancer, which must fail and name it
#   --from-file read the given listings instead of calling AWS (offline, nothing confirmed)
#
# The tagging API lags: after the env stack was torn down it listed removed volumes for at least four
# minutes. So each candidate is confirmed with one read-only describe call to its own service
# (confirm, below). Only a definite not-found error code, an empty answer, or a KMS key pending
# deletion or disabled counts as gone, printed `GONE <type> <id> (tagging API lag)`. Any other
# error, and any type with no describe here, keeps the candidate a leftover: an error never
# reads as clean.
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

listings=("$work/by-environment.json" "$work/by-cluster.json" "$work/enis-environment.json"
  "$work/enis-cluster.json")
# --list is the positive control: it shows what the tagging API returns, unconfirmed.
if [[ " ${mode[*]-} " == *" --list "* ]]; then check "${listings[@]}"; exit $?; fi

# describe <not-found code> <aws arguments...>: sets STATUS to gone, found or error and OUT to the
# answer. The arguments end in a --query that prints nothing when the resource does not exist.
describe() {
  local code="$1" err rc=0
  shift
  err="$work/describe.err"
  OUT="$(aws "$@" --region "$REGION" --output text 2>"$err")" || rc=$?
  if ((rc == 0)); then
    if [[ -z "$OUT" || "$OUT" == None ]]; then STATUS=gone; else STATUS=found; fi
  elif grep -q "($code)" "$err"; then
    STATUS=gone
  else
    sed 's/^/leftover-check: describe error: /' "$err" >&2
    STATUS=error
  fi
}

# confirm <type> <id>: prints gone, found, error or unconfirmed (a type with no describe here).
confirm() {
  local kind="$1" ident="$2" id name
  id="${ident##*/}"
  STATUS=unconfirmed
  OUT=""
  case "$kind" in
    ec2:volume)
      describe InvalidVolume.NotFound ec2 describe-volumes --volume-ids "$id" \
        --query 'Volumes[].VolumeId' ;;
    ec2:network-interface)
      describe InvalidNetworkInterfaceID.NotFound ec2 describe-network-interfaces \
        --network-interface-ids "$id" --query 'NetworkInterfaces[].NetworkInterfaceId' ;;
    ec2:security-group)
      describe InvalidGroup.NotFound ec2 describe-security-groups --group-ids "$id" \
        --query 'SecurityGroups[].GroupId' ;;
    elasticloadbalancing:loadbalancer)
      describe LoadBalancerNotFound elbv2 describe-load-balancers --load-balancer-arns "$ident" \
        --query 'LoadBalancers[].LoadBalancerArn' ;;
    elasticloadbalancing:targetgroup)
      describe TargetGroupNotFound elbv2 describe-target-groups --target-group-arns "$ident" \
        --query 'TargetGroups[].TargetGroupArn' ;;
    kms:key)
      describe NotFoundException kms describe-key --key-id "$ident" --query 'KeyMetadata.KeyState'
      # A key cannot be removed at once: pending deletion (or disabled) is as gone as it gets.
      if [[ "$STATUS" == found && ("$OUT" == PendingDeletion || "$OUT" == Disabled) ]]; then
        STATUS=gone
      fi
      ;;
    logs:log-group)
      name="${ident#*:log-group:}"
      name="${name%:\*}"
      describe ResourceNotFoundException logs describe-log-groups --log-group-name-prefix "$name" \
        --query "logGroups[?logGroupName=='$name'].logGroupName" ;;
  esac
  echo "$STATUS"
}

candidates="$(check --candidates "${listings[@]}")" || exit $?
: >"$work/confirmations.tsv"
while IFS=$'\t' read -r kind ident; do
  [[ -n "$ident" ]] || continue
  printf '%s\t%s\n' "$ident" "$(confirm "$kind" "$ident")" >>"$work/confirmations.tsv"
done <<<"$candidates"

check --confirmations "$work/confirmations.tsv" "${listings[@]}"
