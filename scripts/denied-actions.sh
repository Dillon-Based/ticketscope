#!/usr/bin/env bash
# Prints the AWS actions a run was denied, one `<action> on <resource>` per line, from the
# Terraform and deploy logs it is given (files that do not exist are skipped). env-up.yml writes
# the result to the job summary, so adding a missing action to the deploy role's policy
# (infra/bootstrap/policies/deploy-permissions.json.tftpl) needs no log reading.
#
#   scripts/denied-actions.sh "$RUNNER_TEMP/terraform.log" "$RUNNER_TEMP/deploy.log"
#
# Two message shapes are read: IAM's `not authorized to perform: <action> on resource: <arn>`
# and EKS's `missing permissions for '<action>'` (which names no resource). Account ids are
# replaced with <acct>, because the summary is public on a public repo. Prints nothing, and
# exits 0, when there is nothing to report.
set -uo pipefail

files=()
for f in "$@"; do
  [[ -f "$f" ]] && files+=("$f")
done
((${#files[@]})) || exit 0

{
  grep -ohE 'not authorized to perform: [A-Za-z0-9-]+:[A-Za-z0-9*]+ on resource: .*' "${files[@]}" |
    sed -E 's/not authorized to perform: ([^ ]+) on resource: (.*)/\1 on \2/; s/ (because|Go to) .*//'
  grep -ohE "missing permissions for '[^']+'" "${files[@]}" |
    sed -E "s/missing permissions for '([^']+)'/\1 on (resource not reported)/"
} 2>/dev/null | sed -E 's/[0-9]{12}/<acct>/g; s/[.,;]+$//' | sort -u
exit 0
