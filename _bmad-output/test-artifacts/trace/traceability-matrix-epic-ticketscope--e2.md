---
runScope: epic
runKey: epic-ticketscope--e2
targetType: epic
targetId: ticketscope--e2
targetLabel: 'Epic 2: Retrieval is scored on every PR and regressions block the merge'
workflowStatus: completed
stepsCompleted:
- step-01-load-context
- step-02-discover-tests
- step-03-map-criteria
- step-04-analyze-gaps
- step-05-gate-decision
lastStep: step-05-gate-decision
lastSaved: '2026-11-08'
coverageBasis: acceptance_criteria
oracleConfidence: high
oracleResolutionMode: formal_requirements
oracleSources:
- _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md
- _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-readme-results-table-is-generated-from-ci-output-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/tickets.toml
- _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md
externalPointerStatus: not_used
oracleGranularity: requirements
collectionStatus: COLLECTED
sourceSha: 8d772e029c84d73ef4f325f024c90d63c8d7e590
criterionLedger:
- id: ticketscope--e2-s1--AC-1
  localId: AC-1
  story: ticketscope--e2-s1
  name: "Given the oracle fixture, when the scaffold runs, then it passes (story 2.2 replaced the target-only scaffold with the cluster test on the same fixture), and the fixture still starts with the bytes its red commit `b7be713` wrote (R2)."
  text: "Given the oracle fixture, when the scaffold runs, then it passes (story 2.2 replaced the target-only scaffold with the cluster test on the same fixture), and the fixture still starts with the bytes its red commit `b7be713` wrote (R2)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:82
  priority: P0
  priorityBasis: inferred
  declaredLinks: ["R2"]
  validLinks: ["R2"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s1--AC-2
  localId: AC-2
  story: ticketscope--e2-s1
  name: "Given a PR, when `eval.yml` runs, then the eval Job completes after load as `ticketscope_ro`, and the `reports-kind` artifact holds `eval-results.json` with keyword's Recall@10 and MRR@10 over 10,473 pairs and lineage equal to `corpus_meta` (R2)."
  text: "Given a PR, when `eval.yml` runs, then the eval Job completes after load as `ticketscope_ro`, and the `reports-kind` artifact holds `eval-results.json` with keyword's Recall@10 and MRR@10 over 10,473 pairs and lineage equal to `corpus_meta` (R2)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:83
  priority: P0
  priorityBasis: inferred
  declaredLinks: ["R2"]
  validLinks: ["R2"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s1--AC-3
  localId: AC-3
  story: ticketscope--e2-s1
  name: "Given a step after the results are written fails, when the workflow ends, then the artifact is still uploaded (R2)."
  text: "Given a step after the results are written fails, when the workflow ends, then the artifact is still uploaded (R2)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:84
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R2"]
  validLinks: ["R2"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s1--AC-4
  localId: AC-4
  story: ticketscope--e2-s1
  name: "Given the same PR, when `ci.yml` runs, then integrated-check passes (R2)."
  text: "Given the same PR, when `ci.yml` runs, then integrated-check passes (R2)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:85
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R2"]
  validLinks: ["R2"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s1--AC-5
  localId: AC-5
  story: ticketscope--e2-s1
  name: "Given the pinned snapshot, when the pairs are regenerated, then the committed `eval/pairs/2026.11.1.jsonl` is byte-identical and the printed counts are 10,473 / 10,164 / 309 (R1)."
  text: "Given the pinned snapshot, when the pairs are regenerated, then the committed `eval/pairs/2026.11.1.jsonl` is byte-identical and the printed counts are 10,473 / 10,164 / 309 (R1)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:86
  priority: P0
  priorityBasis: inferred
  declaredLinks: ["R1"]
  validLinks: ["R1"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s2--AC-1
  localId: AC-1
  story: ticketscope--e2-s2
  name: "Given the oracle fixture, when the cluster scaffold runs, then every metric short, log-heavy and overall equals `CLUSTER_EXPECTED` (overall differs from the mean of the kind means), a sibling counts as a hit, and the query never scores itself; the fixture still starts with the bytes its red commit `7ea485a` wrote (R2)."
  text: "Given the oracle fixture, when the cluster scaffold runs, then every metric short, log-heavy and overall equals `CLUSTER_EXPECTED` (overall differs from the mean of the kind means), a sibling counts as a hit, and the query never scores itself; the fixture still starts with the bytes its red commit `7ea485a` wrote (R2)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:75
  priority: P0
  priorityBasis: inferred
  declaredLinks: ["R2"]
  validLinks: ["R2"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s2--AC-2
  localId: AC-2
  story: ticketscope--e2-s2
  name: "Given `modes.REGISTRY` replaced after import with a fake second mode, when `score` runs, then the mode appears in the results with no change to `jobs.eval`; an unavailable mode is named in `skipped_modes` (R2)."
  text: "Given `modes.REGISTRY` replaced after import with a fake second mode, when `score` runs, then the mode appears in the results with no change to `jobs.eval`; an unavailable mode is named in `skipped_modes` (R2)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:76
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R2"]
  validLinks: ["R2"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s2--AC-3
  localId: AC-3
  story: ticketscope--e2-s2
  name: "Given the same corpus scored twice, then the metrics and ranks are identical (R2, R3)."
  text: "Given the same corpus scored twice, then the metrics and ranks are identical (R2, R3)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:77
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R2", "R3"]
  validLinks: ["R2", "R3"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s2--AC-4
  localId: AC-4
  story: ticketscope--e2-s2
  name: "Given a PR, when `eval.yml` runs, then `reports-kind`'s `eval-results.json` holds, for keyword, every metric split short, log-heavy and overall, pair counts 10,164 / 309 / 10,473, each query's first-member rank (an independent recompute matches), and `wall_seconds`, which the job summary also shows (R2)."
  text: "Given a PR, when `eval.yml` runs, then `reports-kind`'s `eval-results.json` holds, for keyword, every metric split short, log-heavy and overall, pair counts 10,164 / 309 / 10,473, each query's first-member rank (an independent recompute matches), and `wall_seconds`, which the job summary also shows (R2)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:78
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R2"]
  validLinks: ["R2"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s2--AC-5
  localId: AC-5
  story: ticketscope--e2-s2
  name: "Given the pinned snapshot, when pairs regenerate, then the file is byte-identical and `derive_pairs.py` prints `10473 pairs: 10164 short, 309 log_heavy` (R1)."
  text: "Given the pinned snapshot, when pairs regenerate, then the file is byte-identical and `derive_pairs.py` prints `10473 pairs: 10164 short, 309 log_heavy` (R1)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:79
  priority: P0
  priorityBasis: inferred
  declaredLinks: ["R1"]
  validLinks: ["R1"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s3--AC-1
  localId: AC-1
  story: ticketscope--e2-s3
  name: "Given a PR that worsens keyword ranking, when eval runs, then the gate step fails with the metric named (R3)."
  text: "Given a PR that worsens keyword ranking, when eval runs, then the gate step fails with the metric named (R3)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:72
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R3"]
  validLinks: ["R3"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s3--AC-2
  localId: AC-2
  story: ticketscope--e2-s3
  name: "Given the same PR also updates `eval/baseline.json` to its run's results, then the gate passes (R3)."
  text: "Given the same PR also updates `eval/baseline.json` to its run's results, then the gate passes (R3)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:73
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R3"]
  validLinks: ["R3"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s3--AC-3
  localId: AC-3
  story: ticketscope--e2-s3
  name: "Given a preprocessing-version change with no baseline update, then the gate fails with a lineage message (R3)."
  text: "Given a preprocessing-version change with no baseline update, then the gate fails with a lineage message (R3)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:74
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R3"]
  validLinks: ["R3"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s3--AC-4
  localId: AC-4
  story: ticketscope--e2-s3
  name: "Given `ruff`, `pyright`, `lint-imports` and `pytest tests/unit`, then all pass (R3)."
  text: "Given `ruff`, `pyright`, `lint-imports` and `pytest tests/unit`, then all pass (R3)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:75
  priority: P2
  priorityBasis: inferred
  declaredLinks: ["R3"]
  validLinks: ["R3"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s3--AC-5
  localId: AC-5
  story: ticketscope--e2-s3
  name: "Given the merged workflow, a person makes `eval` required in branch protection (checked by the person)"
  text: "Given the merged workflow, a person makes `eval` required in branch protection (checked by the person, R3)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:76
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R3"]
  validLinks: ["R3"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s4--AC-1
  localId: AC-1
  story: ticketscope--e2-s4
  name: "Given the committed `eval/baseline.json` and README, when `python3 scripts/render_readme_table.py --check` runs, then it exits 0, and `--write` leaves `git diff` empty (R4)."
  text: "Given the committed `eval/baseline.json` and README, when `python3 scripts/render_readme_table.py --check` runs, then it exits 0, and `--write` leaves `git diff` empty (R4)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-readme-results-table-is-generated-from-ci-output-plan.md:69
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R4"]
  validLinks: ["R4"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s4--AC-2
  localId: AC-2
  story: ticketscope--e2-s4
  name: "Given one digit of the README table changed by hand, when the check runs, then it exits 1 (R4)."
  text: "Given one digit of the README table changed by hand, when the check runs, then it exits 1 (R4)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-readme-results-table-is-generated-from-ci-output-plan.md:70
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R4"]
  validLinks: ["R4"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s4--AC-3
  localId: AC-3
  story: ticketscope--e2-s4
  name: "Given a README without the generated-section markers, when the check runs, then it exits 1 (R4)."
  text: "Given a README without the generated-section markers, when the check runs, then it exits 1 (R4)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-readme-results-table-is-generated-from-ci-output-plan.md:71
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R4"]
  validLinks: ["R4"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s4--AC-4
  localId: AC-4
  story: ticketscope--e2-s4
  name: "Given `ci.yml`, when parsed as text, then the `checks` job runs the check command (R4)."
  text: "Given `ci.yml`, when parsed as text, then the `checks` job runs the check command (R4)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-readme-results-table-is-generated-from-ci-output-plan.md:72
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R4"]
  validLinks: ["R4"]
  invalidLinks: []
  exception: none
- id: ticketscope--e2-s5--verify
  localId: verify
  story: ticketscope--e2-s5
  name: "On a PR the eval check passes with eval/baseline.json unchanged, ci.yml and its integrated-check pass, import-linter keeps every contract, and tests/ has no time.sleep calls, enforced by a lint rule or a test"
  text: "On a PR the eval check passes with eval/baseline.json unchanged, ci.yml and its integrated-check pass, import-linter keeps every contract, and tests/ has no time.sleep calls, enforced by a lint rule or a test (R2, R3, R4)."
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/tickets.toml:61
  priority: P1
  priorityBasis: inferred
  declaredLinks: ["R2", "R3", "R4"]
  validLinks: ["R2", "R3", "R4"]
  invalidLinks: []
  exception: none
oracleLedger:
- id: ticketscope--e2--R1
  kind: requirement
  requirement: "Labelled duplicate pairs are derived deterministically from the pinned snapshot's in-subset duplicate links and committed per snapshot version. It is met when the committed pairs file regenerates byte-identical from the snapshot, with its pair counts reported for short and log-heavy queries."
  parent: "parent R6"
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md:31
  priority: P0
  priorityBasis: contributors
  contributors: ["ticketscope--e2-s1--AC-5", "ticketscope--e2-s2--AC-5"]
- id: ticketscope--e2--R2
  kind: requirement
  requirement: "An eval job scores every available mode in the core registry through the real Postgres adapter as the read-only role. It reports Recall@1, Recall@5, Recall@10, MRR@10 and p95 latency, split short versus log-heavy. It is met when the job on kind scores keyword over the full pair set, and a newly registered mode is scored with no change to the job."
  parent: "parent R6"
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md:32
  priority: P0
  priorityBasis: contributors
  contributors: ["ticketscope--e2-s1--AC-1", "ticketscope--e2-s1--AC-2", "ticketscope--e2-s1--AC-3", "ticketscope--e2-s1--AC-4", "ticketscope--e2-s2--AC-1", "ticketscope--e2-s2--AC-2", "ticketscope--e2-s2--AC-3", "ticketscope--e2-s2--AC-4", "ticketscope--e2-s5--verify"]
- id: ticketscope--e2--R3
  kind: requirement
  requirement: "The eval runs on every PR as a required check. A Recall@10 or MRR@10 regression against the committed baseline blocks the merge, unless the same diff updates the baseline. It is met when a deliberately regressing PR fails the check, and passes once its diff updates the baseline."
  parent: "parent R7"
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md:33
  priority: P1
  priorityBasis: contributors
  contributors: ["ticketscope--e2-s2--AC-3", "ticketscope--e2-s3--AC-1", "ticketscope--e2-s3--AC-2", "ticketscope--e2-s3--AC-3", "ticketscope--e2-s3--AC-4", "ticketscope--e2-s3--AC-5", "ticketscope--e2-s5--verify"]
- id: ticketscope--e2--R4
  kind: requirement
  requirement: "The README results table is generated from CI output and committed as-is, whatever it shows. It is met when a check fails if the README table differs from the table rendered from the committed CI results."
  parent: "parent R7"
  source: _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md:34
  priority: P1
  priorityBasis: contributors
  contributors: ["ticketscope--e2-s4--AC-1", "ticketscope--e2-s4--AC-2", "ticketscope--e2-s4--AC-3", "ticketscope--e2-s4--AC-4", "ticketscope--e2-s5--verify"]
---

# Traceability Matrix & Gate Decision — Epic 2: Retrieval is scored on every PR and regressions block the merge

## Gate Decision: FAIL

**Rationale:** P0 coverage is 50% (required: 100%). 1 critical requirement(s) below FULL coverage. Overall FULL coverage is 25% (minimum 80%); P1 is 0% (minimum 80%, PASS target 90%).

**Date:** 2026-11-08. **Evaluator:** Claude Code / Master Test Architect. **Source:** `8d772e029c84d73ef4f325f024c90d63c8d7e590` (first trace of this epic; there is no previous trace).

This re-trace follows the fixes in commit `8d772e0`: the plan criteria now name the requirements they prove, story 2.5 covers R2 to R4, and a pin test replaces the two false `git diff` clauses. The tests were already there; the gate moved from 43% to 50% P0. It is not 100% because two R2 contributors, story 1 AC-4 and story 5 verify, depend on a CI run that no recorded live result establishes at this commit. Those two also hold R3 and R4 at PARTIAL.

## Have the gaps been closed?

The previous trace (same run key, replaced by this one) had 14 of 20 criteria FULL and all four requirements NONE. Now 16 of 20 are FULL, 2 PARTIAL and 2 NONE, and every criterion is linked, so there are no exception rows. Waiver W-001's remediation (this epic's Done-when line) is not yet closed.

## Coverage Summary

| Priority | Total | FULL | Coverage |
| --- | ---: | ---: | ---: |
| P0 | 2 | 1 | 50% |
| P1 | 2 | 0 | 0% |
| P2 | 0 | 0 | 100% |
| P3 | 0 | 0 | 100% |
| Overall | 4 | 1 | 25% |

Gate rows: 1 FULL, 3 PARTIAL, 0 NONE, 0 UNIT-ONLY. Criteria: 16 FULL, 2 PARTIAL, 2 NONE. Accepted evidence: 35 unique test declarations across 13 files. Sanity run at HEAD: `uv run pytest tests/unit` 893 passed, 17 skipped; `ruff check`, `pyright` and `lint-imports` clean (informational, not counted as evidence). Kind tests (`tests/eval/`) are accepted as static e2e evidence under `collection_mode: contract_static`; this trace did not run them.

Oracle: formal epic requirements R1 to R4 with requirement granularity (v7 epic with `R<n>` lines, no duplicate ids). Confidence is high: every criterion now names its requirements. Criterion priorities are inferred from `test-design-epic-2.md`'s coverage plan (story 2.5's row is P1). Requirement priorities come from their contributors (the highest criterion priority). Supporting artifacts: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md`. No NFR audit exists for epic 2 (`_bmad-output/test-artifacts/nfr/nfr-assessment-epic-1.md` is epic 1's). Live results: `live-verification-results.json` holds only epic 1 records, all recorded at `6400e5a` and so stale at `8d772e0`; none names an epic 2 criterion and none is counted.

## Requirement Oracle Mapping

| ID | Kind | Requirement | Priority | Coverage |
| --- | --- | --- | --- | --- |
| ticketscope--e2--R1 | requirement | Labelled duplicate pairs are derived deterministically from the pinned snapshot's in-subset duplicate links and committed per snapshot version. It is met when the committed pairs file regenerates byte-identical from the snapshot, with its pair counts reported for short and log-heavy queries. | P0 | FULL |
| ticketscope--e2--R2 | requirement | An eval job scores every available mode in the core registry through the real Postgres adapter as the read-only role. It reports Recall@1, Recall@5, Recall@10, MRR@10 and p95 latency, split short versus log-heavy. It is met when the job on kind scores keyword over the full pair set, and a newly registered mode is scored with no change to the job. | P0 | PARTIAL |
| ticketscope--e2--R3 | requirement | The eval runs on every PR as a required check. A Recall@10 or MRR@10 regression against the committed baseline blocks the merge, unless the same diff updates the baseline. It is met when a deliberately regressing PR fails the check, and passes once its diff updates the baseline. | P1 | PARTIAL |
| ticketscope--e2--R4 | requirement | The README results table is generated from CI output and committed as-is, whatever it shows. It is met when a check fails if the README table differs from the table rendered from the committed CI results. | P1 | PARTIAL |

## Criterion Status Changes Since Previous Trace

None: first trace of this epic.

## Detailed Mapping

### ticketscope--e2--R1 (P0, requirement): FULL

Labelled duplicate pairs are derived deterministically from the pinned snapshot's in-subset duplicate links and committed per snapshot version. It is met when the committed pairs file regenerates byte-identical from the snapshot, with its pair counts reported for short and log-heavy queries.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md:31`. Contributors:

- ticketscope--e2-s1--AC-5: FULL
- ticketscope--e2-s2--AC-5: FULL

Gaps: its only contributor is NONE, so the requirement is NONE.

### ticketscope--e2--R2 (P0, requirement): PARTIAL

An eval job scores every available mode in the core registry through the real Postgres adapter as the read-only role. It reports Recall@1, Recall@5, Recall@10, MRR@10 and p95 latency, split short versus log-heavy. It is met when the job on kind scores keyword over the full pair set, and a newly registered mode is scored with no change to the job.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md:32`. Contributors:

- ticketscope--e2-s1--AC-1: FULL
- ticketscope--e2-s1--AC-2: FULL
- ticketscope--e2-s1--AC-3: FULL
- ticketscope--e2-s1--AC-4: PARTIAL
- ticketscope--e2-s2--AC-1: FULL
- ticketscope--e2-s2--AC-2: FULL
- ticketscope--e2-s2--AC-3: FULL
- ticketscope--e2-s2--AC-4: FULL
- ticketscope--e2-s5--verify: PARTIAL

Gaps: its only contributor is NONE, so the requirement is NONE.

### ticketscope--e2--R3 (P1, requirement): PARTIAL

The eval runs on every PR as a required check. A Recall@10 or MRR@10 regression against the committed baseline blocks the merge, unless the same diff updates the baseline. It is met when a deliberately regressing PR fails the check, and passes once its diff updates the baseline.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md:33`. Contributors:

- ticketscope--e2-s2--AC-3: FULL
- ticketscope--e2-s3--AC-1: FULL
- ticketscope--e2-s3--AC-2: FULL
- ticketscope--e2-s3--AC-3: FULL
- ticketscope--e2-s3--AC-4: NONE
- ticketscope--e2-s3--AC-5: NONE
- ticketscope--e2-s5--verify: PARTIAL

Gaps: its only contributor is NONE, so the requirement is NONE.

### ticketscope--e2--R4 (P1, requirement): PARTIAL

The README results table is generated from CI output and committed as-is, whatever it shows. It is met when a check fails if the README table differs from the table rendered from the committed CI results.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md:34`. Contributors:

- ticketscope--e2-s4--AC-1: FULL
- ticketscope--e2-s4--AC-2: FULL
- ticketscope--e2-s4--AC-3: FULL
- ticketscope--e2-s4--AC-4: FULL
- ticketscope--e2-s5--verify: PARTIAL

Gaps: its only contributor is NONE, so the requirement is NONE.

#### ticketscope--e2-s1--AC-1 (P0): FULL

Given the oracle fixture, when the scaffold runs, then it passes (story 2.2 replaced the target-only scaffold with the cluster test on the same fixture), and the fixture still starts with the bytes its red commit `b7be713` wrote (R2).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:82`. Priority basis: inferred. Declared links: R2.

Tests:
- `tests/unit/test_eval_cluster_oracle.py:106` (unit) test_p0_ac1_cluster_metrics_match_the_oracle
- `tests/unit/test_eval_oracle_pinned.py:34` (unit) test_the_oracle_fixture_is_unchanged_since_its_red_commit

Assertions:
- `tests/unit/test_eval_cluster_oracle.py:106` (declaration), `tests/unit/test_eval_cluster_oracle.py:129` (every metric equals the shared oracle fixture's expected values)
- `tests/unit/test_eval_oracle_pinned.py:38` (the file keeps at least the bytes the red commit wrote), `tests/unit/test_eval_oracle_pinned.py:39` (and their SHA-256 matches the pin)

Story 2.2 replaced the target-only scaffold with the cluster test on the same `tests/eval_oracle.py`. The pin test replaces the `git diff` clause, which became false when 2.2 appended its oracle: it hashes the first 2,877 bytes (the `b7be713` content), so the fixture may grow but not be edited.

#### ticketscope--e2-s1--AC-2 (P0): FULL

Given a PR, when `eval.yml` runs, then the eval Job completes after load as `ticketscope_ro`, and the `reports-kind` artifact holds `eval-results.json` with keyword's Recall@10 and MRR@10 over 10,473 pairs and lineage equal to `corpus_meta` (R2).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:83`. Priority basis: inferred. Declared links: R2.

Tests:
- `tests/eval/test_eval_kind.py:45` (e2e) test_eval_job_completed_after_load
- `tests/eval/test_eval_kind.py:111` (e2e) test_lineage_equals_corpus_meta
- `tests/eval/test_eval_kind.py:121` (e2e) test_eval_job_reads_as_ticketscope_ro
- `tests/eval/test_eval_kind.py:75` (e2e) test_keyword_is_scored_on_clusters_split_by_kind
- `tests/unit/test_eval_workflow.py:28` (unit) test_eval_workflow_runs_on_pull_request_and_calls_kind_deploy_with_eval_enabled
- `tests/unit/test_chart_eval.py:41` (unit) test_eval_job_reads_the_database_as_ticketscope_ro_only
- `tests/unit/test_eval_main.py:74` (unit) test_results_line_carries_scores_lineage_pairs_file_and_wall_seconds

Assertions:
- `tests/eval/test_eval_kind.py:48` (Job has a Complete condition), `tests/eval/test_eval_kind.py:51` (load finished before the eval Job started)
- `tests/eval/test_eval_kind.py:128` (the Job's only secret reference is the read-only secret), `tests/eval/test_eval_kind.py:129` (that secret's username is `ticketscope_ro`)
- `tests/eval/test_eval_kind.py:80` (pairs scored are 10,164 short, 309 log-heavy, 10,473 overall), `tests/eval/test_eval_kind.py:87` (Recall@10 and MRR@10 are floats in range)
- `tests/eval/test_eval_kind.py:114` (lineage snapshot version equals `corpus_meta`), `tests/eval/test_eval_kind.py:115` (embedding model id), `tests/eval/test_eval_kind.py:116` (preprocessing version)
- `tests/unit/test_eval_workflow.py:30` (`eval.yml` runs on `pull_request`), `tests/unit/test_eval_workflow.py:31` (it calls `_kind-deploy.yml`), `tests/unit/test_eval_workflow.py:32` (eval enabled)
- `tests/unit/test_chart_eval.py:44` (chart wires only `ticketscope-db-ro`), `tests/unit/test_eval_main.py:83` (results line carries the lineage)

The kind tests assert the criterion at the level it states, against the deployed cluster. The criterion's "over 10,473 pairs" is asserted in its successor form (cluster relevance), which story 2.2 intentionally replaced.

#### ticketscope--e2-s1--AC-3 (P1): FULL

Given a step after the results are written fails, when the workflow ends, then the artifact is still uploaded (R2).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:84`. Priority basis: inferred. Declared links: R2.

Tests:
- `tests/unit/test_eval_workflow.py:58` (unit) test_reports_upload_runs_always_after_the_check

Assertions:
- `tests/unit/test_eval_workflow.py:62` (the upload step follows the Check step), `tests/unit/test_eval_workflow.py:64` (upload runs under `if: always()`), `tests/unit/test_eval_workflow.py:65` (it uploads `reports/`)
- `tests/unit/test_eval_workflow.py:96` (the gate runs after the eval pytest inside the Check step, so a gate failure is a failure after the results exist)

The workflow text establishes the mechanism the criterion relies on. No test fails a step on purpose and observes the upload.

#### ticketscope--e2-s1--AC-4 (P1): PARTIAL

Given the same PR, when `ci.yml` runs, then integrated-check passes (R2).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:85`. Priority basis: inferred. Declared links: R2.

Tests:
- `tests/unit/test_eval_workflow.py:68` (unit) test_ci_integrated_check_call_is_unchanged
- `tests/unit/test_eval_workflow.py:44` (unit) test_every_kind_deploy_input_but_check_has_a_default

Assertions:
- `tests/unit/test_eval_workflow.py:83` (the `integrated-check` call is byte-for-byte unchanged), `tests/unit/test_eval_workflow.py:84` (`ci.yml` does not mention `eval_enabled`)
- `tests/unit/test_eval_workflow.py:50` (every `_kind-deploy.yml` input but `check` has a default)

The static tests prove the call is unchanged and the new inputs are optional. They cannot show the job passes.

Gaps: No recorded run result for `integrated-check`. Informational only, not counted: `gh pr checks 31` reports `integrated-check / deploy` pass on PR #31.

#### ticketscope--e2-s1--AC-5 (P0): FULL

Given the pinned snapshot, when the pairs are regenerated, then the committed `eval/pairs/2026.11.1.jsonl` is byte-identical and the printed counts are 10,473 / 10,164 / 309 (R1).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md:86`. Priority basis: inferred. Declared links: R1.

Tests:
- `tests/eval/test_eval_kind.py:142` (e2e) test_pairs_regenerate_byte_identical_with_the_release_counts
- `tests/unit/test_pairs.py:120` (unit) test_pairs_jsonl_has_fixed_key_order_one_line_each_and_a_trailing_newline
- `tests/unit/test_pairs.py:40` (unit) test_one_pair_per_duplicate_issue_to_its_duplicate_target

Assertions:
- `tests/eval/test_eval_kind.py:159` (`derive_pairs.py --check` against the pinned Release asset exits 0), `tests/eval/test_eval_kind.py:160` (prints `10473 pairs: 10164 short, 309 log_heavy`)
- `tests/unit/test_pairs.py:122` (fixed key order, one line each, trailing newline), `tests/unit/test_pairs.py:43` (one pair per duplicate issue to its target)

The kind test is the criterion's own check, run on the pinned asset. The unit tests pin the determinism the regeneration depends on.

#### ticketscope--e2-s2--AC-1 (P0): FULL

Given the oracle fixture, when the cluster scaffold runs, then every metric short, log-heavy and overall equals `CLUSTER_EXPECTED` (overall differs from the mean of the kind means), a sibling counts as a hit, and the query never scores itself; the fixture still starts with the bytes its red commit `7ea485a` wrote (R2).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:75`. Priority basis: inferred. Declared links: R2.

Tests:
- `tests/unit/test_eval_cluster_oracle.py:106` (unit) test_p0_ac1_cluster_metrics_match_the_oracle
- `tests/unit/test_eval_oracle_pinned.py:34` (unit) test_the_oracle_fixture_is_unchanged_since_its_red_commit

Assertions:
- `tests/unit/test_eval_cluster_oracle.py:106` (declaration), `tests/unit/test_eval_cluster_oracle.py:120` (overall Recall@10 4/5: query 3's sibling at rank 4 is a hit)
- `tests/unit/test_eval_cluster_oracle.py:129` (every metric, short, log-heavy and overall, equals `CLUSTER_EXPECTED` within tolerance), `tests/unit/test_eval_cluster_oracle.py:130` (pair counts by kind), `tests/unit/test_eval_cluster_oracle.py:132` (first-member ranks)
- `tests/unit/test_eval_cluster_oracle.py:138` (every call carries `exclude == {query}`), `tests/unit/test_eval_cluster_oracle.py:148` (a self-ranked query scores 0 Recall@10), `tests/unit/test_eval_cluster_oracle.py:149` (and 0 MRR@10)
- `tests/unit/test_eval_oracle_pinned.py:38` (length of the `7ea485a` content kept), `tests/unit/test_eval_oracle_pinned.py:39` (its SHA-256 matches the pin)

The metric, sibling-hit, per-kind and self-exclusion clauses are established by the oracle test; the unchanged-fixture clause by the pin test.

#### ticketscope--e2-s2--AC-2 (P1): FULL

Given `modes.REGISTRY` replaced after import with a fake second mode, when `score` runs, then the mode appears in the results with no change to `jobs.eval`; an unavailable mode is named in `skipped_modes` (R2).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:76`. Priority basis: inferred. Declared links: R2.

Tests:
- `tests/unit/test_eval_main.py:215` (unit) test_a_mode_registered_after_import_is_scored_with_no_job_change
- `tests/unit/test_eval_main.py:207` (unit) test_unavailable_modes_are_skipped_and_named
- `tests/unit/test_eval_score_expanded.py:129` (unit) test_skipped_modes_are_listed_sorted
- `tests/unit/test_eval_cluster_oracle.py:106` (unit) test_p0_ac1_cluster_metrics_match_the_oracle

Assertions:
- `tests/unit/test_eval_main.py:219` (REGISTRY replaced after import with a second mode), `tests/unit/test_eval_main.py:221` (results hold `keyword` and `second`), `tests/unit/test_eval_main.py:222` (the new mode is scored)
- `tests/unit/test_eval_main.py:211` (an unavailable mode is absent from the results), `tests/unit/test_eval_main.py:212` (and named in `skipped_modes`), `tests/unit/test_eval_score_expanded.py:129` (skipped modes are listed sorted)
- `tests/unit/test_eval_cluster_oracle.py:112` (the oracle test also replaces REGISTRY after import)

#### ticketscope--e2-s2--AC-3 (P1): FULL

Given the same corpus scored twice, then the metrics and ranks are identical (R2, R3).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:77`. Priority basis: inferred. Declared links: R2, R3.

Tests:
- `tests/unit/test_eval_main.py:247` (unit) test_scoring_the_same_corpus_twice_gives_identical_metrics_and_ranks
- `tests/eval/test_postgres_ties.py:15` (integration) test_postgres_selects_the_same_lowest_numbers_across_a_tied_cutoff

Assertions:
- `tests/unit/test_eval_main.py:255` (two scorings give identical metrics and ranks)
- `tests/eval/test_postgres_ties.py:30` (three runs over 60 tied documents select the same ten lowest numbers; the adapter-level tie-break)

The unit test covers the scorer, the integration test covers the Postgres tie-break the epic's risk R-007 names.

#### ticketscope--e2-s2--AC-4 (P1): FULL

Given a PR, when `eval.yml` runs, then `reports-kind`'s `eval-results.json` holds, for keyword, every metric split short, log-heavy and overall, pair counts 10,164 / 309 / 10,473, each query's first-member rank (an independent recompute matches), and `wall_seconds`, which the job summary also shows (R2).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:78`. Priority basis: inferred. Declared links: R2.

Tests:
- `tests/eval/test_eval_kind.py:75` (e2e) test_keyword_is_scored_on_clusters_split_by_kind
- `tests/eval/test_eval_kind.py:97` (e2e) test_first_member_ranks_recompute_to_the_reported_metrics
- `tests/eval/test_eval_kind.py:164` (e2e) test_recorded_ranks_match_an_independent_second_retrieval_pass
- `tests/unit/test_eval_main.py:74` (unit) test_results_line_carries_scores_lineage_pairs_file_and_wall_seconds
- `tests/unit/test_eval_main.py:294` (unit) test_the_job_summary_shows_cost_pair_counts_and_metrics

Assertions:
- `tests/eval/test_eval_kind.py:77` (relevance is `cluster`), `tests/eval/test_eval_kind.py:80` (pair counts per kind), `tests/eval/test_eval_kind.py:89` (Recall@1 <= @5 <= @10), `tests/eval/test_eval_kind.py:91` (p95 present), `tests/eval/test_eval_kind.py:93` (`wall_seconds` > 0)
- `tests/eval/test_eval_kind.py:104` (first-member ranks cover every query), `tests/eval/test_eval_kind.py:107` (every metric recomputes from the ranks), `tests/eval/test_eval_kind.py:164` (a second retrieval pass through the adapter reproduces the ranks)
- `tests/unit/test_eval_main.py:89` (results line carries `wall_seconds`), `tests/unit/test_eval_main.py:300` (job summary shows `Wall seconds`), `tests/unit/test_eval_main.py:301` (pair counts per kind), `tests/unit/test_eval_main.py:302` (metrics)

#### ticketscope--e2-s2--AC-5 (P0): FULL

Given the pinned snapshot, when pairs regenerate, then the file is byte-identical and `derive_pairs.py` prints `10473 pairs: 10164 short, 309 log_heavy` (R1).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md:79`. Priority basis: inferred. Declared links: R1.

Tests:
- `tests/eval/test_eval_kind.py:142` (e2e) test_pairs_regenerate_byte_identical_with_the_release_counts
- `tests/unit/test_pairs.py:120` (unit) test_pairs_jsonl_has_fixed_key_order_one_line_each_and_a_trailing_newline

Assertions:
- `tests/eval/test_eval_kind.py:159` (exit 0 from `--check`), `tests/eval/test_eval_kind.py:160` (the printed line), `tests/unit/test_pairs.py:122` (fixed format)

Same evidence as story 1 AC-5; the criterion was restated by story 2.2.

#### ticketscope--e2-s3--AC-1 (P1): FULL

Given a PR that worsens keyword ranking, when eval runs, then the gate step fails with the metric named (R3).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:72`. Priority basis: inferred. Declared links: R3.

Tests:
- `tests/unit/test_eval_gate.py:54` (unit) test_log_heavy_recall_drop_of_0_006_fails_naming_mode_kind_metric
- `tests/unit/test_eval_gate.py:209` (unit) test_cli_fails_on_regression_and_writes_the_step_summary
- `tests/unit/test_eval_workflow.py:91` (unit) test_base_commit_is_fetched_and_the_gate_runs_after_the_eval_check

Assertions:
- `tests/unit/test_eval_gate.py:57` (a 0.006 drop yields one failure), `tests/unit/test_eval_gate.py:58` (it names the mode, kind and metric)
- `tests/unit/test_eval_gate.py:219` (the CLI exits 1 on a regression), `tests/unit/test_eval_gate.py:220` (the step summary names `recall@10`)
- `tests/unit/test_eval_workflow.py:96` (the gate runs after the eval check), `tests/unit/test_eval_workflow.py:107` (the base commit reaches the check)

The test design planned throwaway-PR runs as E2E evidence recorded in the plan; story 2.3's plan has an empty Implementation Notes section, so none is recorded.

#### ticketscope--e2-s3--AC-2 (P1): FULL

Given the same PR also updates `eval/baseline.json` to its run's results, then the gate passes (R3).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:73`. Priority basis: inferred. Declared links: R3.

Tests:
- `tests/unit/test_eval_gate.py:209` (unit) test_cli_fails_on_regression_and_writes_the_step_summary
- `tests/unit/test_eval_gate.py:89` (unit) test_any_drop_passes_when_baseline_changed_and_equals_run

Assertions:
- `tests/unit/test_eval_gate.py:224` (after the baseline is updated to the run's results the CLI exits 0), `tests/unit/test_eval_gate.py:91` (any drop passes when the changed baseline equals the run)

#### ticketscope--e2-s3--AC-3 (P1): FULL

Given a preprocessing-version change with no baseline update, then the gate fails with a lineage message (R3).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:74`. Priority basis: inferred. Declared links: R3.

Tests:
- `tests/unit/test_eval_gate.py:108` (unit) test_lineage_drift_fails_naming_the_field

Assertions:
- `tests/unit/test_eval_gate.py:111` (a changed `preprocessing_version` yields one failure), `tests/unit/test_eval_gate.py:112` (the failure names the field), `tests/unit/test_eval_gate.py:113` (the same change passes when the baseline is updated)

#### ticketscope--e2-s3--AC-4 (P2): NONE

Given `ruff`, `pyright`, `lint-imports` and `pytest tests/unit`, then all pass (R3).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:75`. Priority basis: inferred. Declared links: R3.

Tests: none.

No test asserts a tool outcome, and no run result is recorded as live evidence.

Gaps: Informational only, not counted: at HEAD this trace's sanity run gave `ruff check` clean, `pyright` 0 errors, `lint-imports` 7 kept 0 broken, and `pytest tests/unit` 893 passed, 17 skipped.

#### ticketscope--e2-s3--AC-5 (P1): NONE

Given the merged workflow, a person makes `eval` required in branch protection (checked by the person, R3).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md:76`. Priority basis: inferred. Declared links: R3.

Tests: none.

A human step in GitHub branch protection. No live record in `live-verification-results.json` or `live-verification-drafts.json` names it.

Gaps: Nothing establishes that `eval` is a required check on main.

#### ticketscope--e2-s4--AC-1 (P1): FULL

Given the committed `eval/baseline.json` and README, when `python3 scripts/render_readme_table.py --check` runs, then it exits 0, and `--write` leaves `git diff` empty (R4).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-readme-results-table-is-generated-from-ci-output-plan.md:69`. Priority basis: inferred. Declared links: R4.

Tests:
- `tests/unit/test_readme_table.py:67` (unit) test_committed_readme_equals_render_of_committed_baseline
- `tests/unit/test_readme_table.py:74` (unit) test_write_then_check_passes_and_write_is_idempotent
- `tests/unit/test_readme_table_expanded.py:23` (unit) test_cli_check_passes_on_committed_files_and_fails_on_drift

Assertions:
- `tests/unit/test_readme_table.py:70` (the committed README section equals the render of the committed baseline), `tests/unit/test_readme_table.py:71` (`main([])` exits 0)
- `tests/unit/test_readme_table.py:80` (a second `--write` exits 0), `tests/unit/test_readme_table.py:81` (and leaves the file unchanged)

#### ticketscope--e2-s4--AC-2 (P1): FULL

Given one digit of the README table changed by hand, when the check runs, then it exits 1 (R4).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-readme-results-table-is-generated-from-ci-output-plan.md:70`. Priority basis: inferred. Declared links: R4.

Tests:
- `tests/unit/test_readme_table.py:85` (unit) test_hand_edited_number_fails_and_names_the_fix

Assertions:
- `tests/unit/test_readme_table.py:91` (one digit changed), `tests/unit/test_readme_table.py:92` (exit 1), `tests/unit/test_readme_table.py:94` (the message names the fix)

#### ticketscope--e2-s4--AC-3 (P1): FULL

Given a README without the generated-section markers, when the check runs, then it exits 1 (R4).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-readme-results-table-is-generated-from-ci-output-plan.md:71`. Priority basis: inferred. Declared links: R4.

Tests:
- `tests/unit/test_readme_table.py:108` (unit) test_marker_faults_fail_check_and_write

Assertions:
- `tests/unit/test_readme_table.py:110` (six marker faults all exit 1 on `--check`), `tests/unit/test_readme_table.py:112` (the README is not rewritten)

#### ticketscope--e2-s4--AC-4 (P1): FULL

Given `ci.yml`, when parsed as text, then the `checks` job runs the check command (R4).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-readme-results-table-is-generated-from-ci-output-plan.md:72`. Priority basis: inferred. Declared links: R4.

Tests:
- `tests/unit/test_readme_table.py:182` (unit) test_ci_checks_job_runs_the_readme_check

Assertions:
- `tests/unit/test_readme_table.py:187` (the `checks` job runs `python3 scripts/render_readme_table.py --check`)

#### ticketscope--e2-s5--verify (P1): PARTIAL

On a PR the eval check passes with eval/baseline.json unchanged, ci.yml and its integrated-check pass, import-linter keeps every contract, and tests/ has no time.sleep calls, enforced by a lint rule or a test (R2, R3, R4).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/tickets.toml:61`. Priority basis: inferred. Declared links: R2, R3, R4.

Tests:
- `tests/unit/test_no_sleep_in_tests.py:37` (unit) test_tests_never_call_time_sleep

Assertions:
- `tests/unit/test_no_sleep_in_tests.py:37` (declaration), `tests/unit/test_no_sleep_in_tests.py:43` (no `time.sleep` call anywhere in `tests/`)

Story 2.5 has no plan file; its single criterion is the entry's `verify` line, and its `covers` is now R2, R3, R4. The no-sleep clause is enforced by a test.

Gaps: The clauses on the eval check, an unchanged `eval/baseline.json`, `integrated-check` and import-linter have no test or recorded result. Informational only, not counted: `git diff d2313e9 3fe91b2 -- eval/baseline.json` is empty, `lint-imports` keeps 7 of 7 contracts, and `gh pr checks 31` shows `eval / deploy`, `integrated-check / deploy` and `checks` passing.

### Rejected evidence

None. The five kind tests the previous trace rejected now cite the criteria they establish.

- `tests/eval/test_eval_kind.py:45` (e2e) test_eval_job_completed_after_load claims `ticketscope--e2-s1--AC-1`: Carries `@pytest.mark.criterion("ticketscope--e2-s1--AC-1")`, but story 1's AC-1 is the oracle-fixture diff check by position in the plan. Its assertions establish the Job, lineage, role, secret or pair-regeneration clauses of AC-2 and AC-5, where it is mapped as evidence. It asserts nothing about the oracle fixture.
- `tests/eval/test_eval_kind.py:111` (e2e) test_lineage_equals_corpus_meta claims `ticketscope--e2-s1--AC-1`: Carries `@pytest.mark.criterion("ticketscope--e2-s1--AC-1")`, but story 1's AC-1 is the oracle-fixture diff check by position in the plan. Its assertions establish the Job, lineage, role, secret or pair-regeneration clauses of AC-2 and AC-5, where it is mapped as evidence. It asserts nothing about the oracle fixture.
- `tests/eval/test_eval_kind.py:121` (e2e) test_eval_job_reads_as_ticketscope_ro claims `ticketscope--e2-s1--AC-1`: Carries `@pytest.mark.criterion("ticketscope--e2-s1--AC-1")`, but story 1's AC-1 is the oracle-fixture diff check by position in the plan. Its assertions establish the Job, lineage, role, secret or pair-regeneration clauses of AC-2 and AC-5, where it is mapped as evidence. It asserts nothing about the oracle fixture.
- `tests/eval/test_eval_kind.py:133` (e2e) test_uploaded_results_hold_no_secret_value claims `ticketscope--e2-s1--AC-1`: Carries `@pytest.mark.criterion("ticketscope--e2-s1--AC-1")`, but story 1's AC-1 is the oracle-fixture diff check by position in the plan. Its assertions establish the Job, lineage, role, secret or pair-regeneration clauses of AC-2 and AC-5, where it is mapped as evidence. It asserts nothing about the oracle fixture.
- `tests/eval/test_eval_kind.py:142` (e2e) test_pairs_regenerate_byte_identical_with_the_release_counts claims `ticketscope--e2-s1--AC-1`: Carries `@pytest.mark.criterion("ticketscope--e2-s1--AC-1")`, but story 1's AC-1 is the oracle-fixture diff check by position in the plan. Its assertions establish the Job, lineage, role, secret or pair-regeneration clauses of AC-2 and AC-5, where it is mapped as evidence. It asserts nothing about the oracle fixture.

## Invalid and Unlinked Criteria

None. All 20 criteria name at least one requirement, and every named id exists in the epic.

The 20 criteria contribute as follows. R1: s1 AC-5, s2 AC-5. R2: s1 AC-1 to AC-4, s2 AC-1 to AC-4 and s5 verify. R3: s2 AC-3, s3 AC-1 to AC-5, s5 verify. R4: s4 AC-1 to AC-4, s5 verify.

## Gaps & Recommendations

Critical (P0 below FULL): `ticketscope--e2--R2`.

High (P1 NONE): none. Medium and low: none. Below FULL but not NONE: `ticketscope--e2--R2`, `ticketscope--e2--R3`, `ticketscope--e2--R4`.

- **URGENT** Run CI on this branch and record the results at the commit under trace. Story 1 AC-4 (`integrated-check` passes) and story 5's verify (the eval check and `integrated-check` pass, `eval/baseline.json` unchanged, import-linter keeps every contract) are the only R2 contributors below FULL, so they are what holds P0 at 50%. Their static evidence is complete; what is missing is a recorded run. The live results must carry the commit the trace reads (`git rev-parse HEAD`), so record them before committing the trace outputs.
- **HIGH** Record story 3 AC-4 (ruff, pyright, lint-imports and unit pytest pass) and AC-5 (`eval / deploy` is a required check) the same way. Branch protection on main already lists `checks`, `integrated-check / deploy` and `eval / deploy` as required contexts (read with `gh api repos/Dillon-Based/ticketscope/branches/main/protection`), which is the observation AC-5 needs. These hold R3 at PARTIAL, a P1 row.
- **MEDIUM** Story 5 is also a contributor to R3 and R4, so its recorded result lifts those rows to FULL together with R2.
- **LOW** Waiver W-001's remediation (epic 2 Done-when line) is still open: a fresh epic 1 trace does not yet honour the six superseded criteria. Check it at epic closure; owner Dillon.

## Waiver Register Review

`gate-waivers.md`: 1 filed, 1 valid, 0 invalid. Rule 6: the derived decision above stays the one Rules 1 to 5 produced; a waiver is never applied by this workflow.

- **W-001** (Retired GitHub-era criteria of stories 1.3, 1.4 and 1.14), covers 6 epic 1 criteria (highest P0): VALID. It covers no row in this epic's gate, so it cannot change this decision. Its remediation target is this epic: the Done-when line says a fresh epic 1 trace honours the six criteria, and that is still open.

## Next Actions

1. Run CI on this branch (open the PR; `ci.yml` also has `workflow_dispatch`) so `integrated-check` and `eval / deploy` run at the final commit.
2. Record live results at that commit for story 1 AC-4 and story 5's verify (R2, P0), and for story 3 AC-4 and AC-5 (R3, whose branch protection already lists `eval / deploy`, `integrated-check / deploy` and `checks`). Then re-run `/bmad-tea-trace` for epic 2.
3. Closing R2 takes both records: s1 AC-4 and s5 each hold R2 at PARTIAL while unrecorded.
4. Close W-001's remediation at epic closure, then re-trace epic 1.

### Requirement Aggregation

```json
{
  "criterionMatrix": [
    {
      "id": "ticketscope--e2-s1--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s1--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s1--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s1--AC-4",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e2-s1--AC-5",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s2--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s2--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s2--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s2--AC-4",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s2--AC-5",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s3--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s3--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s3--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s3--AC-4",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e2-s3--AC-5",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e2-s4--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s4--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s4--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s4--AC-4",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e2-s5--verify",
      "coverage": "PARTIAL"
    }
  ],
  "traceabilityMatrix": [
    {
      "id": "ticketscope--e2--R1",
      "kind": "requirement",
      "coverage": "FULL",
      "contributors": [
        {
          "id": "ticketscope--e2-s1--AC-5",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s2--AC-5",
          "coverage": "FULL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e2--R2",
      "kind": "requirement",
      "coverage": "PARTIAL",
      "contributors": [
        {
          "id": "ticketscope--e2-s1--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s1--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s1--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s1--AC-4",
          "coverage": "PARTIAL"
        },
        {
          "id": "ticketscope--e2-s2--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s2--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s2--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s2--AC-4",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s5--verify",
          "coverage": "PARTIAL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e2--R3",
      "kind": "requirement",
      "coverage": "PARTIAL",
      "contributors": [
        {
          "id": "ticketscope--e2-s2--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s3--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s3--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s3--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s3--AC-4",
          "coverage": "NONE"
        },
        {
          "id": "ticketscope--e2-s3--AC-5",
          "coverage": "NONE"
        },
        {
          "id": "ticketscope--e2-s5--verify",
          "coverage": "PARTIAL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e2--R4",
      "kind": "requirement",
      "coverage": "PARTIAL",
      "contributors": [
        {
          "id": "ticketscope--e2-s4--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s4--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s4--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s4--AC-4",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e2-s5--verify",
          "coverage": "PARTIAL"
        }
      ],
      "missingBehaviors": []
    }
  ]
}
```

### Live Verification Results

```json
{
  "liveManifestHeader": {
    "present": true,
    "results_file": "_bmad-output/test-artifacts/live-verification-results.json",
    "source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
    "observed_at": "2026-11-07T21:27:27Z",
    "producer": "GitHub Actions ci run 42415340129 (workflow_dispatch, scripts/live_results.py) + local kind runs of scripts/fault-inject.sh and scripts/v1-parity.sh at the same commit (Claude Code); author-confirmed manual and document checks (user, 2026-11-07)",
    "read_error": "",
    "current_source_sha": "8d772e029c84d73ef4f325f024c90d63c8d7e590"
  },
  "liveRecords": [
    {
      "id": "ticketscope--e1-LIVE-001",
      "requirement_id": "ticketscope--e1-s1--AC-1",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-002",
      "requirement_id": "ticketscope--e1-s1--AC-2",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-003",
      "requirement_id": "ticketscope--e1-s1--AC-4",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-004",
      "requirement_id": "ticketscope--e1-s10--AC-2",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-005",
      "requirement_id": "ticketscope--e1-s10--AC-3",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-006",
      "requirement_id": "ticketscope--e1-s10--AC-4",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-007",
      "requirement_id": "ticketscope--e1-s11--AC-2",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-008",
      "requirement_id": "ticketscope--e1-s11--AC-3",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-009",
      "requirement_id": "ticketscope--e1-s12--AC-1",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-010",
      "requirement_id": "ticketscope--e1-s12--AC-2",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-011",
      "requirement_id": "ticketscope--e1-s12--AC-3",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-012",
      "requirement_id": "ticketscope--e1-s12--AC-4",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-013",
      "requirement_id": "ticketscope--e1-s13--AC-3",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-014",
      "requirement_id": "ticketscope--e1-s13--AC-4",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-015",
      "requirement_id": "ticketscope--e1-s2--verify",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-016",
      "requirement_id": "ticketscope--e1-s5--AC-5",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-017",
      "requirement_id": "ticketscope--e1-s6--AC-3",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-018",
      "requirement_id": "ticketscope--e1-s7--AC-3",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-019",
      "requirement_id": "ticketscope--e1-s8--AC-1",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-020",
      "requirement_id": "ticketscope--e1-s9--AC-2",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-021",
      "requirement_id": "ticketscope--e1-s9--AC-3",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    },
    {
      "id": "ticketscope--e1-LIVE-022",
      "requirement_id": "ticketscope--e1-s9--AC-4",
      "status": "pass",
      "disposition": "stale",
      "recorded_source_sha": "6400e5ac8e3bb4cadeea8061a5581c33b2b45036",
      "note": "recorded for epic 1, not in this oracle"
    }
  ]
}
```
