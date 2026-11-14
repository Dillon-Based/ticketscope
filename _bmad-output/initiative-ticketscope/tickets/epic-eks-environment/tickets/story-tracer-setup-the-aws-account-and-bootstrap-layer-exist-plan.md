---
title: 'Tracer setup: the AWS account and bootstrap layer exist'
type: 'feature'
ticket: '1'
created: '2026-11-12'
status: 'built'
baseline_revision: '9814559b1a2d8923fbec49b031ed8459007bfa2a'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Epic 5 has nothing to deploy into: no AWS account hardening, hostname certificate, deploy identity, state/backup bucket, image registry or cost alarm exists, and no keyless way for CI to reach AWS.

**Approach:** The agent writes `infra/bootstrap` (Terraform, AD-15) with its policies as plain JSON templates that pytest renders and checks before any apply. The person does the account, domain and local apply steps, guided by `infra/bootstrap/README.md`.

## Boundaries & Constraints

**Always:** Account id, alert email, domain, admin ARN and repo are Terraform variables with no defaults, supplied by an untracked `*.tfvars`. Region `us-east-1`. The deploy role trusts one OIDC `sub`, `repo:<repo>:environment:eks`, with no wildcard (GitHub environment `eks`, whose branch rule admits story branches). Deploy-role permissions are scoped to `ticketscope-*` names and the bucket's `env/` and `backups/` prefixes, and never reach `bootstrap/` state. Bucket: public access blocked, lifecycle rule, `prevent_destroy`. ECR keeps the last 10 images. Bootstrap state starts local, then migrates into the bucket under `bootstrap/` (written in the README as a second step). Tests are written before the Terraform.

**Never:** No `env` stack, workflows, Helm or cluster work (stories 5.2+). No stored AWS credential anywhere, and no write role for the agent. No account id, email or key in tracked files. Nothing destroys the bucket or zone.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Trust policy | `repo` and environment `eks` | One `sub` condition equal to `repo:<repo>:environment:eks`, audience `sts.amazonaws.com`, no `*` | Test fails on wildcard or missing repo |
| Deploy permissions | Rendered policy | S3 limited to `env/*` and `backups/*`, IAM limited to `ticketscope-*` | Test fails on any `bootstrap/` resource or `Resource: "*"` with write actions |
| Read-only role | Admin assumes it | `get-caller-identity` works, `s3 create-bucket` is denied, `iam simulate-principal-policy` and Cost Explorer read work | Person records any denial |
| Re-apply | Applied once | Second `terraform plan` shows no changes | Person fixes drift before closing |

</frozen-after-approval>

## Code Map

- `.github/workflows/ci.yml` -- add a `terraform` job (fmt -check, `init -backend=false`, validate for `infra/bootstrap`); add `infra/**` to `evidence` needs. Follow `charts` job style and its `_job()` test helper in `tests/unit/test_ci_containers.py`.
- `.github/kind-paths.yml` -- `infra/**` must not trigger kind jobs; leave unchanged.
- `.gitignore` -- has no Terraform entries yet.
- `tests/unit/test_infra_bootstrap.py` -- new; tag `@pytest.mark.criterion("ticketscope--e5-s1--AC-<n>")`; `tests.target.REPO` for the root.
- `infra/bootstrap/` -- new; none exists. Terraform is not installed locally (`which terraform` empty); the CI job and the person's machine run it.
- Spine: AD-15 (contents), AD-23 (env owns IRSA roles, not bootstrap).

## Tasks & Acceptance

**Execution:**
- [ ] `tests/unit/test_infra_bootstrap.py` -- trust policy, deploy-policy scope, backup-prefix scope, ignore patterns, tracked-file secret scan, `ci.yml` terraform job -- tests first (R6)
- [ ] `infra/bootstrap/policies/*.json.tftpl` -- deploy trust, deploy permissions, read-only extras -- rendered by the test with plain substitution
- [ ] `infra/bootstrap/*.tf` -- versions (terraform ~> 1.17, aws ~> 6), variables, zone data source, ACM cert + DNS validation, OIDC provider + deploy role, S3 bucket, ECR x2, $8 budget, read-only role, outputs
- [ ] `infra/bootstrap/README.md` -- apply runbook: account, MFA, admin identity, domain, tfvars, apply, state migration, GitHub environment `eks`, read-only profile, verification commands
- [ ] `.gitignore` -- `*.tfstate*`, `*.tfplan`, `.terraform/`, `*.tfvars` (`.terraform.lock.hcl` stays committed)
- [ ] `.github/workflows/ci.yml` -- terraform job as above

**Acceptance Criteria:**
- Given the repo, when pytest runs, then the trust, scope, ignore, scan and CI tests pass with no AWS access.
- Given an applied bootstrap, when the verify list in the ticket is run, then every item passes and a second plan is empty.
- Given a dispatched workflow in environment `eks`, when it assumes the deploy role, then it prints the caller identity with no AWS secret or variable in the repo.

## Implementation Notes

## Plan Change Log

## Review Triage Log

Pass 1 (quick): 1 high, 2 medium, 3 low, 1 false, 1 maybe-false.

| Verdict | Route | Finding and evidence |
|---|---|---|
| high | patch | Deploy role could rewrite its own trust/inline policy: `role/ticketscope-*` matches `ticketscope-deploy` and `ticketscope-readonly`. Scope narrowed to `ticketscope-env-*`, test asserts bootstrap roles match no pattern. |
| medium | patch | 12-digit scan matches hex hashes in a committed lock file. Scan skips `.terraform.lock.hcl`. |
| low | patch | `backend.tf` ignore entry untested. Added to the test. |
| low | patch | README verify list missed empty second plan, versioning, lifecycle. Added. |
| low | reject | Lock file absent: Terraform not installed here, person generates and commits it (README). |
| low | reject | `eks:*` is resource-scoped to `ticketscope-*` ARNs, and 5.2 widens it under the same test. Fix adds complexity. |
| false | reject | Bucket-name test: the real name is `ticketscope-${account_id}`, the policy takes the bucket as input, nothing diverges. |
| maybe-false | defer | `ReadOnlyAccess` likely reads `bootstrap/` state; state holds no secrets, deny needs the bucket name in the template. |
| medium | defer | Residual: deploy role can still attach any managed policy to `ticketscope-env-*` roles it creates; a permissions boundary or `iam:PolicyARN` condition waits for 5.2, when env's real needs are known. |

## Design Notes

Deploy permissions start narrow and are widened by story 5.2 as the tracer shows what `env` needs, always under the same test. The agent's read-only role is trusted from `admin_principal_arn`, so the person's profile does `role_arn` plus `source_profile`; that config lives in `~/.aws`, not the repo. Verification of the account plan and credit terms is recorded in the README, not gating.

## Verification

**Commands:**
- `uv run pytest tests/unit/test_infra_bootstrap.py tests/unit/test_ci_containers.py` -- expected: pass
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports` -- expected: pass
- `terraform -chdir=infra/bootstrap fmt -check && terraform -chdir=infra/bootstrap init -backend=false && terraform -chdir=infra/bootstrap validate` -- expected: pass (needs terraform installed)

**Manual checks (if no CLI):**
- The ticket's verify list, run by the person after apply: `terraform plan`, `dig NS`, `aws acm describe-certificate`, `aws budgets describe-budgets`, `aws ecr get-lifecycle-policy`, `aws s3api get-public-access-block`, dispatched OIDC workflow, read-only profile denial.
