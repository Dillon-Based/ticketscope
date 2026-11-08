---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-08'
runScope: 'epic'
runKey: 'epic-2'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline-retrospective.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md
  - src/ticketscope/core/modes.py
  - src/ticketscope/core/ports.py
  - src/ticketscope/core/snapshot.py
  - src/ticketscope/core/derive.py
  - src/ticketscope/adapters/postgres.py
  - src/ticketscope/jobs/ingest/jira.py
  - deploy/charts/ticketscope/templates/jobs.yaml
  - deploy/charts/ticketscope/values.yaml
  - .github/workflows/ci.yml
  - .github/workflows/_kind-deploy.yml
  - scripts/kind-up.sh
  - tests/waiting.py
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/nfr-criteria.md
---

# Test Design: Epic 2 - Retrieval is scored on every PR and regressions block the merge

**Date:** 2026-11-08
**Author:** Dillon
**Status:** Draft

Epic slug: `epic-eval-gate`. Epic requirements R1–R4 (initiative R6, R7). Stories 2.1 to 2.5 from `tickets/tickets.toml`, one lane.

---

## Executive Summary

**Scope:** full test design for Epic 2, against the refined epic (`refined: true`), the adopted architecture spine (AD-7, AD-12, AD-13, AD-17, AD-19, AD-21, AD-22, AD-26) and the five approved entries in `tickets/tickets.toml`. Every coverage row cites the epic R ids it proves, so the end-of-epic trace can link criteria to requirements (epic-search-baseline retro, G1).

No epic 2 code exists yet. `eval/` holds only epic 1's `golden-queries.json`. Every scenario below is planned, and none has run. The plan follows the epic's recorded sequence: story 2.1 scores against the linked target only, and story 2.2 replaces that with cluster relevance (epic Notes, Decision 2026-11-08). Section "Independent Oracles" names, for each metric, a check that does not come from the code under test.

**Risk Summary:**

- Total risks: 8
- High-priority risks (≥6): 3 (R-005 at 9, R-001 at 6, R-003 at 6)
- Critical categories: DATA (silent metric errors; pair derivation), BUS (the gate fails to block)

**Coverage Summary:**

- P0 scenarios: 26 (~16–28 hours)
- P1 scenarios: 59 (~25–45 hours)
- P2/P3 scenarios: 4 (~2–4 hours)
- **Total effort**: ~43–77 hours (~1–2 weeks)

---

## Not in Scope

| Item | Reasoning | Mitigation |
| ---- | --------- | ---------- |
| **Dense and hybrid modes** | Owned by epic-hybrid-retrieval; this epic only scores them (epic Boundaries). | The mode-pickup row (R-002) registers a fake second mode, so epic 3's modes are scored with no change to `jobs.eval`. |
| **A target score** | "There is no target score: the gate blocks regressions, not misses" (epic Boundaries). | No test asserts a minimum Recall@k or MRR@10. The P0 oracle rows assert that the numbers are computed correctly, not that they are high. |
| **Publishing the README** | Epic-reviewer-package publishes the table (story 2.4 description). | Story 2.4's render check keeps the committed table equal to the render from `eval/baseline.json`. |
| **Waiver W-001 remediation** | A Done when line made "as a ticket-tree and TEA tooling change outside the build loop, not a product story" (epic Notes, Decision 2026-11-08). | Listed as an Exit Criterion, checked at epic closure by a fresh epic 1 trace; owner Dillon. No coverage row, because no story owns it. |
| **The eval Job on EKS** | The Job is rendered only when `eval.enabled` is set, which is in CI (AD-22). | Chart render tests keep it off by default. |

---

## Risk Assessment

Sources were read in this order: the epic file, `tickets.toml`, the spine, epic 1's test design and retrospective, then the code named in the inputs. Each risk opens with the source's own words, followed by the failure consequence. IDs follow the order in which each risk's statement first appears in the epic file (R1 at line 31 through the Workflow constraint at line 45).

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R-001 | DATA | "Labelled duplicate pairs are derived deterministically ... met when the committed pairs file regenerates byte-identical from the snapshot" (epic R1; Constraints, Determinism). Two sources word the pair rule differently. The epic's Queries constraint and story 2.1 say "one query per in-subset duplicate link". AD-26 and ingest's `report()` count one pair per duplicate issue, through `core.duplicate_target`; `report()` produced the published 10,473 / 10,164 / 309. A per-link reading gives a different pair set whenever a duplicate issue carries two in-subset links. Unsorted output or an unordered set gives a different byte stream on each run. Consequence: every metric is computed on the wrong ground truth, or the committed file churns and the baseline with it. | 2 | 3 | 6 | Regenerate from the pinned asset and compare the SHA-256 with the committed file. Pin the counts to the Release `snapshot-2026.11.1` notes, which a different code path (ingest `report()`) produced. Unit-test the AD-26 rule on two-link issues. Clarification C-1 goes to the PO. | Dillon; story 2.1 | Story 2.1 |
| R-003 | BUS | "The gate (story 3) is the least certain story" (epic Notes, Decision 2026-11-08), and "Making it a required check is a person's step in GitHub branch protection" (Constraints, Workflow). Mechanisms: (a) "unless the same diff updates the baseline" needs the PR base commit, and `actions/checkout` fetches depth 1 by default; (b) 0.005 compared in binary floating point, where 0.400 − 0.395 = 0.0050000000000000044 > 0.005; (c) keyword's embedding model id is "none", and null, `"none"` and `""` can compare unequal; (d) an off-by-one at the 199/200 kind floor; (e) branch protection never set. Consequence: a regressing PR merges, or a good PR is blocked. | 3 | 2 | 6 | Unit decision table at every boundary; an Integration test of diff detection on a temporary git repo; throwaway PRs on GitHub for the four story 2.3 verify cases; the required-check setting confirmed by a person. | Dillon; story 2.3 | Story 2.3 |
| R-005 | DATA | "A query's relevant set is its duplicate cluster ... minus the query itself. Recall@k counts a hit when any member is in the top k. MRR@10 uses the first member's rank, and 0 past 10" (Constraints, Hit definition). "Story 1 is likely over 800 added lines. It is flagged for the independent review" (epic Notes, Decision 2026-11-08). In epic 1, self-review in large stories missed test defects (retro Z4). The scoring code is the thing under test, and the session that writes it also writes its tests, so both can share one wrong reading: recall as the fraction of the cluster found, overall as the mean of the two kind means, the query counted as relevant, MRR not zeroed past 10, the wrong cluster edges, or story 2.1's target-only relevance left in a code path after story 2.2. Consequence: wrong numbers become `eval/baseline.json`, the README table and the reference every later PR is gated against. The gate cannot see the error, because it compares the code with itself. | 3 | 3 | 9 | Independent oracles (section below): a hand-computed fixture with exact fractions, committed by a red-mode session before each build; a third-party IR library cross-check; per-query ranks in the artifact, recomputed by a separate script. The independent review on story 2.1 checks that the oracle fixture is unchanged since its red commit. | Dillon; stories 2.1 and 2.2 | Fixture before story 2.1's build; cluster oracle before story 2.2's build |

Score rationale:

- **R-001:** probability 2, because the published counts give a strong check, but the two wordings disagree in the sources today. Impact 3, because wrong ground truth corrupts every metric.
- **R-003:** probability 3, because the epic itself calls the gate the least certain story and five separate mechanisms can break it. Impact 2, because the brief's cut list already accepts losing the blocking check: "A cut drops only the required merge check (R7)" (epic Boundaries). The artifact still reports the scores to a reviewer.
- **R-005:** probability 3, because six independent definitional choices can each slip, and epic 1's evidence shows that self-review missed defects in stories of this size. Impact 3, because wrong scores are published and then enforced, and R6, the part that survives a cut, is exactly these numbers.

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-002 | TECH | "A newly registered mode is scored with no change to the job" (epic R2); AD-19 prevents "eval hard-coding modes". `core.modes.REGISTRY` is a read-only `MappingProxyType`, so a test can register a fake mode only by replacing the module attribute. If `jobs.eval` binds the registry at import, or names `keyword`, a test that patches `jobs.eval`'s own reference still passes while epic 3's dense mode goes unscored. A mode whose `available` is false and is skipped silently hides a missing mode. | 2 | 2 | 4 | The fake-mode test patches `ticketscope.core.modes.REGISTRY` after `jobs.eval` is imported. The unavailable mode is named in the results. | Story 2.2 |
| R-004 | BUS | "The README results table is generated from CI output and committed as-is" (epic R4). AD-12 says it is "never edited by hand". The README is rendered from "the committed `eval/baseline.json`, which is the CI results artifact committed by a baseline update" (epic Notes, Decision). Nothing checks that a committed `baseline.json` came from a CI run: any change to it passes the gate, and the README check compares the README against a render of that same file. A check that finds no generated-section markers can also pass on an empty comparison. Consequence: the README shows numbers no CI run produced. | 2 | 2 | 4 | Story 2.4's render check, with the missing-marker case. Proposed for story 2.3: a changed `baseline.json` must equal this run's results within the tolerance. | Stories 2.4 and 2.3 |
| R-006 | PERF | "The full set is scored on every PR" (Constraints, Queries); story 2.2 "records its wall-clock cost on kind so the full-set decision can be revisited". Each run is 10,473 queries, each a `get_issue` and a `keyword_search`, and `PostgresCorpusStore` opens one connection per call, which makes about 21,000 connections. `_kind-deploy.yml` has `timeout-minutes: 45`, and that includes kind-up. The run time is UNKNOWN. Consequence: slow feedback on every PR, or a required check that times out. | 2 | 2 | 4 | Story 2.2 records the Job's wall clock in the artifact and the job summary. Set the Job's `activeDeadlineSeconds` and the workflow timeout from that record. | Story 2.2 |
| R-007 | TECH | "p95 latency is reported and never gated" (Constraints, Metrics; AD-12 prevents "flaky latency blocks"). "Gate tolerance: 0.005 absolute, per metric, per mode, per ticket kind" (Constraints). "The log-heavy margin is thin" (epic Notes). With 309 log-heavy queries, one flipped query moves a log-heavy metric by 1/309 ≈ 0.0032, and two move it by 0.0065, which exceeds the tolerance. The adapter's inner `ORDER BY score LIMIT k` has no tie-break (`adapters/postgres.py`, `_KEYWORD_SQL`), so BM25 ties at the k-th score can change which issues are returned from run to run. Consequence: the required check flaps on unchanged code. | 2 | 2 | 4 | An Integration test with planted BM25 ties shows that two runs return identical top-k lists. Proposed for story 2.2's verify: two runs give identical metrics. | Story 2.2 |
| R-008 | OPS | "`eval.yml` runs on PRs through `_kind-deploy.yml`, then the eval Job in the `ticketscope` release, then the gate and a results artifact" (Constraints, Workflow). AD-22 says the Job is "rendered only when `eval.enabled` is set", and AD-7 says eval connects as `ticketscope_ro`. Story 2.1 says "ci.yml's integrated-check keeps passing on the changed reusable workflow". Mechanisms: the Job also renders in ci.yml's cluster; it runs as the owner role; it scores before load has finished; its results never reach `reports/`, so they are lost when the cluster is torn down; a new required input on `_kind-deploy.yml` breaks ci.yml's call. | 2 | 2 | 4 | A kind check of the Job's role, its ordering after load and the artifact, including a forced failure; chart render tests; a workflow parse test. | Story 2.1 |

### Low-Priority Risks (Score 1-2)

No low-priority risks are registered.

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |

### Clarifications for the PO (not scored)

The sources are silent or disagree on these points. This plan tests the stated assumption, and the "Proposed Story Updates" section carries the wording to the PO.

- **C-1, pair rule.** The epic's Queries constraint and story 2.1 say "one pair per in-subset duplicate link". AD-26 and ingest `report()` say one pair per duplicate issue, through `core.duplicate_target`. The published 10,473 count comes from the AD-26 rule. *Assumption:* AD-26 binds, and the pair count must equal 10,473.
- **C-2, cluster edges.** The sources do not say whether "the connected component over in-subset duplicate links" uses every in-subset `duplicate_links` entry of every issue, in both directions, or only the pair edges. The two readings differ for a duplicate issue linked to two targets. *Assumption:* every in-subset duplicate link, in both directions, as the Hit definition's wording reads.
- **C-3, mode-set changes.** The sources do not say what the gate does when a baselined mode is missing from the run (for example, it became unavailable), or when the run has a mode the baseline lacks (epic 3's first dense PR). *Assumption:* a missing gated mode fails unless the baseline is updated; a new mode passes and is reported.
- **C-4, tolerance edge.** "Within 0.005 absolute" is read as inclusive: a drop of exactly 0.005 passes.
- **C-5, README number format.** The rounding and precision of README numbers are not stated. The render check only needs the format to be deterministic.

### Risk Category Legend

- **TECH**: Technical/Architecture (flaws, integration, scalability)
- **SEC**: Security (access controls, auth, data exposure)
- **PERF**: Performance (SLA violations, degradation, resource limits)
- **DATA**: Data Integrity (loss, corruption, inconsistency)
- **BUS**: Business Impact (UX harm, logic errors, revenue)
- **OPS**: Operations (deployment, config, monitoring)

---

## NFR Planning

**Purpose:** Capture epic-specific NFR thresholds, planned validation, and evidence expected for later `nfr-assess`. This is not a final evidence audit.

| NFR Category | Requirement / Threshold | Risk Link | Planned Validation | Evidence Needed |
| ------------ | ----------------------- | --------- | ------------------ | --------------- |
| Security | Eval connects as `ticketscope_ro` through the existing read-only Secret (AD-7, story 2.1). Eval pairs carry no person identifiers or unmasked text (Provenance convention). | R-008 | Unit: the chart's eval Job takes its database env from `ticketscope-db-ro` only. E2E: the run succeeds as that role, and the artifact contains no Secret value. Unit: every pairs-file line holds only the agreed keys. | Chart render test report; `eval.yml` job log; artifact |
| Performance | p95 retrieval latency is reported and never gated (AD-12). The eval run's wall-clock cost on kind is recorded (story 2.2). Run-time budget: UNKNOWN. `_kind-deploy.yml` caps the whole job at 45 minutes. | R-006 | E2E: the artifact and the job summary carry p95 per mode and kind, and the Job's wall clock. Unit: the gate passes when p95 grows 100 times. | Results artifact; job summary |
| Reliability | Pairs regenerate byte-identical (R1). The gate is reproducible on unchanged code (tolerance 0.005; R3). The artifact survives cluster teardown (AD-17). | R-001, R-007, R-008 | Integration: SHA-256 regeneration; two ranking runs with planted ties. E2E: the artifact is uploaded when a later step fails. | CI test report; `eval.yml` run with the forced failure |
| Maintainability | New modes are scored with no job change (R2, AD-19). import-linter keeps the AD-1 layers with `jobs.eval` added. No sleep-based polling in tests (epic 1 test review, G3). | R-002 | Unit: the fake-mode test. CI: `lint-imports`. Unit: a guard against `time.sleep` in `tests/`. | CI test report |

**Unknown thresholds:**

- the eval run's time budget on kind;
- the Job's `activeDeadlineSeconds`;
- whether eval runs as a Helm hook or is started by `eval.yml` (story 2.1 allows either);
- the README number format (C-5).

Story 2.2's first recorded run sets the first two.

---

## Independent Oracles

Risk R-005 exists because a scorer and the tests written in the same session can agree on a wrong answer. Each metric therefore has a reference value that does not come from `jobs.eval`.

**Protocol:**

1. Before story 2.1's build, a `/bmad-tea-automate` red-mode session commits the synthetic fixture and its target-only expected values. Before story 2.2's build, it commits the cluster expected values. The build session does not author them.
2. Expected values are exact fractions (`fractions.Fraction`). They are compared to the scorer's floats within 1e-9.
3. The independent review on story 2.1 (flagged at over 800 lines) checks that the fixture's expected values are unchanged since the red commit. Any change in a later story's diff is a review finding.

**Synthetic fixture** (issue numbers; every link in the "duplicates" direction from the duplicate side, mirrored as "duplicated_by" on the target):

- Links 2→1 and 3→1 form cluster {1, 2, 3}. Link 5→4 forms {4, 5}. Link 7→6 forms {6, 7}. Link 9→8 forms {8, 9}.
- Queries 2, 3 and 5 are `short`. Queries 7 and 9 are `log_heavy`. Issues 100 and up are fillers in no cluster.
- Scripted rankings, as returned after exclusion. Rank 11 means "not in the top 10":

| Query | Kind | Linked target, rank | First cluster member, rank | Why it is in the fixture |
| ----- | ---- | ------------------- | -------------------------- | ------------------------ |
| 2 | short | 1, rank 3 | sibling 3, rank 2 | A sibling ranks above the target |
| 3 | short | 1, rank 11 | sibling 2, rank 4 | A miss under target-only, a hit under cluster relevance |
| 5 | short | 4, rank 1 | 4, rank 1 | Plain hit at rank 1 |
| 7 | log_heavy | 6, rank 10 | 6, rank 10 | MRR boundary: 1/10 |
| 9 | log_heavy | 8, rank 11 | 8, rank 11 | MRR is 0 past 10 |

**Expected values:**

| Metric | Oracle | Story 2.1, target-only (overall) | Story 2.2, cluster: short | Story 2.2, cluster: log-heavy | Story 2.2, cluster: overall |
| ------ | ------ | -------------------------------- | ------------------------- | ----------------------------- | --------------------------- |
| Recall@1 | Hand-computed hit rate | not reported | 1/3 | 0 | 1/5 |
| Recall@5 | Hand-computed hit rate | not reported | 1 | 0 | 3/5 |
| Recall@10 | Hand-computed hit rate | 3/5 | 1 | 1/2 | 4/5 |
| MRR@10 | Hand-computed, first member's rank, 0 past 10 | 43/150 | 7/12 | 1/20 | 37/100 |

Each common mistake gives a different, detectable value:

- **Mean of the two kind means as "overall".** Gives R@1 1/6, R@5 1/2, R@10 3/4, MRR@10 19/60.
- **Recall as the fraction of the cluster found.** Gives a short R@5 of 5/6, because query 3 has only sibling 2 in its top 5.
- **Target-only relevance left in place after story 2.2.** Gives an overall R@10 of 3/5 instead of 4/5.

**Other oracles:**

| What is checked | Independent oracle | Row |
| --------------- | ------------------ | --- |
| A sibling counts as a hit | Query 3: under cluster relevance, sibling 2 at rank 4 is a hit, although the linked target is at rank 11 | P0 cluster row (2.2) |
| The query never scores itself | Metric-level case: query 2's ranking holds 2 itself at rank 1 and no other member in the top 10. The result is a miss (R@10 0, RR 0). Separately, a spy retriever records `exclude == {query}` on every call | P0 cluster row (2.2); P0 interim row (2.1) |
| Per-kind split | The table above, with unequal kind sizes (3 short and 2 log-heavy), so the overall value differs from the mean of the two kind means | P0 cluster row (2.2) |
| Cluster membership | Hand-listed components: {1,2,3}, {4,5}, {6,7}, {8,9}, and the chain 13→14→15 as one cluster; a link to an issue outside the subset adds no member | P0 cluster row (2.2) |
| The same metrics from a second implementation | A third-party IR metrics library (hit rate at k and MRR at 10, for example `ranx`) scores the same scripted run. It is a dev-only dependency (proposed) | P0 cluster row (2.2) |
| Metrics on the real run | The artifact carries each query's first-member rank (proposed); a separate script recomputes every aggregate from those ranks | P1 story 2.2 kind row |
| Pair counts | Release `snapshot-2026.11.1` notes, written by ingest `report()` in epic 1: 10,473 total, 10,164 short, 309 log-heavy | P0 pairs row (2.1) |
| Byte-identical pairs | The SHA-256 of the committed `eval/pairs/2026.11.1.jsonl` | P0 pairs row (2.1) |
| Lineage | The `corpus_meta` row, read separately on the cluster | P0 kind row (2.1) |
| Gate decisions | A hand-written decision table at every boundary | P1 gate row (2.3) |
| README table | A render of the committed `baseline.json`, plus a hand-edited copy | P1 README row (2.4) |

---

## Entry Criteria

- [x] Architecture spine adopted (AD-1 to AD-26)
- [x] Epic refined and its 5 entries planned
- [x] Kind threshold settled at 3; 309 log-heavy pairs, above the floor of 200 (epic Notes, 2026-11-08)
- [ ] PR #20 merged, so stories land through a branch and a PR each (epic Notes, Decision 2026-11-08)
- [ ] C-1 and C-2 answered by the PO, or the stated assumptions accepted
- [ ] The synthetic oracle fixture committed by a red-mode session before story 2.1's build

## Exit Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing (or failures triaged)
- [ ] No open high-priority / high-severity bugs
- [ ] `eval.yml` passes on a PR, and `ci.yml`'s integrated-check passes on the same PR (epic Notes: `eval.yml` on kind is this epic's integrated check)
- [ ] The eval check is shown as required on `main` (story 2.3, a person's step)
- [ ] R-001, R-003 and R-005 mitigations complete
- [ ] Waiver W-001 remediated at closure: epic 1's superseded criteria are recorded as superseded, and a fresh epic 1 trace honours them (epic Done when; owner Dillon)

---

## Test Coverage Plan

P0, P1, P2 and P3 are priorities, not execution timing. The Execution Strategy section decides when each test runs. The Owner column names the story whose build writes the test. The R ids column names the epic requirements each row proves. Test Level uses the template's canonical names: Unit, Integration and E2E. In this epic, E2E always means a run on kind through `_kind-deploy.yml`.

### P0 (Critical)

**Criteria**: Critical business, security, data-integrity, or compliance impact with no safe
workaround. Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| Cluster-relevance metrics equal the hand-computed oracle, split short, log-heavy and overall | R2 | Unit | R-005 | 10 | Story 2.2 | Mechanism: the scorer and the tests written in the same session share one wrong reading. Boundary: none; pure functions over a fake store and a scripted retriever, so the level is Unit. Scenarios, on the fixture in "Independent Oracles": (1) short R@1 1/3, R@5 1, R@10 1, MRR@10 7/12. (2) Log-heavy 0, 0, 1/2, 1/20. (3) Overall 1/5, 3/5, 4/5, 37/100, which differ from the mean of the kind means. (4) Query 3 flips from a miss under 2.1 to a hit: sibling 2 at rank 4 counts. (5) Recall is a hit rate: short R@5 is 1, not 5/6. (6) The query never scores itself: query 2 alone in its own top 10 is a miss. (7) MRR boundary: first member at rank 10 gives 1/10; at rank 11 it gives 0. (8) Each query's kind comes from the store's persisted kind, not from `derive_kind` (AD-8): the fake store holds a body that would derive the other kind. (9) Clusters equal the hand-listed components, including the 13→14→15 chain; a link outside the subset adds no member. (10) A third-party IR library scores the same run to the same values (proposed dev dependency). Consequence: wrong numbers are committed as the baseline, published and enforced. Workaround: none; the gate compares the code with itself. |
| Interim target-only metrics equal the hand-computed oracle, and every mode is called with its query excluded | R2 | Unit | - | 5 | Story 2.1 | Story 2.1's relevance is the linked target only (epic Decision 2026-11-08). Scenarios: (1) overall R@10 3/5 and MRR@10 43/150 on the same fixture. (2) Query 3 is a miss (target at rank 11); story 2.2's row flips it. (3) MRR is 0 past rank 10. (4) A spy retriever records `k == 10` and `exclude == frozenset({query})` on every call, for every mode (AD-19). (5) `pairs_scored` equals the number of pairs in the file, so no query is dropped silently. Story 2.2 replaces the expected values of (1) and (2) and keeps (3)–(5). P0 because the rank, cut-off and exclusion machinery written here carries into every later story. Consequence and workaround: as in the R-005 row. |
| `eval/pairs/2026.11.1.jsonl` regenerates byte-identical, with the published counts | R1 | Integration | R-001 | 5 | Story 2.1 | Mechanism: unordered output, or a pair rule that differs from AD-26. Boundary: the pinned Release asset is read and the pairs file is written, which crosses one file boundary, so the level is Integration. Scenarios: (1) regenerating from the checksum-verified `snapshot-2026.11.1` asset gives a SHA-256 equal to the committed file's. (2) Two regenerations, one in a fresh process with a different `PYTHONHASHSEED`, give identical bytes. (3) Counts are 10,473 total, 10,164 short and 309 log-heavy, equal to the Release notes (independent producer: ingest `report()`). (4) Every pair's query is a duplicate-class issue, and its target equals `core.duplicate_target(query)` (AD-26). (5) Lines are sorted by query number, and each line holds only the agreed keys: numbers and kind, no text (Provenance). Consequence: wrong or unstable ground truth under every metric. Workaround: none once the baseline is committed on it. |
| `eval.yml` scores keyword on kind after load, as `ticketscope_ro`, and the results artifact survives teardown | R2 | E2E | R-008 | 6 | Story 2.1 | Mechanism: the Job's role, ordering, rendering or artifact path is wrong. Boundary: the workflow, the chart and the cluster are separate deployables, so the level is E2E. Scenarios: (1) on a PR, `eval.yml` runs `_kind-deploy.yml`; the eval Job reaches Complete after load; the artifact holds keyword's Recall@10 and MRR@10 with `pairs_scored == 10473`. (2) The artifact's snapshot version, embedding model id and preprocessing version equal the `corpus_meta` row read separately with `psql`. (3) The Job's database env references `ticketscope-db-ro` (`kubectl get job -o jsonpath`), and the run succeeded as that role. (4) On a throwaway branch where a step after the Job fails on purpose, the artifact is still uploaded. (5) `ci.yml`'s integrated-check passes on the same PR head. (6) The artifact contains no Secret value or connection string. Waits use `kubectl wait --for=condition=complete` with a timeout, never `sleep`. Consequence: no CI-produced scores exist; this is the epic's integrated check (epic Notes). Workaround: none in CI. |

**Total P0**: 26 tests, ~16–28 hours

### P1 (High)

**Criteria**: Core, frequent, or complex behavior with material user reach and a limited workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| The gate decision table: tolerance, gated metrics, lineage and kind floor | R3 | Unit | R-003 | 15 | Story 2.3 | Mechanism: boundary and comparison errors in the gate. Boundary: a pure function over two results JSONs and an "updated in this diff" flag, so the level is Unit. Scenarios: (1) keyword's log-heavy R@10 drops 0.006 → fail, naming mode, kind and metric. (2) A drop of exactly 0.005 with binary-inexact values (0.400 → 0.395) → pass (C-4). (3) A drop of 0.0051 → fail. (4) Overall rises while log-heavy MRR@10 drops 0.006 → fail. (5) R@1 and R@5 drop 0.1 → pass, because they are reported, not gated. (6) p95 grows 100 times → pass, and p95 is in the report. (7) Any drop → pass when the baseline is updated in the diff. (8)–(10) The snapshot version, the embedding model id, or the preprocessing version differs, with no baseline update → fail, with a message naming the field (one case each). (11) Keyword's null embedding model id in both files is a match. (12) 199 log-heavy pairs without `kind_floor_decision` → fail. (13) 199 with a dated reason → pass. (14) 200 without a decision → pass. (15) A `kind_floor_decision` missing its date or its reason → fail. Consequence: a regressing PR merges, or a good PR is blocked. Workaround: a reviewer reads the artifact; the brief's cut list accepts losing the blocking check (epic Boundaries), so P1, not P0. |
| The gate detects a baseline update in the same diff | R3 | Integration | - | 3 | Story 2.3 | On a temporary git repository: (1) the head commit changes `eval/baseline.json` → updated. (2) The head commit leaves it unchanged → not updated. (3) `eval.yml`'s checkout makes the PR base commit available, through `fetch-depth` or an explicit fetch of `github.event.pull_request.base.sha`; checked by parsing `eval.yml`. |
| The gate blocks on real PRs, and the check is required | R3 | E2E | - | 4 | Story 2.3 | Story 2.3's verify, run on throwaway PRs. Each run URL is recorded in the story plan as evidence. (1) A PR that worsens keyword ranking on purpose fails the eval check. (2) The same PR passes once it updates `eval/baseline.json`. (3) A PR that changes the preprocessing version without a baseline update fails with a lineage message. (4) GitHub shows the eval check as required on `main` (a person's step; `hitl = true`). |
| A changed baseline equals the run that justifies it | R3, R4 | Unit | - | 2 | Story 2.3 | Proposed (see Proposed Story Updates). (1) The diff changes `baseline.json`, and its metrics and lineage equal this run's results within 0.005 → pass. (2) `baseline.json` hand-edited to a value the run did not produce → fail. Closes the R-004 gap, where any baseline edit passes. |
| New modes are picked up with no job change; an unavailable mode is skipped and named | R2 | Unit | R-002 | 3 | Story 2.2 | Mechanism: `jobs.eval` binds or names modes. Boundary: none; the registry and a fake store. Scenarios: (1) a fake second mode, registered by replacing `ticketscope.core.modes.REGISTRY` with a new `MappingProxyType` after `jobs.eval` is imported, appears in the results with every metric. (2) A fake mode whose `available` is false is absent from the metrics and named in the results' skipped list. (3) With only keyword registered, the results list exactly keyword. Consequence: epic 3's modes go unscored, or the job needs editing (fails R2). Workaround: edit the job. |
| The README table equals its render from `eval/baseline.json`, and a hand edit fails | R4 | Unit | R-004 | 5 | Story 2.4 | Mechanism: the README drifts from CI output, or the check passes on an empty comparison. Boundary: the README file and the baseline file, both read by one script, so the level is Unit. Scenarios: (1) the render of the committed `baseline.json` equals the README's generated section byte for byte. (2) A changed number in the README fails the check. (3) A README with missing or duplicated markers fails the check. (4) A fixture baseline with an extra mode renders an extra row with no script change. (5) `ci.yml`'s `checks` job runs the README check (parse test). Consequence: the README shows numbers no CI run produced. Workaround: re-render and commit. |
| Rankings and metrics are identical across runs on the same corpus | R2, R3 | Integration | R-007 | 2 | Story 2.2 | Mechanism: the adapter's inner `ORDER BY score LIMIT k` has no tie-break, so a tie at the k-th score can change the top k. Boundary: Postgres, through the real adapter. On a Postgres container from the in-repo image, with a synthetic corpus whose BM25 scores tie at the 10th position: (1) two runs return identical top-10 lists for every query. (2) Two eval runs over the synthetic pair set give identical metrics, excluding p95. One flipped log-heavy query moves a metric by 1/309 ≈ 0.0032, so two flips break the 0.005 tolerance. Consequence: the required check flaps on unchanged code. Workaround: re-run, which blocks merges meanwhile. |
| Pair derivation follows the AD-26 rule | R1 | Unit | - | 7 | Story 2.1 | On synthetic `SnapshotIssueV2` records: (1) one pair per duplicate-class issue, with its target from `core.duplicate_target`. (2) A target outside the snapshot gives no pair. (3) An issue resolved `Fixed` that carries duplicate links gives no pair. (4) An issue with both a "duplicates" and a "duplicated_by" link gives one pair, to the "duplicates" target. (5) An issue with two "duplicates" links gives one pair, to the lowest target number (C-1). (6) A pair is counted under the query issue's kind. (7) Line order, key order and the trailing newline are fixed. |
| The eval Job renders only when enabled, as `ticketscope_ro`, after load | R2 | Unit | - | 5 | Story 2.1 | `helm template` tests, like epic 1's chart tests: (1) default values render no eval Job (AD-22). (2) `eval.enabled=true` renders it, with command `ticketscope-eval`. (3) Its database env comes from `ticketscope-db-ro`, with no reference to the owner Secret. (4) It runs after load: either a hook weight greater than load's `"0"` with `before-hook-creation`, or no hook, with `eval.yml` starting it. (5) `activeDeadlineSeconds` is set. |
| Workflow wiring keeps `ci.yml` working and keeps the results | R2, R3 | Unit | - | 4 | Story 2.1 | Parse tests: (1) `eval.yml` triggers on `pull_request` and calls `_kind-deploy.yml`. (2) Every input story 2.1 adds to `_kind-deploy.yml` has a default, so `ci.yml`'s integrated-check call is unchanged. (3) The results JSON is written under `reports/` before the "Upload test reports" step, which keeps `if: always()`. (4) `scripts/kind-up.sh` sets `eval.enabled` only when asked; it is off by default. |
| Eval reads lineage and runs every query as the read-only role | R2 | Integration | - | 1 | Story 2.1 | On a migrated Postgres container: `jobs.eval`'s `corpus_meta` read and its search queries all succeed as `ticketscope_ro` (AD-7 default privileges). `CorpusStore` exposes only `corpus_version()`, so the lineage read is a new adapter path. |
| The story 2.2 artifact carries every metric, split by kind, with counts and cost | R2 | E2E | - | 5 | Story 2.2 | On a PR, in `eval.yml` on kind: (1) keyword's R@1, R@5, R@10, MRR@10 and p95 for short, log-heavy and overall. (2) Pair counts per kind: 10,164 short, 309 log-heavy, 10,473 total. (3) The run's wall-clock cost. (4) A skipped-modes list, empty on kind. (5) Proposed: each query's first-member rank; a separate script recomputes every aggregate from those ranks and matches. |
| The refactor sweep changes no behaviour or score | R2, R3, R4 | E2E | - | 3 | Story 2.5 | On story 2.5's PR: (1) the eval check passes, and `git diff` of `eval/baseline.json` against the base is empty. (2) `ci.yml` and its integrated-check pass. (3) `lint-imports` keeps every contract with `jobs.eval` in the jobs layer. |

**Total P1**: 59 tests, ~25–45 hours

### P2 (Medium)

**Criteria**: Secondary behavior with narrower user reach and an acceptable workaround. Risk score
is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| The eval run's wall-clock cost on kind is recorded and fits its limits | R2 | E2E | R-006 | 2 | Story 2.2 | Mechanism: about 21,000 short connections for 10,473 queries, inside a 45-minute job. Boundary: the Job on kind. Scenarios: (1) the Job's wall clock is in the artifact and the job summary. (2) The Job's `activeDeadlineSeconds` and the workflow timeout exceed the recorded duration; the margin is UNKNOWN until the first run. Consequence: slow feedback, or a timed-out check. Workaround: the full-set decision is revisitable (story 2.2), so P2. |
| Query text is the query issue's title and description, without comments | R2 | Unit | - | 1 | Story 2.1 | Per the confirmed Decision (epic Notes, 2026-11-08): a token that appears only in a comment is absent from the query text. |

**Total P2**: 3 tests, ~1.5–3 hours

### P3 (Low)

**Criteria**: Rare, cosmetic, or experimental behavior with minimal impact and an easy workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| No sleep-based polling in tests | R2, R3 | Unit | - | 1 | Story 2.5 | A guard, such as ruff's banned-API rule or a test, fails when `tests/` calls `time.sleep`. Kind waits use `kubectl wait` or `tests/waiting.py`'s `eventually` (epic 1 test review, G3). Workaround: review catches it. |

**Total P3**: 1 test, ~0.5 hours

Why the bands look like this:

- **P0.** Only metric correctness, the pairs and the kind run are P0. A wrong metric or wrong ground truth is a data-integrity failure that no later check can see, and without the kind run no CI-produced score exists.
- **P1 for the gate.** The gate carries a score-6 risk, but it is P1: the brief's cut list already accepts losing the blocking check (epic Boundaries), and the artifact still reports scores to a reviewer.
- **P1 for the README.** A README drift is recoverable by re-rendering.
- **P2 for cost.** The cost row is P2 because the full-set decision is explicitly revisitable.

P0 count per story: story 2.1 has 16 (three rows), story 2.2 has 10 (one row), and stories 2.3, 2.4 and 2.5 have none.

---

## Execution Strategy

**Philosophy:** Run every functional scenario in pull requests while the suite stays under 15 minutes.
Defer only work with material infrastructure or duration cost. P0 through P3 are priority and are not
execution timing; this section decides when tests run and the coverage plan above decides what they are.

- **Pull request, `ci.yml`:**
  - `checks` runs ruff, pyright, import-linter and every Unit and Integration test: the oracle rows, the gate table, the README check, chart and workflow parse tests, and the Postgres-container tests.
  - The pair regeneration test downloads the pinned asset and verifies its checksum first.
  - `integrated-check` is unchanged and must keep passing.
- **Pull request, `eval.yml`:**
  - `_kind-deploy.yml` brings up kind, then the eval Job runs, then the gate, and the results JSON is copied to `reports/` before the upload step.
  - The E2E rows run here. Each PR now brings up two kind clusters (one in `ci.yml`, one in `eval.yml`). Their combined duration is UNKNOWN until story 2.2 records it (R-006).
- **One-off, story 2.3:** throwaway PRs for the regressing, baseline-update and lineage cases, and a person's branch-protection step. Their run URLs are the evidence.
- **Nightly:** none planned.
- **Weekly:** none planned.

Do not re-list the individual tests here. They are already in the coverage plan.

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 26 | 0.6–1.1 | ~16–28 | The oracle fixture by hand, and the first `eval.yml` on kind, are the main cost |
| P1 | 59 | 0.4–0.8 | ~25–45 | The gate table is cheap per case; the throwaway PRs and the tie-planted corpus are not |
| P2 | 3 | 0.5–1.0 | ~1.5–3 | Mostly reading the first recorded run |
| P3 | 1 | 0.25–0.5 | ~0.5 | One lint rule |
| **Total** | **89** | **-** | **~43–77** | **~1–2 weeks** |

### Prerequisites

**Test Data:**

- The synthetic oracle fixture: issues, links, scripted rankings and exact-fraction expected values (red-mode session, before story 2.1 and again before story 2.2).
- The pinned `snapshot-2026.11.1` asset and its checksum (values pin), and its Release notes' pair counts.
- A synthetic corpus with planted BM25 ties at the 10th position (story 2.2).
- Gate fixture result JSONs at each boundary, including 199 and 200 log-heavy pairs (story 2.3).

**Tooling:**

- pytest, ruff, pyright, import-linter, `helm template`.
- A third-party IR metrics library as a dev-only dependency (proposed; story 2.2).
- `kubectl wait` and `tests/waiting.py` for every wait on kind.

**Environment:**

- kind through `scripts/kind-up.sh` and `_kind-deploy.yml` (AD-17), with `eval.enabled` set only by `eval.yml`.
- A Postgres container from the in-repo image for Integration tests.

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths**: ≥80% (snapshot → pairs → eval Job → results → gate → README)
- **Security scenarios**: 100% (the read-only role and the no-secret artifact check; no SEC risk is open)
- **Business logic**: ≥90% of `jobs.eval`'s metric and gate functions, because they are the thing under test
- **Edge cases**: ≥50%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Security tests (SEC category) pass 100% (no SEC risk is open for this epic)
- [ ] Performance targets met (PERF category): no gated threshold; p95 and wall clock are reported
- [ ] Planned NFR evidence exists or `nfr-assess` has documented CONCERNS/waivers

---

## Mitigation Plans

### R-005: Silent metric errors (Score: 9)

**Mitigation Strategy:**

1. A red-mode session commits the oracle fixture and the exact-fraction expected values before each build: target-only before story 2.1, cluster before story 2.2.
2. Story 2.2's oracle includes the cases that separate the definitions: query 3 (target versus cluster), recall as a hit rate versus a fraction of the cluster, overall versus the mean of the kind means, and MRR at ranks 10 and 11.
3. A third-party IR library cross-checks the same scripted run (proposed dev dependency).
4. The artifact carries per-query first-member ranks, and a separate script recomputes the real run's aggregates (proposed).
5. The independent review on story 2.1 (over 800 lines) confirms that the fixture is unchanged since its red commit.

**Owner:** Dillon (stories 2.1 and 2.2)
**Timeline:** fixture before story 2.1's build; cluster values before story 2.2's build
**Status:** Planned
**Verification:** both P0 Unit rows pass against fixture values the build session did not author.
**Residual risk:** the oracle checks the definitions the PO confirmed; C-1 and C-2 still need an answer, and a wrong answer there would be encoded in both the code and the oracle.

### R-001: Pair derivation (Score: 6)

**Mitigation Strategy:**

1. Story 2.1 derives pairs with `core.duplicate_target` (AD-26) and writes sorted lines with a fixed key order.
2. A regeneration test compares SHA-256s and counts against the Release notes.
3. The PO answers C-1, so the epic's wording and AD-26 agree.

**Owner:** Dillon (story 2.1)
**Timeline:** story 2.1
**Status:** Planned
**Verification:** the P0 pairs row passes in `ci.yml`.
**Residual risk:** 9 of 10 sampled pairs were judged real duplicates (epic Notes, spike 12), so the label noise is known but not measured further.

### R-003: The gate fails to block (Score: 6)

**Mitigation Strategy:**

1. The gate is a pure function tested at every boundary, with the tolerance compared exactly. For example, round both values to a fixed number of decimals, or use `Decimal`, before comparing.
2. Diff detection is tested on a temporary git repository, and `eval.yml` fetches the base commit.
3. Throwaway PRs demonstrate the four story 2.3 verify cases on GitHub.
4. A person marks the check required, and the exit criteria record it.

**Owner:** Dillon (story 2.3)
**Timeline:** story 2.3
**Status:** Planned
**Verification:** the P1 gate rows pass, and the throwaway PR run URLs are recorded.
**Residual risk:** C-3 (mode-set changes) is untested until the PO decides; epic 3's first dense PR is the first real case.

---

## Assumptions and Dependencies

### Assumptions

1. C-1 to C-5 hold as stated under "Clarifications for the PO".
2. kind in CI is production for this epic (initiative Assumption, carried from epic 1).
3. A GitHub-hosted runner fits two kind clusters per PR, one per workflow, since they run in separate jobs.

### Dependencies

1. PR #20 merges before the epic starts (epic Notes).
2. The red-mode oracle session runs before story 2.1's build.
3. The PO answers C-1 and C-2, or accepts the stated assumptions.

### Risks to Plan

- **Risk**: the regeneration test needs the snapshot asset in `ci.yml`, a network fetch.
  - **Impact**: a GitHub Releases outage fails `checks`.
  - **Contingency**: run the regeneration step in `eval.yml` instead, which already depends on the asset through load.
- **Risk**: the eval run plus kind-up exceeds `_kind-deploy.yml`'s 45 minutes.
  - **Impact**: the required check always times out.
  - **Contingency**: story 2.2's recorded cost reopens the full-set decision (epic Constraints, Queries).

---

## Proposed Story Updates

These changes are for the PO to apply. This plan does not edit `tickets.toml` or the epic.

| Story | Proposed `verify` change | Why |
| ----- | ------------------------ | --- |
| 2.1 | Add: "the printed counts equal Release `snapshot-2026.11.1`'s notes: 10,473 pairs, 10,164 short and 309 log-heavy (R1); the target-only metrics match the hand-computed oracle committed before the build (R2); the results artifact is uploaded even when a later step fails (R2)." | R-001, R-005, R-008. The current verify says only that the counts "are printed". |
| 2.1 | Description wording: align "one pair per in-subset duplicate link" with AD-26's "one pair per duplicate issue, through `core.duplicate_target`", or record the intended rule (C-1). | R-001. The published counts come from the AD-26 rule. |
| 2.2 | Add: "the cluster metrics match the hand-computed oracle for every metric, short, log-heavy and overall, including a case where overall differs from the mean of the kind means (R2); two runs on the same corpus give identical metrics (R2, R3); the artifact carries each query's first-member rank, and an independent recompute matches (R2)." | R-005, R-007. |
| 2.2 | Clarify in the fake-mode clause: "registered by replacing `ticketscope.core.modes.REGISTRY`". | R-002. `REGISTRY` is a read-only `MappingProxyType`. |
| 2.3 | Add: "unit tests pass a drop of exactly 0.005 and fail 0.0051; 200 log-heavy pairs pass without `kind_floor_decision`; a changed `baseline.json` that differs from this run's results fails (R3, R4)." The last clause also needs a description change. | R-003, R-004. |
| 2.3 | Record the answer to C-3 (a missing or a new mode) in the description, with a verify case. | R-003. |
| 2.4 | Add: "a README with missing generated-section markers fails the check (R4)." | R-004. |
| 2.5 | Add: "`tests/` has no `time.sleep` calls, enforced by a lint rule or a test." | Epic 1 test review G3; P3 row. |

---

## Follow-on Workflows (Manual)

- Run `/bmad-tea-automate` in red mode to commit the oracle fixture and failing P0 tests before story 2.1's build (separate workflow; not auto-run).
- Run `/bmad-tea-automate` for broader coverage once implementation exists.
- Run `/bmad-tea-nfr` once the first `eval.yml` run records p95 and wall clock.
- Run `/bmad-tea-trace` at epic closure, together with the W-001 remediation.

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: Dillon Date: ____
- [ ] Tech Lead: Dillon Date: ____
- [ ] QA Lead: Dillon Date: ____

**Comments:**

---

## Interworking & Regression

| Service/Component | Impact | Regression Scope |
| ----------------- | ------ | ---------------- |
| **Epic 1 snapshot, load and adapter** | Eval reads the pinned snapshot, `corpus_meta`, persisted kind, and `PostgresCorpusStore` | Epic 1's load and `/v1` tests; this plan's lineage and tie-break rows |
| **Epic 1 `_kind-deploy.yml` and `ci.yml`** | Story 2.1 changes the reusable workflow | `ci.yml`'s integrated-check on every story PR; the workflow parse row |
| **Epic 3 dense and hybrid** | Registers modes that eval scores; updates `baseline.json` with an embedding model id | Mode-pickup row; gate lineage and C-3 cases |
| **Epic 8 reviewer package** | Publishes the README table | README render row |

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization
- `nfr-criteria.md` - NFR planning

### Related Documents

- PRD: none. Initiative requirements stand in: `_bmad-output/initiative-ticketscope/initiative-ticketscope.md`
- Epic: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md`
- Stories: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/tickets.toml`
- Architecture: `_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md`
- Epic 1 test design and retrospective: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/`
- Tech Spec: none

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `bmad-tea-test-design`
**Version**: 4.0 (BMad v6)
