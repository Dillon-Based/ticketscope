---
runScope: 'epic'
runKey: 'epic-1'
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-06'
outputFile: '_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md'
---

# Test design run: epic-1 (epic-search-baseline), re-run after refinement

This checkpoint replaces the pre-refinement run. The previous plan in this folder was deleted, so only one epic-1 plan exists.

- Step 1: Epic-level mode, epic 1 (`epic-search-baseline`). Output written into the epic's folder at the user's request, for adoption as the epic's companion.
- Step 2: Loaded the refined epic, `tickets.toml` (11 entries), the tracer and ingest story files, the architecture spine, the initiative, the brief and the addendum. Stack from the spine: Python 3.14, FastAPI, psycopg, pytest, ruff, pyright, import-linter. Page is server-rendered with no JS framework, so no browser tooling.
- Step 3: One open risk, R-004 (BUS, 3×2=6): keyword ranking can pass the epic's checks on irrelevant results. R-001 (spine), R-002 (outcome precedence and terms, story 4) and R-003 (story 2 spike gating story 3) are closed and regression-covered. Runner fit is tracked as an assumption.
- Step 4: 58 planned tests (P0 3, P1 40, P2 14, P3 1), ~36–64 hours. R-004 is one API-level row owned by story 5's golden-query file and story 11's assertions.
- Step 5: Sequential mode. Checklist validation passed. Dependency flagged: story 5's and story 11's entries need to name the golden-query file and the twin assertions.
