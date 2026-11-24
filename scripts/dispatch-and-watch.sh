#!/usr/bin/env bash
# Dispatches a workflow on a ref, finds the run it started, and waits for it to finish.
#
#   scripts/dispatch-and-watch.sh <workflow file> <ref> [-f name=value]...
#
# Needs GH_TOKEN (or a gh login) and GH_REPO (owner/name). The run id is printed as `run-id: N`
# and, under GitHub Actions, written to $GITHUB_OUTPUT as `run_id` before the wait starts, so a
# caller can still use it when the run fails. Exit status is the dispatched run's: 0 only when it
# concluded success.
#
# With WATCH_JOB set, the wait ends when that job of the run completes (its conclusion is the exit
# status), not when the whole run does; env-check uses it to stop at env-up's `env` job instead of
# waiting out the `expire` job that sleeps until the environment's expiry.
set -euo pipefail

[[ $# -ge 2 ]] || { echo "usage: scripts/dispatch-and-watch.sh <workflow file> <ref> [-f name=value]..." >&2; exit 2; }
workflow="$1"
ref="$2"
shift 2
: "${GH_REPO:?set GH_REPO to owner/name}"

# GitHub stamps runs to the second, so back the mark off a little; the run is then the oldest
# one created at or after it.
mark="$(date -u -d '-5 seconds' +%Y-%m-%dT%H:%M:%SZ)"
gh workflow run "$workflow" --ref "$ref" "$@"

run_id=""
for _ in $(seq 1 24); do
  sleep 5
  run_id="$(gh run list --workflow "$workflow" --event workflow_dispatch --branch "$ref" \
    --created ">=$mark" --json databaseId,createdAt \
    --jq 'sort_by(.createdAt) | .[0].databaseId // empty')"
  [[ -n "$run_id" ]] && break
done
[[ -n "$run_id" ]] || { echo "::error::dispatched $workflow but found no run of it within two minutes" >&2; exit 1; }

echo "run-id: $run_id"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then echo "run_id=$run_id" >> "$GITHUB_OUTPUT"; fi
if [[ -z "${WATCH_JOB:-}" ]]; then
  gh run watch "$run_id" --interval 30 --exit-status
  exit
fi
while true; do
  state="$(gh run view "$run_id" --json status,conclusion,jobs)"
  job="$(jq -r --arg job "$WATCH_JOB" '[.jobs[] | select(.name == $job and .status == "completed")] | .[0].conclusion // empty' <<<"$state")"
  if [[ -n "$job" ]]; then
    echo "job $WATCH_JOB: $job"
    [[ "$job" == success ]]
    exit
  fi
  # The run ended without that job completing (it was skipped, or an earlier job failed).
  if [[ "$(jq -r '.status' <<<"$state")" == completed ]]; then
    echo "run $run_id ended $(jq -r '.conclusion' <<<"$state") without job $WATCH_JOB completing" >&2
    exit 1
  fi
  sleep 30
done
