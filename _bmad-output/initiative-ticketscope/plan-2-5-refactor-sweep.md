---
title: 'Refactor sweep: dedupe pin parser and kinds, keep time.sleep out of tests'
type: 'refactor'
ticket: '5'
created: '2026-11-08'
status: 'built'
baseline_revision: 'd2313e946d2dfda99f330da3db3e989c5746fb5b'
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

**Problem:** The epic's review findings left duplicated helpers (the chart snapshot-pin parser in `scripts/derive_pairs.py` and `tests/target.py`; the kinds tuple in `jobs.eval.gate` and `jobs.eval.score`), and nothing stops `time.sleep` from entering `tests/` (epic-search-baseline test review G3).

**Approach:** Move the pin parser to `ticketscope.adapters.release` and import it from both callers; derive the gate's `KINDS` from the scorer's. Add a unit test that fails on any `time.sleep` in `tests/`. Behaviour, scores and `eval/baseline.json` do not change.

</intent-contract>

## Implementation Notes

Oneshot: about 80 changed lines across five files, all mechanical. `scripts/render_readme_table.py` keeps its own `KINDS` on purpose: it is standard-library only so CI runs it without installing the project. The kinds tuples in oracle tests stay independent copies by design.

## Plan Change Log

## Review Triage Log

### 2026-11-08 — Review pass
- verdicts: 2 findings — high 0, medium 0, low 2, false 0, maybe-false 0
- findings:
  - `[low]` `[patch]` The no-sleep detector flagged only calls, so `wait=time.sleep` slipped through — it now flags any `time.sleep` reference (attribute or imported name); a case was added to the detector test. `from time import *` and `importlib` spellings are not covered: nothing in the repo uses them and covering them adds machinery.
  - `[low]` `[reject]` `snapshot_pin` survives as a one-line wrapper in `scripts/derive_pairs.py` and `tests/target.py` — the wrappers keep the default chart path and six existing callers unchanged; the parser itself now lives once in `adapters/release.py`.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports` -- expected: clean
- `uv run pytest tests/unit` -- expected: pass, including the new no-sleep test
- `python3 scripts/render_readme_table.py --check && git diff --exit-code eval/baseline.json` -- expected: pass, baseline untouched

## Auto Run Result

**Summary.** The chart snapshot-pin parser now lives once, in `ticketscope.adapters.release.read_snapshot_pin`. The gate's `KINDS` derives from the scorer's. A unit test fails on any `time.sleep` in `tests/`. Behaviour, scores and `eval/baseline.json` are unchanged.

**Files changed.**
- `src/ticketscope/adapters/release.py` — hosts `read_snapshot_pin` (moved, unchanged regexes and errors).
- `scripts/derive_pairs.py`, `tests/target.py` — call it instead of carrying their own copy.
- `src/ticketscope/jobs/eval/gate.py` — `KINDS = (*score.KINDS, "overall")`.
- `tests/unit/test_no_sleep_in_tests.py` — AST scan of `tests/` for `time.sleep` (called or passed), plus detector spelling cases.
- Left alone on purpose: `scripts/render_readme_table.py` (standard library only, so CI runs it without installing the project) and the oracle tests' independent kinds tuples.

**Review.** Quick lens, 2 findings: 1 low patched, 1 low rejected, 0 deferred. Follow-up review recommended: false (patched counts: high 0, medium 0, low 1).

**Verification.** `ruff check`, `ruff format`, `pyright`, `lint-imports` (7 kept, 0 broken) clean; `pytest tests/unit` 910 passed; `render_readme_table.py --check` passes; `eval/baseline.json` has no diff.

**Residual risks.** The PR's eval check and ci.yml's integrated-check have not run here; orchestrator verification is outstanding. The `base.sha` rerun deferral in `deferred-work.md` was left as is. `tickets.py mark` was not run.

status: built
