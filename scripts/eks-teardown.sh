#!/usr/bin/env bash
# Tears the EKS environment down in AD-24 order (story 5.4); env-down.yml calls it, then runs
# scripts/leftover-check.sh. Nothing is force-deleted and no finalizer is touched.
#
#   scripts/eks-teardown.sh --kubeconfig <file>
#   scripts/eks-teardown.sh --skip-cluster      # the cluster never came up: Terraform only
#
# Order:
#   1. helm uninstall ticketscope
#   2. delete the PVCs of the app namespace (the EBS CSI driver removes the volumes)
#   3. delete the Gateway and wait until its ALB is gone, with the controller still running
#   4. helm uninstall platform
#   5. wait until tagged ENIs and volumes are gone
#   6. terraform destroy of infra/env (the caller has run `terraform init`; TF_VAR_* are set)
#
# A Gateway whose ALB is not gone in time prints its finalizers and the remedy, and the script
# exits 1 before `platform` is uninstalled: the controller must stay to finish the job.
#
# Env overrides:
#   ALB_WAIT_SECONDS          give-up time for the ALB (default 900, 15 minutes)
#   ENI_VOLUME_WAIT_SECONDS   give-up time for tagged ENIs and volumes (default 600, 10 minutes)
#   POLL_SECONDS              pause between polls (default 10)
#   ENVIRONMENT_TAG           value of the `environment` tag (default eks)
#   CLUSTER_NAME              cluster name, the controller's cluster tag (default ticketscope-env)
#   AWS_REGION                default us-east-1
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat >&2 <<'EOF'
usage: scripts/eks-teardown.sh --kubeconfig <file>
       scripts/eks-teardown.sh --skip-cluster
EOF
  exit 2
}

KUBECONFIG_FILE=""
SKIP_CLUSTER=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) [[ $# -ge 2 ]] || usage; KUBECONFIG_FILE="$2"; shift 2 ;;
    --skip-cluster) SKIP_CLUSTER=1; shift ;;
    -h | --help) usage ;;
    *) echo "eks-teardown: unknown argument $1" >&2; usage ;;
  esac
done
if ((SKIP_CLUSTER == 0)); then
  [[ -n "$KUBECONFIG_FILE" ]] || usage
  [[ -f "$KUBECONFIG_FILE" ]] || { echo "eks-teardown: kubeconfig $KUBECONFIG_FILE not found" >&2; usage; }
  export KUBECONFIG="$KUBECONFIG_FILE"
fi

ALB_WAIT_SECONDS="${ALB_WAIT_SECONDS:-900}"
ENI_VOLUME_WAIT_SECONDS="${ENI_VOLUME_WAIT_SECONDS:-600}"
POLL_SECONDS="${POLL_SECONDS:-10}"
ENVIRONMENT_TAG="${ENVIRONMENT_TAG:-eks}"
CLUSTER_NAME="${CLUSTER_NAME:-ticketscope-env}"
REGION="${AWS_REGION:-us-east-1}"
PLATFORM_NS=platform
APP_NS=ticketscope
GATEWAY=ticketscope

START_EPOCH=$(date +%s)
STAGE_EPOCH=$START_EPOCH
SUMMARY=()
CURRENT=""
log() { printf '[%s +%4ss] %s\n' "$(date -u +%H:%M:%S)" "$(($(date +%s) - START_EPOCH))" "$*"; }
# stage <name>: closes the previous stage's timer and opens this one.
stage() {
  local now
  now=$(date +%s)
  if [[ -n "$CURRENT" ]]; then SUMMARY+=("$(printf '%-28s %5ss' "$CURRENT" "$((now - STAGE_EPOCH))")"); fi
  CURRENT="${1:-}"
  STAGE_EPOCH=$now
  if [[ -n "$CURRENT" ]]; then log "stage: $CURRENT"; fi
}
# The summary is printed even on failure, between a header and `total`, like eks-deploy.sh.
summary() {
  stage ""
  echo "--- eks-teardown stage times ---"
  if ((${#SUMMARY[@]})); then printf '%s\n' "${SUMMARY[@]}"; fi
  printf '%-28s %5ss\n' total "$(($(date +%s) - START_EPOCH))"
}
trap summary EXIT

# alb_gone: true only when the tagging API answers and lists no load balancer of this cluster.
# An `aws` error is "not gone", never "gone".
alb_gone() {
  local out
  out="$(aws resourcegroupstaggingapi get-resources --region "$REGION" \
    --resource-type-filters elasticloadbalancing:loadbalancer \
    --tag-filters "Key=elbv2.k8s.aws/cluster,Values=$CLUSTER_NAME" \
    --query 'ResourceTagMappingList[].ResourceARN' --output text)" || return 1
  [[ -z "$out" || "$out" == None ]]
}

# eni_volume_gone: true only when no tagged ENI or volume is listed; an `aws` error is "not gone".
eni_volume_gone() {
  local out
  out="$(aws ec2 describe-network-interfaces --region "$REGION" \
    --filters "Name=tag:environment,Values=$ENVIRONMENT_TAG" \
    --query 'NetworkInterfaces[].NetworkInterfaceId' --output text)" || return 1
  [[ -z "$out" || "$out" == None ]] || return 1
  out="$(aws ec2 describe-network-interfaces --region "$REGION" \
    --filters "Name=tag:elbv2.k8s.aws/cluster,Values=$CLUSTER_NAME" \
    --query 'NetworkInterfaces[].NetworkInterfaceId' --output text)" || return 1
  [[ -z "$out" || "$out" == None ]] || return 1
  out="$(aws ec2 describe-volumes --region "$REGION" \
    --filters "Name=tag:environment,Values=$ENVIRONMENT_TAG" \
    --query 'Volumes[].VolumeId' --output text)" || return 1
  [[ -z "$out" || "$out" == None ]]
}

# wait_for <seconds> <function>: polls until the function succeeds or the time is up.
wait_for() {
  local until_epoch=$(($(date +%s) + $1))
  until "$2"; do
    if (($(date +%s) >= until_epoch)); then return 1; fi
    sleep "$POLL_SECONDS"
  done
}

stuck_gateway() {
  echo "eks-teardown: the ALB of Gateway $GATEWAY is still there after ${ALB_WAIT_SECONDS}s." >&2
  echo "Finalizers on the Gateway:" >&2
  kubectl -n "$PLATFORM_NS" get gateway "$GATEWAY" -o jsonpath='{.metadata.finalizers}' >&2 || true
  echo >&2
  cat >&2 <<EOF
Remedy: the load balancer controller (release platform) is left installed so it can finish.
Read its log (kubectl -n $PLATFORM_NS logs deploy/aws-load-balancer-controller) and the
Gateway's events (kubectl -n $PLATFORM_NS describe gateway $GATEWAY), fix the cause, then
dispatch env-down again. Nothing was force-deleted and no finalizer was removed.
EOF
}

log "eks-teardown start (cluster ${CLUSTER_NAME}, environment ${ENVIRONMENT_TAG})"

if ((SKIP_CLUSTER == 0)); then
  stage "helm-uninstall-app"
  helm uninstall ticketscope --namespace "$APP_NS" --ignore-not-found --wait --timeout 10m

  stage "delete-pvcs"
  kubectl -n "$APP_NS" delete pvc --all --ignore-not-found --wait=true --timeout=10m

  stage "gateway-and-alb"
  kubectl -n "$PLATFORM_NS" delete gateway "$GATEWAY" --ignore-not-found --wait=false
  log "waiting up to ${ALB_WAIT_SECONDS}s for the ALB to go, with the controller running"
  if ! wait_for "$ALB_WAIT_SECONDS" alb_gone; then
    stuck_gateway
    exit 1
  fi
  log "the ALB is gone"

  stage "helm-uninstall-platform"
  helm uninstall platform --namespace "$PLATFORM_NS" --ignore-not-found --wait --timeout 10m

  stage "enis-and-volumes"
  log "waiting up to ${ENI_VOLUME_WAIT_SECONDS}s for tagged ENIs and volumes to go"
  if ! wait_for "$ENI_VOLUME_WAIT_SECONDS" eni_volume_gone; then
    echo "eks-teardown: tagged ENIs or volumes are still listed after ${ENI_VOLUME_WAIT_SECONDS}s" >&2
    exit 1
  fi
else
  log "no cluster: skipping the Kubernetes steps"
fi

stage "terraform-destroy"
terraform -chdir=infra/env destroy -auto-approve -input=false

stage ""
log "eks-teardown done; run scripts/leftover-check.sh next"
