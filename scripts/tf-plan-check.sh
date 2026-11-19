#!/usr/bin/env bash
# infra/env plans with no AWS credential (story 5.5), and a deliberately broken copy fails.
# Run by ci.yml's terraform job and by scripts/check.sh. It downloads providers and modules
# (init -backend=false) and never reaches AWS: the provider is mocked in infra/env/tests.
#
#   scripts/tf-plan-check.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT

# A scratch data dir, so a stack a person applied for real keeps its own backend state.
export TF_DATA_DIR="$scratch/data"
terraform -chdir=infra/env init -backend=false -input=false >/dev/null
terraform -chdir=infra/env test
echo "tf-plan-check: infra/env plans with no AWS credential" >&2

# Negative case: a copy that references an undeclared local must fail the test, for that reason.
neg="$scratch/env-broken"
cp -R infra/env "$neg"
rm -rf "$neg/.terraform"
printf '\noutput "deliberately_broken" {\n  value = local.does_not_exist\n}\n' >>"$neg/outputs.tf"
export TF_DATA_DIR="$scratch/data-broken"
terraform -chdir="$neg" init -backend=false -input=false >/dev/null
if out="$(terraform -chdir="$neg" test 2>&1)"; then
  echo "tf-plan-check: the deliberately broken copy passed, so the check cannot fail" >&2
  exit 1
fi
if ! grep -q "undeclared local value" <<<"$out"; then
  echo "$out" >&2
  echo "tf-plan-check: the broken copy failed, but not on the planted reference" >&2
  exit 1
fi
echo "tf-plan-check: the deliberately broken copy fails as designed" >&2
