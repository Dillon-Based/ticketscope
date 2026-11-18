#!/usr/bin/env bash
# Prints the shell setup the hand-run EKS steps need, to be eval'd in each terminal (bash or zsh):
#
#   eval "$(scripts/eks-env.sh <fixed hostname>)"
#
# It reads the account, certificate and zone from AWS (after scripts/aws-login.sh), so nothing
# is copied by hand and no id is committed. It prints, on stdout only, exports for AWS_PROFILE,
# KUBECONFIG, REG (the ECR registry), CERT (the bootstrap certificate ARN), TICKETSCOPE_ZONE_ID,
# TICKETSCOPE_STATE_BUCKET and TICKETSCOPE_HOSTNAME, a `cd` to the repo root, and the Docker Desktop bin dir on PATH when
# its credential helper is missing from it. It also writes the untracked infra/env/terraform.tfvars
# when absent. Any failure prints nothing on stdout and exits non-zero, so a bad eval does nothing.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${1:-${TICKETSCOPE_HOSTNAME:-}}"
PROFILE="${AWS_PROFILE:-ticketscope-sso}"
REGION=us-east-1
KUBECONFIG_PATH="${TICKETSCOPE_KUBECONFIG:-/tmp/ticketscope-eks.kubeconfig}"
DOCKER_BIN=/Applications/Docker.app/Contents/Resources/bin

fail() { echo "eks-env: $*" >&2; exit 1; }
[[ -n "$HOST" ]] || fail "usage: eval \"\$(scripts/eks-env.sh <fixed hostname>)\""

aws_() { aws --profile "$PROFILE" --region "$REGION" "$@"; }

ACCOUNT="$(aws_ sts get-caller-identity --query Account --output text 2>/dev/null)" ||
  fail "not signed in as profile $PROFILE: run scripts/aws-login.sh"

CERT="$(aws_ acm list-certificates \
  --query "CertificateSummaryList[?DomainName=='${HOST}' && Status=='ISSUED'].CertificateArn | [0]" \
  --output text)"
[[ -n "$CERT" && "$CERT" != None ]] || fail "no issued certificate for $HOST in $REGION (is bootstrap applied?)"

ZONE_ID="$(aws_ route53 list-hosted-zones-by-name --dns-name "$HOST" \
  --query "HostedZones[?Name=='${HOST}.'].Id | [0]" --output text)"
ZONE_ID="${ZONE_ID##*/}"
[[ -n "$ZONE_ID" && "$ZONE_ID" != None ]] || fail "no hosted zone named $HOST"

TFVARS="${TICKETSCOPE_TFVARS:-$ROOT/infra/env/terraform.tfvars}"
if [[ ! -f "$TFVARS" ]]; then
  # Only the default path is checked: an override (the tests') is the caller's to place.
  if [[ -z "${TICKETSCOPE_TFVARS:-}" ]]; then
    git -C "$ROOT" check-ignore -q "$TFVARS" || fail "infra/env/terraform.tfvars is not git-ignored; not writing it"
  fi
  printf 'account_id = "%s"\nzone_id    = "%s"\n' "$ACCOUNT" "$ZONE_ID" >"$TFVARS"
  echo "eks-env: wrote infra/env/terraform.tfvars (untracked)" >&2
fi

printf 'export AWS_PROFILE=%q\n' "$PROFILE"
printf 'export KUBECONFIG=%q\n' "$KUBECONFIG_PATH"
printf 'export REG=%q\n' "${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
printf 'export CERT=%q\n' "$CERT"
printf 'export TICKETSCOPE_STATE_BUCKET=%q\n' "ticketscope-${ACCOUNT}"
printf 'export TICKETSCOPE_ZONE_ID=%q\n' "$ZONE_ID"
printf 'export TICKETSCOPE_HOSTNAME=%q\n' "$HOST"
if [[ -x "$DOCKER_BIN/docker-credential-desktop" ]] && ! command -v docker-credential-desktop >/dev/null; then
  printf 'export PATH="$PATH:%s"\n' "$DOCKER_BIN"
fi
printf 'cd %q\n' "$ROOT"
echo "eks-env: ready for $HOST" >&2
