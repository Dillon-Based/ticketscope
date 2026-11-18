#!/usr/bin/env bash
# Installs the two releases on an applied EKS environment (AD-13, AD-17); story 5.3's
# workflow calls it. Terraform owns AWS resources; every Helm release is installed here.
#
#   scripts/eks-deploy.sh --kubeconfig <file> --tag <image tag> --hostname <fixed host> \
#       --certificate-arn <bootstrap ACM arn> --ecr-registry <account>.dkr.ecr.<region>.amazonaws.com
#
# Order: Gateway API CRDs, the controller's CRDs, `platform`, `ticketscope`. Prints the time
# of each stage and a summary at the end. Idempotent: re-running upgrades in place.
#
# Cluster facts (cluster name, VPC id, IRSA role ARNs) come from `terraform output -json` of
# infra/env, or from the file named by ENV_OUTPUTS_JSON.
#
# Env overrides:
#   GATEWAY_API_VERSION  standard-channel Gateway API CRD release (default v1.6.0, the version the controller is built for)
#   TARGET_ANNOTATION    sets external-dns.kubernetes.io/target on the Gateway: the fallback
#                        when external-dns does not read the ALB's address (AD-14)
#   ENV_OUTPUTS_JSON     a file holding `terraform -chdir=infra/env output -json`
#   READY_TIMEOUT        seconds to wait for https://<hostname>/ (default 900)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat >&2 <<'EOF'
usage: scripts/eks-deploy.sh --kubeconfig <file> --tag <image tag> --hostname <host>
                             --certificate-arn <arn> --ecr-registry <registry host>
All five are required. Nothing is installed when one is missing.
EOF
  exit 2
}

need_value() { [[ "$1" -ge 2 ]] || usage; }
KUBECONFIG_FILE=""
TAG=""
HOSTNAME_VALUE=""
CERTIFICATE_ARN=""
ECR_REGISTRY=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) need_value "$#"; KUBECONFIG_FILE="${2:-}"; shift 2 ;;
    --tag) need_value "$#"; TAG="${2:-}"; shift 2 ;;
    --hostname) need_value "$#"; HOSTNAME_VALUE="${2:-}"; shift 2 ;;
    --certificate-arn) need_value "$#"; CERTIFICATE_ARN="${2:-}"; shift 2 ;;
    --ecr-registry) need_value "$#"; ECR_REGISTRY="${2:-}"; shift 2 ;;
    -h | --help) usage ;;
    *) echo "eks-deploy: unknown argument $1" >&2; usage ;;
  esac
done
[[ -n "$KUBECONFIG_FILE" && -n "$TAG" && -n "$HOSTNAME_VALUE" && -n "$CERTIFICATE_ARN" && -n "$ECR_REGISTRY" ]] || usage
[[ -f "$KUBECONFIG_FILE" ]] || { echo "eks-deploy: kubeconfig $KUBECONFIG_FILE not found" >&2; usage; }

for tool in kubectl helm jq curl tar; do
  command -v "$tool" >/dev/null || { echo "eks-deploy: $tool is required" >&2; exit 1; }
done

export KUBECONFIG="$KUBECONFIG_FILE"
GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.6.0}"
READY_TIMEOUT="${READY_TIMEOUT:-900}"
PLATFORM_NS=platform
APP_NS=ticketscope
PG_TAG="18-${TAG}"
CHARTS=deploy/charts

if [[ -n "${ENV_OUTPUTS_JSON:-}" ]]; then
  OUTPUTS="$(cat "$ENV_OUTPUTS_JSON")"
else
  OUTPUTS="$(terraform -chdir=infra/env output -json)"
fi
out() { jq -er ".$1.value" <<<"$OUTPUTS"; }
CLUSTER_NAME="$(out cluster_name)"
VPC_ID="$(out vpc_id)"
LBC_ROLE_ARN="$(out lb_controller_role_arn)"
DNS_ROLE_ARN="$(out external_dns_role_arn)"

START_EPOCH=$(date +%s)
STAGE_EPOCH=$START_EPOCH
SUMMARY=()
log() { printf '[%s +%4ss] %s\n' "$(date -u +%H:%M:%S)" "$(($(date +%s) - START_EPOCH))" "$*"; }
# stage <name>: closes the previous stage's timer and opens this one.
CURRENT=""
stage() {
  local now
  now=$(date +%s)
  if [[ -n "$CURRENT" ]]; then SUMMARY+=("$(printf '%-28s %5ss' "$CURRENT" "$((now - STAGE_EPOCH))")"); fi
  CURRENT="${1:-}"
  STAGE_EPOCH=$now
  if [[ -n "$CURRENT" ]]; then log "stage: $CURRENT"; fi
}
summary() {
  stage ""
  echo "--- eks-deploy stage times ---"
  if ((${#SUMMARY[@]})); then printf '%s\n' "${SUMMARY[@]}"; fi
  printf '%-28s %5ss\n' total "$(($(date +%s) - START_EPOCH))"
}


WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"; summary' EXIT

log "eks-deploy start (tag ${TAG}, cluster ${CLUSTER_NAME})"

stage "crds"
# The Gateway API CRDs and the controller's own, shared with the CI check (eks-crds.sh).
GATEWAY_API_VERSION="$GATEWAY_API_VERSION" scripts/eks-crds.sh

stage "platform"
# The TargetGroupConfigurations land in the app namespace, so it exists first.
kubectl create namespace "$APP_NS" --dry-run=client -o yaml | kubectl apply -f -
cat >"$WORK/platform-env.yaml" <<EOF
gateway:
  hostname: "${HOSTNAME_VALUE}"
  externalDnsTarget: "${TARGET_ANNOTATION:-}"
  aws:
    certificateArn: "${CERTIFICATE_ARN}"
aws-load-balancer-controller:
  clusterName: "${CLUSTER_NAME}"
  vpcId: "${VPC_ID}"
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: "${LBC_ROLE_ARN}"
external-dns:
  domainFilters: ["${HOSTNAME_VALUE}"]
  txtOwnerId: "${CLUSTER_NAME}"
  serviceAccount:
    annotations:
      eks.amazonaws.com/role-arn: "${DNS_ROLE_ARN}"
EOF
helm upgrade --install platform "$CHARTS/platform" \
  --namespace "$PLATFORM_NS" --create-namespace \
  -f "$CHARTS/platform/values-eks.yaml" -f "$WORK/platform-env.yaml" \
  --wait --timeout 15m
log "waiting for Gateway ticketscope to be Programmed"
kubectl -n "$PLATFORM_NS" wait gateway/ticketscope --for=condition=Programmed --timeout=10m

stage "ticketscope"
# No --wait: Helm's wait would hold the hooks on api readiness, and that needs load.
helm upgrade --install ticketscope "$CHARTS/ticketscope" \
  --namespace "$APP_NS" --create-namespace \
  -f "$CHARTS/ticketscope/values-eks.yaml" \
  --set-string "hostname=${HOSTNAME_VALUE}" \
  --set-string "image.app.repository=${ECR_REGISTRY}/ticketscope-app" \
  --set-string "image.app.tag=${TAG}" \
  --set-string "image.postgres.repository=${ECR_REGISTRY}/ticketscope-postgres" \
  --set-string "image.postgres.tag=${PG_TAG}" \
  --timeout 25m

stage "api-mcp-ready"
kubectl -n "$APP_NS" rollout status deploy/ticketscope-api --timeout=10m
kubectl -n "$APP_NS" rollout status deploy/ticketscope-mcp --timeout=5m

stage "https-answers"
# The record and the ALB may lag the pods: poll the public hostname until the page answers.
deadline=$(($(date +%s) + READY_TIMEOUT))
until curl -fsS -o /dev/null --max-time 10 "https://${HOSTNAME_VALUE}/"; do
  if (($(date +%s) > deadline)); then
    echo "eks-deploy: https://${HOSTNAME_VALUE}/ did not answer within ${READY_TIMEOUT}s" >&2
    kubectl -n "$PLATFORM_NS" get gateway ticketscope -o yaml >&2 || true
    exit 1
  fi
  sleep 10
done
log "https://${HOSTNAME_VALUE}/ answers"
echo "TICKETSCOPE_PUBLIC_URL=https://${HOSTNAME_VALUE}"
stage ""
log "eks-deploy done"
