---
runScope: 'epic'
runKey: 'epic-6'
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-26'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/epic-mcp-oauth.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
  - src/ticketscope/mcp/server.py
  - .venv/.../mcp/server/auth (SDK 2.3.0)
  - deploy/charts/ticketscope/templates/mcp.yaml
  - .github/workflows/mcp-e2e.yml
  - '{tea-knowledge}/risk-governance.md'
  - '{tea-knowledge}/probability-impact.md'
  - '{tea-knowledge}/test-levels-framework.md'
  - '{tea-knowledge}/test-priorities-matrix.md'
  - '{tea-knowledge}/nfr-criteria.md'
  - '{tea-knowledge}/playwright-cli.md'
---

# Test Design Progress — epic 6 (epic-mcp-oauth)

## Step 1: Mode detection

- Mode: Epic-Level (user named "epic 6"; epic file has R1–R5 with acceptance criteria and seven sliced entries).
- epic_num: 6; run_scope: epic; run_key: epic-6.
- Inputs: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/epic-mcp-oauth.md`, `.../tickets/tickets.toml`, architecture spine.
- No prior checkpoint for epic-6.

## Step 2: Context

- Stack: backend (pyproject.toml; no package.json, no Pact artifacts, so no contract-testing fragments). No UI in scope; browser exploration skipped.
- Fragments: risk-governance, probability-impact, test-levels-framework, test-priorities-matrix, nfr-criteria (security epic), playwright-cli (auto browser mode; unused).
- No system-level test design exists; prior epic plans 3–5 used as house format.
- Existing coverage: tests/mcp/* are all `-m kind` (client, replay, trace, unreachable api); tests/unit/test_mcp_*.py cover server in-process, settings, captured-request pin, chart. No auth code, no JWT dependency yet.
- SDK facts (mcp 2.3.0): `MCPServer(token_verifier=, auth=AuthSettings)` wires BearerAuthBackend + RequireAuthMiddleware; metadata route registered at `/.well-known/oauth-protected-resource{resource path}` (RFC 9728 path insertion, i.e. `/…/mcp`); missing scope returns 403 `insufficient_scope` naming the scope; 401 body is generic "Authentication required"; SDK only checks `exp` when present; audience check compares `AccessToken.resource` to `resource_server_url`.
- Gateway: mcp HTTPRoute is PathPrefix `/mcp` only today; tunnel listener admits only the /mcp route; `/healthz` probes are pod-local, not routed.

## Step 3: Risk register (full text in test-design-epic-6.md)

Sources read in order: epic file (Constraints, Notes), epic tickets.toml (stories 1–7), spine AD-5/AD-14/AD-25, then mcp.yaml and the mcp 2.3.0 SDK auth modules.

| Risk | Cat | P | I | Score | Gap statement |
| R-001 | SEC | 2 | 3 | 6 | "mcp has no auth default that bypasses a check" (Constraints › Values) + story 4 render check |
| R-002 | TECH | 2 | 3 | 6 | "CI never calls the hosted authorisation server" — stub imitates recorded claims |
| R-003 | BUS | 2 | 3 | 6 | spike "proving Claude Desktop completes the flow" (Notes; story 1) |
| R-004 | SEC | 2 | 3 | 6 | story 3 "nothing invalid passes" |
| R-005 | OPS | 2 | 2 | 4 | story 3 key cache and one refetch on unknown kid |
| R-006 | OPS | 2 | 2 | 4 | story 3 "if the keys cannot be fetched ... refused ... stays Ready" |
| R-007 | SEC | 2 | 3 | 6 | story 3 token/header/key never in a log line or span |
| R-008 | SEC | 3 | 1 | 3 | story 3 generic error body + SDK 403 insufficient_scope naming the scope |
| R-009 | SEC | 1 | 3 | 3 | story 4 stub issuer "nothing about it renders in any other release" |
| R-010 | TECH | 3 | 3 | 9 | story 4 "The route table does not change" vs mcp.yaml routing only /mcp and SDK path-inserted metadata |
| R-011 | OPS | 2 | 2 | 4 | story 7 AuthKit "configured in the WorkOS dashboard by a person" |
| R-012 | SEC | 2 | 3 | 6 | story 7 recording committed "with no token or key visible"; AGENTS.md person-identifier policy |

NFR: security thresholds defined (refusal cases, no leakage); reliability thresholds UNKNOWN (key cache TTL, refetch interval, JWKS timeout, clock leeway); performance: no auth-latency budget (UNKNOWN).

## Step 4: Coverage plan

- P0: R-001 (API), R-004 (API), R-012 (E2E), constraint row (B) no AuthKit credential anywhere (Unit) — 25 scenarios.
- P1: R-002 (E2E), R-003 (E2E), R-007 (Integration), R-009 (Integration), R-010 (E2E), rows (C)–(G) — 59 scenarios.
- P2: R-005, R-006, R-008 (API), R-011 (E2E), row (H) — 18 scenarios. P3: row (I) — 1.
- Execution: PR (ci.yml unit/API/render; mcp-e2e.yml kind with auth on), hand-run spike and live window; no nightly/weekly.
- Estimates: ~50–100 hours total. Gates: P0 100%, P1 ≥95%, R-010 mitigated before stories 2 and 4 are planned.

## Step 5: Output

- Execution mode: sequential (epic-level is single-worker).
- Output: `_bmad-output/test-artifacts/test-design/test-design-epic-6.md`.
- Validated: every table row matches its header's cell count; Score = P × I for all 12 risks; each risk has exactly one coverage row; band totals P0 25, P1 59, P2 18, P3 1 (103).
- Open: C-1 to C-8 for the PO; Proposed Story Updates (R-010 on stories 6.2 and 6.4 first).
