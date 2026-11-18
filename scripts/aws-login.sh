#!/usr/bin/env bash
# Signs the CLI in with the admin identity (the Identity Center role) and checks who it is.
# `aws login` reuses the browser's AWS console session, so be signed in to the console in the
# ticketscope account first. Prints no account id.
set -euo pipefail

profile="${1:-ticketscope-sso}"
role="${TICKETSCOPE_ADMIN_ROLE:-AccountFullAccessRole}"

# Credentials in the environment override a profile and caused the wrong identity before.
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE

aws login --profile "$profile"

arn="$(aws sts get-caller-identity --profile "$profile" --query Arn --output text)"
case "$arn" in
  *":assumed-role/$role/"*)
    # The role name is the same in every account; the bootstrap bucket tells this one apart.
    bucket="$(aws s3api list-buckets --profile "$profile" \
      --query "Buckets[?starts_with(Name, 'ticketscope-')].Name | [0]" --output text 2>/dev/null || true)"
    if [[ -z "$bucket" || "$bucket" == None ]]; then
      echo "wrong account: it has no ticketscope bootstrap bucket; sign in to the console in the ticketscope account and retry." >&2
      exit 1
    fi
    echo "ok: signed in as $role"
    echo "next: export AWS_PROFILE=$profile"
    ;;
  *)
    echo "wrong identity (${arn##*:}); sign in to the console as $role in the ticketscope account and retry." >&2
    exit 1
    ;;
esac
