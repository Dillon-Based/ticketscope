#!/usr/bin/env bash
# Tears the EKS environment down in AD-24 order (story 5.4); env-down.yml calls it, then runs
# scripts/leftover-check.sh. Nothing is force-deleted and no finalizer is touched.
#
#   scripts/eks-teardown.sh --kubeconfig <file> --hostname <name> --zone-id <id>
#   scripts/eks-teardown.sh --skip-cluster --hostname <name> --zone-id <id>   # Terraform only
#
# --hostname and --zone-id default to TICKETSCOPE_HOSTNAME and TICKETSCOPE_ZONE_ID (what
# scripts/eks-env.sh exports); one of the two is required.
#
# Order:
#   1. helm uninstall ticketscope
#   2. delete the PVCs of the app namespace (the EBS CSI driver removes the volumes)
#   3. delete the Gateway and wait until its ALB and the Gateway object are gone, with the
#      controller still running
#   4. delete the controller's configuration objects and wait until each is gone, controller still
#      running: the TargetGroupConfigurations (app namespace), the LoadBalancerConfigurations
#      (platform namespace), then the GatewayClass. They belong to the `platform` release, carry
#      the controller's finalizers, and helm would delete them together with the controller.
#   5. helm uninstall platform
#   6. wait until tagged ENIs and volumes are gone
#   7. terraform destroy of infra/env (the caller has run `terraform init`; TF_VAR_* are set)
#   8. delete the hostname's A and AAAA records from the zone (external-dns leaves them), then
#      list again: the zone must hold none
#
# A Gateway or configuration object that is not gone in time prints its finalizers and the remedy,
# and the script exits 1 before `platform` is uninstalled: the controller must stay to finish.
#
# Exit status: 0 clean; 1 a stage failed (nothing after it ran); 2 usage; 3 the environment was
# destroyed but the DNS step could not read the zone, could not delete the hostname's A and AAAA
# records, or still found them afterwards. external-dns writes no TXT ownership records, so it
# never deletes them; on failure the script prints the commands that delete them by hand. The step
# runs after the destroy so billing stops anyway.
#
# Env overrides:
#   ALB_WAIT_SECONDS          give-up time for the ALB and the Gateway (default 900, 15 minutes)
#   CONFIG_WAIT_SECONDS       give-up time for each configuration object (default 300, 5 minutes)
#   ENI_VOLUME_WAIT_SECONDS   give-up time for tagged ENIs and volumes (default 600, 10 minutes)
#   POLL_SECONDS              pause between polls (default 10)
#   GATEWAY_CLASS             the GatewayClass name, gateway.className on EKS (default alb)
#   ENVIRONMENT_TAG           value of the `environment` tag (default eks)
#   CLUSTER_NAME              cluster name, the controller's cluster tag (default ticketscope-env)
#   AWS_REGION                default us-east-1
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat >&2 <<'EOF'
usage: scripts/eks-teardown.sh --kubeconfig <file> [--hostname <name>] [--zone-id <id>]
       scripts/eks-teardown.sh --skip-cluster [--hostname <name>] [--zone-id <id>]
(--hostname and --zone-id default to TICKETSCOPE_HOSTNAME and TICKETSCOPE_ZONE_ID; both required)
EOF
  exit 2
}

KUBECONFIG_FILE=""
SKIP_CLUSTER=0
DNS_NAME="${TICKETSCOPE_HOSTNAME:-}"
ZONE_ID="${TICKETSCOPE_ZONE_ID:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) [[ $# -ge 2 ]] || usage; KUBECONFIG_FILE="$2"; shift 2 ;;
    --skip-cluster) SKIP_CLUSTER=1; shift ;;
    --hostname) [[ $# -ge 2 ]] || usage; DNS_NAME="$2"; shift 2 ;;
    --zone-id) [[ $# -ge 2 ]] || usage; ZONE_ID="$2"; shift 2 ;;
    -h | --help) usage ;;
    *) echo "eks-teardown: unknown argument $1" >&2; usage ;;
  esac
done
if ((SKIP_CLUSTER == 0)); then
  [[ -n "$KUBECONFIG_FILE" ]] || usage
  [[ -f "$KUBECONFIG_FILE" ]] || { echo "eks-teardown: kubeconfig $KUBECONFIG_FILE not found" >&2; usage; }
  export KUBECONFIG="$KUBECONFIG_FILE"
fi
DNS_NAME="${DNS_NAME%.}"
[[ -n "$DNS_NAME" && -n "$ZONE_ID" ]] || { echo "eks-teardown: the hostname and the zone id are required" >&2; usage; }

ALB_WAIT_SECONDS="${ALB_WAIT_SECONDS:-900}"
CONFIG_WAIT_SECONDS="${CONFIG_WAIT_SECONDS:-300}"
ENI_VOLUME_WAIT_SECONDS="${ENI_VOLUME_WAIT_SECONDS:-600}"
POLL_SECONDS="${POLL_SECONDS:-10}"
GATEWAY_CLASS="${GATEWAY_CLASS:-alb}"
ENVIRONMENT_TAG="${ENVIRONMENT_TAG:-eks}"
CLUSTER_NAME="${CLUSTER_NAME:-ticketscope-env}"
REGION="${AWS_REGION:-us-east-1}"
PLATFORM_NS=platform
APP_NS=ticketscope
GATEWAY=ticketscope
# The controller's configuration kinds, fully qualified so no other API group's kind is matched.
TGC=targetgroupconfiguration.gateway.k8s.aws
LBC=loadbalancerconfiguration.gateway.k8s.aws

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

# gateway_gone: true only when the cluster answers and the Gateway object no longer exists. The
# controller removes its finalizer after it deletes the ALB, target groups and security group, and
# the ALB leaves the tagging API first, so the ALB alone is not enough to uninstall the controller.
gateway_gone() {
  local out
  out="$(kubectl -n "$PLATFORM_NS" get gateway "$GATEWAY" --ignore-not-found -o name)" || return 1
  [[ -z "$out" ]]
}

# alb_and_gateway_gone: both conditions, in one poll.
alb_and_gateway_gone() { alb_gone && gateway_gone; }

# Configuration objects are named by <namespace> <kind> <name>: an empty namespace means
# cluster-scoped, an empty name means every object of the kind.
# target_args <namespace> <kind> <name>: the kubectl arguments that select them.
target_args() {
  TARGET=()
  if [[ -n "$1" ]]; then TARGET+=(-n "$1"); fi
  TARGET+=("$2")
  if [[ -n "$3" ]]; then TARGET+=("$3"); fi
}

# none_listed <namespace> <kind> <name>: true only when the cluster answers and lists none of them.
# A kubectl error is "not gone", never "gone".
none_listed() {
  local out
  target_args "$@"
  out="$(kubectl get "${TARGET[@]}" --ignore-not-found -o name)" || return 1
  [[ -z "$out" ]]
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

# wait_for <seconds> <command...>: polls until the command succeeds or the time is up.
wait_for() {
  local until_epoch=$(($(date +%s) + $1))
  shift
  until "$@"; do
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

# stuck_config <namespace> <kind> <name>: the report for configuration objects still there after
# CONFIG_WAIT_SECONDS.
stuck_config() {
  target_args "$@"
  echo "eks-teardown: ${TARGET[*]} is still there after ${CONFIG_WAIT_SECONDS}s." >&2
  echo "Finalizers:" >&2
  kubectl get "${TARGET[@]}" -o custom-columns='NAME:.metadata.name,FINALIZERS:.metadata.finalizers' >&2 || true
  cat >&2 <<EOF
Remedy: the load balancer controller (release platform) is left installed so it can remove its
finalizers. Read its log (kubectl -n $PLATFORM_NS logs deploy/aws-load-balancer-controller) and
the object's events (kubectl describe ${TARGET[*]}), fix the cause, then dispatch env-down again.
Nothing was force-deleted, no finalizer was removed and nothing was patched.
EOF
}

# delete_and_wait <namespace> <kind> <name>: deletes the objects, waits until the cluster lists
# none of them, and on timeout reports them and exits 1 (before `platform` is uninstalled).
delete_and_wait() {
  target_args "$@"
  if [[ -n "$3" ]]; then
    kubectl delete "${TARGET[@]}" --ignore-not-found --wait=false
  else
    kubectl delete "${TARGET[@]}" --all --ignore-not-found --wait=false
  fi
  log "waiting up to ${CONFIG_WAIT_SECONDS}s for ${TARGET[*]} to go, with the controller running"
  if ! wait_for "$CONFIG_WAIT_SECONDS" none_listed "$@"; then
    stuck_config "$@"
    exit 1
  fi
  log "${TARGET[*]} is gone"
}

# DNS: only the hostname's A and AAAA records are ever listed or changed. The zone's NS and SOA
# records, the certificate validation records and every other name are never selected, and the
# deploy role may change only those two types for this name, with the DELETE action.
DNS_FILTER="ResourceRecordSets[?Name=='${DNS_NAME}.' && (Type=='A' || Type=='AAAA')]"

# dns_listing: prints the hostname's A and AAAA records (name and type, tab separated). Fails when
# the zone cannot be read; that is never clean.
dns_listing() {
  aws route53 list-resource-record-sets --hosted-zone-id "$ZONE_ID" \
    --query "$DNS_FILTER.[Name,Type]" --output text
}

dns_remedy() {
  cat >&2 <<EOF
They point at a load balancer that no longer exists and break the next env-up's DNS stage.
Remedy (with an identity that may change the zone, after checking the listing above):
  aws route53 list-resource-record-sets --hosted-zone-id $ZONE_ID \\
    --query "$DNS_FILTER" --output json \\
    | jq '{Changes: [.[] | {Action: "DELETE", ResourceRecordSet: .}]}' > stale-records.json
  aws route53 change-resource-record-sets --hosted-zone-id $ZONE_ID \\
    --change-batch file://stale-records.json
EOF
}

# dns_clean_up: external-dns writes no TXT ownership records, so it never deletes the hostname's
# A and AAAA records. After the destroy they are deleted here, then listed again. Returns 0 only
# when the zone was read and holds none afterwards; any failure returns 1 (exit 3 semantics).
dns_clean_up() {
  local out batch
  if ! out="$(dns_listing)"; then
    echo "eks-teardown: could not list the records of zone $ZONE_ID; the DNS check is not clean" >&2
    return 1
  fi
  if [[ -z "$out" || "$out" == None ]]; then
    log "no A or AAAA record for $DNS_NAME is left in the zone"
    return 0
  fi
  log "deleting the stale records external-dns left for $DNS_NAME:"
  printf '%s\n' "$out"
  batch="$(mktemp)"
  if ! aws route53 list-resource-record-sets --hosted-zone-id "$ZONE_ID" \
    --query "{Changes: $DNS_FILTER.{Action: 'DELETE', ResourceRecordSet: @}}" --output json >"$batch" \
    || ! aws route53 change-resource-record-sets --hosted-zone-id "$ZONE_ID" \
      --change-batch "file://$batch" >/dev/null; then
    rm -f "$batch"
    echo "eks-teardown: could not delete the records of $DNS_NAME from zone $ZONE_ID:" >&2
    printf '%s\n' "$out" >&2
    dns_remedy
    return 1
  fi
  rm -f "$batch"
  if ! out="$(dns_listing)"; then
    echo "eks-teardown: could not list the records of zone $ZONE_ID after the delete; not clean" >&2
    return 1
  fi
  if [[ -n "$out" && "$out" != None ]]; then
    echo "eks-teardown: the zone still holds records for $DNS_NAME after the delete:" >&2
    printf '%s\n' "$out" >&2
    dns_remedy
    return 1
  fi
  log "the stale records for $DNS_NAME are deleted"
}

log "eks-teardown start (cluster ${CLUSTER_NAME}, environment ${ENVIRONMENT_TAG})"

if ((SKIP_CLUSTER == 0)); then
  stage "helm-uninstall-app"
  helm uninstall ticketscope --namespace "$APP_NS" --ignore-not-found --wait --timeout 10m

  stage "delete-pvcs"
  kubectl -n "$APP_NS" delete pvc --all --ignore-not-found --wait=true --timeout=10m

  stage "gateway-and-alb"
  kubectl -n "$PLATFORM_NS" delete gateway "$GATEWAY" --ignore-not-found --wait=false
  log "waiting up to ${ALB_WAIT_SECONDS}s for the ALB and the Gateway to go, with the controller running"
  if ! wait_for "$ALB_WAIT_SECONDS" alb_and_gateway_gone; then
    stuck_gateway
    exit 1
  fi
  log "the ALB and the Gateway are gone"

  # Live finding: `helm uninstall platform` deleted these together with the controller, the
  # controller went first, and they stayed Terminating on its finalizers until helm gave up.
  stage "controller-config-objects"
  delete_and_wait "$APP_NS" "$TGC" ""
  delete_and_wait "$PLATFORM_NS" "$LBC" ""
  delete_and_wait "" gatewayclass "$GATEWAY_CLASS"

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

stage "dns-records"
dns_clean=1
dns_clean_up || dns_clean=0

stage ""
if ((dns_clean == 0)); then
  echo "eks-teardown: the environment is destroyed, but the DNS step failed (see above)" >&2
  exit 3
fi
log "eks-teardown done; run scripts/leftover-check.sh next"
