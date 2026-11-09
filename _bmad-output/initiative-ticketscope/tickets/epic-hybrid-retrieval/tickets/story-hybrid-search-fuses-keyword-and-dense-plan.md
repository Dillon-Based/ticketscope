---
title: 'Hybrid search fuses keyword and dense'
type: 'feature'
ticket: 2
created: '2026-11-09'
status: done
baseline_revision: '684c8f4b6c95bb7665cb8ebc7c0d97096b942948'
route: 'oneshot'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** `core.modes.REGISTRY` has keyword and dense only; `/v1` already admits `mode=hybrid` and `score_kind=rrf` in the contract but nothing serves them.

**Approach:** Add `HybridRetriever` in `src/ticketscope/core/modes.py` over a `KeywordRetriever` and a `DenseRetriever`. Each side is asked for `k + |exclude|` non-excluded candidates, fused by equal-weight reciprocal rank fusion (`1/(60+rank)`, 1-based ranks), ties broken by issue number ascending. Register `hybrid` (`score_kind="rrf"`), available only when dense is (embedder present and embeddings loaded; keyword is always available). `/v1` and eval need no code change: the registry drives both. The `embeddings {model}` span and db spans already nest under `retrieval hybrid`.

</intent-contract>

## Implementation Notes

Oneshot: about 40 lines of source plus tests. Tests update `skipped_modes` expectations in eval tests, because eval has no embedder and now also skips `hybrid`; `jobs/eval` is untouched.

## Verification

**Commands:**
- `uv run pytest tests/unit -q` -- expected: all pass (includes `tests/unit/test_hybrid_expanded.py`)
- `uv run ruff check . && uv run ruff format --check . && uv run pyright` -- expected: clean

## Review Triage Log

### 2026-11-09 — Review pass
- verdicts: 7 findings — high 0, medium 0, low 3, false 2, maybe-false 0 (2 reported as non-defects)
- findings:
  - `[low]` `[patch]` `test_fusion_is_reproducible` accepted two orders — tightened to the single correct `[1, 4, 2, 3]`.
  - `[low]` `[patch]` redundant either-order assertion in the exclude test — removed.
  - `[low]` `[patch]` k-larger-than-sides test checked membership only — now asserts order and scores.
  - `[low]` `[reject]` db spans under `retrieval hybrid` untested — the `retrieval` span wraps the whole `.search()`; the embeddings child is asserted; db spans come from psycopg instrumentation, unchanged and covered by the kind test.
  - `[false]` `[reject]` k + 2|exclude| over-fetch is wasteful — it is the spec's "at least k + |exclude|" per side; harmless.
  - `[false]` `[reject]` registry-mismatch tests use an artificial registry — hybrid is now registered, so the registry-miss path is only reachable by removing a mode; the real registry is covered by test_hybrid.
  - `[false]` `[reject]` verification not run — run by the author: pytest, ruff, pyright, lint-imports all pass.


### 2026-11-09 — Follow-up review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings: none. The context-free quick reviewer inspected the baseline diff and surrounding code, including the expanded tests.

## Auto Run Result

Status: built (preserved; ticket completion belongs to the orchestrator).

- **Summary:** Follow-up review of the existing hybrid implementation and expanded regression coverage found no defects. Equal-weight reciprocal rank fusion uses constant 60, deterministic issue-number ties, exclusion-aware candidates, and registry-driven availability and score kind.
- **Files:** Existing implementation in `src/ticketscope/core/modes.py`; fusion, registry, API and span tests in `tests/unit/test_hybrid.py`; kind coverage in `tests/integrated/test_dense_kind.py`; registry expectation updates in the existing unit suites. This pass retains `tests/unit/test_hybrid_expanded.py` from the preceding automation pass (10 cases for k bounds, exclusion, uniqueness, deterministic order, record precedence, and availability), its automation summary and result artifact, and updates this plan's review and verification evidence.
- **Review:** Quick lens only; zero findings, zero patches, zero new deferred items, zero rejected findings. Existing triage entries and deferred-work ledger entries were preserved.
- **Follow-up review recommended:** false; patched counts: high 0, medium 0, low 0.
- **Verification:** `uv run pytest tests/unit -q`: 992 passed, including all 10 expanded cases. `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, and `uv run lint-imports`: passed (7 import contracts kept).
- **Residual risks:** Hybrid kind checks were not run. The existing `kind-ticketscope` deployment uses `ticketscope-app:story-3-1-final2` and has dense mode disabled; it does not verify this implementation. Deployment and the orchestrator's independent acceptance verification remain outstanding. Eval's model-enabled wiring belongs to later work.
