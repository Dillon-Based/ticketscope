#!/usr/bin/env bash
# What a GitHub Actions run did, in a few dozen lines: the run's and each job's result, failed
# steps, then the notable log lines (scripts/run_summary.py). Account ids print as <acct>.
#
#   scripts/run-summary.sh <run id> [--max-lines N]
#
# Read an env-up or env-down run with this instead of grepping `gh run view --log`.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

[[ $# -ge 1 && "$1" =~ ^[0-9]+$ ]] || { echo "usage: scripts/run-summary.sh <run id> [--max-lines N]" >&2; exit 2; }
run="$1"
shift

gh run view "$run" --json workflowName,event,status,conclusion,createdAt,headSha,jobs --jq '
  "\(.workflowName) #\(.event) \(.status)/\(.conclusion // "-") sha \(.headSha[0:7]) at \(.createdAt)",
  (.jobs[] | "  job \(.name): \(.conclusion // .status)",
    (.steps[] | select(.conclusion == "failure") | "    failed step: \(.name)"))'
# Annotations carry what no log shows: a job an environment protection rule rejected never
# starts, and its only record is the annotation.
for job in $(gh run view "$run" --json jobs --jq '.jobs[].databaseId'); do
  gh api "repos/{owner}/{repo}/check-runs/$job/annotations" \
    --jq '.[] | select(.annotation_level != "notice") | "  annotation: \(.message)"' 2>/dev/null |
    sed -E 's/[0-9]{12}/<acct>/g' || true
done
echo
if [[ "$(gh run view "$run" --json status --jq .status)" != completed ]]; then
  echo "(run still in progress; logs are available when it completes)"
  exit 0
fi
if ! gh run view "$run" --log >"${TMPDIR:-/tmp}/run-summary-$run.log" 2>/dev/null; then
  echo "(no log: a job that never started, for example one an environment rule rejected)"
  exit 0
fi
python3 scripts/run_summary.py "$@" <"${TMPDIR:-/tmp}/run-summary-$run.log"
rm -f "${TMPDIR:-/tmp}/run-summary-$run.log"
