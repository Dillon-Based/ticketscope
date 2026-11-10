---
title: 'Refactor sweep (epic hybrid retrieval)'
type: 'refactor'
ticket: '7'
created: '2026-11-10'
status: done
baseline_revision: '6752efe8c8cbbe24846b84e25ab7aeca46f859c1'
route: 'oneshot'
route_source: 'auto'
risk: 'low'
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

**Problem:** The epic left duplicated helpers: the keyword and dense retrievers each repeat the "over-fetch by |exclude|, drop excluded, trim to k" step; the postgres adapter repeats the issue column list across three SQL strings and the connect/fetchone pattern; five unit-test files each define the same `_issue(number)` builder; and a stale `sed` backup `tests/eval/test_eval_kind.py-E` is committed.

**Approach:** Behaviour-preserving cleanup only. One shared exclude helper in `core/modes.py`, a shared column constant and fetch helper in the postgres adapter, one `issue_record` builder in `tests/factories.py`, and delete the stray backup. `CorpusStore` issue-lookup methods (`get_issue`, and the by-key lookup epic 4.4 adds), `eval/baseline.json`, and scores are untouched.

</intent-contract>

## Implementation Notes

Oneshot: the change is mechanical and small, with no new behaviour. Candidates came from the epic's plans (duplicated helpers across retrievers and the postgres adapter, test structure) and a read of `core/modes.py`, `adapters/postgres.py` and the unit tests. Deferred items DW-3 to DW-7 are behaviour or environment work, not cleanup, so they stay open.

Follow-up verification repairs (2026-11-10): restored `PostgresCorpusStore.get_issue` and `_ISSUE_SQL` verbatim to their baseline implementations, preserving the ticket's lookup boundary. `_fetchone` now accepts `LiteralString`, matching psycopg's query contract; this fixes the newly exposed Pyright failure without casts or suppression. The expanded issue-SQL assertion compares whitespace-normalized column order so the original lookup SQL stays intact. Existing cleanup and all expanded coverage are preserved. Plan status remains orchestrator-owned.

## Verification

**Commands:**
- `uv run pyright` -- expected: no errors
- `TICKETSCOPE_TEST_PG_IMAGE=ticketscope-postgres:18-story35-local uv run pytest -q` -- expected: non-kind suite passes, including the expanded story tests and real Postgres adapter tests
- `uv run pytest tests/unit -q` -- expected: all pass
- `uv run ruff check . && uv run ruff format --check .` -- expected: clean
- `uv run lint-imports` -- expected: every contract kept
- `git diff --stat -- eval/baseline.json` -- expected: empty

## Review Triage Log

### 2026-11-10 — Review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings: none (quick lens checked the retriever helper, the SQL column constant and f-string conversion, `_fetchone`, the `issue_record` factory and the deleted backup, and found no unmet criteria or bugs)

### 2026-11-10 — Follow-up review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings: none (quick reviewer inspected the complete baseline diff, then the refreshed diff after verification repairs; neither inspection reported findings)

## Auto Run Result

Status: built. The plan's frontmatter status was preserved; ticket completion belongs to the orchestrator.

**Summary.** Completed follow-up verification and repairs of the existing cleanup. Restored the issue lookup and its SQL to baseline and fixed the SQL helper's query typing. Existing deferred-work ledger entries were neither edited nor reopened.

**Files changed.**
- `src/ticketscope/core/modes.py`: shared exclusion/trim helper for keyword and dense retrieval.
- `src/ticketscope/adapters/postgres.py`: shared retrieval column list and metadata fetch helper; `LiteralString` preserves psycopg's query typing. `get_issue` and `_ISSUE_SQL` match baseline exactly.
- `tests/factories.py` and five retriever/contract test files: reuse the issue-record factory.
- `tests/eval/test_eval_kind.py-E`: removed stale backup.
- `tests/unit/test_refactor_sweep_37_expanded.py`: retains all 12 expanded tests; the issue lookup SQL assertion compares whitespace-normalized column order.
- Automation summary and prior automation result: retain the existing test-generation evidence.
- This plan: verification repairs, command outcomes, and follow-up review evidence.

**Review.** Quick review completed twice, with zero findings. Reviewer patches: high 0, medium 0, low 0. Deferred: 0. Rejected: 0. Parent verification repairs: SQL helper query type and restoration of the excluded issue lookup implementation. Follow-up review recommended: false.

**Verification.**
- `TICKETSCOPE_TEST_PG_IMAGE=ticketscope-postgres:18-story35-local uv run pytest -q`: 1112 passed, 49 kind tests deselected, 1 xfailed. Includes all expanded tests and all 16 real Postgres tests in disposable containers.
- `uv run pytest tests/unit -q`: 1096 passed, 1 xfailed before the verification repairs; the complete non-kind suite above reran the unit tests after repairs.
- `uv run pyright`: 0 errors, 0 warnings.
- `uv run ruff check .` and `uv run ruff format --check .`: clean, 137 files formatted.
- `uv run lint-imports`: 7 contracts kept, 0 broken.
- `uv run python scripts/render_readme_table.py --check`: passes.
- Baseline diff for `eval/baseline.json`: empty. AST comparison confirms `get_issue` and `_ISSUE_SQL` are identical to baseline `6752efe8c8cbbe24846b84e25ab7aeca46f859c1`.

**Residual risks.** PR eval and integrated kind CI have not been run for this revision; they remain for the orchestrator's verification. The existing cluster was not used as evidence for undeployed local changes. No human decision is required.
