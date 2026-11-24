#!/usr/bin/env bash
# Installs the two releases on an applied EKS environment (AD-13, AD-17); story 5.3's
# workflow calls it. Terraform owns AWS resources; every Helm release is installed here.
#
#   scripts/eks-deploy.sh --kubeconfig <file> --tag <image tag> --hostname <fixed host> \
#       --certificate-arn <bootstrap ACM arn> --ecr-registry <account>.dkr.ecr.<region>.amazonaws.com
#
# Order: Gateway API CRDs, the controller's CRDs, `platform`, `ticketscope`, then the DNS
# stages (`dns_visible` on the zone's own name servers, `dns_public` on a public resolver) and
# the HTTPS poll. Prints the time of each stage and a summary at the end. Idempotent: re-running upgrades in place.
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
#   DNS_TIMEOUT          seconds each DNS stage waits for the record (default 900)
#   PUBLIC_RESOLVER      resolver the dns_public stage asks (default 1.1.1.1)
#   ZONE_NAME_SERVERS    space-separated name servers of the zone; read from Route53 when unset
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat >&2 <<'EOF'
usage: scripts/eks-deploy.sh --kubeconfig <file> --tag <image tag> --hostname <host>
                             --certificate-arn <arn> --ecr-registry <registry host>
                             --incarnation <id> [--restore-from <id>]
The first six are required (the incarnation names this environment's backup folder). Nothing is installed when one is missing.
--restore-from names the previous incarnation's folder: the database recovers from it and nothing is loaded (R11).
EOF
  exit 2
}

need_value() { [[ "$1" -ge 2 ]] || usage; }
KUBECONFIG_FILE=""
TAG=""
HOSTNAME_VALUE=""
CERTIFICATE_ARN=""
ECR_REGISTRY=""
INCARNATION=""
RESTORE_FROM=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --kubeconfig) need_value "$#"; KUBECONFIG_FILE="${2:-}"; shift 2 ;;
    --tag) need_value "$#"; TAG="${2:-}"; shift 2 ;;
    --hostname) need_value "$#"; HOSTNAME_VALUE="${2:-}"; shift 2 ;;
    --certificate-arn) need_value "$#"; CERTIFICATE_ARN="${2:-}"; shift 2 ;;
    --ecr-registry) need_value "$#"; ECR_REGISTRY="${2:-}"; shift 2 ;;
    --incarnation) need_value "$#"; INCARNATION="${2:-}"; shift 2 ;;
    --restore-from) need_value "$#"; RESTORE_FROM="${2:-}"; shift 2 ;;
    -h | --help) usage ;;
    *) echo "eks-deploy: unknown argument $1" >&2; usage ;;
  esac
done
[[ -n "$KUBECONFIG_FILE" && -n "$TAG" && -n "$HOSTNAME_VALUE" && -n "$CERTIFICATE_ARN" && -n "$ECR_REGISTRY" && -n "$INCARNATION" ]] || usage
# The incarnation becomes the plugin's serverName, a folder name under backups/ (R11).
[[ "$INCARNATION" =~ ^[a-z0-9][a-z0-9-]{0,62}$ ]] || { echo "eks-deploy: --incarnation must be lowercase letters, digits and dashes" >&2; usage; }
if [[ -n "$RESTORE_FROM" ]]; then
  [[ "$RESTORE_FROM" =~ ^[a-z0-9][a-z0-9-]{0,62}$ ]] || { echo "eks-deploy: --restore-from must be lowercase letters, numbers and dashes" >&2; usage; }
  [[ "$RESTORE_FROM" != "$INCARNATION" ]] || { echo "eks-deploy: --restore-from must differ from --incarnation" >&2; usage; }
fi
[[ -f "$KUBECONFIG_FILE" ]] || { echo "eks-deploy: kubeconfig $KUBECONFIG_FILE not found" >&2; usage; }

for tool in kubectl helm jq curl tar dig aws; do
  command -v "$tool" >/dev/null || { echo "eks-deploy: $tool is required" >&2; exit 1; }
done

export KUBECONFIG="$KUBECONFIG_FILE"
GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.6.0}"
READY_TIMEOUT="${READY_TIMEOUT:-900}"
DNS_TIMEOUT="${DNS_TIMEOUT:-900}"
PUBLIC_RESOLVER="${PUBLIC_RESOLVER:-1.1.1.1}"
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
BACKUP_ROLE_ARN="$(out cnpg_backup_role_arn)"
BACKUP_BUCKET="$(out backup_bucket)"

# shellcheck disable=SC2034  # read by summary() in lib/stages.sh
STAGES_TITLE=eks-deploy
# shellcheck source=/dev/null
source "$ROOT/scripts/lib/stages.sh"


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
# restoreFrom is set only for a recreate: the Cluster recovers and no load Job renders (R11).
RESTORE_ARGS=()
if [[ -n "$RESTORE_FROM" ]]; then RESTORE_ARGS=(--set-string "backup.restoreFrom=${RESTORE_FROM}"); fi
helm upgrade --install ticketscope "$CHARTS/ticketscope" \
  --namespace "$APP_NS" --create-namespace \
  -f "$CHARTS/ticketscope/values-eks.yaml" \
  --set-string "hostname=${HOSTNAME_VALUE}" \
  --set-string "image.app.repository=${ECR_REGISTRY}/ticketscope-app" \
  --set-string "image.app.tag=${TAG}" \
  --set-string "image.postgres.repository=${ECR_REGISTRY}/ticketscope-postgres" \
  --set-string "image.postgres.tag=${PG_TAG}" \
  --set-string "backup.destinationPath=s3://${BACKUP_BUCKET}/backups/" \
  --set-string "backup.serverName=${INCARNATION}" \
  ${RESTORE_ARGS[@]+"${RESTORE_ARGS[@]}"} \
  --set-string "database.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn=${BACKUP_ROLE_ARN}" \
  --timeout 25m

stage "api-mcp-ready"
kubectl -n "$APP_NS" rollout status deploy/ticketscope-api --timeout=10m
kubectl -n "$APP_NS" rollout status deploy/ticketscope-mcp --timeout=5m

# A resolver that is asked before the record exists caches the miss (the zone's negative TTL is
# 15 minutes), so the zone's own name servers are polled first and the public one only after.
# resolves <server> <name>: succeeds when the server answers an A record for the name.
resolves() { [[ -n "$(dig +short +time=3 +tries=1 A "@$1" "$2" 2>/dev/null)" ]]; }
# wait_dns <server> <label>: polls until <server> answers for the hostname or DNS_TIMEOUT passes.
wait_dns() {
  local until_epoch=$(($(date +%s) + DNS_TIMEOUT))
  until resolves "$1" "$HOSTNAME_VALUE"; do
    if (($(date +%s) > until_epoch)); then
      echo "eks-deploy: $2 did not answer for ${HOSTNAME_VALUE} within ${DNS_TIMEOUT}s" >&2
      return 1
    fi
    sleep 5
  done
}

stage "dns_visible"
NAME_SERVERS="${ZONE_NAME_SERVERS:-}"
if [[ -z "$NAME_SERVERS" ]]; then
  # The hosted zone is the fixed hostname itself (bootstrap); its delegation set is the truth.
  ZONE_ID="$(aws route53 list-hosted-zones-by-name --dns-name "$HOSTNAME_VALUE" \
    --query "HostedZones[?Name=='${HOSTNAME_VALUE}.'].Id | [0]" --output text)"
  ZONE_ID="${ZONE_ID##*/}"
  [[ -n "$ZONE_ID" && "$ZONE_ID" != None ]] || { echo "eks-deploy: no hosted zone named ${HOSTNAME_VALUE}" >&2; exit 1; }
  NAME_SERVERS="$(aws route53 get-hosted-zone --id "$ZONE_ID" \
    --query 'DelegationSet.NameServers' --output text)"
fi
[[ -n "$NAME_SERVERS" ]] || { echo "eks-deploy: no name servers found for ${HOSTNAME_VALUE}" >&2; exit 1; }
for ns in $NAME_SERVERS; do
  wait_dns "$ns" "name server $ns"
done
log "every name server of the zone answers for ${HOSTNAME_VALUE}"

stage "dns_public"
wait_dns "$PUBLIC_RESOLVER" "public resolver $PUBLIC_RESOLVER"
log "public resolver ${PUBLIC_RESOLVER} answers"

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
