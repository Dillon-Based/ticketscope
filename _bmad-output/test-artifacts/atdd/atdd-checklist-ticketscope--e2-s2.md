---
runScope: 'story'
runKey: 'story-ticketscope--e2-s2'
testMode: 'red'
testEntry: 'bmad-tea-automate'
workflowStatus: 'completed'
stepsCompleted: ['step-01-preflight-and-context', 'step-02-generation-mode', 'step-03-test-strategy', 'step-04c-aggregate', 'step-05-validate-and-complete']
lastStep: 'step-05-validate-and-complete'
lastSaved: '2026-11-08'
test_mode: 'red'
test_operation: 'create'
auto_validate: true
auto_heal_failures: true
max_healing_iterations: 3
use_mcp_healing: true
healing_rounds_used: 0
workflowType: 'testarch-atdd'
storyId: '2.2'
storyKey: 'ticketscope--e2-s2'
storyFile: ''
ticketRef: '2 @ _bmad-output/initiative-ticketscope/tickets/epic-eval-gate'
atddChecklistPath: '_bmad-output/test-artifacts/atdd/atdd-checklist-ticketscope--e2-s2.md'
generatedTestFiles:
  - 'tests/unit/test_eval_cluster_oracle.py'
generatedSupportFiles:
  - 'tests/eval_oracle.py (appended section only)'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md
  - src/ticketscope/jobs/eval/score.py
  - src/ticketscope/core/pairs.py
  - tests/eval_oracle.py
  - tests/unit/test_eval_oracle.py
  - knowledge/data-factories.md
  - knowledge/component-tdd.md
  - knowledge/test-quality.md
  - knowledge/test-healing-patterns.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/ci-burn-in.md
acceptanceCriteria:
  - id: 'AC-1'
    idSource: 'generated'
    text: "The cluster metrics match the hand-computed oracle committed before the build for every metric, short, log-heavy and overall, including a case where overall differs from the mean of the kind means, a sibling duplicate counts as a hit and the query never scores itself (R2); registering a fake second mode by replacing ticketscope.core.modes.REGISTRY makes it appear in the results with no change to jobs.eval (R2); two runs on the same corpus give identical metrics (R2, R3); on a PR the artifact holds every metric for keyword split short, log-heavy and overall, the pair counts per kind, each query's first-member rank that an independent recompute matches, and the run's cost (R2)."
---

# ATDD Checklist - Epic 2, Story 2: Scores count the whole duplicate cluster, split by ticket kind

**Date:** 2026-11-08
**Author:** Dillon (TEA red-mode session)
**Primary Test Level:** Unit (backend; pytest)

---

## Story Summary

Relevance becomes the query's duplicate cluster instead of story 2.1's linked target. Results gain Recall@1 and Recall@5, p95 latency, the short, log-heavy and overall split, pair counts per kind, each query's first-member rank, the list of skipped modes, and the run's cost. Ranking becomes reproducible.

---

## Acceptance Criteria

The ticket has only a `verify` line and the story plan does not exist yet, so the verify line is the single criterion, which carries the story's covers R2 (story-identity contract, section 2, rule 3).

| ID   | ID source | Acceptance criterion |
| ---- | --------- | -------------------- |
| AC-1 | generated | The verify line above, verbatim. |

---

## Story Integration Metadata

- **Story ID:** `2.2`. **Story Key:** `ticketscope--e2-s2`. **Story File:** none (v7 entry, not pulled).
- **Ticket:** `2 @ _bmad-output/initiative-ticketscope/tickets/epic-eval-gate`. The builder's plan, `tickets/story-scores-count-the-whole-duplicate-cluster-split-by-ticket-kin-plan.md`, does not exist yet.
- **Generated:** `tests/unit/test_eval_cluster_oracle.py`, plus a section appended to `tests/eval_oracle.py`.

When the 2.2 build plans this story, list both files in the plan's Code Map and Verification.

---

## Red-Phase Test Scaffold Created

**File:** `tests/unit/test_eval_cluster_oracle.py`

- ✅ `test_p0_ac1_cluster_metrics_match_the_oracle` (`[P0] AC-1`, marker `criterion("ticketscope--e2-s2--AC-1")`)
  - **Status:** RED, skipped. Activated against 2.1's code, it fails with `ValueError: pair must have exactly the keys ('query', 'target', 'kind'), got ['kind', 'query', 'relevant', 'target']`, because the scorer has no cluster input yet.
  - **First assertion:** overall Recall@10 equals 4/5. Query 3's sibling at rank 4 is a hit; target-only relevance gives 3/5.
  - **Then:** all 12 metrics (short, log-heavy, overall × R@1, R@5, R@10, MRR@10) equal `CLUSTER_EXPECTED`; pairs per kind are 3, 2 and 5; `relevance == "cluster"`; first-member ranks are `[[2,2],[3,4],[5,1],[7,10],[9,None]]`; every query is searched once with `k == 10` and `exclude == {query}`; and a retriever that returns the query itself (`SELF_RANKING`) scores R@10 0 and MRR@10 0.

## Oracle Additions (`tests/eval_oracle.py`)

Appended below story 2.1's values, which are unchanged: `CLUSTER_RELEVANT`, `FIRST_MEMBER_RANKS`, `CLUSTER_EXPECTED` (exact fractions), `CLUSTER_PAIRS_BY_KIND`, `SELF_RANKING`, and, for the cluster-derivation test, `MEMBERSHIP_ISSUES`, `MEMBERSHIP_LINKS` and `EXPECTED_CLUSTERS` (a 13→14→15 chain, and a link to 999 outside the subset). The file also documents the wrong readings' values: mean of the kind means 1/6, 1/2, 3/4, 19/60; fraction-of-cluster short R@5 5/6; target-only R@10 3/5.

**The rule:** the 2.2 build does not edit this file. Its review checks that `git diff <this red commit>.. -- tests/eval_oracle.py` is empty.

---

## Seam the Scaffold Assumes

- Each pairs line gains `relevant`: the sorted cluster minus the query. The cluster's links live only in the snapshot, so `core` derives the clusters there (every in-subset link, in both directions, per C-2) and the pairs file carries them. The pairs file is regenerated, keeping it sorted and byte-identical.
- `results["relevance"] == "cluster"`; `results["modes"][mode]` holds `short`, `log_heavy` and `overall` (each with `recall@1`, `recall@5`, `recall@10`, `mrr@10`, `pairs_scored`) and `first_member_ranks`.
- If the build carries the cluster or names the keys differently, it adapts only this file's setup and key lookups, and records that in its plan. The values and what each assertion means stay as written.

---

## Implementation Checklist

### Test: `test_p0_ac1_cluster_metrics_match_the_oracle`

- [ ] `core`: derive clusters (connected components over every in-subset duplicate link, both directions); pairs carry `relevant`; regenerate `eval/pairs/2026.11.1.jsonl` (counts unchanged: 10,473, 10,164 and 309)
- [ ] `jobs.eval.score`: cluster relevance; R@1, R@5, R@10 and MRR@10 per kind and overall (over all queries); `pairs_scored` per kind; `first_member_ranks`; `relevance: "cluster"`
- [ ] **Retire story 2.1's `test_p0_ac1_keyword_target_only_metrics_match_the_oracle`.** Its target-only values no longer hold, and its `k`, `exclude` and `pairs_scored` checks are carried by this leaf. Leave the `TARGET_ONLY_*` constants untouched.
- [ ] Update story 2.1's kind tests and unit tests that read the old flat result keys or `relevance == "target"`
- [ ] Remove the skip block; confirm it fails first, then passes: `uv run pytest tests/unit/test_eval_cluster_oracle.py`

### Green-phase work for AC-1 (test design rows owned by story 2.2)

- [ ] **P0, Unit.** Cluster derivation equals `EXPECTED_CLUSTERS` from `MEMBERSHIP_LINKS` over `MEMBERSHIP_ISSUES`, including the chain and the link outside the subset.
- [ ] **P0, Unit.** A third-party IR library (e.g. `ranx`, as a dev-only dependency) scores the same scripted run to `CLUSTER_EXPECTED`.
- [ ] **P0, Unit.** Each query's kind comes from the pair's kind, which `derive_kind` computes and load persists (AD-8). A fake store holding a body that would derive the other kind does not change it.
- [ ] **P1, Unit, R-002.** A fake second mode, registered by replacing `ticketscope.core.modes.REGISTRY` after import, appears with every metric. An unavailable mode is absent from the metrics and named in a skipped list. With only keyword registered, the results list exactly keyword.
- [ ] **P1, Integration, R-007.** BM25 ties at the 10th score resolve the same way every run (the adapter's inner `ORDER BY` gets a tie-break); two eval runs give identical metrics, p95 excluded.
- [ ] **P1, E2E (kind).** The artifact holds keyword's R@1, R@5, R@10, MRR@10 and p95 for short, log-heavy and overall; pairs 10,164, 309 and 10,473; the run's wall clock (also in the job summary); an empty skipped list; and first-member ranks from which a separate script recomputes every aggregate and matches.
- [ ] **P2, E2E (kind), R-006.** The Job's `activeDeadlineSeconds` and `_kind-deploy.yml`'s `timeout-minutes` exceed the recorded duration (settles the item deferred from 2.1 in `_bmad-output/deferred-work.md`).

---

## Test Execution Evidence

- **Route:** project-native pytest; neither TEA verifier supports pytest.
- **Disposable copy:** `$CLAUDE_JOB_DIR/tmp/red-copy-22`. Only the leaf's `@pytest.mark.skip(...)` block was removed; a `diff` confirmed that was the only change.
- **Result:** 1 activated, 1 failed for the intended missing behavior (`ValueError` from `as_pair`: no cluster input), 0 load errors, 0 production changes. Repair rounds used: 0 of 3. **Status: verified red.**
- **Soundness probe (copy only, deleted afterwards):** a throwaway cluster scorer made the leaf **pass**. Each wrong reading failed:
  - Overall as the mean of the kind means fails on the first assertion (0.75 vs 0.8).
  - Target-only relevance left in place fails on the first assertion (0.6 vs 0.8).
  - Counting the query as relevant fails on the self-ranking check (1.0 vs 0.0).
- **Worktree:** `uv run pytest tests/unit` gives 758 passed and 18 skipped (this scaffold plus the helm-gated tests). ruff, ruff format and pyright are clean. Story 2.1's leaf still passes.

---

## Notes

- **C-2 and C-3 are settled** (epic Notes, 2026-11-08): the cluster uses every in-subset link in both directions; a missing gated mode fails and a new mode passes (in 2.3's description and verify).
- **Execution mode was sequential.** One leaf, with every input already loaded.
- **Red mode changes no ticket, plan or story status.**
