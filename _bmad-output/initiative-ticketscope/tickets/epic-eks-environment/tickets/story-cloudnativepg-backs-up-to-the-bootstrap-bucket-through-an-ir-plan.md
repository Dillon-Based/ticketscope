---
title: 'CloudNativePG backs up to the bootstrap bucket through an IRSA role'
type: 'feature'
ticket: '6'
created: '2026-11-20'
status: done
baseline_revision: '11aa8426e55c582bce6430a0ea6349931c7552ee'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick-inline]
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The EKS release has `backup.enabled: false`: the Cluster archives no WAL and takes no backup, and no IAM role lets its pods write to the bootstrap bucket (R8). Backups on kind use static SeaweedFS keys, which EKS must not (R6).

**Approach:** The `env` stack makes an IRSA role for the Cluster's service account `ticketscope/ticketscope-db` with a tested minimal S3 policy on the `backups/` prefix. The chart annotates that account from `database.serviceAccount.annotations`, sets the ObjectStore to `inheritFromIAMRole`, takes the plugin's `serverName` from a value, and adds a ScheduledBackup. `eks-deploy.sh` passes the role ARN, bucket and incarnation id; `env-up` triggers one on-demand backup after the smoke check. The plugin chart moves to 0.9.0 (plugin v0.16.0).

## Boundaries & Constraints

**Always:** `values-eks.yaml` holds environment facts only; the role ARN, bucket and incarnation come from `eks-deploy.sh`. kind keeps its SeaweedFS static credentials and renders as before. `spec.serviceAccountName` stays unset and no `skipEmptyWalArchiveCheck` annotation is added. Objects live under `backups/<serverName>/`. The policy starts from the candidate set (object: Put, Get, Delete, AbortMultipartUpload, ListMultipartUploadParts on `backups/*`; bucket: ListBucket with `s3:prefix` `backups/*`, ListBucketMultipartUploads) and is tightened against failures; the exact needed set goes in Implementation Notes. Plugin issue 892 (Secret read in the namespace) is recorded, not fixed.

**Never:** No AWS key in any pod, Secret, repo or workflow. No Pod Identity (fallback only if IRSA fails on the first recreate). No change to the deploy role's policy unless a live denial proves it needed. No hand-written baseline or README table. The agent runs no AWS or cluster write; a person runs `env-up` and the live checks.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| EKS values | `values-eks.yaml` plus role ARN, bucket, incarnation | SA annotation `eks.amazonaws.com/role-arn`, `inheritFromIAMRole: true`, plugin `serverName`, ScheduledBackup | No error |
| kind values | `values-kind.yaml` | SeaweedFS Secret copy, no annotation, no `serverName` | No error |
| IRSA without ARN | `inheritFromIAMRole` set, no role ARN | render fails with a message | `helm template` exit 1 |
| State prefix | role vs `s3:GetObject` on `env/*` | `implicitDeny` | Never allowed |
| Missing incarnation | `eks-deploy.sh` without `--incarnation` | usage error, nothing installed | exit 2 |

</frozen-after-approval>

## Code Map

- `infra/env/irsa.tf` -- add `aws_iam_policy_document`/`aws_iam_policy` `ticketscope-env-cnpg-backup` and an IRSA module (`namespace_service_accounts = ["ticketscope:ticketscope-db"]`, `policies` map, same name prefix); `outputs.tf` -- `cnpg_backup_role_arn`, `backup_bucket`. The bucket is `ticketscope-${var.account_id}` (bootstrap `local.bucket`).
- `deploy/charts/ticketscope/templates/database.yaml` -- Cluster: `serviceAccountTemplate.metadata.annotations` from `database.serviceAccount.annotations`; `serverName` beside `barmanObjectName` when set. `backup.yaml` -- `inheritFromIAMRole` branch exists; require an annotation or fail. New `scheduledbackup.yaml` (`method: plugin`). `values.yaml` -- `backup.serverName`, `backup.scheduled`, `database.serviceAccount.annotations`.
- `deploy/charts/ticketscope/values-eks.yaml` -- `backup.enabled: true`, `credentials.inheritFromIAMRole: true`; no ARN, bucket or incarnation. `values-kind.yaml` -- unchanged.
- `deploy/charts/platform/Chart.yaml`, `Chart.lock` -- `plugin-barman-cloud` 0.8.1 to 0.9.0 (appVersion v0.16.0); `tests/unit/test_chart_backup_expanded.py:388` pins 0.8.1.
- `scripts/eks-deploy.sh` -- `--incarnation`, `--backup-bucket`; read `cnpg_backup_role_arn`; `--set-string` backup.destinationPath, backup.serverName, database.serviceAccount.annotations. New `scripts/eks-backup.sh` -- `kubectl create` a plugin `Backup`, wait for `completed`, print its objects' prefix.
- `.github/workflows/env-up.yml` -- pass `TICKETSCOPE_STATE_BUCKET` and `inc-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}`; run `eks-backup.sh` after the smoke step, outside the clock.
- `tests/unit/test_chart_eks.py` (reserved keys, `database.serviceAccount.annotations` is named), `test_chart_backup.py`, `test_infra_env.py` (HCL text asserts; no account id literal), `test_env_up_workflow.py`, `tests/unit/test_eks_backup.py` (new).
- `docs/runbooks/eks-tracer.md` -- live steps; the epic's deferred-work file for issue 892.
- Do not touch: `scripts/kind-up.sh`, `values-kind.yaml`, `_kind-deploy.yml`, `eval/baseline.json`, `infra/bootstrap`.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/unit/*` above -- red first: render asserts (EKS annotation, `serverName`, `inheritFromIAMRole`, ScheduledBackup; kind unchanged; missing ARN fails; no `serviceAccountName`, no `skipEmptyWalArchiveCheck`), policy text (actions, `backups/*`, no `env/*`), workflow and script wiring
- [ ] `infra/env/irsa.tf`, `outputs.tf` -- role, policy, outputs
- [ ] chart templates and values, `platform/Chart.*` -- values and templates per the Code Map; `helm dependency update` for the lock
- [ ] `scripts/eks-deploy.sh`, `scripts/eks-backup.sh`, `env-up.yml`, runbook -- wiring and live steps incl. `aws iam simulate-principal-policy` on the role (readonly profile) for `env/*` denied and `backups/*` allowed

**Acceptance Criteria:**
- Given the EKS values and the three facts, when the chart renders, then the Cluster's account carries the role annotation, the ObjectStore inherits the role, the plugin entry has `serverName`, a ScheduledBackup exists, and no static key Secret renders.
- Given kind values, when rendered, then output is as before apart from the ScheduledBackup.
- Given a person runs `env-up`, when it finishes, then the Cluster archives WAL, the on-demand Backup is `completed`, its objects are under `backups/<incarnation>/`, and the pods hold no AWS key.
- Given the policy limited to the candidate actions, when a backup, a restore read and a retention delete run, then each succeeds, and the exact set needed is in Implementation Notes with the Secret names and the plugin Role's rules.
- Given the role, when simulated on the Terraform state prefix, then it is denied.

## Implementation Notes

- Built directly, no subagent. `scripts/check.sh` passes (ruff, pyright, imports, pytest, terraform incl. mocked plan, actionlint, shellcheck).
- Decision: `backup.scheduled.enabled` defaults to `false` in `values.yaml` and is set to `true` in `values-eks.yaml`, because an existing test and the epic's "must not change kind" rule keep kind free of a ScheduledBackup. The plan's Design Notes said "on by default"; the EKS release still has it on.
- Decision: the IRSA-without-ARN failure is checked in `backup.yaml` (needs `database.serviceAccount.annotations["eks.amazonaws.com/role-arn"]`).
- Plugin chart `plugin-barman-cloud` 0.8.1 to 0.9.0 (appVersion v0.16.0); `Chart.lock` refreshed with `helm dependency update`.
- Policy as committed is the candidate set, untested live: object Put/Get/Delete/AbortMultipartUpload/ListMultipartUploadParts on `backups/*`; ListBucket with prefix `backups/*`; ListBucketMultipartUploads. The needed set, Secret names and plugin Role rules are still to be recorded by the live run (runbook section 8).
- Not done here (a person runs it): live `env-up`, the completed Backup, objects in the bucket, the policy simulation.
- Decision (user, 2026-11-20): for the November window the restore read and the retention delete are shown by `iam simulate-principal-policy` only (`s3:GetObject`, `s3:DeleteObject` allowed on `backups/*`). The real restore and the real retention delete are done in the December drills (stories 5.7 and 5.8), which then confirm or tighten the policy set.

- Live finding, run 44802980572 (2026-11-20): apply, deploy and smoke passed; the on-demand Backup stayed `started` for 900 s and the step failed. The plugin sidecar's `barman-cloud-check-wal-archive` failed on every attempt with "Permission denied when accessing bucket ... Forbidden". Cause: its bucket check is `HeadBucket`, which IAM evaluates as `s3:ListBucket` with no `s3:prefix` key, so the prefix-conditioned statement never matched. Only a `backup.info` was written (Put works). Fix: a second `s3:ListBucket` statement `BackupBucketReachable` with `Null s3:prefix = true` (infra/env/irsa.tf). Whether `GetBucketLocation` or another action is also needed is settled by the re-run.
- `iam simulate-principal-policy` returned `explicitDeny` for every action on this role (`AllowedByOrganizations: false`, no matched statement), including ones the plugin actually performed. `simulate-custom-policy` on the policy document is the usable check: `env/*` implicitDeny, `backups/*` Put/Get/Delete allowed.
- The read-only role's EKS view access does not cover the CNPG custom resources; pod logs are readable.

- Live result, run 44802980572, incarnation `inc-44802980572-1` (2026-11-20), after the policy gained `BackupBucketReachable` by hand at 20:54Z (`iam create-policy-version`; the same statement is in `infra/env/irsa.tf`, so the next `env-up` creates it):
  - The on-demand Backup `ticketscope-db-ondemand-inc-44802980572-1` is `completed` (plugin, v0.16.0 on chart 0.9.0). The bucket holds `backups/inc-44802980572-1/base/20261120T195011/{backup.info,data.tar}` (186 MB) and 25 gzip WAL files under `wals/0000000100000000/`. The `env-up` step failed only because it timed out at 900 s while the policy was wrong; the backup finished at 20:55:33Z once the policy was fixed.
  - R6: the service account `ticketscope-db` carries only `eks.amazonaws.com/role-arn`; both database pods have `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` and no access key variable; `spec.serviceAccountName` is unset.
  - Needed policy set (live-proven for backup and WAL archive): object `PutObject`, `GetObject`, `DeleteObject`, `AbortMultipartUpload`, `ListMultipartUploadParts` on `backups/*`; `ListBucket` with `s3:prefix` `backups/*`; `ListBucket` with `Null s3:prefix` (HeadBucket); `ListBucketMultipartUploads`. `GetBucketLocation` was not needed. Restore read (`GetObject`) and retention delete (`DeleteObject`) are simulation-only for now (user, 2026-11-20); `GetObject`/`DeleteObject` are not yet exercised by a real restore or prune, so December's drills confirm or tighten them.
  - Namespace Secrets: `sh.helm.release.v1.ticketscope.v1`, `ticketscope-db-app`, `ticketscope-db-ca`, `ticketscope-db-replication`, `ticketscope-db-ro`, `ticketscope-db-server`. No backup-credential Secret exists on EKS (`ticketscope-backup-s3` is kind only).
  - Plugin Role `ticketscope-db-barman-cloud` (RoleBinding to `ticketscope-db`): `objectstores` named `ticketscope-backup` get/watch/list; `objectstores/status` update; `secrets` get/watch/list for every Secret in the namespace (plugin issue 892, accepted and recorded, not fixed). The operator's own Role `ticketscope-db` limits `secrets` to the six Cluster Secrets.
  - Not yet seen: the ScheduledBackup has not fired (its `0 0 3 * * *` schedule is never reached in a short-lived environment). Its render is tested; a fire is observed in a longer window.
  - The ObjectStore status update logged "object has been modified" once (a harmless conflict; the plugin skips and carries on).
  - The IAM-policy denied-actions summary and the deploy role needed no change: no `iam` denial occurred on the new role or policy.
- Live result, `env-up` run 45219791550 from `main` at e0d1278, incarnation `inc-45219791550-1` (2026-11-23), with no hand step: the policy now carries `BackupBucketReachable` from `infra/env/irsa.tf`. The on-demand Backup `ticketscope-db-ondemand-inc-45219791550-1` is `completed` inside the step's timeout. Read under `ticketscope-readonly`, the bucket holds `backups/inc-45219791550-1/base/20261123T170656/{backup.info,data.tar}` (186 MB) and the WAL archive (26 objects in all). The same window's restore drill (story 5.7) read the base backup and WALs back through the role, so `GetObject` and the listings are now live-proven for a restore.
- Accepted as done (user, 2026-11-23, live window moved up from December): the ScheduledBackup fire and the retention delete (`DeleteObject` on prune) are still unobserved. Both are carried in `deferred-work.md`.

## Plan Change Log

## Review Triage Log

Quick lens run inline by the build session (no review subagent was requested). Verdicts: 0 high, 0 medium, 2 low, 0 false.

| Verdict | Route | Finding and evidence |
|---|---|---|
| low | rejected (needs live run) | The candidate policy may lack an action Barman calls (for example `s3:GetBucketLocation`). Unknowable offline; the plan routes it to the live run, which records the set that was needed. |
| low | rejected (cosmetic) | `lenses_ran` holds `quick-inline` because the lens ran in this session rather than a subagent. |

Checked by reading the diff against the criteria: the Cluster takes `serviceAccountTemplate` annotations and no `serviceAccountName`; `serverName` sits beside `barmanObjectName`; the ObjectStore inherits the role with no keys or endpoint; kind renders as before (no annotation, no `serverName`, no ScheduledBackup); the policy never names `env/`; `eks-backup.sh` runs after the clock stops; the deploy role's existing `ticketscope-env-*` IAM and `backups/*` S3 grants cover the new role, so no bootstrap re-apply is expected.

## Design Notes

The ScheduledBackup is on by default (`0 0 3 * * *`, never reached in a 4-hour life); the on-demand Backup, not the schedule, is the live proof. `eks-backup.sh` runs after the clock stops so R1 is untouched. A live person run is hitl: the plan's unit and render checks run here, `env-up` and the simulation run by hand.

## Verification

**Commands:**
- `scripts/check.sh` -- expected: all static jobs pass
- `uv run pytest tests/unit/test_chart_backup.py tests/unit/test_chart_eks.py tests/unit/test_infra_env.py tests/unit/test_env_up_workflow.py tests/unit/test_eks_backup.py` -- expected: pass
- `helm template` of both releases with EKS and kind values -- expected: renders as in the matrix

**Manual checks (if no CLI):**
- A person runs `env-up`, then `kubectl -n ticketscope get backups.postgresql.cnpg.io,scheduledbackups` (readonly kubeconfig): Backup `completed`; `aws s3 ls --profile ticketscope-readonly` shows `backups/<incarnation>/`; `simulate-principal-policy` denies `env/*`.
