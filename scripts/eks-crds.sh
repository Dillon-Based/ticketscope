#!/usr/bin/env bash
# Installs the Gateway API standard-channel CRDs and the AWS Load Balancer Controller's own
# CRDs into the cluster `kubectl` points at (the controller's Helm chart ships neither). Shared
# by eks-deploy.sh and the CI check in check-eks-gateway.sh, so both install the same bundle.
#
#   GATEWAY_API_VERSION  standard-channel Gateway API release (default v1.6.0, the version the
#                        controller is built for: against v1.3.0 it disables ALBGatewayAPI)
#
# Also adds the chart repositories and builds deploy/charts/platform's dependencies, because the
# controller's CRDs are read from the pinned chart tarball so they match its version.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

GATEWAY_API_VERSION="${GATEWAY_API_VERSION:-v1.6.0}"
CHARTS=deploy/charts

kubectl apply --server-side -f \
  "https://github.com/kubernetes-sigs/gateway-api/releases/download/${GATEWAY_API_VERSION}/standard-install.yaml"
helm repo add eks https://aws.github.io/eks-charts --force-update >/dev/null
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/ --force-update >/dev/null
helm repo add cnpg https://cloudnative-pg.github.io/charts --force-update >/dev/null
helm repo add seaweedfs https://seaweedfs.github.io/seaweedfs/helm --force-update >/dev/null
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts --force-update >/dev/null
helm repo add grafana-community https://grafana-community.github.io/helm-charts --force-update >/dev/null
helm dependency build "$CHARTS/platform"
LBC_TGZ="$(ls "$CHARTS"/platform/charts/aws-load-balancer-controller-*.tgz | head -1)"
for crd in crds.yaml gateway-crds.yaml; do
  tar xzf "$LBC_TGZ" -O "aws-load-balancer-controller/crds/${crd}" | kubectl apply --server-side -f -
done
kubectl wait --for=condition=Established --timeout=2m \
  crd/gateways.gateway.networking.k8s.io \
  crd/httproutes.gateway.networking.k8s.io \
  crd/referencegrants.gateway.networking.k8s.io \
  crd/loadbalancerconfigurations.gateway.k8s.aws \
  crd/targetgroupconfigurations.gateway.k8s.aws
