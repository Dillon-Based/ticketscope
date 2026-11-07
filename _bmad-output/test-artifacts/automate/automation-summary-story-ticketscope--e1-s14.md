---
runScope: 'story'
runKey: 'story-ticketscope--e1-s14'
storyId: '1.14'
storyKey: 'ticketscope--e1-s14'
ticketRef: '1.14 @ _bmad-output/initiative-ticketscope/tickets/epic-search-baseline'
storyFile: ''
testMode: 'expand'
testEntry: 'bmad-tea-automate'
test_mode: 'expand'
test_operation: 'create'
auto_validate: true
auto_heal_failures: true
max_healing_iterations: 3
use_mcp_healing: true
healing_rounds_used: 0
workflowStatus: 'completed'
stepsCompleted: ['step-01-preflight-and-context', 'step-02-identify-targets', 'step-03-generate-tests', 'step-03c-aggregate', 'step-04-validate-and-summarize']
lastStep: 'step-04-validate-and-summarize'
lastSaved: '2026-11-06'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus-findings/outcome-mapping.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus-findings/measure.py
  - src/ticketscope/core/derive.py
  - src/ticketscope/core/snapshot.py
  - tests/unit/test_derive_jira.py
  - tests/unit/test_derive.py
  - pyproject.toml
---

# Automation Summary: story 1.14, Derive Jira outcome and kind in core

Mode selection: expand. The request named it explicitly ("expand mode").
Run: autonomous, BMad-Integrated (v7 ticket `1.14` resolved through `tickets.py find`).
Stack: backend (pytest; `pyproject.toml`, `tests/unit/conftest.py`). Execution mode: sequential. No subagents were dispatched for this single pure-function target.
No ATDD checklist exists for this story. There were no pre-v7 story artifacts to migrate.

## Context

- Criteria (ticket `verify` + plan ACs): one case per Jira outcome class, an unmapped resolution reading unknown, answered and not-answered cases, `{code}`/`{noformat}` kind cases either side of the threshold, and a derivation version that differs from story 4's.
- Test design rows: "Jira outcome derivation in core" (12) and "Jira kind rule in core" (3), owner story 14, P1.
- Existing coverage: `tests/unit/test_derive_jira.py` (built with the story) already covers every matrix row and test-design case. This run adds coverage beyond the matrix; it does not duplicate it.
- Knowledge fragments applied: test-levels-framework, test-priorities-matrix, data-factories, selective-testing, ci-burn-in, test-quality, plus the healing fragments (test-healing-patterns, selector-resilience, timing-debugging). Playwright Utils, Pact and Playwright CLI branches did not open: there is no JS/Playwright runner and no contract artifacts.

## Coverage plan (all Unit level, pure core functions)

| Area | Priority | What it adds over the existing suite |
|---|---|---|
| Resolution table parity | P1 | `RESOLUTION_OUTCOME` equals spike 12's `measure.py` table entry for entry. The table is read with `ast.literal_eval`, never executed. Keys are normalised. |
| Every mapped value | P1 | All 86 values give the right class, `/v1` source, summary and `ref=None`. |
| Unmapped values from the dump | P1 | All 9 values that outcome-mapping.md leaves unknown read `UNKNOWN`. |
| Duplicate spellings / ref | P1/P2 | `Duplicate Issue`, case and whitespace variants, the ref built from another project's key. |
| Trim semantics | P2 | Summary trimmed; inner whitespace not normalised. |
| Schema-version dispatch | P1 | v1 issues keep the GitHub rules; `{code}` in a v1 body is not a fence; backtick fences still count in v2. |
| Answered rule edges | P1/P2 | Type-name matching (case, substring), other types, every fixed-class value, no comments, unmapped without an answer, open Question, missing `resolved_at`, +1 s boundary, cross-timezone comparison, answered-class resolutions keep their own summary. |
| AD-26 edges | P1/P2 | No links, unmapped resolution, direction beats number, equal-number tie-break by key regardless of order, trimmed resolution. |
| Derivation version | P1/P2 | Carries the threshold; rejects a threshold below 1. |
| Toggle regex | P2 | None, plain text, lookalikes (`{codex}`, `{ code }`, a newline in params), case and parameters, mixed toggle pairing, mid-line split. |
| v2 model contract | P1/P2 | JSON-shaped record parses; `schema_version` must be 2; extra/identity fields refused; bad direction; naive `created_at`; frozen; derivation does not mutate the issue. |

## Files created/updated

- Created: `tests/unit/test_derive_jira_expanded.py`, 147 collected tests (parametrised), P1 and P2 tags in docstrings.
- No fixtures or support files were needed. Factories are local builders (`make_jira_issue`, `jira_comment`, `dup_link`, `make_github_issue`, `answered_question`).
- Production source unchanged. The existing tests are unchanged.

## Execution (run and heal)

- Command: `uv run pytest tests/unit/test_derive_jira_expanded.py -q`
- Initial: 147 executed, 147 passed, 0 failed, 0 skipped. Final: same.
- Static checks: the first run found one ruff SIM300 (a Yoda assert) and two formatting diffs in the generated file. `ruff check --fix` and `ruff format` fixed them; this was lint conformance, not a test-behaviour repair. Afterwards `ruff check .`, `ruff format --check .`, `pyright` (0 errors) and `lint-imports` (6 kept) all pass.
- Full suite: `uv run pytest`: 359 passed, 4 deselected (the `kind` marker).
- Healing rounds used: 0. Execution status: **passed**.

## Product defects

None found.

## Assumptions and risks (for the owner)

- **Mixed toggle pairing (pinned, unspecified).** `{code}` … `{noformat}` closes as one block, because both become ``` fences. The sources do not say how Jira pairs them. `test_mixed_toggle_types_close_each_other` pins core's current behaviour. Update it if story 5 or 13 decides otherwise.
- **Parity test reads a planning artifact.** `test_resolution_table_matches_spike_12_verbatim` reads the spike's `measure.py` under `_bmad-output/`. If that folder moves, the test fails loudly rather than skipping.
- The deferred `link_type` question (plan, deferred to story 13) is still open. This run does not test a non-Duplicate `link_type`, because the intended behaviour is undecided.
- A closed issue with `resolved_at=None` is never answered. This matches the spike and the plan's rejected finding, and is pinned by `test_closed_question_without_resolved_at_is_not_answered`.

## Playwright Utils deviations

None (no Playwright runner in this project; the mandate does not apply to pytest).

## Next recommended workflow

`bmad-tea-trace` for epic 1 once story 13 lands. Alternatively, `bmad-tea-test-review` on `tests/unit/test_derive_jira*.py`.
