#!/usr/bin/env bash
# Signs the CLI in as the bootstrap admin IAM user and checks who it signed in as.
# `aws login` reuses the browser's AWS session, so sign in as the IAM user in a private
# window (or a dedicated browser profile) first. Prints no account id.
set -euo pipefail

profile="${1:-ticketscope-admin}"

# Credentials in the environment override a profile and caused the wrong identity before.
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE

echo "Sign in as the IAM user in a private window or dedicated browser profile first."
aws login --remote --profile "$profile"

arn="$(aws sts get-caller-identity --profile "$profile" --query Arn --output text)"
case "$arn" in
  *:user/ticketscope-admin)
    echo "ok: signed in as the ticketscope-admin IAM user"
    echo "next: export AWS_PROFILE=$profile"
    ;;
  *)
    echo "wrong identity (${arn##*:}); the browser session is not the IAM user. Sign out, retry in a private window." >&2
    exit 1
    ;;
esac
