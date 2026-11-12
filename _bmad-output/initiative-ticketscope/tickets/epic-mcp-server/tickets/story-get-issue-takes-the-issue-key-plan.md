---
title: 'get_issue takes the issue key'
type: 'feature'
ticket: 4
created: '2026-11-11'
status: done
baseline_revision: ea879da80c9ddeb6c578f002972f060155e5e730
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/test-design-epic-4.md'
  - '{project-root}/_bmad-output/test-artifacts/atdd/atdd-checklist-ticketscope--e4-s4.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** An MCP client can search but cannot fetch an issue by the key it reads (`MCL-6629`); `/v1` exposes only the internal number, and a key joined into a URL path can silently resolve to a different issue (`../6629`).

**Approach:** Add an optional `key` to the `/v1` `Issue`, derived from `url`; add `GET /v1/issues/by-key/{key}` over a new `CorpusStore.get_issue_by_key`; add a `get_issue(key)` MCP tool that percent-encodes the key and verifies the returned key.

## Boundaries & Constraints

**Always:** `Issue.key: str | None = None` (C-8; an older body still validates). Key derived by one function reusing `core.derive.MOJANG_BROWSE_URL`; null when the url is not exactly `MOJANG_BROWSE_URL` + a key matching `^[A-Z][A-Z0-9]*-[1-9][0-9]*$`. No new column, reload or preprocessing change. The path key must match that pattern exactly (no case/whitespace normalisation) else problem+json 404 (C-4); unknown key is also 404. The by-key response body equals `GET /v1/issues/{number}`. Postgres lookup is an exact match on `url` with the value as a bound parameter. apiclient percent-encodes the key as one path segment (`quote(key, safe="")`). Tool errors come through story 3's `ApiClientError` path.

**Never:** Edit `tests/key_oracle.py` or `tests/unit/test_key_oracle_pinned.py` (pinned; import the oracle). Change `GET /v1/issues/{number}` beyond the added key, touch the page, or change `eval/baseline.json`. No bare `ApiClient` URL joining of an unescaped key.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Known key | `get_issue("MCL-6629")` of a loaded issue | Structured `IssueResponse` whose `issue.key` is that key, with outcome | No error |
| Unknown key | well-formed key matching no issue | API 404 problem detail | tool `is_error` with the API's detail |
| Hostile key | each of `tests.key_oracle.HOSTILE_KEYS` | never another issue; `FORBIDDEN_NUMBER` never fetched | tool `is_error` |
| Dot-segment key | `DOT_SEGMENT_KEYS` through a spy transport | request path stays `/v1/issues/by-key/<encoded>` | `is_error` |
| Key mismatch | fake /v1 returns an issue with a different key | no issue returned | tool `is_error` |
| Non-browse url | url not a browse url (v1-shaped fixture) | `key` is null | none |
| URL derivation | each `URL_TO_KEY` row; every `snapshot/fixture.jsonl` issue | derived key equals oracle / snapshot `key` | none |
| Search results | `POST /v1/search` | each `issue` carries `key` | none |

</intent-contract>

## Code Map

- `src/ticketscope/contract/search.py` -- `Issue` (add `key`); `IssueDetail` subclasses it.
- `src/ticketscope/core/derive.py:84` -- `MOJANG_BROWSE_URL`; add the key-from-url function and `KEY_PATTERN` here (core, importable by http).
- `src/ticketscope/core/ports.py`, `core/fakes.py` -- `CorpusStore.get_issue` neighbours; add `get_issue_by_key(key) -> IssueDetail | None` (fake: match on `url == MOJANG_BROWSE_URL + key`).
- `src/ticketscope/adapters/postgres.py:112` -- `_ISSUE_SQL`/`get_issue`; add a by-url query, bound parameter, runs as `ticketscope_ro`.
- `src/ticketscope/http/app.py` -- `_results` and `get_issue` route build `Issue`/`IssueDetail`: set `key`; add `/v1/issues/by-key/{key}` (declare before/alongside `/v1/issues/{number}`; sharing one body builder).
- `src/ticketscope/apiclient/__init__.py` -- add `get_issue(key) -> IssueResponse` with the same error mapping as `search`.
- `src/ticketscope/mcp/server.py` -- add `get_issue` tool; output schema from `IssueResponse`; mismatch -> `is_error`.
- `scripts/v1_parity.py` (+ `scripts/v1-parity.sh` pass-through) -- option on `compare` dropping exactly `issue.key` from each result before comparing.
- `tests/key_oracle.py` -- read-only oracle. `tests/postgres/conftest.py` -- `pg_conninfo` fixture. `tests/mcp/test_search_tool.py` -- kind client test pattern. `tests/mcp/captured/*.json`, `tests/unit/test_mcp_captured_pin.py` -- check whether adding a tool breaks the captured Claude Desktop replay and pin; update per their documented procedure if so.

## Tasks & Acceptance

**Execution:**
- [ ] `src/ticketscope/contract/search.py`, `core/derive.py` -- add `key` and the url-derived key function -- one source for the key
- [ ] `core/ports.py`, `core/fakes.py`, `adapters/postgres.py` -- by-key lookup -- exact url match, bound parameter
- [ ] `http/app.py` -- set `key` on every `/v1` issue; by-key route with pattern check and 404s -- C-4
- [ ] `apiclient/__init__.py`, `mcp/server.py` -- encoded `get_issue`, tool and key check -- R-007
- [ ] `scripts/v1_parity.py` (and `.sh` if it forwards options) -- drop-`issue.key` option -- parity stays meaningful
- [ ] tests -- unit (oracle rows, hostile keys, spy transport, mismatch, parity script pass/fail on other difference, every v2 fixture issue url key == snapshot key, search carries key), Postgres container test (as `ticketscope_ro`, SQL-shaped key returns nothing, agrees with fake), kind client test (key from a `search_similar_issues` result) -- verify line

**Acceptance Criteria:**
- Given a search result's key, when `get_issue` is called with it, then the issue with that key and its outcome returns, valid against the generated schema.
- Given an unknown key, when `get_issue` is called, then `is_error` carries the API's detail.
- Given any hostile key, when `get_issue` is called, then `is_error` and no other issue is fetched.
- Given two bodies differing only in `issue.key`, when the parity script compares with the option, then it passes; any other difference fails.
- Given the existing suite, when run, then it passes with `eval/baseline.json` unchanged.

## Implementation Notes

## Plan Change Log

## Review Triage Log

### 2026-11-11 — Review pass
- verdicts: 4 findings — high 0, medium 0, low 3, false 1, maybe-false 0
- findings:
  - `[false]` `[reject]` Telemetry `_SearchBrokenStore` doubles lack `get_issue_by_key`, so pyright fails — `uv run pyright` reports 0 errors on the final tree; `_client` does not type the store against the protocol.
  - `[low]` `[reject]` `--drop-issue-key` re-serialises bodies, so key order and whitespace stop counting — real but negligible: the API emits a fixed order, the option is opt-in, and the fix would add complexity.
  - `[low]` `[reject]` `GET /v1/issues/by-key/` (empty key) answers 307, not a problem+json 404 — confirmed by running it; the tool still returns `is_error` and no other issue, only with a less specific message; a fix needs an extra route.
  - `[low]` `[reject]` Postgres test passes no NUL-bearing key — hypothetical; no oracle value contains one.


### 2026-11-11 — Follow-up review pass
- verdicts: 3 findings — high 0, medium 1, low 2, false 0, maybe-false 0
- findings:
  - `[low]` `[reject]` Empty key does not receive a problem+json 404 — carried: same location and claim as the prior rejected empty-key row; routing is unchanged. The tool errors without returning another issue; an extra route would add complexity for an input outside everyday use.
  - `[low]` `[reject]` `--drop-issue-key` normalizes JSON serialization beyond dropping the field — carried: same location and claim as the prior rejected parity row; implementation is unchanged. The API emits fixed serialization; the opt-in comparison still detects other JSON value differences, and preserving raw serialization would add complexity.
  - `[medium]` `[patch]` Verification found `tests/mcp/test_search_tool.py` treats real corpus key `MCL-1` as unknown — the deployed server correctly returned that issue. Replaced the test input with `MCL-99999999999999999999`, asserted the direct API returns 404, and compared the tool error text to its problem detail. All 21 MCP kind tests pass.

## Design Notes

Percent-encode with `urllib.parse.quote(key, safe="")` so `/`, `?` and `#` stay inside one segment. `quote` leaves `.` alone, so a key that is exactly `..` or `.` would still be a dot segment: a spy-transport test on `DOT_SEGMENT_KEYS` decides, and if any path resolves outside `/v1/issues/by-key/`, also encode `.` as `%2E`. The client sends hostile keys and lets the API 404 them; it does not pre-validate.

## Verification

**Commands:**
- `uv run pytest tests/unit tests/mcp -m "not kind"` -- expected: pass, including `test_key_oracle_pinned.py`
- `uv run pytest tests/postgres` -- expected: pass or skip without a Postgres image
- `uv run ruff check . && uv run pyright` -- expected: clean
- `uv run python scripts/v1_parity.py compare --help` -- expected: shows the drop-key option

## Auto Run Result

Status: built. Existing plan status preserved; completion belongs to the orchestrator.

**Summary:** Reviewed the existing issue-key implementation and the preceding expanded-test artifacts. Corrected the kind test's unknown-key assumption: `MCL-1` exists in the pinned corpus. The test now proves its missing-key input receives a direct API 404 and checks the tool carries the same problem detail.

**Files changed in this follow-up:**
- `tests/mcp/test_search_tool.py`: valid missing-key fixture and direct API/detail assertions.
- `tests/unit/test_get_issue_by_key_expanded.py`: reviewed and retained the preceding automation run's 38 expanded cases.
- `_bmad-output/test-artifacts/automate/automation-summary-story-ticketscope--e4-s4.md` and `_bmad-output/initiative-ticketscope/bmad-build-auto-result-4.4-tea.automate-1-g1.md`: retained automation hand-off artifacts.
- This plan: follow-up triage and verification evidence. No change to its status.

**Implementation carried forward:** optional URL-derived contract key; strict by-key API route over the port, fake and bound-parameter Postgres lookup; encoded apiclient lookup and MCP tool with returned-key validation; additive response updates; parity drop-key option; eval store forwarding and acceptance tests.

**Review:** quick lens; two carried low rejections (empty-key API routing and opt-in JSON serialization normalization), with reasons above. Verification found one medium test defect and it was patched. Patched entries: high 0, medium 1, low 0. Deferred: 0. Follow-up review recommended: false (follow-up pass, no high patch). Existing deferred-work ledgers untouched.

**Verification:**
- `uv run pytest tests/unit tests/mcp -m "not kind"`: 1,316 passed, 21 deselected after the correction.
- `TICKETSCOPE_TEST_PG_IMAGE=ticketscope-postgres:18-e46e89ccf5fd205e1ed6eec0f5745671f8c17e1e TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1 uv run pytest tests/postgres`: 35 passed, including read-only by-key lookup and fake agreement.
- `uv run ruff check .`: passed. `uv run pyright`: zero errors/warnings.
- `uv run python scripts/v1_parity.py compare --help`: exposes `--drop-issue-key`.
- `TICKETSCOPE_GATEWAY_URL=http://127.0.0.1:18081 TICKETSCOPE_GATEWAY_HOST=ticketscope.kind.internal uv run pytest -m kind tests/mcp --tb=short`: all 21 passed, including Claude Desktop captured-request replay, search-to-key round trip and unknown-key detail. Initial attempt lacked a port-forward; a valid forward resolved it. The next run identified the test fixture defect fixed above.
- Live parity: baseline `ea879da80c9ddeb6c578f002972f060155e5e730` API source ran in a temporary directory in the current API pod against the same corpus. All three requests captured by `scripts/v1_parity.py` match the current Gateway responses with `--drop-issue-key`. Unit coverage verifies other JSON-value differences fail comparison.
- `EVAL_ENABLED=1 scripts/kind-up.sh`: successful retry, all three modes scored over 10,473 pairs in 743.3 seconds. First attempt failed during the Postgres image rollout with "database system is shutting down"; retry after database Ready succeeded.
- `uv run python -m ticketscope.jobs.eval.gate --baseline eval/baseline.json --results reports/eval-results.json --base-sha ea879da80c9ddeb6c578f002972f060155e5e730`: PASSED.
- `TICKETSCOPE_GATEWAY_URL=http://127.0.0.1:18080 TICKETSCOPE_GATEWAY_HOST=ticketscope.kind.internal uv run pytest -m kind tests/eval --tb=short`: 11 passed in 156.40 seconds, including independent retrieval-rank checks and byte-identical pair regeneration.
- `eval/baseline.json`, the independent key oracle and pin test, and captured Claude Desktop request bytes remain unchanged from baseline.

**Residual risks:** the two carried low issues remain as documented. CI's hosted `mcp-e2e.yml` itself was not invoked here; its local kind test command passed. No human decision is required.
