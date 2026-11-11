#!/usr/bin/env bash
# The only kind bring-up (AD-17), used locally and by _kind-deploy.yml.
#
#   scripts/kind-up.sh
#
# Builds the two images for the native arch if missing, creates the kind
# cluster, starts cloud-provider-kind, loads the images, installs `platform`
# (--wait) and then `ticketscope`, and waits for api and mcp to be Ready (a rebuilt
# image under the deployed tag restarts both). Prints
# timestamps and the Gateway address. Idempotent: re-running upgrades in place.
#
# Env overrides:
#   TAG            image tag (default: git SHA of HEAD, AD-16)
#   FORCE_BUILD=1  rebuild images even if the tag exists locally
#   CLUSTER_NAME   kind cluster name (default: ticketscope)
#   EVAL_ENABLED=1 render the eval Job (a hook after load; eval.yml only) and give
#                  Helm longer to wait for it (default: off)
#   EMBEDDINGS_COMPUTE=1  set embeddings.computeOnKind: load computes embeddings with the baked
#                  model and api serves mode=dense; Helm waits longer for the load (default: off).
#                  The no-pin path: when values.yaml pins an embedding asset, load loads that
#                  asset and computes nothing, whatever this flag says.
#   TUNNEL_HOSTNAME  the tunnel's hostname, added to the Gateway, the /mcp route and mcp's
#                  allowed hosts (default: the stand-in in the kind values files)
#
# When $GITHUB_ENV is set, exports TICKETSCOPE_GATEWAY_URL,
# TICKETSCOPE_GATEWAY_HOST and TICKETSCOPE_KIND_UP_TO_READY_SECONDS to later steps.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CLUSTER_NAME="${CLUSTER_NAME:-ticketscope}"
# Kubernetes 1.36 everywhere (AD-16); the digest is the one kind v0.33 publishes.
KIND_NODE_IMAGE="kindest/node:v1.36.4@sha256:099e049362a1526b2db71494e1947aae99bd16290d7c895f2b7ea312e3cbfaed"
CPK_IMAGE="registry.k8s.io/cloud-provider-kind/cloud-controller-manager:v0.12.0"
CPK_CONTAINER="${CLUSTER_NAME}-cloud-provider-kind"
# Default read from the kind values so there is one stand-in, not two.
TUNNEL_HOSTNAME="${TUNNEL_HOSTNAME:-$(sed -n 's/^  tunnelHostname: *//p' deploy/charts/platform/values-kind.yaml | head -1)}"
TAG="${TAG:-$(git rev-parse HEAD)}"
APP_IMAGE="ticketscope-app:${TAG}"
# CNPG reads the Postgres major from the tag (regex ^(\d\.?)+), so the
# Postgres image tag leads with it: 18-<git SHA> (AD-16 still holds).
PG_MAJOR=18
PG_TAG="${PG_MAJOR}-${TAG}"
PG_IMAGE="ticketscope-postgres:${PG_TAG}"
PLATFORM_NS=platform
APP_NS=ticketscope
GATEWAY_NAME=ticketscope
KCTX="kind-${CLUSTER_NAME}"

START_EPOCH=$(date +%s)
log() { printf '[%s +%4ss] %s\n' "$(date -u +%H:%M:%S)" "$(($(date +%s) - START_EPOCH))" "$*"; }
k() { kubectl --context "$KCTX" "$@"; }

for tool in docker kind kubectl helm git; do
  command -v "$tool" >/dev/null || { echo "kind-up: $tool is required" >&2; exit 1; }
done

log "kind-up start (tag ${TAG})"

# 1. Images, native arch only. BUILT is set to 1 when build() built its image.
build() {
  local image=$1 dockerfile=$2
  BUILT=0
  if [[ "${FORCE_BUILD:-0}" != 1 ]] && docker image inspect "$image" >/dev/null 2>&1; then
    log "image $image present"
  else
    log "building $image"
    docker build -f "$dockerfile" -t "$image" .
    BUILT=1
  fi
}
build "$APP_IMAGE" images/app.Dockerfile
APP_BUILT=$BUILT
build "$PG_IMAGE" images/postgres.Dockerfile

# 2. Cluster.
if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  log "kind cluster $CLUSTER_NAME exists"
else
  log "creating kind cluster $CLUSTER_NAME"
  kind create cluster --name "$CLUSTER_NAME" --image "$KIND_NODE_IMAGE" --wait 180s
fi

# 3. cloud-provider-kind on the host's docker, on the kind network: gives the
#    Envoy Service its LoadBalancer IP. Its own Gateway and Ingress are off;
#    Envoy Gateway in the platform release implements the GatewayClass.
if [[ "$(docker inspect -f '{{.State.Running}}' "$CPK_CONTAINER" 2>/dev/null || true)" != true ]]; then
  docker rm -f "$CPK_CONTAINER" >/dev/null 2>&1 || true
  log "starting cloud-provider-kind"
  docker run -d --name "$CPK_CONTAINER" --network kind \
    -v /var/run/docker.sock:/var/run/docker.sock \
    "$CPK_IMAGE" --gateway-channel=disabled --enable-default-ingress=false >/dev/null
else
  log "cloud-provider-kind running"
fi

# 4. Images into the node.
log "loading images into kind"
kind load docker-image --name "$CLUSTER_NAME" "$APP_IMAGE" "$PG_IMAGE"

# 5. platform, waited.
log "installing platform"
# `dependency build` resolves non-OCI repos only through `helm repo add`.
helm repo add cnpg https://cloudnative-pg.github.io/charts --force-update >/dev/null
helm repo add seaweedfs https://seaweedfs.github.io/seaweedfs/helm --force-update >/dev/null
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts --force-update >/dev/null
helm repo add grafana-community https://grafana-community.github.io/helm-charts --force-update >/dev/null
helm dependency build deploy/charts/platform
helm --kube-context "$KCTX" upgrade --install platform deploy/charts/platform \
  --namespace "$PLATFORM_NS" --create-namespace \
  -f deploy/charts/platform/values-kind.yaml \
  --set-string "gateway.tunnelHostname=${TUNNEL_HOSTNAME}" \
  --wait --timeout 10m
log "waiting for Gateway $GATEWAY_NAME to be Programmed"
k -n "$PLATFORM_NS" wait "gateway/${GATEWAY_NAME}" --for=condition=Programmed --timeout=5m

# 6. ticketscope. No --wait: Helm's wait would hold the hooks on api readiness,
#    and api readiness needs load. migrate polls for the database itself.
# A rebuilt image under an unchanged tag leaves the pod template as it was, so
# Helm rolls nothing: note the deployed api image, to restart api below. A new
# tag (or no api yet) needs no restart; Helm's rollout covers it.
DEPLOYED_APP_IMAGE=$(k -n "$APP_NS" get deploy/ticketscope-api \
  -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || true)
DEPLOYED_MCP_IMAGE=$(k -n "$APP_NS" get deploy/ticketscope-mcp \
  -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || true)
# EVAL_ENABLED=1 adds the eval hook after load; Helm blocks on it, so allow it longer.
EVAL_ARGS=()
HELM_TIMEOUT=25m
if [[ "${EVAL_ENABLED:-0}" == 1 ]]; then
  EVAL_ARGS=(--set eval.enabled=true)
  HELM_TIMEOUT=60m  # migrate and load, then eval's 2700 s deadline
  log "installing ticketscope (hooks: migrate, then load, then eval)"
else
  log "installing ticketscope (hooks: migrate, then load)"
fi
# EMBEDDINGS_COMPUTE=1: load computes embeddings on the CPU (about 19 minutes for the snapshot,
# spike 3.3) and api loads the model, so Helm waits longer for the load hook. It adds to the
# timeout instead of replacing it: with EVAL_ENABLED too, load's compute comes before eval's
# deadline (25m alone is 50m; with eval, 60m becomes 85m).
if [[ "${EMBEDDINGS_COMPUTE:-0}" == 1 ]]; then
  EVAL_ARGS+=(--set embeddings.computeOnKind=true)
  HELM_TIMEOUT="$(( ${HELM_TIMEOUT%m} + 25 ))m"
  log "embeddings on: load computes them unless values.yaml pins an embedding asset (it wins)"
fi
helm --kube-context "$KCTX" upgrade --install ticketscope deploy/charts/ticketscope \
  --namespace "$APP_NS" --create-namespace \
  -f deploy/charts/ticketscope/values-kind.yaml \
  --set-string "mcp.tunnelHostname=${TUNNEL_HOSTNAME}" \
  --set-string "image.app.tag=${TAG}" \
  --set-string "image.postgres.tag=${PG_TAG}" \
  ${EVAL_ARGS[@]+"${EVAL_ARGS[@]}"} \
  --timeout "$HELM_TIMEOUT"
if [[ "$APP_BUILT" == 1 && "$DEPLOYED_APP_IMAGE" == "$APP_IMAGE" ]]; then
  log "app image rebuilt under the deployed tag: restarting api"
  k -n "$APP_NS" rollout restart deploy/ticketscope-api
fi
if [[ "$APP_BUILT" == 1 && "$DEPLOYED_MCP_IMAGE" == "$APP_IMAGE" ]]; then
  log "app image rebuilt under the deployed tag: restarting mcp"
  k -n "$APP_NS" rollout restart deploy/ticketscope-mcp
fi
log "waiting for api to be Ready"
k -n "$APP_NS" rollout status deploy/ticketscope-api --timeout=5m
READY_EPOCH=$(date +%s)
log "api Ready: $((READY_EPOCH - START_EPOCH))s from kind-up start"
# mcp is stateless and its probes never call api, so it is Ready on its own.
log "waiting for mcp to be Ready"
k -n "$APP_NS" rollout status deploy/ticketscope-mcp --timeout=5m
# api is Ready once the primary serves; the replica may still be joining.
# Bring-up is done when the Cluster reports every instance ready (AD-18: 2).
log "waiting for Cluster ticketscope-db to be Ready"
k -n "$APP_NS" wait clusters.postgresql.cnpg.io/ticketscope-db --for=condition=Ready --timeout=10m
log "Cluster Ready: $(($(date +%s) - START_EPOCH))s from kind-up start"

# 7. Gateway address. On Linux the LoadBalancer IP is reachable from the host.
#    On macOS kind nodes are not, so port-forward the Envoy Service instead.
HOSTNAME_VALUE=$(sed -n 's/^hostname: *//p' deploy/charts/ticketscope/values-kind.yaml | tr -d '"')
if [[ "$(uname -s)" == Darwin ]]; then
  ENVOY_SVC=$(k -n "$PLATFORM_NS" get svc -o name \
    -l "gateway.envoyproxy.io/owning-gateway-name=${GATEWAY_NAME},gateway.envoyproxy.io/owning-gateway-namespace=${PLATFORM_NS}")
  if [[ -z "$ENVOY_SVC" ]]; then
    echo "kind-up: no Envoy Service found for Gateway ${PLATFORM_NS}/${GATEWAY_NAME}; cannot port-forward" >&2
    exit 1
  fi
  pkill -f "port-forward.*${ENVOY_SVC#service/}" 2>/dev/null || true
  nohup kubectl --context "$KCTX" -n "$PLATFORM_NS" port-forward "$ENVOY_SVC" 18080:80 \
    >/tmp/ticketscope-gateway-port-forward.log 2>&1 &
  disown
  sleep 2
  GATEWAY_URL="http://127.0.0.1:18080"
else
  GATEWAY_IP=$(k -n "$PLATFORM_NS" get "gateway/${GATEWAY_NAME}" -o jsonpath='{.status.addresses[0].value}')
  GATEWAY_URL="http://${GATEWAY_IP}"
fi

log "Gateway: ${GATEWAY_URL} (Host: ${HOSTNAME_VALUE})"
echo "TICKETSCOPE_GATEWAY_URL=${GATEWAY_URL}"
echo "TICKETSCOPE_GATEWAY_HOST=${HOSTNAME_VALUE}"
if [[ -n "${GITHUB_ENV:-}" ]]; then
  {
    echo "TICKETSCOPE_GATEWAY_URL=${GATEWAY_URL}"
    echo "TICKETSCOPE_GATEWAY_HOST=${HOSTNAME_VALUE}"
    echo "TICKETSCOPE_KIND_UP_TO_READY_SECONDS=$((READY_EPOCH - START_EPOCH))"
  } >>"$GITHUB_ENV"
fi
log "kind-up done"
