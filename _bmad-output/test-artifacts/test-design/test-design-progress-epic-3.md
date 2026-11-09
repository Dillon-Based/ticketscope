---
runScope: 'epic'
runKey: 'epic-3'
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-08'
---

# Progress: test design for epic 3 (epic-hybrid-retrieval)

## Step 1: mode and run identity

- Mode: epic-level, because the user named epic 3 ("lets do an epic 3 test design").
- `epic_num` 3, `run_scope` epic, `run_key` epic-3. Slug `epic-hybrid-retrieval`.
- Inputs: the refined epic file and its 8-entry `tickets/tickets.toml`. Both exist only on branch `worktree-plan-epic-3-rebased` (commit 498dcf1), not yet on `main`. This run's worktree branches from it.
- No earlier epic-3 checkpoint existed.

## Step 2: context loaded

- Stack: backend (Python 3.14, uv, Postgres, Helm, kind). No frontend, so no browser exploration.
- Knowledge fragments: risk-governance, probability-impact, test-levels-framework, test-priorities-matrix, nfr-criteria (the epic carries performance, reliability, security and maintainability requirements).
- Read: epic file, tickets.toml, architecture spine (AD-1 to AD-26), epic 2 test design and retrospective, `core/modes.py`, `core/ports.py`, `core/fakes.py`, `adapters/postgres.py`, `jobs/load/main.py`, `jobs/eval/{main,score,gate}.py`, `http/app.py`, `telemetry.py`, `settings.py`, chart values, `eval.yml`, `publish-snapshot.sh`, migration 0001, waivers and deferred work.
- Existing tests: 40+ unit modules, `tests/eval` (kind and Postgres ties), `tests/integrated`, `tests/smoke`. Helm is installed here, so the chart render tests run.

## Step 3: risks

Seven scored risks (R-001 to R-007); three at score 6 (R-001, R-003, R-007). Seven clarifications (C-1 to C-7) go to the PO. Details are in the final document.

## Step 4: coverage plan

112 scenarios: 28 P0, 71 P1, 12 P2, 1 P3. Each of the seven risks has exactly one risk-linked row. One oracle protocol (cosine and RRF fixtures, numpy recompute, embedder reference vectors).

## Step 5: output

- Plan: `_bmad-output/test-artifacts/test-design/test-design-epic-3.md`, copied beside the epic at `tickets/epic-hybrid-retrieval/test-design-epic-3.md` as epic 2's was.
- Checked from disk: score = probability x impact for all seven risks, table cell counts match their headers, scenario totals match the summary.
- No browser sessions were opened.
