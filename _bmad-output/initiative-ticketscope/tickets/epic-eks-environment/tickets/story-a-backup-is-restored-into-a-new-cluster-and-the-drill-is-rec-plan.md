---
title: 'A backup is restored into a new cluster and the drill is recorded'
type: 'feature'
ticket: '7'
created: '2026-11-20'
status: 'built'
baseline_revision: '84ac56a3cc4cd87a7cfcfb5ddfbf69f80da6013b'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick-inline]
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-cloudnativepg-backs-up-to-the-bootstrap-bucket-through-an-ir-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A backup has never been restored. Until a recovery Cluster reads one and shows the same corpus, R9 is unproven, and the first real restore (and any bug in it) would land in the live window.

**Approach:** `scripts/restore-drill.sh` takes an on-demand backup, creates a one-instance recovery Cluster `ticketscope-restore` (`bootstrap.recovery` through `externalClusters` and the Barman plugin, reading the source's `serverName`), waits for it, and gathers `corpus_meta`, the issue count and an ordered digest of issue numbers from both. `scripts/restore_drill.py` compares them with the pinned Release's `Issues:` count, exits non-zero on any difference, and renders the masked record `docs/drills/restore-drill.md`. The recovery account is added to the backup role's trust.

## Boundaries & Constraints

**Always:** The comparison and the masking are plain Python with unit tests; the script only gathers and orchestrates. A listing, kubectl or psql error is never read as a match (exit 2). The recovery Cluster does not archive (no plugins entry): it reads only. The record holds no account id, ARN account segment, load balancer or EKS endpoint hostname, token or key. A person runs the drill; the agent runs no cluster write.

**Never:** No restore into the source Cluster, no edit of the source's `serverName` or ObjectStore, no second archive writer, no hand-written drill result, no change to `eval/baseline.json`. R11 (restore from a previous incarnation) is story 5.10's.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Match | same `corpus_meta`, count, digest; count equals the Release's | `restore drill: OK`, exit 0 | none |
| Count differs | restored count differs | names the field, exit 1 | none |
| Meta or digest differs | any other field differs | names the field, exit 1 | none |
| Release count differs | both equal each other, not the Release | exit 1 | none |
| Unreadable input | missing key or bad JSON | exit 2 | never reads as OK |
| Not ready | recovery Cluster not Ready in time | script exits 1 with its log | no record rendered |

</frozen-after-approval>

## Code Map

- `scripts/restore_drill.py` (new) -- `compare(source, restored, expected)`, `expected-issues` (the pin via `ticketscope.adapters.release.read_snapshot_pin` on `deploy/charts/ticketscope/values.yaml`, then the Release body's `Issues: N` as `tests/eks/test_public_smoke.py::_release_count` does), `record` (masks, writes the markdown). Style of `scripts/leftover_check.py`.
- `scripts/restore-drill.sh` (new) -- stages timed like `scripts/eks-deploy.sh` (`stage`, summary); reuses `scripts/eks-backup.sh`; queries as `postgres` through `kubectl exec <pod> -c postgres -- psql -d app -tAc` (as `scripts/fault-inject.sh` `sql()`); the source's `serverName` is read from `.spec.plugins[0].parameters.serverName`, image and storage from the source Cluster; deletes the recovery Cluster at the end.
- `infra/env/irsa.tf` -- `namespace_service_accounts` gains `ticketscope:ticketscope-restore` (the recovery Cluster's account is named after it). Takes effect at the next `env-up`.
- `docs/drills/restore-drill.md` (new) -- committed skeleton (commands, "not yet run"); replaced by the rendered record after the live run. `docs/runbooks/eks-tracer.md` -- one pointer.
- `tests/unit/test_restore_drill.py` (new) -- matrix rows, masking, the grep test over `docs/drills/`; `tests/unit/test_backup_irsa.py` -- the trust list assertion; `scripts/check.sh` and `.github/workflows/ci.yml` -- `shellcheck scripts/restore-drill.sh` (kept identical).
- Do not touch: `scripts/eks-deploy.sh`, `env-up.yml`, the chart, `infra/bootstrap`.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/unit/test_restore_drill.py` -- red first: every matrix row, the digest and Release comparisons, masking of 12-digit ids, ARNs, ELB and EKS hostnames, and the grep test (no account id, key id or secret in any `docs/drills/*.md`)
- [ ] `scripts/restore_drill.py` -- compare, expected-issues, record
- [ ] `scripts/restore-drill.sh`, `infra/env/irsa.tf`, `tests/unit/test_backup_irsa.py` -- orchestration and the trust entry
- [ ] `docs/drills/restore-drill.md`, runbook pointer, `scripts/check.sh` and `ci.yml` -- skeleton and wiring

**Acceptance Criteria:**
- Given a live environment with a completed backup, when a person runs `scripts/restore-drill.sh`, then the restored `corpus_meta` equals the source's, the issue count and the ordered digest match, and the count equals the pinned Release's.
- Given differing counts, meta or digests, when `restore_drill.py compare` runs, then it exits non-zero naming the field.
- Given the live run's log, when the record is rendered, then `docs/drills/restore-drill.md` holds the commands, output and timings with no account id or credential, and a test greps it.
- Given the restore needs `GetObject` and a retention delete, when the drill ran, then the Implementation Notes say which of the policy's actions it exercised for real.

## Implementation Notes

- Built directly, no subagent. `scripts/check.sh` passes (ruff, pyright, imports, pytest, terraform incl. the mocked plan, actionlint, shellcheck).
- `scripts/restore_drill.py` holds `compare`, `mask`, `render_record`, `expected-issues` and the CLI (exit 0 match, 1 difference, 2 unreadable). `scripts/restore-drill.sh` gathers the snapshots as `postgres` through `kubectl exec ... psql` and is driven end to end in `tests/unit/test_restore_drill_script.py` against a stub `kubectl` and `uv` (the applied recovery Cluster, exit codes, record, cleanup).
- The stub test caught a real bug before any live run: the `x` helper echoed each command to stdout, and `gather` redirected stdout into the snapshot JSON. It now echoes to stderr, which the script tees into the log.
- `scripts/eks-backup.sh` gained an optional `--name-suffix`, so the drill takes its own Backup in the same incarnation (the objects still land under `backups/<serverName>/`). Not in the plan's file list; needed so a second on-demand backup does not collide with 5.6's.
- `infra/env/irsa.tf`: the backup role's trust lists `ticketscope:ticketscope-restore` too. It takes effect at the next `env-up`; a window that started before this change needs `terraform apply` (or a hand trust edit) first, or the recovery pod cannot assume the role.
- `docs/drills/restore-drill.md` is a committed skeleton ("not yet run"); the grep test covers every file in `docs/drills/`. The live run replaces it with the rendered record.
- Unknown, settled by the live run: whether the plugin reconciles an ObjectStore Role for a recovery Cluster that only names the plugin under `externalClusters` (0.16.0 binds its Role to the Cluster's account name). If the recovery job is Forbidden on the ObjectStore, the fix is a Role and RoleBinding for `ticketscope-restore`, recorded here.
- Not exercised yet: the live restore, the real `expected-issues` fetch from GitHub, and (per 5.6's decision) the retention delete. The restore exercises `GetObject` and `ListBucket` for real.

## Plan Change Log

## Review Triage Log

Quick lens run inline by the build session (no review subagent was requested). Verdicts: 0 high, 0 medium, 1 low, 0 false.

| Verdict | Route | Finding and evidence |
|---|---|---|
| low | rejected (needs live run) | The plugin may not create an ObjectStore Role for a recovery Cluster; unknowable offline, recorded in Implementation Notes with the fix. |

Checked against the diff: the recovery Cluster has no plugins entry and no archive path; the comparison treats missing or malformed input as exit 2; the record is masked and a test greps every `docs/drills/*.md`; the source Cluster and its ObjectStore are only read; the stub run covers every matrix row.

## Design Notes

The recovery Cluster's account is `ticketscope-restore`, not `ticketscope-db`, so it needs its own trust entry; the plugin binds its Role to the Cluster's account name (0.16.0). Recovery replays to the end of the archive; nothing writes to the corpus, so the counts and digest stay comparable. The skeleton record lets the grep test run before the live window.

## Verification

**Commands:**
- `scripts/check.sh` -- expected: all static jobs pass
- `uv run pytest tests/unit/test_restore_drill.py tests/unit/test_backup_irsa.py` -- expected: pass

**Manual checks (if no CLI):**
- A person runs `scripts/restore-drill.sh` on an `env-up` environment (admin kubeconfig: the read-only role cannot read CNPG objects), then `restore_drill.py record`, and commits the record.
