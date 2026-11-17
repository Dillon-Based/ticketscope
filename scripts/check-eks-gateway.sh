#!/usr/bin/env bash
# Offline check of the EKS Gateway objects against the real CRDs (no AWS): creates a throwaway
# kind cluster, installs the CRDs eks-deploy.sh installs, and has the API server validate the
# rendered EKS platform Gateway, LoadBalancerConfiguration and TargetGroupConfiguration with a
# server-side dry run, which evaluates the CRDs' CEL rules (a `helm template` cannot).
# The tracer found one such rule the hard way: a `Terminate` listener needs certificateRefs or
# options. A negative control applies a listener with neither and expects the server to refuse it.
#
#   scripts/check-eks-gateway.sh
#   CLUSTER_NAME=gwcheck  KEEP=1 to keep the cluster for inspection
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CLUSTER_NAME="${CLUSTER_NAME:-gwcheck}"
# The node image kind-up.sh pins, read from it so there is one source.
KIND_NODE_IMAGE="$(sed -n 's/^KIND_NODE_IMAGE="\(.*\)"$/\1/p' scripts/kind-up.sh | head -1)"
[[ -n "$KIND_NODE_IMAGE" ]] || { echo "check-eks-gateway: no KIND_NODE_IMAGE in kind-up.sh" >&2; exit 1; }

for tool in kind kubectl helm; do
  command -v "$tool" >/dev/null || { echo "check-eks-gateway: $tool is required" >&2; exit 1; }
done

WORK="$(mktemp -d)"
export KUBECONFIG="$WORK/kubeconfig"
cleanup() {
  if [[ "${KEEP:-0}" != 1 ]]; then kind delete cluster --name "$CLUSTER_NAME" >/dev/null 2>&1 || true; fi
  rm -rf "$WORK"
}
trap cleanup EXIT

kind delete cluster --name "$CLUSTER_NAME" >/dev/null 2>&1 || true
kind create cluster --name "$CLUSTER_NAME" --image "$KIND_NODE_IMAGE" --wait 120s

scripts/eks-crds.sh
kubectl create namespace platform
kubectl create namespace ticketscope

# The templates a Gateway chain on EKS is made of. Placeholders stand in for the values the
# deploy script sets; none is real.
helm template platform deploy/charts/platform \
  -f deploy/charts/platform/values-eks.yaml \
  --set gateway.hostname=check.example.test \
  --set gateway.aws.certificateArn=arn:aws:acm:us-east-1:000000000000:certificate/00000000-0000-0000-0000-000000000000 \
  --set aws-load-balancer-controller.clusterName=check \
  --set aws-load-balancer-controller.vpcId=vpc-0 \
  --show-only templates/gateway.yaml \
  --show-only templates/loadbalancerconfiguration.yaml \
  --show-only templates/targetgroupconfiguration.yaml >"$WORK/rendered.yaml"
echo "rendered $(grep -c '^kind:' "$WORK/rendered.yaml") objects"
kubectl apply --dry-run=server -f "$WORK/rendered.yaml"

# Negative control: the check must be able to fail.
cat >"$WORK/bad-gateway.yaml" <<'EOF'
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: bad
  namespace: platform
spec:
  gatewayClassName: alb
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        mode: Terminate
EOF
if kubectl apply --dry-run=server -f "$WORK/bad-gateway.yaml" >"$WORK/bad.out" 2>&1; then
  echo "check-eks-gateway: the control Gateway (Terminate with no certificateRefs or options) was accepted, so this check proves nothing" >&2
  exit 1
fi
grep -q "certificateRefs or options must be specified" "$WORK/bad.out" || {
  echo "check-eks-gateway: the control was refused for another reason:" >&2
  cat "$WORK/bad.out" >&2
  exit 1
}
echo "ok: rendered EKS Gateway objects are valid against the CRDs, and the negative control is refused"
