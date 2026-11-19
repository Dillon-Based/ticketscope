---
title: 'A PR check renders both environments and validates Terraform'
type: 'feature'
ticket: '5'
created: '2026-11-19'
status: 'built'
baseline_revision: '88e564469bd2b8a887b6fbb332db1118af206948'
route: 'full'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran:
  - quick
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A PR cannot show that both charts render with each environment file, that an environment file stays inside AD-25's allowlist, or that `infra/env` plans without AWS access. Only `fmt` and `validate` run today.

**Approach:** Add offline checks to the PR gate: render both charts with both environment files and assert the EKS render's host list; enforce the allowlist with a named key set; run `infra/env`'s plan under a mocked AWS provider, with a negative case proving a broken module fails. The kind path filter stays as it is, because the kind jobs do not depend on `infra/`.

## Boundaries & Constraints

**Always:** No AWS credential and no network call to AWS in any new check. Every new CI `run:` line also appears verbatim in `scripts/check.sh` (`tests/unit/test_check_script.py` enforces it). New chart and Terraform tests carry `@pytest.mark.criterion("ticketscope--e5-s5--AC-<n>")`. Existing kind jobs and `values-kind.yaml` stay unchanged.

**Never:** Do not add `infra/**` to `.github/kind-paths.yml`'s `kind` list: a PR that touches only `infra/**` must not start the kind deploy. `deploy/**` already covers the charts. No `helm_release`, no committed account id, hostname or ARN, and no backend init in the PR check.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Clean EKS render | Both charts with `values-eks.yaml` and a live-style hostname | Renders; mcp allowed hosts are exactly that hostname | Non-zero exit fails the check |
| Override of a product default | `values-eks.yaml` sets `retrieval.defaultMode` or `snapshot.*` | Test fails | Named key in the failure message |
| Key outside the allowlist | A `values-eks.yaml` key not in AD-25's list | Test fails | Named key in the failure message |
| Plan with no credential | `infra/env` under a mocked AWS provider | `terraform test` passes | Failure fails the job |
| Deliberately broken module | Copy of `infra/env` with a bad reference | `terraform test` fails | The script exits non-zero |
| PR touching only `infra/**` | Path filter | No kind jobs start | Test asserts the kind list |

## Code Map

- `deploy/charts/ticketscope/values-eks.yaml`, `deploy/charts/platform/values-eks.yaml` -- environment facts only; the render test reads them, and nothing is edited unless the allowlist check finds a stray key.
- `deploy/charts/ticketscope/templates/_helpers.tpl` (`ticketscope.mcpHosts`) -- builds the mcp allowed-hosts list; the test asserts its output on the EKS render.
- `tests/unit/test_chart_eks.py` -- existing EKS render tests and the `PLATFORM_ENV_KEYS` / `TICKETSCOPE_ENV_KEYS` allowlist; extend, do not replace.
- `tests/unit/test_chart_backup.py` (`_render`, `_docs`, `needs_platform_deps`) -- render helpers to reuse.
- `infra/env/*.tf`, `infra/env/terraform.tfvars` -- the stack under test. Its data sources are `aws_caller_identity` (eks.tf), `aws_iam_roles` (eks.tf) and `aws_availability_zones` (main.tf); main.tf slices two zones, so the mock must supply at least two.
- `tests/unit/test_infra_env.py` -- static Terraform text checks; the new text checks go here.
- `.github/workflows/ci.yml` -- `charts` job (render test list) and `terraform` job (new plan-check step).
- `.github/kind-paths.yml` -- the kind list already has `deploy/**`; no change needed.
- `scripts/check.sh`, `tests/unit/test_check_script.py` -- the local mirror and the test that enforces it.
- `_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md` -- AD-25, the allowlist's source.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/unit/test_chart_eks.py` -- parametrize over the two charts × two environment files; assert each renders, the EKS render has no `ticketscope.kind.internal`, and mcp's allowed hosts equal the hostname with no `*` -- R7
- [ ] `tests/unit/test_chart_eks.py` -- name the AD-25 allowlist keys, including the IRSA role annotation and the instance placement rule as reserved keys under the `database.` prefix (no value uses them yet); add a test that a key outside the allowlist fails -- AD-25, C-4
- [ ] `infra/env/tests/plan.tftest.hcl` (new) -- `mock_provider "aws"`, `override_data` for `aws_availability_zones` with two names, `command = plan` on the root module -- Terraform plan with no credential
- [ ] `scripts/tf-plan-check.sh` (new) -- runs `terraform -chdir=infra/env test`, then copies `infra/env` to a temp dir, adds a broken reference, and asserts the test fails -- negative case
- [ ] `.github/workflows/ci.yml` (`charts` and `terraform` jobs) -- add the new chart tests to the list; add a `terraform` step running `scripts/tf-plan-check.sh` after `validate` -- R7
- [ ] `scripts/check.sh` -- add the same `run:` line as ci.yml -- keeps `test_check_script.py` green
- [ ] `tests/unit/test_infra_env.py` -- text checks: the test file exists, the script is in both `ci.yml` and `check.sh`, and `kind-paths.yml`'s kind list has no `infra/**` -- R7

**Acceptance Criteria:**
- Given a PR, when `ci.yml` runs, then `charts` renders both charts with both environment files and its render tests pass (R7).
- Given a `values-eks.yaml` that overrides `retrieval.defaultMode`, a `snapshot.*` key, or a key outside the allowlist, when the tests run, then they fail and name the key (R7).
- Given `infra/env` with no AWS credential, when the `terraform` job runs `scripts/tf-plan-check.sh`, then the mocked plan passes (R7).
- Given a deliberately broken module in the negative case, when `scripts/tf-plan-check.sh` runs, then the broken copy fails and the script reports the expected failure (R7).
- Given a PR that touches only `infra/**`, when the path filter runs, then no kind job starts (R7).

## Design Notes

Story 2 already gave `charts` a `helm lint` on both environment files, and `test_chart_eks.py` renders them. This story adds the missing pieces: the four-way render, the EKS host check, the allowlist names, and the plan. The kind path filter is already right, so the story's "gains infra/**" clause is not applied: the kind jobs do not read `infra/`.

## Verification

**Commands:**
- `uv run pytest tests/unit/test_chart_eks.py tests/unit/test_infra_env.py tests/unit/test_check_script.py` -- expected: pass (chart tests skip without helm, so run them locally with helm present)
- `scripts/tf-plan-check.sh` -- expected: the positive test passes and the negative case fails as designed
- `scripts/check.sh` -- expected: "check: all passed"

**Manual checks (if no CLI):**
- On the PR, `charts`, `terraform` and `checks` are green; `integrated-check / deploy` is skipped when only `infra/**` changed.

## Implementation Notes

- Implemented directly, with no coding subagent: the session's rules allow subagents only when the user asks for one.
- Deviation: the chart tests went into `tests/unit/test_chart_eks.py`, which the `charts` job already runs, so the job's test list is unchanged. The static tests went into a new `tests/unit/test_tf_plan_check.py` rather than `test_infra_env.py`.
- Deviation: `scripts/tf-plan-check.sh` makes its own scratch `TF_DATA_DIR` and runs `init -backend=false` itself. `check.sh`'s scratch wrapper only covers `terraform -chdir=` lines, so the script would otherwise read a real `.terraform` in the checkout.
- Deviation: the mock needed `mock_data` defaults for `aws_caller_identity`, `aws_iam_session_context` (`arn` and `issuer_arn`), `aws_iam_policy_document` (`json = "{}"`) and `aws_partition`. Without them the EKS and IRSA modules fail on random strings. The two-zone override is as planned.
- The account id is assembled from two parts in `plan.tftest.hcl`. A literal 12-digit id trips `test_infra_bootstrap.py`'s no-account-id check, and the EKS module needs a 12-digit account inside an ARN, so a non-numeric placeholder does not work.
- The kind path filter is unchanged. `deploy/**` already covers the charts and `infra/` is not a kind dependency.
- Reserved names: `database.serviceAccount.annotations` and `database.instancePlacement` are in the ticketscope allowlist, and no committed value sets them.
- Verified locally: `scripts/check.sh` passes ("check: all passed"). The plan check also passes with every AWS credential source pointed at nothing. Not run here: the `charts` job on a PR, the manual PR checks, and the path-filter behaviour on a real PR.

## Review Triage Log

Pass 1 (quick, run inline by the implementing session, not a context-free subagent): 0 findings. Checked against the acceptance criteria and matrix rows above and the repo's AGENTS.md rules: criterion tags on every new test, no account id or ARN literal in `infra/`, no "production" wording, `uv run` for pytest, and the `check.sh` mirror of every new CI line.

Two observations, not findings:
- The negative case matches Terraform's "undeclared local value" wording, which a future Terraform release could change. The failure would then be loud, not silent.
- The matrix row "the script exits non-zero" is read as "exits non-zero when the broken copy passes". The script exits zero when the copy fails as designed.
