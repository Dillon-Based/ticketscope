# shellcheck shell=bash
# The timed-stage log of eks-deploy.sh and eks-teardown.sh, sourced by them; never run on its own.
# Defines log, stage and summary. Set STAGES_TITLE (the name in the "--- <title> stage times ---" header) before calling summary.
#   `stage <name>` closes the previous stage's timer and opens this one; `stage ""` only closes.
#   `summary` prints each stage's seconds and the total, even on a failed run (call it from a trap).

START_EPOCH=$(date +%s)
STAGE_EPOCH=$START_EPOCH
SUMMARY=()
CURRENT=""
log() { printf '[%s +%4ss] %s\n' "$(date -u +%H:%M:%S)" "$(($(date +%s) - START_EPOCH))" "$*"; }
stage() {
  local now
  now=$(date +%s)
  if [[ -n "$CURRENT" ]]; then SUMMARY+=("$(printf '%-28s %5ss' "$CURRENT" "$((now - STAGE_EPOCH))")"); fi
  CURRENT="${1:-}"
  STAGE_EPOCH=$now
  if [[ -n "$CURRENT" ]]; then log "stage: $CURRENT"; fi
}
summary() {
  stage ""
  echo "--- ${STAGES_TITLE} stage times ---"
  if ((${#SUMMARY[@]})); then printf '%s\n' "${SUMMARY[@]}"; fi
  printf '%-28s %5ss\n' total "$(($(date +%s) - START_EPOCH))"
}
