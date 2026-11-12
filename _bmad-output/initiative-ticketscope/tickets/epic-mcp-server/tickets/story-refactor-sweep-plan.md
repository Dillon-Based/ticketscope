---
title: 'Refactor sweep (epic 4)'
type: 'refactor'
ticket: '6'
created: '2026-11-12'
status: 'built'
baseline_revision: 'cc3f2e1fb377552de6bc9f3a48ce54466f86d058'
route: 'full'
route_source: 'auto'
risk: 'low'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Epic 4 left duplication: the two tool handlers in `mcp/server.py` repeat their success/error/logging shape, the Tempo parsing exists twice (`tests/mcp/tempo.py`, private helpers in `tests/smoke/test_gateway.py`), `tests/mcp` repeats `_gateway()`, and the api and mcp chart templates repeat the Service block.

**Approach:** Behaviour-preserving cleanup only. Decision (R-008): **unify** the Tempo helpers into one `tests/tempo.py` used by both `tests/mcp` and `tests/smoke`.

## Boundaries & Constraints

**Always:** `/v1` contract, span tree, tool output and rendered chart manifests unchanged (`helm template` output byte-identical before and after); `eval/baseline.json` untouched; import-linter contracts R1, R2, R3, R5 hold; `tests/mcp/captured/*` untouched.

**Never:** change behaviour, add features, edit `eval/baseline.json`, touch `tests/unit/test_mcp_captured_pin.py` fixtures.

</frozen-after-approval>

## Code Map

- `src/ticketscope/mcp/server.py` -- two tool handlers duplicate the `ApiClientError` → tool-error mapping and the ok-result construction.
- `src/ticketscope/apiclient/__init__.py` -- reviewed; no duplication worth changing (error classes and `_send`/`_validated` are already single-sourced).
- `tests/mcp/tempo.py` -- the copy; becomes `tests/tempo.py`. `tests/smoke/test_gateway.py:616-740` -- private `_attributes`, `_spans`, `_kind`, `_tempo` to replace.
- `tests/mcp/test_search_tool.py`, `test_trace.py` -- each define `_gateway()`; share one `gateway()` in new `tests/kind.py` (also used by smoke and integrated).
- `tests/unit/test_mcp_tempo_helper.py` -- imports `tests.mcp.tempo`; retarget.
- `deploy/charts/ticketscope/templates/{api,mcp}.yaml`, `_helpers.tpl` -- identical Service block; extract `ticketscope.service` helper.

## Tasks & Acceptance

**Execution:**
- [ ] `src/ticketscope/mcp/server.py` -- extract shared result/error helpers
- [ ] `tests/tempo.py`, `tests/mcp/*`, `tests/smoke/test_gateway.py`, `tests/unit/test_mcp_tempo_helper.py` -- unify Tempo helpers, share `_gateway`
- [ ] chart -- `ticketscope.service` helper

**Acceptance Criteria:**
- Given the refactor, when `helm template` runs, then output equals the pre-change render.
- Given the refactor, when unit tests, ruff, pyright and lint-imports run, then all pass.

## Implementation Notes

Route full by size; implemented directly (no subagent spawn requested).

## Plan Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest tests/unit tests/mcp -m "not kind"` -- passes
- `uv run ruff check . && uv run ruff format --check . && uv run lint-imports` -- pass
- `helm template ...` diff against the pre-change render -- empty

- Done: Tempo helpers unified in `tests/tempo.py` (decision R-008: unified, not deferred); `gateway()` in `tests/kind.py`; `server.py` `_ok`/`_tool_error`/`_failure`; chart `ticketscope.service` helper. `helm template` identical apart from the random generated password. Local: pytest 1324 passed, ruff, pyright, lint-imports (10 kept), README table check pass. Kind/CI jobs (mcp-e2e, eval) not run locally.
