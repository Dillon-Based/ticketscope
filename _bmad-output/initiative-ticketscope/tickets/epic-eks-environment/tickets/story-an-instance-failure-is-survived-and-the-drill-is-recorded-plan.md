---
title: 'An instance failure is survived and the drill is recorded'
type: 'feature'
ticket: '8'
created: '2026-11-24'
status: done
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

**Problem:** R10 is unproven: nothing forces the two CloudNativePG instances onto different nodes, and no node has ever been lost under traffic. Plugin bug #828 (failover with two instances archiving to one archive) may break the two-instance case.

**Approach:** The EKS values require the instances on different nodes (kind's do not). `scripts/failure-drill.sh` starts a one-second search probe on the public hostname, terminates the node holding the primary, and times promotion, the probe's next success and the failed requests between. `scripts/failure_drill.py` computes those figures and renders the masked record `docs/drills/failure-drill.md`. If #828 bites, the record states what failed and this story proposes the fix or the limit.

## Boundaries & Constraints

**Always:** Timings and counts come from plain, unit-tested Python reading the probe log and event timestamps; the script only gathers. A probe, kubectl or aws error is never read as a success (exit 2). The two instances' nodes are recorded before the failure, and the drill refuses to terminate if they share a node. After promotion, the Cluster's archive status shows no error and archiving continues under the unchanged `serverName`. The record holds no account id, instance id, node name, ARN account segment, load balancer or EKS hostname, or token. A person runs the drill with admin credentials; the agent runs no cluster or AWS write.

**Never:** No one-instance drill and no weakening of the drill if #828 bites. No change to `serverName`, the ObjectStore or the retention. No hand-written result, no change to `eval/baseline.json`. Kind's values keep their default placement. R11 is story 5.10's.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Survived | probe log with a failure window, a new primary, a later success | recovery seconds (terminate to next success), promotion seconds, failed count; verdict OK | none |
| No failure seen | probe never fails | verdict OK, failed count 0 | none |
| Never recovers | no success after the terminate | verdict FAILED, exit 1 | no record claims recovery |
| Same node | both instances on one node | script exits 1 before terminating | nothing terminated |
| Unreadable input | missing or malformed log or events | exit 2 | never reads as OK |
| Archive error | `lastFailedWAL` set or archiving not continuing | verdict FAILED naming it, exit 1 | the record keeps the Cluster status |

</frozen-after-approval>

## Code Map

- `deploy/charts/ticketscope/values.yaml` -- `database.instances: 2` (line 131); add `database.instancePlacement: ""`.
- `deploy/charts/ticketscope/templates/database.yaml` -- the Cluster; when the value is `required`, render `affinity` with `enablePodAntiAffinity: true`, `podAntiAffinityType: required`, `topologyKey: kubernetes.io/hostname`.
- `deploy/charts/ticketscope/values-eks.yaml` -- sets `database.instancePlacement: required`. The key is already in `RESERVED_ENV_KEYS` (`tests/unit/test_chart_eks.py:42`); move it to `TICKETSCOPE_ENV_KEYS` proper and assert it in a render test (EKS has it, kind does not; the helpers `_ticketscope_eks`, `_docs` are there).
- `scripts/failure_drill.py` (new) -- `analyze(probe_log, events)`, `placement_ok`, `archive_ok`, `record`; imports `mask` from `scripts/restore_drill.py`. Style of that file (exit 0/1/2).
- `scripts/failure-drill.sh` (new) -- stages and `x` helper as in `scripts/restore-drill.sh`; `primary_of` pattern; node of a pod from `.spec.nodeName`, EC2 id from the node's `.spec.providerID`, terminate with `aws ec2 terminate-instances`; promotion from `.status.currentPrimary`; archive from `.status.conditions` ContinuousArchiving and `.status.lastArchivedWAL`/`lastFailedWAL` after `pg_switch_wal()`. Probe: `curl -s -o /dev/null -w` POST `q=launcher crash` to `$URL/` every second, as `tests/eks/test_public_smoke.py` does.
- `docs/drills/failure-drill.md` (new) -- committed skeleton ("not yet run"); `docs/runbooks/eks-tracer.md:197` -- one pointer.
- `tests/unit/test_failure_drill.py`, `tests/unit/test_failure_drill_script.py` (new) -- matrix rows and masking; the script end to end against stub `kubectl`, `aws`, `curl` as `tests/unit/test_restore_drill_script.py` does; the grep test over `docs/drills/` already exists in `test_restore_drill.py:126`.
- `scripts/check.sh` and `.github/workflows/ci.yml:133` -- `shellcheck scripts/failure-drill.sh`, identical in both.
- Do not touch: `infra/`, `scripts/eks-deploy.sh`, `env-up.yml`, `values-kind.yaml`.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/unit/test_failure_drill.py`, `tests/unit/test_chart_eks.py` -- red first: matrix rows, masking, EKS requires placement and kind does not
- [ ] `deploy/charts/ticketscope/` (values, template, `values-eks.yaml`) -- the placement rule
- [ ] `scripts/failure_drill.py` -- analyze, checks, record
- [ ] `scripts/failure-drill.sh`, `tests/unit/test_failure_drill_script.py` -- orchestration and its stub run
- [ ] `docs/drills/failure-drill.md`, runbook pointer, `scripts/check.sh`, `ci.yml` -- skeleton and wiring

**Acceptance Criteria:**
- Given the EKS values, when the chart renders, then the Cluster requires anti-affinity on hostname; given kind's values, then it does not.
- Given a live environment, when a person runs the drill, then the record shows the two instances on different nodes before the failure, a promoted standby, the probe succeeding again, the recovery time and the failed-request count.
- Given the promoted primary, when archive status is read, then it shows no error and archiving continues under the one `serverName`.
- Given `docs/drills/`, when the grep test runs, then no account id or credential is found.
- Given #828 bites, when the drill fails, then the record and Implementation Notes say exactly what failed and propose the fix or limit.

## Implementation Notes

- Built directly, no subagent. `scripts/check.sh` passes (ruff, pyright, imports, pytest, terraform incl. the mocked plan, actionlint, shellcheck). The platform-chart render tests skip here (dependencies not built); the placement render test is on the ticketscope chart and runs.
- `database.instancePlacement` stays in `RESERVED_ENV_KEYS` (the AD-25 name); it is now implemented. Required anti-affinity is rendered through the Cluster's `affinity` block.
- `scripts/failure_drill.py` holds `analyze`, `placement_ok`, `archive_problems`, `mask` (adds node names and instance ids to `restore_drill.mask`) and `render_record`; `scripts/failure-drill.sh` is driven end to end in `tests/unit/test_failure_drill_script.py` against stub `kubectl`, `aws`, `curl`, `uv`.
- Archive check: ContinuousArchiving must be True, `lastArchivedWAL` must advance after a forced `pg_switch_wal()` on the new primary, no `lastFailedWAL` newer than the last archived, and `serverName` unchanged. A WAL name compares as a string; a timeline change after promotion raises the prefix, so it reads as advance.
- Not exercised yet: the live run (promotion, probe, archive status on EKS) and whether plugin bug #828 bites. Both are settled by a person's run, which then replaces the skeleton `docs/drills/failure-drill.md`.
- Accepted as built (user, 2026-11-24), with the live drill not yet run: a person runs `scripts/failure-drill.sh` in the December window and replaces the skeleton `docs/drills/failure-drill.md` with the record. R10 and whether plugin bug #828 bites stay unproven until then (deferred-work entry).

## Plan Change Log

## Review Triage Log

Quick lens, one pass. Verdicts: 1 high, 4 medium, 3 low, 1 false, 1 not a defect.

| Verdict | Route | Finding and evidence |
|---|---|---|
| high | patch | Placement check passed with a Pending standby (null `nodeName`) and counted job pods; now instance pods only (`cnpg.io/podRole=instance`), each scheduled and Ready; stub test added. |
| medium | patch | Empty `serverName` passed the archive check by construction; now an unreadable input (exit 2). The check stays "serverName unchanged" plus WAL advance after a forced switch. |
| medium | patch | A probe log with nothing after the termination read as OK; now exit 2. |
| medium | patch | aws and cluster-read failures after the termination had undocumented exit codes and no record; terminate failure and an unreadable Cluster exit 2, archive polling tolerates a read error and analyze flags it. |
| low | patch | Record's placement line was index text; now states `placement_ok` of the real node list. |
| low | patch | Chart silently ignored a typo such as `Required`; now fails the render, test added. |
| low | patch | Unawaited `tee` could drop the log's last lines; `sleep 1` before the record. |
| false/low | rejected | `database.instancePlacement` stays in `RESERVED_ENV_KEYS`: an existing test pins that set and the notes record the choice. |
| n/a | none | AC-5 (#828 bites) is settled only by a person's live run. |

## Design Notes

Required anti-affinity leaves the replacement standby Pending until the node group brings a new node; that is the real shape of a node loss. The drill runs last in the shared live window with stories 6 and 7 (test design C-8), and needs `values-eks.yaml` deployed by `env-up` before the window, so the first `env-up` after merge carries the rule.

## Verification

**Commands:**
- `scripts/check.sh` -- expected: all static jobs pass
- `uv run pytest tests/unit/test_failure_drill.py tests/unit/test_failure_drill_script.py tests/unit/test_chart_eks.py` -- expected: pass

**Manual checks (if no CLI):**
- A person runs `scripts/failure-drill.sh` on an `env-up` environment with admin credentials, then commits the rendered record to `docs/drills/failure-drill.md`.
