---
runScope: 'story'
runKey: 'story-ticketscope--e2-s1'
testMode: 'red'
testEntry: 'bmad-tea-automate'
workflowStatus: 'completed'
stepsCompleted: ['step-01-preflight-and-context', 'step-02-generation-mode', 'step-03-test-strategy', 'step-04c-aggregate', 'step-05-validate-and-complete']
lastStep: 'step-05-validate-and-complete'
test_mode: 'red'
test_operation: 'create'
auto_validate: true
auto_heal_failures: true
max_healing_iterations: 3
use_mcp_healing: true
healing_rounds_used: 0
lastSaved: '2026-11-08'
workflowType: 'testarch-atdd'
storyId: '2.1'
storyKey: 'ticketscope--e2-s1'
storyFile: ''
ticketRef: '1 @ _bmad-output/initiative-ticketscope/tickets/epic-eval-gate'
atddChecklistPath: '_bmad-output/test-artifacts/atdd/atdd-checklist-ticketscope--e2-s1.md'
generatedTestFiles:
  - 'tests/unit/test_eval_oracle.py'
generatedSupportFiles:
  - 'tests/eval_oracle.py'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate.md
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
  - src/ticketscope/core/modes.py
  - src/ticketscope/core/ports.py
  - src/ticketscope/core/model.py
  - src/ticketscope/core/fakes.py
  - src/ticketscope/core/derive.py
  - src/ticketscope/core/snapshot.py
  - tests/conftest.py
  - tests/factories.py
  - tests/unit/test_modes.py
  - pyproject.toml
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
    text: "On a PR, eval.yml deploys to kind, runs the eval Job after load, and uploads a results artifact with keyword's Recall@10 and MRR@10 over every pair plus the corpus lineage (R2); ci.yml's integrated-check still passes on the same PR; regenerating eval/pairs/2026.11.1.jsonl from the snapshot yields a byte-identical file, and its short and log-heavy counts are printed (R1)."
---

# ATDD Checklist - Epic 2, Story 1: Tracer: keyword is scored on kind and CI uploads the results

**Date:** 2026-11-08
**Author:** Dillon (TEA red-mode session)
**Primary Test Level:** Unit (backend; pytest)

---

## Story Summary

The tracer bullet for epic-eval-gate goes from the pinned snapshot to a CI artifact. A pure core function derives `eval/pairs/2026.11.1.jsonl`. `jobs.eval` scores every available registry mode as `ticketscope_ro`, with target-only relevance. The chart gains an eval Job behind `eval.enabled`, and `eval.yml` uploads the results JSON from kind.

**As a** reviewer of ticketscope
**I want** retrieval scores that CI produced on labelled data
**So that** I can trust the numbers, and later stories can gate merges on them (initiative R6)

---

## Acceptance Criteria

The ticket has only a `verify` line and the story plan does not exist yet. So the verify line is the single criterion, which carries the story's covers R1 and R2 (story-identity contract, section 2, rule 3).

| ID   | ID source | Acceptance criterion |
| ---- | --------- | -------------------- |
| AC-1 | generated | On a PR, eval.yml deploys to kind, runs the eval Job after load, and uploads a results artifact with keyword's Recall@10 and MRR@10 over every pair plus the corpus lineage (R2); ci.yml's integrated-check still passes on the same PR; regenerating eval/pairs/2026.11.1.jsonl from the snapshot yields a byte-identical file, and its short and log-heavy counts are printed (R1). |

---

## Story Integration Metadata

- **Story ID:** `2.1`
- **Story Key:** `ticketscope--e2-s1`
- **Story File:** none (v7 entry, not pulled)
- **Ticket:** `1 @ _bmad-output/initiative-ticketscope/tickets/epic-eval-gate` (v7). The builder's plan, `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-tracer-keyword-is-scored-on-kind-and-ci-uploads-the-results-plan.md`, does not exist yet.
- **Checklist Path:** `_bmad-output/test-artifacts/atdd/atdd-checklist-ticketscope--e2-s1.md`
- **Generated Test Files:** `tests/unit/test_eval_oracle.py`
- **Generated Support Files:** `tests/eval_oracle.py` (the independent oracle)
- **Test design:** `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md` (risks R-001, R-005, R-008; Independent Oracles protocol)

When `bmad-build` plans this story, list both generated files in the plan's Code Map and the task that turns the scaffold green.

---

## Red-Phase Test Scaffolds Created

### Unit Tests (1 test)

**File:** `tests/unit/test_eval_oracle.py`

- ✅ **Test:** `test_p0_ac1_keyword_target_only_metrics_match_the_oracle` (`[P0] AC-1`, marker `criterion("ticketscope--e2-s1--AC-1")`)
  - **Status:** RED, skipped. Activated, it fails with `ModuleNotFoundError: No module named 'ticketscope.jobs.eval'` raised in the test body.
  - **Verifies:** keyword's overall Recall@10 equals 3/5 (the first assertion), then MRR@10 equals 43/150, `pairs_scored` equals 5, every oracle query is searched exactly once, each with `k == 10`, `exclude == {query}`, and the query issue's description in the query text.
  - **Mitigates:** R-005 (silent metric errors). The expected values are exact fractions that the build session does not author.

### API / E2E Tests

None. The stack is backend with no HTTP surface in this story. The kind run is an E2E row for the build, listed below.

---

## Support Files Created

### Independent oracle

**File:** `tests/eval_oracle.py`

**Exports:** `DUPLICATE_LINKS`, `PAIRS` (one per duplicate issue, per AD-26), `FILLERS`, `RANKINGS` (scripted top 10 per query), `TARGET_ONLY_RECALL_AT_10 = Fraction(3, 5)`, `TARGET_ONLY_MRR_AT_10 = Fraction(43, 150)`, `TOLERANCE = 1e-9`, and the `Pair` and `Kind` types.

**The rule:** the build session does not edit this file. The independent review on story 2.1 checks that it is unchanged since its red commit. Story 2.2's red session adds the cluster values in its own commit.

**Deviation from test-quality "unique data":** issue numbers are fixed on purpose. An oracle is only independent if a person can redo the arithmetic from the file alone.

---

## Seam the Scaffold Assumes

From the story description and spine AD-19. If the build names these differently, it adapts only the call site and key lookups, and records that in its plan. The values and what each assertion means stay as written.

- `ticketscope.jobs.eval.score(store, pairs)` scores every mode in `core.modes.REGISTRY` whose `available(store)` holds. It reads the registry when called: the test replaces `ticketscope.core.modes.REGISTRY` after importing the job.
- `pairs` are the parsed lines of `eval/pairs/<snapshot>.jsonl`, with keys `query`, `target` and `kind`.
- Query text is built from the query issue's title and description through `CorpusStore.get_issue`.
- The return value is the results dict, with `results["modes"]["keyword"]` holding `"recall@10"`, `"mrr@10"` and `"pairs_scored"`.

---

## Implementation Checklist

### Test: `test_p0_ac1_keyword_target_only_metrics_match_the_oracle`

**File:** `tests/unit/test_eval_oracle.py`

- [ ] Add the `ticketscope.jobs.eval` package (jobs layer; import-linter contracts unchanged)
- [ ] `score(store, pairs)`: iterate `modes.REGISTRY` at call time, skip unavailable modes, build each retriever from the store
- [ ] Per pair: query text = the query issue's title and description; `search(text, k=10, exclude=frozenset({query}))`
- [ ] Target-only relevance: Recall@10 is the share of pairs whose target is in the top 10; MRR@10 is the mean of 1/rank, with 0 past rank 10
- [ ] Results carry `pairs_scored` equal to the number of pairs given
- [ ] Remove the `@pytest.mark.skip` block; confirm it fails first, then passes: `uv run pytest tests/unit/test_eval_oracle.py`
- [ ] ✅ Test passes (green phase) with `tests/eval_oracle.py` unchanged

### Green-phase work for AC-1 (rows from the epic 2 test design, owned by the build)

These are AC-1's remaining clauses and branches. The red workflow allows one red leaf per criterion, so they are listed here rather than scaffolded.

- [ ] **P0, Integration, R1, R-001.** `eval/pairs/2026.11.1.jsonl` regenerates byte-identical: (1) its SHA-256 equals the committed file's; (2) a fresh process with a different `PYTHONHASHSEED` gives the same bytes; (3) counts are 10,473 total, 10,164 short and 309 log-heavy, equal to the Release `snapshot-2026.11.1` notes; (4) each target equals `core.duplicate_target(query)`; (5) lines are sorted by query and hold only `query`, `target` and `kind`.
- [ ] **P0, E2E (kind), R2, R-008.** `eval.yml` on a PR: (1) the Job reaches Complete after load, and the artifact holds keyword's Recall@10 and MRR@10 with `pairs_scored == 10473`; (2) the artifact's lineage equals the `corpus_meta` row read with `psql`; (3) the Job's database env references `ticketscope-db-ro`; (4) the artifact uploads even when a later step fails; (5) `ci.yml`'s integrated-check passes on the same head; (6) the artifact holds no Secret value. Waits use `kubectl wait`, never `sleep`.
- [ ] **P1, Unit, R1.** The AD-26 pair rule on synthetic `SnapshotIssueV2` records (`tests/factories.snapshot_issue`): one pair per duplicate issue; a target outside the snapshot gives no pair; a `Fixed` issue gives no pair; a duplicate with both directions pairs to its "duplicates" target; two "duplicates" links pair to the lowest number; each pair carries the query's kind; line order, key order and the trailing newline are fixed.
- [ ] **P1, Unit (helm template), R2.** The eval Job renders only with `eval.enabled=true`; its command is `ticketscope-eval`; its database env comes from `ticketscope-db-ro` only; it runs after load; `activeDeadlineSeconds` is set.
- [ ] **P1, Unit (parse), R2.** `eval.yml` runs on `pull_request` and calls `_kind-deploy.yml`; every new `_kind-deploy.yml` input has a default; the results JSON lands under `reports/` before the `if: always()` upload; `kind-up.sh` leaves `eval.enabled` off by default.
- [ ] **P1, Integration, R2.** On a migrated Postgres container, `jobs.eval`'s `corpus_meta` read and its searches succeed as `ticketscope_ro`.
- [ ] **P2, Unit, R2.** A token that appears only in a comment is absent from the query text.

---

## Running Tests

```bash
# The scaffold (skipped until activated)
uv run pytest tests/unit/test_eval_oracle.py -rs

# After removing the skip block, before implementation: expect ModuleNotFoundError
uv run pytest tests/unit/test_eval_oracle.py

# Unit suite
uv run pytest tests/unit
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete) ✅

- ✅ One red-phase scaffold for AC-1, skipped with a reason that names what re-enables it
- ✅ Independent oracle committed before the build
- ✅ Implementation checklist and green-phase rows recorded
- No data-testid attributes, UI flows or HTTP mocks apply (backend story)

### GREEN Phase (build)

Activate the scaffold, confirm it fails, then implement `jobs.eval` until it passes. Then work through the green-phase rows above. Do not edit `tests/eval_oracle.py`.

### REFACTOR Phase

Story 2.5's sweep owns cross-story cleanup. The oracle's values never change in a refactor.

---

## Test Execution Evidence

### RED Verification (run-and-heal)

- **Route:** project-native pytest. `tea-atdd-red-check` is Playwright-only and `tea-unit-check` is Vitest or Jest only, so neither fits a pytest scaffold.
- **Disposable copy:** the worktree was copied to `$CLAUDE_JOB_DIR/tmp/red-copy` (without `.venv`, `.git` or `_bmad*`), and only the leaf's `@pytest.mark.skip(...)` block was removed. A `diff` against the permanent scaffold shows that block as the only change.
- **Command:** `uv run pytest tests/unit/test_eval_oracle.py -q --junitxml=<fresh report>`, with the project's own pyproject config. The process budget is pytest's default (no timeouts are configured); the run took 0.03 s.

```text
>       eval_job = importlib.import_module("ticketscope.jobs.eval")
E   ModuleNotFoundError: No module named 'ticketscope.jobs.eval'
FAILED tests/unit/test_eval_oracle.py::test_p0_ac1_keyword_target_only_metrics_match_the_oracle
1 failed in 0.03s
```

**Summary:**

- Total generated tests: 1. Activated: 1. Failed for the intended missing behavior: 1. Load or setup errors: 0. Production or config changes: none.
- Repair rounds used: 0 of 3. Healed files: none.
- Status: **verified red**

**Scaffold soundness probe (disposable copy only, not committed):** a throwaway reference `jobs/eval.py` with target-only scoring made the activated test **pass**. Not excluding the query failed on `exclude == frozenset({2})`, and searching with `k=20` failed on `k == 10`. The probe file was deleted, and nothing from it entered the worktree.

**Permanent scaffold, in the worktree:** `uv run pytest tests/unit` gave 716 passed and 18 skipped (the scaffold plus the helm-gated tests); ruff, ruff format and pyright are clean on both files; import-linter kept 7 contracts and broke 0.

---

## Notes

- **C-1, the pair rule, is still open for the PO.** The ticket's description says "one pair per in-subset duplicate link". AD-26 and the published 10,473 count say one pair per duplicate issue, through `core.duplicate_target`. This oracle and the green-phase rows follow the test design's stated assumption, AD-26. In this fixture every duplicate has exactly one link, so the two readings agree here; they diverge only on the P1 two-link rows.
- **Execution mode was sequential.** No subagents were requested, and every input was already loaded.
- **The design's "Proposed Story Updates" for 2.1 are not applied.** Red mode changes no ticket, plan or story status; Sofia (`bmad-agent-po`) applies them.
- **The Independent Oracles protocol needs a check at review.** The review on story 2.1 (flagged at over 800 lines) should confirm `git diff <red commit>.. -- tests/eval_oracle.py` is empty.

---

## Knowledge Base References Applied

- **test-quality.md:** skip reasons name what re-enables the test; assertions can fail (shown by the probe); one concern per test
- **data-factories.md:** existing `tests/factories.py` builders are reused for the green-phase pair-rule rows; the oracle deliberately uses fixed data
- **test-levels-framework.md / test-priorities-matrix.md:** Unit for pure scoring, Integration for the file and database boundaries, E2E for kind; P0 to P2 taken from the epic 2 design
- **test-healing-patterns.md:** used to classify the red result as "intended missing behavior"
- **component-tdd.md / ci-burn-in.md:** loaded as the core and backend set; no component surface, and no burn-in needed for a 0.03 s deterministic unit test

---

**Generated by BMad TEA Agent** - 2026-11-08
