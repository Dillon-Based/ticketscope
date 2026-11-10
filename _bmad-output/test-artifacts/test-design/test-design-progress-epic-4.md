---
runScope: 'epic'
runKey: 'epic-4'
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-10'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/.memlog.md
  - _bmad-output/initiative-ticketscope/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
  - _bmad-output/test-artifacts/test-design/test-design-epic-3.md
  - _bmad-output/test-artifacts/gate-waivers.md
  - src/ticketscope/contract/search.py
  - src/ticketscope/http/app.py
  - src/ticketscope/telemetry.py
  - src/ticketscope/settings.py
  - src/ticketscope/core/ports.py
  - src/ticketscope/core/fakes.py
  - src/ticketscope/core/derive.py
  - src/ticketscope/adapters/postgres.py
  - .importlinter
  - pyproject.toml
  - uv.lock
  - deploy/charts/ticketscope/values.yaml
  - deploy/charts/ticketscope/values-kind.yaml
  - deploy/charts/ticketscope/templates/api.yaml
  - .github/workflows/ci.yml
  - .github/workflows/eval.yml
  - .github/workflows/_kind-deploy.yml
  - .github/kind-paths.yml
  - scripts/kind-up.sh
  - scripts/v1_parity.py
  - scripts/fault-inject.sh
  - tests/conftest.py
  - tests/target.py
  - tests/waiting.py
  - tests/smoke/test_gateway.py
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/nfr-criteria.md
---

# Progress: test design for epic 4 (epic-mcp-server)

## Step 1: mode and run identity

- Mode: epic-level, because the user named epic 4 (`/bmad-tea-test-design epic 4`).
- `epic_num` 4, `run_scope` epic, `run_key` epic-4. Slug `epic-mcp-server`.
- Inputs: the refined epic file and its `tickets/tickets.toml`, committed on branch `epic-4-plan-mcp-server` (commit 3cb8a82), not yet on `main`.
- No earlier epic-4 checkpoint existed.

## Step 2: context loaded

- Stack: backend (Python 3.14, uv, Postgres, Helm, kind). No frontend, so no browser exploration.
- Knowledge fragments: risk-governance, probability-impact, test-levels-framework, test-priorities-matrix, nfr-criteria (the epic carries security, reliability and observability requirements).
- No system-level test design exists; epic 3's plan is the format reference.
- Code facts that shape the plan:
  - No `ticketscope.mcp` or `ticketscope.apiclient` yet. `uv.lock` has `httpx2` 2.16 and a transitive `httpx`, but neither the `mcp` SDK nor `opentelemetry-instrumentation-httpx`.
  - `contract.ModeName` is a `Literal`, so a client-side `SearchRequest` rejects an unknown mode before the API sees it.
  - `http.app` answers every `/v1` error as problem+json (422 with `errors`, 404, 503, 500).
  - The kind Gateway listener pins `hostname: ticketscope.kind.internal` (platform `values-kind.yaml`).
  - `scripts/kind-up.sh` waits for, and on a same-tag rebuild restarts, only `ticketscope-api`.
  - `scripts/v1_parity.py compare` requires byte-identical bodies; it has no way to drop `issue.key`.
  - `ci.yml`'s `evidence` job reads only its own run's `reports-*`; a separate `mcp-e2e.yml` run does not feed `live-verification-results.json`.
  - `tests/waiting.eventually` and the smoke Tempo helpers (`_spans`, `_poll_trace`, `_tempo` via the API-server service proxy) are the patterns to copy; `test_no_sleep_in_tests.py` forbids `time.sleep`.
  - Epic 3's oversized tracer (3.1) shows `review: thorough` with two follow-up passes, so the independent-review control now works.

## Step 3: risks

Eleven scored risks, R-001 to R-011, numbered by first gap statement (epic file, then tickets.toml, then spine, then code):

| ID | Cat | Gap | P | I | Score |
| --- | --- | --- | --- | --- | --- |
| R-001 | SEC | "There is none yet; epic 6 adds it" — unauthenticated /mcp on a public tunnel | 2 | 2 | 4 |
| R-002 | TECH | Tunnel fidelity: "if ngrok's free plan fails a check"; quick tunnels "lack SSE" | 2 | 2 | 4 |
| R-003 | TECH | Claude Desktop compatibility is "the least certain part" and "not re-run in CI" | 2 | 3 | 6 |
| R-004 | TECH | Story 1 "likely more than 800 added lines" | 2 | 2 | 4 |
| R-005 | BUS | "not the contract's Literal, so an invalid mode reaches the API": apiclient's request model can still reject locally | 2 | 2 | 4 |
| R-006 | OPS | "Envoy otherwise 404s the tunnel's Host header": the listener hostname is not in the story's list | 3 | 2 | 6 |
| R-007 | DATA | key "null when the url is not a browse URL"; spine "silently getting a different issue" | 2 | 3 | 6 |
| R-008 | TECH | Tempo lookup duplicated; "unifying ... left for a later sweep" | 2 | 1 | 2 |
| R-009 | OPS | "scaling api to zero as the suite's last step" | 2 | 2 | 4 |
| R-010 | TECH | Spine "GenAI semconv drift ... revisit at the next telemetry change" | 2 | 1 | 2 |
| R-011 | OPS | kind-up "waits for api to be Ready" and restarts only api | 2 | 2 | 4 |

Clarifications C-1 to C-9 (httpx2 instrumentation, finding the no-context trace, header vs `_meta` traceparent, key format, unreachable-API detail and timeout, non-problem error bodies, evidence pipeline, key field optionality, protocol versions Claude Desktop sends). Details in the final document.

NFR: security (no auth, host check, no committed credential, only /mcp on the tunnel host), reliability (stateless at two replicas, errors never protocol failures, mcp readiness independent of api), maintainability (import-linter, one contract, no sleeps). Unknown thresholds: apiclient timeout, mcp resources, tunnel bandwidth, Tempo ingestion bound for the mcp check.

## Step 4: coverage plan

122 scenarios: 23 P0, 82 P1, 13 P2, 4 P3. Each of the eleven risks has exactly one risk-linked row: R-003 and R-007 at P0; R-001, R-004, R-005, R-006 and R-009 at P1; R-002 and R-011 at P2; R-008 and R-010 at P3. The third P0 row is the core `search_similar_issues` contract on kind (no risk link). Seven independent oracles: snapshot `key` against the url-derived key, the direct `/v1` body through the Gateway, `jsonschema` against the generated schema, `values.yaml`'s default mode, problem bodies recorded from the real app factory, Tempo parent links, and Claude Desktop's captured handshake.

## Step 5: output

- Execution mode: sequential (one epic document).
- Plan: `_bmad-output/test-artifacts/test-design/test-design-epic-4.md`, copied beside the epic at `tickets/epic-mcp-server/test-design-epic-4.md` as epic 3's was.
- Checked from disk: score = probability x impact for all eleven risks, every table row's cell count matches its header, scenario totals (23, 82, 13, 4 = 122) match the summary, and each risk has exactly one risk-linked row.
- No browser sessions were opened. No `workflow.on_complete` hook is set.

## Edit: clarifications decided (2026-11-10)

- Dillon decided C-1 to C-9, each with the recommended option. The plan's Clarifications section now records them as decisions, and the entry criteria, NFR table, R-007 and Proposed Story Updates were updated to match.
- Evidence for C-4: `httpx2` 2.16 builds `/v1/issues/by-key/../6629` as `GET /v1/issues/6629` and `MCL-6629?x=1` as a query string; percent-encoding the key keeps it one segment. R-007's mechanism (a) is confirmed.
- No risk score, priority or scenario count changed. Table validation re-run clean.
