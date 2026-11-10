---
title: 'Integrated check on kind'
type: 'feature'
ticket: '8'
created: '2026-11-10'
status: done
baseline_revision: '3c0cddd40e2c3bc98179b9e54bd413051c831306'
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

**Problem:** The epic's Done when (R1-R5) is only partly checked on kind: tests/integrated/test_dense_kind.py covers load from the pinned asset, dense and hybrid answers and the api budget, but nothing checks the omitted-mode default, readiness on a model mismatch, the model-choice record, or that the committed eval baseline and README carry all three modes.

**Approach:** Add `tests/integrated/test_hybrid_check.py` (marker `kind`) with one test per missing line, and map every R to its test in the module docstring. `integrated-check` already runs `tests/integrated`, so CI picks it up with no workflow change.

</intent-contract>

## Implementation Notes

Oneshot: a single new test file (~120 lines), no product code. Readiness mismatch is provoked by updating `corpus_meta.embedding_model_id` through psql and restored in `finally`, then the api is awaited Ready. The default-mode check ties the chart value, the deployment env, the best overall MRR@10 in `eval/baseline.json` and a mode-less `/v1/search`. R1/R2 stay in `test_dense_kind.py` (not duplicated); the live eval Job's three modes stay in `tests/eval` (eval workflow).

## Review Triage Log

### 2026-11-10 — Review pass
- verdicts: 8 findings — high 0, medium 2, low 3, false 1, maybe-false 0 (two more low rejected)
- findings:
  - `[medium]` `[patch]` Recovery wait used `pytest.fail`, which `eventually` does not retry — now asserts.
  - `[medium]` `[patch]` Test never waited for the api pod Ready condition — added `kubectl wait --for=condition=Ready`.
  - `[low]` `[patch]` Restore hardcoded the model id — now reads the original from `corpus_meta` first.
  - `[low]` `[patch]` R4 check ignored `skipped_modes` — now asserts it is empty. README/baseline sync stays with the `checks` job's `render_readme_table.py --check`.
  - `[low]` `[patch]` `_baseline` return annotation wrong; docstring omitted R5's resource half — fixed both.
  - `[false]` `[reject]` Default-equals-best-MRR rule is not in the epic — it is the epic's Default mode constraint.
  - `[low]` `[reject]` Interruption leaves `corpus_meta` wrong — a CI job's cluster is disposable; a guard adds complexity.
  - `[low]` `[reject]` R3 is checked by substring and a globbed file name — adequate for a committed prose record.

### 2026-11-10 — Follow-up review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings: []

## Verification

- `uv run ruff check . && ruff format --check . && pyright && lint-imports && pytest` -- pass (1096 passed)
- `pytest -m kind tests/integrated` on local kind via port-forward -- 15 passed


## Auto Run Result

Status: built (preserved; ticket completion belongs to the orchestrator).

**Summary.** Follow-up quick review of the integrated kind checks and the existing expanded coverage found no defects. The implementation checks the chart default through a mode-less search, readiness failure and recovery on a model mismatch, the model-choice record, and the three-mode committed eval artifacts. Existing dense tests cover the pinned embedding load, dense/hybrid query results, and the API budget.

**Files changed.** `tests/integrated/test_hybrid_check.py` adds the integrated checks (already committed). `tests/unit/test_hybrid_check_38_expanded.py` adds five cluster-free checks (supplied in the working tree). `bmad-build-auto-result-3.8-tea.automate-1.md` preserves the supplied test-expansion report. This plan records follow-up review and verification.

**Review.** Quick lens: no findings. Patches: high 0, medium 0, low 0. Nothing deferred or rejected in this pass. Follow-up review recommended: false. Existing deferred-work ledger entries were not modified.

**Verification.** `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`, and `uv run lint-imports` passed. `uv run pytest`: 1101 passed, 16 skipped (Postgres integration tests without their configured database), 53 deselected, 1 expected failure. `uv run python scripts/render_readme_table.py --check` passed. `uv run pytest -m kind tests/integrated` through a local Gateway port-forward: 15 passed, including all four hybrid integrated checks and readiness recovery.

**Residual risks.** This follow-up verified the existing local kind deployment, not a newly created cluster or a GitHub-hosted CI run. The existing CI integrated-check workflow runs the suite on a fresh deployment. Orchestrator verification and ticket completion remain outstanding; no ticket status transition or `tickets.py mark` was performed.
