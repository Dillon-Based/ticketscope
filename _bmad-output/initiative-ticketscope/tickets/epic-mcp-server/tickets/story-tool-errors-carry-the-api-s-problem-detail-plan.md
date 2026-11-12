---
title: 'Tool errors carry the API''s problem detail'
type: 'feature'
ticket: '3'
created: '2026-11-11'
status: done
baseline_revision: '32097a0f78110003b152365ba426328d4df7dc9a'
route: 'full'
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

**Problem:** A failed `/v1` call reaches the MCP client as `Error executing tool search_similar_issues: api returned 422: ...` (the SDK's prefix plus `ApiError`'s own wording), a non-problem error falls back to the reason phrase, and an unreachable API or a 200 that fails the contract is an opaque crash text. R3 needs the API's own detail, a named unreachable reason, and a status-naming generic reason.

**Approach:** `apiclient` raises typed errors that each carry the exact text for the client; the tool returns `CallToolResult(is_error=True)` with that text, so it is the API's detail verbatim, never a JSON-RPC error.

## Boundaries & Constraints

**Always:** `mcp` keeps no mode list: an invalid mode is rejected by the API's 422 detail. Timeout is `TICKETSCOPE_API_TIMEOUT_SECONDS` (already in settings and the chart, default 10). Success output stays the `/v1/search` body unchanged, with the same outputSchema and a text block of the serialised JSON. `mcp`/`apiclient` import only `contract`, `apiclient`, `settings`, `telemetry`.

**Never:** return a response body that is not a problem+json `detail` (C-6); include a stack trace or exception text in a tool error; edit `tests/mcp/captured/`; add `get_issue` (story 4.4) or spans (story 4.5).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Problem response | 422/404/500/503 with `application/problem+json` and a `detail` | tool `is_error`, text == `detail` | none |
| Refused connection | `ConnectError` | text `ticketscope API unreachable: connection refused` | none |
| Timeout | `TimeoutException` | text `ticketscope API unreachable: timed out after <n>s` (n = configured timeout, `:g`) | none |
| Other transport failure | `ReadError`, `RemoteProtocolError` | `ticketscope API unreachable: connection lost` | none |
| Not a problem body | HTML 502, truncated or non-problem JSON on a non-2xx | text names the status and a generic reason, never the body | none |
| Contract failure | 200 whose body fails `SearchResponse` or is not JSON | text `ticketscope API returned HTTP 200: response did not match the contract` | none |
| Bad arguments | `k`=0, 51, or non-integer; missing query | `is_error`, API never called | SDK input validation |

</intent-contract>

## Code Map

- `src/ticketscope/apiclient/__init__.py` -- `ApiError(status, detail)` (problem), `_detail`, `ApiClient.search`; add `ApiClientError` base with `.message`, `ApiError` (problem, message = detail), `ApiBadResponse(status, reason)`, `ApiUnreachable(reason)`; keep the `mode` and `k` handling untouched.
- `src/ticketscope/mcp/server.py` -- `search_similar_issues` returns `SearchResponse` and logs `status=api_<n>` / `status=error`; becomes `Annotated[CallToolResult, SearchResponse]` so outputSchema is unchanged (SDK `func_metadata` lines ~416-440), building the success `CallToolResult` itself (text block `to_json(indent=2)` plus `structured_content = model_dump(mode="json")`).
- `src/ticketscope/http/app.py:42-95` -- the real problem handlers; the unit tests record bodies from `create_app` over `httpx2.ASGITransport(raise_app_exceptions=False)` with `ticketscope.core.fakes.InMemoryCorpusStore`.
- `tests/unit/test_apiclient.py`, `tests/unit/test_mcp_expanded.py`, `tests/unit/test_mcp_server.py` -- 4.1 tests that pin the old reason-phrase fallback and `ValueError`; update them to the new behaviour.
- `tests/mcp/test_search_tool.py` -- kind client tests; add the unknown-mode case.
- `src/ticketscope/settings.py:50`, `deploy/charts/ticketscope/templates/mcp.yaml:34`, `values.yaml` `mcp.apiTimeoutSeconds: 10` -- timeout already wired; do not change.

## Tasks & Acceptance

**Execution:**
- [ ] `src/ticketscope/apiclient/__init__.py` -- typed errors; problem detection requires `application/problem+json` and a non-empty string `detail`; transport errors map to `ApiUnreachable`; non-2xx without a problem and 2xx contract/JSON failure map to `ApiBadResponse` -- C-5, C-6
- [ ] `src/ticketscope/mcp/server.py` -- return `CallToolResult(is_error=True)` with `error.message` for any `ApiClientError`; keep one log line per call -- R3
- [ ] `tests/unit/test_apiclient.py`, `tests/unit/test_mcp_expanded.py`, `tests/unit/test_mcp_server.py` -- update 4.1 tests; add problem bodies recorded from the real app (422, 404, 500, 503) plus refused, timeout, HTML 502, truncated body, 200 contract failure, each `is_error` with expected text and never a JSON-RPC `error`; k=0, k=51, non-integer k
- [ ] `tests/mcp/test_search_tool.py` -- kind test: unknown mode returns `is_error` whose text equals the `detail` of a direct `POST /v1/search` 422 through the Gateway

**Acceptance Criteria:**
- Given an unknown mode, when the tool is called on kind, then `is_error` is true and its text equals the API's 422 detail.
- Given any of 422, 404, 500, 503, refused connection, timeout, HTML 502, or a 200 failing the contract, when the tool is called, then the result is `isError: true` with the specified text and no JSON-RPC `error`.
- Given a successful call, then structured output, text block and outputSchema are unchanged and `mcp-e2e.yml`'s Claude Desktop replay still passes.

## Implementation Notes

Implemented by a subagent per the plan; typed errors in `apiclient`, tool returns `CallToolResult`. The 4.1 tests that pinned the reason-phrase fallback and `ValueError` were updated (the reason-phrase test removed). The kind test and Claude Desktop replay need a cluster and were not run locally.

## Plan Change Log

## Review Triage Log

### 2026-11-11 — Review pass
- verdicts: 2 findings — high 0, medium 1, low 1, false 0, maybe-false 0
- findings:
  - `[medium]` `[patch]` `httpx2.DecodingError` is a `RequestError` but not a `TransportError`, so a bad-encoding body escaped as an opaque SDK crash text — verified in the httpx2 MRO; fixed by catching `RequestError`, test case added.
  - `[low]` `[patch]` direct imports of `mcp_types` and `pydantic_core`, which are transitive — fixed by importing from `mcp.types` and using `model_dump_json(indent=2)`.

### 2026-11-11 — Follow-up review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings: none. The context-free Quick reviewer inspected the complete change since the baseline, including the expanded error-path tests.
- Patched counts: high 0, medium 0, low 0. Follow-up review recommended: false.

## Design Notes

The SDK prefixes any raised `ToolError` with `Error executing tool <name>: `, so exact detail equality needs the tool to return the `CallToolResult` itself; `Annotated[CallToolResult, SearchResponse]` keeps the generated output schema and skips output validation only for errors.

## Verification

**Commands:**
- `uv run pytest tests/unit -q` -- expected: pass
- `uv run ruff check . && uv run ruff format --check . && uv run pyright` -- expected: clean
- `uv run lint-imports` -- expected: contracts kept

## Auto Run Result

Status: built (hand-back result; ticket plan status remains under orchestrator control).

**Summary:** Follow-up Quick review of the full ticket change found no defects. Existing typed API errors and MCP tool-error results satisfy the ticket. Expanded error-path tests are included in the reviewed change.

**Files changed in this pass:**
- `tests/unit/test_apiclient_errors_expanded.py` — 11 existing automation cases covering problem media types, detail preservation and safe transport messages; reviewed and verified.
- `_bmad-output/test-artifacts/automate/automation-summary-story-ticketscope--e4-s3.md` — automation coverage summary.
- `_bmad-output/initiative-ticketscope/bmad-build-auto-result-4.3-tea.automate-1.md` — prior automation result.
- This plan — follow-up review findings and verification evidence.

**Review:** Quick lens; 0 findings, 0 patches, 0 deferred, 0 rejected. Patched counts: high 0, medium 0, low 0. Follow-up review recommended: false.

**Verification:**
- `uv run pytest tests/unit -q` — 1233 passed, including all 11 expanded error-path cases.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — 164 files already formatted.
- `uv run pyright` — 0 errors, warnings or informations.
- `uv run lint-imports` — 10 contracts kept, 0 broken.
- `TUNNEL_HOSTNAME=blitz-utmost-jarring.ngrok-free.dev scripts/kind-up.sh` — current application image deployed to kind successfully, using image tag `2c8320869653d6126887845acc6a447f4ebd982b`.
- `TICKETSCOPE_GATEWAY_URL=http://127.0.0.1:18080 TICKETSCOPE_GATEWAY_HOST=ticketscope.kind.internal TICKETSCOPE_TUNNEL_HOST=blitz-utmost-jarring.ngrok-free.dev uv run pytest -m kind tests/mcp -q --tb=short` — 20 passed, including unknown-mode exact detail equality and all captured Claude Desktop requests. The first attempt failed because the bring-up process's local port-forward ended with its tool session; rerunning with a managed forward held alive for the test process passed. The managed forward was stopped afterward.

**Residual risks:** GitHub Actions itself was not invoked. Its MCP test command passed locally against the deployed current image. No human decision is needed.

**Orchestrator boundary:** No existing deferred-work ledger entry was modified. No `tickets.py mark` command was run. Plan status was preserved; final completion is the orchestrator's responsibility.
