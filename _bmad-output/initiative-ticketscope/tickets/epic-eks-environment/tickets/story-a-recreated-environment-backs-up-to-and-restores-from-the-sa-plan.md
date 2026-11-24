---
title: 'A recreated environment backs up to and restores from the same bucket'
type: 'feature'
ticket: '9'
created: '2026-11-23'
status: 'done'
baseline_revision: 'd43b982dfa4fe0faf3429485de1023c9761dd796'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-a-backup-is-restored-into-a-new-cluster-and-the-drill-is-rec-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 5.6 gave each `env-up` its own `serverName`, but nothing restores a new environment from the previous one, `env-down` takes no last backup, and the destroy-and-recreate path (R11, R2) has never run. A stale or reused archive prefix would fail the second environment only at WAL archive time, after an apply has been paid for.

**Approach:** `env-up` takes `restore_from`; with it set, the chart's Cluster bootstraps by recovery from `backups/<restore_from>/` (no load) and archives under its own incarnation. A check before `terraform apply` refuses an incarnation whose prefix already exists, or a `restore_from` with no backup. `env-down` takes `backup_first`. The smoke step prints `corpus_meta` and the issue count to the job summary. The agent then dispatches env-up, env-down (backup_first), env-up (restore_from) and records the result in `docs/drills/`.

## Boundaries & Constraints

**Always:** The incarnation check is plain Python with unit tests, run before `terraform apply` and before any image build. `restore_from` and the incarnation match `^[a-z0-9][a-z0-9-]{0,62}$`. Inputs reach shell only through `env:`. The agent only dispatches workflows and reads (read-only AWS profile, `scripts/run-summary.sh`); one environment at a time, each expiring within 4 hours. Unset `restore_from` behaves exactly as before. The record holds no account id, ARN account segment or credential, and a test greps it.

**Never:** No `skipEmptyWalArchiveCheck`, no reuse of a `serverName`, no write to or delete in the first incarnation's prefix, no edit of the bootstrap layer, no hand-written drill result. `kind` and CI behaviour unchanged (`values-kind.yaml`, `_kind-deploy.yml`). No Pod Identity (IRSA stays).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fresh | no `restore_from`; new incarnation | check passes; load runs as before | none |
| Recreate | `restore_from` names a prefix holding a base backup | check passes; recovery, no load job | none |
| Prefix exists | incarnation's prefix already in the bucket | refused before apply | job fails naming the prefix |
| Unknown source | `restore_from` prefix absent or has no base backup | refused before apply | job fails |
| Same id | `restore_from` equals the incarnation | refused | job fails |
| Bad name | input fails the pattern | refused | job fails |
| Unreadable listing | S3 listing errors | refused, never read as "absent" | job fails |

</frozen-after-approval>

## Code Map

- `.github/workflows/env-up.yml` -- `INCARNATION=inc-${RUN_ID}-${ATTEMPT}` set in the facts step; add input `restore_from`, validated in `plan`; add a check step before `terraform plan`/`apply`; pass `--restore-from` to deploy; add a corpus-facts summary step after the smoke check (keep the clock untouched). Deploy role may list `backups/*` already (`deploy-permissions.json.tftpl`).
- `.github/workflows/env-down.yml` -- add boolean `backup_first`; in `teardown`, after the kubeconfig and before `eks-teardown.sh`, take the backup when the cluster is present (reads the Cluster's `serverName`, calls `scripts/eks-backup.sh --name-suffix pre-down`, fails the job before teardown on a failed backup).
- `scripts/eks-deploy.sh` -- optional `--restore-from <id>` becomes `--set-string backup.restoreFrom=`; same name pattern.
- `deploy/charts/ticketscope/templates/database.yaml`, `jobs.yaml`, `values.yaml` -- `backup.restoreFrom` (default empty): Cluster gets `bootstrap.recovery` + `externalClusters` (as `scripts/restore-drill.sh` builds it) instead of `initdb`; the `load` hook is not rendered. Managed role, IRSA annotation and archive `serverName` stay. `values-eks.yaml` untouched (an input, not an environment fact).
- `scripts/incarnation_check.py` (new) -- `check(incarnation, restore_from, prefixes)`; CLI reads the `aws s3api list-objects-v2 --prefix backups/ --delimiter /` JSON. Style of `scripts/leftover_check.py`.
- `scripts/eks-corpus-facts.sh` (new) -- `kubectl exec <primary> -c postgres -- psql` JSON of `corpus_meta`, issue count (as `restore-drill.sh` `gather`).
- `scripts/recreate_drill.py` (new) -- `compare` (corpus facts of both incarnations equal), `archive-diff` (object listings of the first prefix before and after identical), `record` (reuses `restore_drill.mask`). `docs/drills/recreate-drill.md` is its output.
- Tests: `tests/unit/test_env_up_workflow.py`, `test_env_down_workflow.py`, `test_chart_backup*.py`, new `test_incarnation_check.py`, `test_recreate_drill.py`. Wire shellcheck in `scripts/check.sh` and `ci.yml` (kept identical).
- Do not touch: `infra/bootstrap`, `infra/env`, `scripts/eks-teardown.sh`, kind files.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/unit/test_incarnation_check.py`, `tests/unit/test_recreate_drill.py` -- red first: every matrix row, differing facts, a changed first prefix, masking, the grep test over `docs/drills/`
- [ ] `scripts/incarnation_check.py`, `scripts/recreate_drill.py` -- green
- [ ] chart templates and `values.yaml`, `tests/unit/test_chart_backup*.py` -- `restoreFrom` renders recovery and no load; unset renders as today
- [ ] `scripts/eks-deploy.sh`, `scripts/eks-corpus-facts.sh`, `env-up.yml`, `env-down.yml` and their tests -- inputs, the check before apply, the facts in the summary, `backup_first`
- [ ] `scripts/check.sh`, `ci.yml`, `docs/runbooks/env-up.md`, `env-down.md` -- wiring and the new inputs
- [ ] Live (agent, after merge-ready push): dispatch env-up, env-down `backup_first`, env-up `restore_from`, env-down; list the first prefix before and after; render `docs/drills/recreate-drill.md`

**Acceptance Criteria:**
- Given an incarnation whose prefix exists, when the input check runs, then it fails before `terraform apply`, shown by a unit test and by the step order.
- Given the live sequence, when the second environment archives, then it uses its own `serverName`, shows no "Expected empty archive" failure and no `skipEmptyWalArchiveCheck`, and its `corpus_meta` and issue count equal the first's.
- Given both environments, when each answers over HTTPS, then they served the same hostname under the same bootstrap certificate.
- Given the first prefix listed before and after the second environment, then key, size and ETag sets are identical.

## Implementation Notes

- Built by a subagent from this plan; the incarnation check sits in the `plan` job, not `env`, because `build` runs before `env` and the check must precede any build. The parent added the smoke change (a restored environment has no load Job, so the smoke reads the database count) and, after the first live run, printed the corpus facts to the run log, since a step summary cannot be read through the API.
- Live drill, 2026-11-23 (record: `docs/drills/recreate-drill.md`): env-up 45260100245, env-down with `backup_first` 45266017998, env-up with `restore_from` 45268386170, env-down 45272176321. The second environment's `corpus_meta` (including `loaded_at`), issue count, digest, hostname and certificate fingerprint equal the first's; it archived under `backups/inc-45268386170-1/` with no "Expected empty archive"; the first folder's 29 objects were identical by key, size and ETag before and after.
- Not run: the control recreate without the `serverName` change (a third environment; November's hour budget). Whether plugin issue 767 reproduces on current versions stays unknown.
- Found, deferred: the leftover check cannot confirm deleted subnets, so both `env-down` runs ended red after a complete destroy (deferred-work.md).
- The ScheduledBackup (03:00 UTC) did not fire in either window; the deferred item from story 5.6 stays open.

## Plan Change Log

## Review Triage Log

Quick lens, pass 1 (high 0, medium 3, low 1, false 1, rejected 1):

- medium, patch -- corpus-facts step ran before the on-demand backup, so a report failure skipped the backup. Moved after it.
- medium, patch -- `compare` skipped hostname and certificate because the facts JSON never carried them. The env-up step now adds both to the JSON block.
- medium, patch -- `backup_first` failed on a half-built environment with no Cluster resource and left it billing. The lookup is tolerant and says so in the summary; an unusable serverName still fails.
- false -- "smoke compares the database with itself": `_restored_count` is still compared with the Release's published count in `test_the_loaded_issue_count_equals_the_pinned_releases_count`.
- rejected (low) -- `--base-listing` without `--restore-from`: no caller does it and the fix adds a guard.
- not a defect -- no drill record or live evidence yet: the live task is open work.

Also found by the parent before review: a restored environment renders no load Job, so the smoke could not read a load report; it now reads the database count when `restore_from` is set.

## Design Notes

- Load is skipped on restore: it is idempotent against `corpus_meta`, but a restored database already holds the corpus and `loaded_at`; equal `loaded_at` in both summaries is the proof the second did not reload.
- The live window costs about 2 environment-hours against November's 25-hour budget, which already holds about 10 dispatches. The control run without the `serverName` change (plugin issue 767) is not run, because it is a third environment; the record says so.
- The dispatch ref is this story's `worktree*` branch (the `eks` environment's branch rule); env-up's `expire` job dispatches env-down from `main`, which is only a backstop.

## Verification

**Commands:**
- `scripts/check.sh` -- expected: all static jobs pass
- `uv run pytest tests/unit -q` -- expected: pass
- `helm template deploy/charts/ticketscope -f deploy/charts/ticketscope/values-eks.yaml --set backup.destinationPath=s3://b/backups/ --set backup.restoreFrom=inc-1-1 --set backup.serverName=inc-2-1` -- expected: Cluster has `bootstrap.recovery`, no load Job
- `scripts/run-summary.sh <run id>` -- expected: each dispatched run's result for the record
