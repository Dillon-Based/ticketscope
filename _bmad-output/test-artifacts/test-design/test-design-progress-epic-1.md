---
runScope: 'epic'
runKey: 'epic-1'
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-06'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md
  - _bmad-output/initiative-ticketscope/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/initiative-ticketscope.md
  - _bmad-output/initiative-ticketscope/brief-ticketscope/brief-ticketscope.md
  - _bmad-output/initiative-ticketscope/brief-ticketscope/addendum.md
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/nfr-criteria.md
  - knowledge/playwright-cli.md
---

# Step 1: Mode detection

- Mode: Epic-Level (user asked for "the first epic"; active initiative `initiative-ticketscope` holds epics in `tickets/`).
- Epic: id 1, `epic-search-baseline` — "Keyword search over Kubernetes issues, deployed on kind". Covers R1, R2, R3, R5, R8, R11.
- Prerequisites: epic file with requirements present; brief + addendum available as architecture context. No architecture doc yet.
- No prior checkpoint: fresh run.

# Step 2: Context loaded

- Config: playwright_utils=true, pactjs_utils=true (package absent, contract testing not relevant), pact_mcp=mcp (n/a), browser_automation=auto, test_stack_type=auto.
- Detected stack: none yet (greenfield: no package.json, pyproject, go.mod, or tests). Target stack from epic: fullstack (one search page + retrieval API + ingest job + Helm/kind infra).
- Artifacts: epic-search-baseline (no stories yet, refined=false), initiative R1–R13, brief, addendum. No PRD, no architecture doc (bmad-architecture run is planned before stories), no system-level test design.
- Existing coverage: none. Browser exploration skipped: no running app.
- Knowledge fragments: risk-governance, probability-impact, test-levels-framework, test-priorities-matrix, nfr-criteria, playwright-cli.
- Gaps: stack/language, API contract, span contract, outcome-source rule ("how it ended") are undecided; they are architecture outputs.

# Step 3: Risk assessment

Gap statements (source order: epic, tickets.toml, initiative, brief, addendum): the epic file and tickets.toml state none; initiative Notes (shared decisions unsettled); initiative Open questions (how it ended; corpus terms); brief Problem (keyword search fails both kinds). The brief's Open Questions repeat the initiative's and are merged into them.

| Risk ID | Category | Description | Probability | Impact | Score |
|---|---|---|---|---|---|
| R-001 | TECH | Shared decisions not yet settled (retrieval API contract, span conventions, chart and CI layout, schema ownership; initiative Notes); epics 2-7 build on them, so drift breaks downstream epics | 2 | 3 | 6 |
| R-002 | DATA | How it ended: outcome source undecided (initiative Open question); R1 needs an outcome for every issue, so outcomes go missing or wrong | 3 | 2 | 6 |
| R-003 | BUS | Corpus terms unknown (initiative Open question): storing and serving issue text in a public demo index may be disallowed, forcing a schema/corpus rework | 2 | 2 | 4 |
| R-004 | BUS | Keyword search fails both kinds of ticket (brief Problem): epic 1 ships keyword only, so its vague/log-heavy acceptance passes on any ranked list while results are irrelevant or noise-drowned | 3 | 2 | 6 |

Scope constraints (regression assertions, not scored): issues API read only; only public material, nothing youscope-derived; no server-side LLM generation; claim-discipline phrase check.

Clarifications (no source statement): API rate limits and token handling for ingest; ingest re-run idempotency; CI time budget for the kind deploy per PR; rule classifying short vs log-heavy; corpus size for epic 1.

NFR planning: performance UNKNOWN (no latency or CI duration target; p95 belongs to epic 2); reliability = CNPG data survives pod restart on PVs, backups/drills out (epic 5); security = read-only source access, token handling UNKNOWN; observability = one trace per search with retrieval + DB spans, GenAI semconv (R8); compliance = R-003 + claim discipline.

# Step 4: Coverage plan

- P0 (3): Helm chart on kind smoke, E2E.
- P1 (24): R-001 contract, API (5); R-002 outcome per closing path, Integration (6); R-004 relevance on golden queries, API (4); ingest fields, Integration (4); search page journey, E2E (2); one trace per search, E2E (1); span contract attributes, API (2).
- P2 (12): R-003 stored-field allow-list, Integration (2); input validation, API (3); page empty/error states, E2E (2); short vs log-heavy rule, Unit (3); read-only source access, Integration (1); CNPG data survives primary pod deletion, E2E (1).
- P3 (3): long snippet rendering, E2E (1); Unicode query normalisation, Unit (2).
- Execution: PR = everything except the CNPG pod-deletion test and live-source ingest smoke (nightly) and full-corpus ingest (weekly).
- Estimates: ~33-56 h total.
- Gates: P0 100%, P1 >=95%, R-001/R-002/R-004 mitigated before epic close.

# Step 5: Output

- Execution mode: sequential (epic-level, single document).
- Output: `_bmad-output/test-artifacts/test-design/test-design-epic-1.md`.
- Checklist validation: passed after fixes (week-range timeline, priority-vs-timing note, cosmetic test moved to Component, PR fail-fast order, residual risk per mitigation, escaped pipe in R-004 row).
- Completed 2026-11-06.
