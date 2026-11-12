---
workflowType: 'testarch-test-review'
runScope: 'epic'
runKey: 'epic-4'
---

# Test Quality Review: epic-mcp-server (epic 4) test suite

**Quality Score**: 89/100 (B - Good)
**Raw Deduction Score**: 94/100
**Score Cap**: 89/100
**Score Override Rule**: Highest severity MEDIUM caps effective score at 89: min(raw deduction score 94, 89) = 89.
**Review Date**: 2026-11-12
**Review Mode**: full-file
**Reviewer**: Dillon (interactive invocation of bmad-tea-test-review, background session)

---

Note: This review audits existing tests; it does not generate tests.
Coverage mapping and coverage gates are out of scope here. Use `trace` for coverage decisions.

## Executive Summary

**Overall Assessment**: Good

**Recommendation**: Approve with Comments
**Verdict Rule**: No Critical or High, effective score >= 70, and findings remain => Approve with Comments.

**Context Basis**: pr_diff

**Context Waivers Applied**: 0

**Execution Mode**: sequential

### Key Strengths

✅ Independent oracles are pinned. `tests/key_oracle.py` and the captured Claude Desktop requests are frozen by byte hash (`tests/unit/test_key_oracle_pinned.py`, `tests/unit/test_mcp_captured_pin.py`). The oracle is cross-checked against the snapshot `key` field, not against the parser under test.

✅ Hostile-input tests prove the negative. `tests/unit/test_get_issue_by_key.py` uses a spy store and a spy transport to show that no hostile key reaches issue number 6629 and that every key stays one path segment. The Postgres adapter is checked through the read-only role and against the fake (`tests/postgres/test_issue_by_key_postgres.py`).

✅ Error text is tested for what it must not leak. Problem details are replayed from real app answers (`recorded_problems`), and the apiclient tests assert that a response body, an exception text or a non-problem media type never reaches the tool error.

### Advisory Observations

ℹ️ Stories 4.1 to 4.3 and 4.6 have no `@pytest.mark.criterion` tags, and story 4.4 has them only on the oracle pin, not on the behaviour tests in `tests/unit/test_get_issue_by_key*.py`. `AGENTS.md` requires the tag and `scripts/live_results.py` reads it, so those criteria cannot be traced to a result.

ℹ️ Three in-process MCP harnesses do the same job: `_run` in `tests/unit/test_mcp_server.py`, `_run` in `tests/unit/test_mcp_trace.py` and `_tool_run` in `tests/unit/test_get_issue_by_key.py`. `_client()` and the constant `QUERY` are copied across `tests/mcp/test_search_tool.py`, `test_trace.py` and `test_unreachable_api.py`. Test modules also import each other's privates: `test_mcp_expanded.py` takes `_run` and `_call` from `test_mcp_server.py`, `test_chart_tunnel_listener.py` takes `_docs` and `_render` from `test_chart_backup.py`, and `test_mcp_replica_check.py` imports a kind test module and calls its test function directly. A shared `tests/mcp_harness.py` would remove the copies.

ℹ️ `tests/unit/test_mcp_workflow.py` and `tests/unit/test_tunnel_script.py` assert substrings of YAML and shell text. `trap cleanup EXIT` and `kill "$PID"` being present does not show the tunnel stops, and `text.index("# 7. Gateway address")` depends on a comment. This is the pattern `test_eval_workflow.py` already uses, so it is consistent, but these checks prove wiring text, not behaviour.

ℹ️ `tests/tempo.py` `search()` and `_get()` turn every non-200 answer, and any JSON parse failure, into an empty list. A Tempo outage then surfaces in `tests/mcp/test_trace.py` as "expected one trace in the window, found []", which hides the cause. The helper's unit tests (`test_mcp_tempo_helper.py`) cover span parsing only.

ℹ️ `tests/mcp/test_unreachable_api.py` scales `api` to zero. Its safety rests on `--deselect` in `mcp-e2e.yml` and on file-name order locally, and the docstring says "never by test order". Running `tests/mcp` under xdist, or with a different ordering plugin, would put the outage in the middle of the suite.

ℹ️ The two helm-based files (`test_chart_mcp.py`, `test_chart_tunnel_listener.py`) skip silently when `helm` is absent. CI installs helm, so no check is lost there. Unlike the container tests, no `TICKETSCOPE_REQUIRE_*` switch makes the skip fail locally.

### Summary

The epic 4 suite is sound: the unit layer checks behaviour against real or independent oracles, and the kind layer proves each requirement through the Gateway without any timer waits. No test is disabled, vacuous or order-dependent, so nothing blocks. The scored findings are about test-data construction and one test that checks too many things.

---

## Quality Criteria Assessment

| Criterion                            | Status          | Violations | Basis                                              | Notes                                                                                                                         |
| ------------------------------------ | --------------- | ---------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Disabled or Focused Tests            | ✅ PASS         | 0          | Absolute                                           | Only `skipif(helm missing)` with a stated, still-true reason; no `skip`, `xfail` or `only`.                                   |
| Hard Waits (sleep, waitForTimeout)   | ✅ PASS         | 0          | Absolute                                           | Every kind wait goes through `tests.waiting.eventually`.                                                                      |
| Determinism (assertions always run)  | ✅ PASS         | 0          | Absolute                                           | No assertion hides behind a branch or a `try`; kind trace tests use `secrets` ids, not the clock.                             |
| Isolation (cleanup, no shared state) | ✅ PASS         | 0          | Absolute                                           | `tests/unit/conftest.py` autouse restores env, logging and the tracer provider; `api_at_zero` restores replicas in `finally`. |
| Data Factories                       | ⚠️ WARN         | 2          | Applicability: the file constructs domain payloads | `/v1` issue bodies built inline while `tests.factories.issue_payload` exists.                                                 |
| Explicit Assertions                  | ✅ PASS         | 0          | Absolute                                           | No test without an assertion; the parametrised replay test asserts inside `_send`.                                            |
| Multi-concern tests                  | ⚠️ WARN         | 1          | Absolute                                           | One test asserts four unrelated subjects.                                                                                     |
| Test Length (≤1000 lines)            | ✅ PASS         | 0          | Absolute                                           | Longest file `tests/unit/test_get_issue_by_key.py`, 324 lines.                                                                |
| Test Duration (≤1.5 min)             | ➖ Not measured | -          | Not measured                                       | A static read cannot time a run                                                                                               |

**Total Violations**: 0 Critical, 0 High, 3 Medium, 0 Low

**Convention Baseline**: 79 test files outside the review set; 8 sampled (`tests/eval/test_eval_kind.py`, `tests/postgres/test_eval_reuse_postgres.py`, `tests/unit/test_chart_defaults_expanded.py`, `test_ci_containers.py`, `test_derive.py`, `test_eval_main.py`, `test_hybrid_expanded.py`, `test_integrated_check_expanded.py`). Convention: dataFactories (3 of 8 sampled, emerging, `tests.factories` builders).

---

## Quality Score Breakdown

```text
Starting Score:          100
Critical Violations:     -0 × 10 = -0
High Violations:         -0 × 5 = -0
Medium Violations:       -3 × 2 = -6
Low Violations:          -0 × 1 = -0

Bonus Points:
  Comprehensive Fixtures: +0
  Data Factories:        +0
  Network-First:         +0
  Perfect Isolation:     +0
  All Test IDs:          +0
                         --------
Total Bonus:             +0

Raw Deduction Score:     94/100
Score Cap:               89/100 (MEDIUM)
Effective Score:         89/100
Grade:                   B
```

---

## Critical Issues (Must Fix)

No critical issues detected. ✅

---

## Recommendations (Should Fix)

### 1. One telemetry test checks four unrelated subjects

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_mcp_trace.py:326`
**Row**: M3

**Issue**: `test_setup_without_db_does_not_instrument_psycopg` asserts that psycopg is not instrumented, that the provider's `service.name` is `ticketscope-mcp`, that the semconv opt-in environment variable is set, and, after a second `setup` call for the API, that psycopg is instrumented once. A failure names the test, not which of the four broke. The test name also covers only the first.

**Fix**: Split into three tests: `instrument_db=False` skips psycopg (and the API call instruments it once), setup names the provider's service, and setup sets the semconv opt-in. Share the monkeypatched `instrument_psycopg` spy through a fixture.

---

### 2. `get_issue` response body built inline in the trace tests

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_mcp_trace.py:45`
**Row**: M2

**Issue**: `ISSUE_BODY` writes out a full `/v1` issue and outcome payload by hand, although `tests.factories.issue_payload` and `outcome_payload` build exactly this shape and take overrides. When the contract gains a required field, the factory is updated in one place and this literal silently drifts.

**Fix**: Build it from the factories:
`{"issue": issue_payload(6629, url="https://bugs.mojang.com/browse/MCL-6629", key="MCL-6629", body=None), "outcome": outcome_payload()}`.

---

### 3. `_issue_line` repeats the same payload shape

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_get_issue_by_key.py:67`
**Row**: M2

**Issue**: `_issue_line` hand-builds the same `/v1` issue and outcome payload and bypasses `tests.factories.issue_payload` and `outcome_payload`. It is a second copy of the shape in finding 2, in the epic's other main test file, and the two copies differ in `state` (`open` vs `closed`) for no stated reason.

**Fix**: Build it from the same factories, with `key`, `url` and `body=None` as overrides, and move the shared builder into `tests/factories.py` so both files call one function.

---

## Decision

**Recommendation**: Approve with Comments

---

## Reviewed Files

- `tests/mcp/test_claude_desktop_replay.py` (87 lines)
- `tests/mcp/test_search_tool.py` (264 lines)
- `tests/mcp/test_trace.py` (236 lines)
- `tests/mcp/test_unreachable_api.py` (88 lines)
- `tests/postgres/test_issue_by_key_postgres.py` (71 lines)
- `tests/unit/test_apiclient.py` (173 lines)
- `tests/unit/test_apiclient_errors_expanded.py` (71 lines)
- `tests/unit/test_chart_mcp.py` (124 lines)
- `tests/unit/test_chart_tunnel_listener.py` (47 lines)
- `tests/unit/test_get_issue_by_key.py` (324 lines)
- `tests/unit/test_get_issue_by_key_expanded.py` (181 lines)
- `tests/unit/test_key_oracle_pinned.py` (59 lines)
- `tests/unit/test_mcp_captured_pin.py` (45 lines)
- `tests/unit/test_mcp_expanded.py` (187 lines)
- `tests/unit/test_mcp_replica_check.py` (38 lines)
- `tests/unit/test_mcp_server.py` (215 lines)
- `tests/unit/test_mcp_settings.py` (34 lines)
- `tests/unit/test_mcp_tempo_helper.py` (73 lines)
- `tests/unit/test_mcp_trace.py` (334 lines)
- `tests/unit/test_mcp_trace_expanded.py` (69 lines)
- `tests/unit/test_mcp_workflow.py` (46 lines)
- `tests/unit/test_tunnel_script.py` (31 lines)

## Review Context

- `_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/test-design-epic-4.md`
- `tests/key_oracle.py`
- `tests/tempo.py`
- `tests/kind.py`
- `tests/factories.py`
- `tests/unit/conftest.py`
- `src/ticketscope/telemetry.py`
- `src/ticketscope/mcp/main.py`
