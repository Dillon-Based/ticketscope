#!/usr/bin/env bash
# Read-only: does the deploy role's live policy match infra/bootstrap's template? Run it before
# dispatching env-up or env-down after a change to deploy-permissions.json.tftpl; a template
# change reaches AWS only when a person re-applies bootstrap.
#
#   scripts/bootstrap-drift.sh            # uses AWS_PROFILE, default ticketscope-readonly
#
# Exit 0: matches. 1: drift (printed). 2: an AWS call failed or the input was unreadable.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

export AWS_PROFILE="${AWS_PROFILE:-ticketscope-readonly}"
REGION=us-east-1
ROLE=ticketscope-deploy
POLICY=ticketscope-deploy

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

if ! account="$(aws sts get-caller-identity --query Account --output text 2>"$work/err")"; then
  echo "bootstrap-drift: cannot read the caller identity: $(sed -E 's/[0-9]{12}/<acct>/g' "$work/err")" >&2
  exit 2
fi
if ! aws iam get-role-policy --role-name "$ROLE" --policy-name "$POLICY" \
  --query PolicyDocument --output json >"$work/live.json" 2>"$work/err"; then
  echo "bootstrap-drift: cannot read the role policy: $(sed -E 's/[0-9]{12}/<acct>/g' "$work/err")" >&2
  exit 2
fi

python3 scripts/bootstrap_drift.py \
  --template infra/bootstrap/policies/deploy-permissions.json.tftpl \
  --account-id "$account" --region "$REGION" --bucket "ticketscope-$account" \
  --live "$work/live.json"
