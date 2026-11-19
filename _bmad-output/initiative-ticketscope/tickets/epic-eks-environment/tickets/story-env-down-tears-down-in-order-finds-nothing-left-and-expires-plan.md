---
title: 'env-down tears down in order, finds nothing left, and expires forgotten environments'
type: 'feature'
ticket: '4'
created: '2026-11-18'
status: 'built'
baseline_revision: '59ccbefed030eb8b4419ed689a7c2318a29c87ae'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-env-up-deploys-through-oidc-and-records-its-time-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Only a person tears the environment down, by hand. A controller removed before the Gateway's ALB is gone leaks AWS resources, nothing proves the account is clean (R3), and a forgotten environment breaks the $10 month (R4).

**Approach:** `env-down.yml` (dispatch and hourly schedule) runs `scripts/eks-teardown.sh` in AD-24 order, then `scripts/leftover-check.sh`, which lists tagged resources and fails on any. The schedule destroys only environments whose `expires_at` tag has passed.

## Boundaries & Constraints

**Always:** Teardown order is AD-24 as amended: `helm uninstall ticketscope`, delete PVCs, delete the Gateway and wait until its ALB is gone with the controller running, `helm uninstall platform`, wait for tagged ENIs and volumes, `terraform destroy` of `env`, leftover check. Wait limits: ALB gone 15 min, ENIs and volumes 10 min, each overridable by env var for tests. A stuck Gateway prints its finalizers and the remedy, the job fails, nothing is force-deleted and `platform` stays installed. The check is read-only, filters on the `environment` tag (and the controller's cluster tag), never selects `stack=bootstrap` or any other environment's tag, and treats an `aws` error, an unreadable listing or a missing key as a failure, never as clean. `--dry-run` injects a tagged ALB and must fail naming it; `--list` prints what is found for the positive control. `env-down` and `env-up` share one concurrency group (`cancel-in-progress: false`). The sweep reads `expires_at` from the VPC's tag, skips an unexpired or untagged environment with a summary line, and fails when a tagged leftover exists with no environment. `env-up` gains an optional `expiry_minutes` (5 to 240, overrides hours) so a 15-minute expiry can be stamped. The agent dispatches only environments expiring within 4 hours, one at a time, and runs no AWS write command outside the workflows. The controller flag `manage-backend-security-group-rules` stays at its default.

**Never:** No force-delete, no finalizer removal, no `terraform destroy` of `bootstrap`, no ARN of a bootstrap resource in any command of `env-down`. Do not change kind behaviour. Do not hand-write `eval/baseline.json` or the README table.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Clean teardown | env up, dispatched | seven steps in order, check clean | n/a |
| Stuck Gateway | ALB not gone at 15 min | finalizer and remedy printed, job fails before `platform` uninstall | no force-delete |
| Leftover | tagged ALB, TG, ENI, volume, SG, KMS key or log group | check fails and names each | exit non-zero |
| Foreign or bootstrap resource | other tag value or `stack=bootstrap` | ignored | n/a |
| API error or empty output | `aws` exits non-zero | check fails | never reads clean |
| Sweep, unexpired | `expires_at` in the future | skipped, summary says when | n/a |
| Sweep, expired | `expires_at` past | full teardown, no dispatch | as above |

</frozen-after-approval>

## Code Map

- `.github/workflows/env-up.yml` -- model for OIDC, `eks` environment, `expires_at` stamping (`date -u -d "+N hours"`), group `env-up`; add `expiry_minutes`, rename group to `eks-environment`.
- `scripts/eks-deploy.sh` -- style and stage-timer pattern; kubeconfig and cluster facts; platform ns `platform`, app ns `ticketscope`, Gateway `ticketscope`.
- `scripts/mask_aws_list.py`, `tests/fixtures/aws/up.json`, `down.json` -- real `resourcegroupstaggingapi get-resources` recordings (up, after teardown); the check's unit oracle.
- `infra/env/versions.tf`, `variables.tf` -- default tags `project`, `stack=env`, `environment`, `expires_at`; EBS volumes tagged `environment`.
- `infra/bootstrap/policies/deploy-permissions.json.tftpl` -- needs read actions for the check (`tag:GetResources`, `elasticloadbalancing:Describe*`, `logs:DescribeLogGroups`, `kms:ListKeys`/`DescribeKey`/`ListResourceTags`). `StateAndBackupsObjects` allows delete under `env/*` and `backups/*` only; confirm by simulation that nothing else in the bootstrap bucket is deletable. `readonly-extras` already has the simulate action.
- `tests/unit/test_env_up_workflow.py` -- parse-test style; asserts the concurrency group and input set, so it changes with env-up.
- `scripts/check.sh`, `.github/workflows/ci.yml` -- shellcheck lines must match verbatim (`test_check_script.py`).
- `docs/runbooks/env-up.md` -- manual teardown; point to `env-down` once it exists.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/unit/test_leftover_check.py` -- written first, red: each of ALB, TG, ENI, volume, SG, KMS key, log group injected into `down.json` fails and is named; `up.json` lists ALB, TG, SG, volumes (positive control); foreign tag, bootstrap-tagged and clean input pass; `aws` error and malformed JSON fail; `--dry-run` fails; no `delete` verb in the script -- the check is the oracle, so it is written before it
- [ ] `tests/unit/test_eks_teardown.py` -- red: stub `helm`, `kubectl`, `aws`, `terraform` on PATH; calls arrive in AD-24 order; a stub that never reports the ALB gone fails before `helm uninstall platform` with finalizers printed and no `patch`/`--force`; give-up times from env vars
- [ ] `tests/unit/test_env_down_workflow.py` -- dispatch plus hourly cron; shared group; `id-token: write` only on env jobs; no `pull_request`; sweep skips unexpired; no bootstrap ARN or `-chdir=infra/bootstrap`
- [ ] `scripts/leftover_check.py`, `scripts/leftover-check.sh` -- classify by ARN service and type; modes check, `--list`, `--dry-run`, `--from-file`
- [ ] `scripts/eks-teardown.sh` -- AD-24 steps with timers, waits and the stuck-Gateway report
- [ ] `.github/workflows/env-down.yml` -- find (sweep decision) then teardown then leftover check; summary of stage times
- [ ] `.github/workflows/env-up.yml`, `tests/unit/test_env_up_workflow.py` -- `expiry_minutes`, shared group
- [ ] `infra/bootstrap/policies/deploy-permissions.json.tftpl`, `scripts/check.sh`, `.github/workflows/ci.yml`, `docs/runbooks/env-down.md` -- read actions, shellcheck lines, runbook

**Acceptance Criteria:**
- Given recorded output with a tagged leftover of each kind, when the check runs, then it fails and names it; given `down.json`, it passes (R3).
- Given an unreachable API, when the check runs, then it fails (R3).
- Given the stub that never removes the ALB, when teardown runs, then it fails before `platform` is uninstalled (R3).
- Given `scripts/check.sh`, when run, then it passes.

## Implementation Notes

Live record (2026-11-18/19, after merge in PR #75):

- First scheduled run did not appear within about an hour of the merge; dispatched runs worked.
- Runs 1 and 2 of `env-down` (no environment up) failed at the leftover check with `tag:GetResources` denied until bootstrap was re-applied with the new read actions; the check exited 2 and never read clean. After the re-apply, `env-down` on an empty account was green.
- Positive control (`--list` while up) found the ALB, two target groups, four security groups and two volumes, 37 tagged resources in all. It found no ENI: the ALB's and the nodes' ENIs carry neither tag, so the tag-based ENI wait and ENI leg are vacuous (deferred entry stays open; `terraform destroy` still fails on a leftover ENI).
- First `env-down` on a live environment (run 44424242091) failed: the ALB left the tagging API within seconds, `gateway-and-alb` finished in 2 s, `helm uninstall platform` removed the controller, and the Gateway stayed Terminating (finalizer owned by the controller), failing the uninstall after 10 minutes. Fixed by also waiting for the Gateway object to be gone (`gateway_gone`), with a regression test. The environment was left with no controller and a stuck Gateway, to be cleaned by hand.

## Plan Change Log

## Review Triage Log

- high, patch: leftover-check step piped to `tee` without `pipefail`, so a failing check left the job green. Verified in `env-down.yml`; fixed with `set -o pipefail` and a test assertion.
- low, merged into the item above: stage-times step shows the verdict line only; the job result was already wrong because of it, now fixed.
- maybe-false, defer: ENI tag filters may match nothing if controller and CNI ENIs are untagged; settled by the live `--list` run. Entry added to `deferred-work.md`.
- false: "test file not read, so coverage unconfirmed" is not a defect claim; `test_leftover_check.py` ran and passed in `scripts/check.sh`.
- false: empty Implementation Notes and unrun manual checks; they need the live account and `main`, as the plan states.

## Design Notes

The Python module holds the classification so unit tests need no AWS; the `.sh` wrapper only calls `aws resourcegroupstaggingapi get-resources` (paginated, `--tag-filters Key=environment,Values=$ENV`, and again for `Key=elbv2.k8s.aws/cluster`) and ENIs through `ec2 describe-network-interfaces`, which the tagging API can omit. A resource counts as leftover when its tag matches and it is not `stack=bootstrap`; after `destroy` the state is empty, so any such resource is outside state.

## Verification

**Commands:**
- `scripts/check.sh` -- expected: `check: all passed`
- `uv run pytest tests/unit/test_leftover_check.py tests/unit/test_eks_teardown.py tests/unit/test_env_down_workflow.py tests/unit/test_env_up_workflow.py` -- expected: pass
- `scripts/leftover-check.sh --dry-run` -- expected: non-zero, names the injected ALB

**Manual checks (after merge to `main`, because `schedule` and dispatch need the default branch; the `eks` branch rule admits `main`):**
- The agent dispatches `env-up` (4 h expiry), runs `scripts/leftover-check.sh --list` under `ticketscope-readonly` (lists the Gateway's ALB, a target group, the security group, the PVC volumes), dispatches `env-down`, and reads the run: AD-24 order, check clean, then a read-only recheck (R3).
- IAM `simulate-principal-policy` for the deploy role against bootstrap ARNs is denied; `terraform plan -lock=false` of `infra/bootstrap` shows no change (R3).
- Dispatch `env-up` with `expiry_minutes=15`; the scheduled run destroys it with no dispatch; record time past expiry against expiry plus one sweep period plus teardown time (R4).
- Record every denied action added to the deploy role in Implementation Notes.
