#!/usr/bin/env bash
# Runs, in one command, the checks the `checks`, `terraform` and `workflows` jobs of
# .github/workflows/ci.yml run, on the whole repo. Run it before opening a PR.
#
#   scripts/check.sh
#
# Not mirrored, because they need helm and the network, docker, or a cluster: the `charts`,
# `eks-gateway`, `containers`, `integrated-check` and `images` jobs.
#
# Every `run` line below must appear verbatim in ci.yml, and every such command in ci.yml must
# appear here; tests/unit/test_check_script.py enforces both, so the two cannot drift.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

missing=()
for tool in uv terraform actionlint shellcheck; do
  command -v "$tool" >/dev/null || missing+=("$tool")
done
if ((${#missing[@]})); then
  echo "check: missing ${missing[*]}; install them first (terraform is hashicorp/tap/terraform on brew)" >&2
  exit 1
fi

# Terraform steps use a scratch data dir per stack, like CI's fresh checkout: a stack that was
# `init`ed for real keeps its backend in its own `.terraform`, and `init -backend=false` would
# then ask for AWS credentials. The real `.terraform` dirs are left alone.
scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

run() {
  echo "+ $*" >&2
  if [[ "$1" == terraform && "$2" == -chdir=* ]]; then
    local dir="$scratch/${2#-chdir=}"
    mkdir -p "$dir"
    TF_DATA_DIR="$dir" "$@"
  else
    "$@"
  fi
}

run uv sync --locked
run uv run ruff check .
run uv run ruff format --check .
run uv run pyright
run uv run lint-imports
run uv run pytest --ignore=tests/postgres --ignore=tests/image
run python3 scripts/render_readme_table.py --check
run terraform -chdir=infra/bootstrap fmt -check
run terraform -chdir=infra/bootstrap init -backend=false
run terraform -chdir=infra/bootstrap validate
run terraform -chdir=infra/env fmt -check
run terraform -chdir=infra/env init -backend=false
run terraform -chdir=infra/env validate
run actionlint -ignore 'SC2016:info'
run shellcheck scripts/eks-deploy.sh

echo "check: all passed" >&2
