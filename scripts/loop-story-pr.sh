#!/usr/bin/env bash
# Build one ticket with bmad-loop on its own branch, then land it through a PR
# that CI gates. Run from the main checkout, one story at a time, in build order.
#
#   scripts/loop-story-pr.sh 2.1            # epic taken from the ref's epic id
#   NO_MERGE=1 scripts/loop-story-pr.sh 2.1 # stop after CI is green; merge by hand
#
# Needs: bmad-loop with [scm] isolation = "worktree" (the story builds in its own
# worktree and is merged into the branch checked out here), gh authenticated, and
# branch protection on main requiring the CI checks.
set -euo pipefail

ref="${1:?usage: $0 <ticket ref, e.g. 2.1>}"
branch="story-${ref//./-}"
root="$(git rev-parse --show-toplevel)"
cd "$root"

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "error: tracked changes in $root; commit or stash them first" >&2
  exit 1
fi

git switch main
git pull --ff-only
git switch -c "$branch"

base="$(git rev-parse HEAD)"
bmad-loop run --story "$ref" --max-stories 1

# Only a finished build is pushed: the loop may also pause on an escalation,
# a budget stop or a person's step, and that work is not ready for a PR.
status="$(uv run _bmad/method/scripts/tickets.py --project-root "$root" find "$ref" \
  | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
if [[ "$status" != "built" && "$status" != "done" ]]; then
  echo "stopped: ticket $ref is '$status', not built or done; branch $branch left for inspection" >&2
  exit 2
fi
if [[ "$(git rev-parse HEAD)" == "$base" ]]; then
  echo "stopped: the run made no commit on $branch" >&2
  exit 2
fi

git push -u origin "$branch"
gh pr create --base main --head "$branch" --fill

# Checks take a moment to register on a new PR.
for _ in $(seq 1 12); do
  if gh pr checks "$branch" 2>/dev/null | grep -q .; then break; fi
  sleep 10
done
gh pr checks "$branch" --watch --fail-fast

if [[ -n "${NO_MERGE:-}" ]]; then
  echo "CI green on $branch; NO_MERGE set, leaving the PR open"
  exit 0
fi

gh pr merge "$branch" --squash --delete-branch
git switch main
git pull --ff-only
echo "ticket $ref merged to main"
