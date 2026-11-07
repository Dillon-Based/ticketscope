---
workflowType: 'testarch-test-review'
runScope: 'epic'
runKey: 'epic-1'
---

# Test Quality Review: epic-search-baseline (epic 1) test suite

**Quality Score**: 79/100 (C - Acceptable)
**Raw Deduction Score**: 79/100
**Score Cap**: 79/100
**Score Override Rule**: Highest severity HIGH caps effective score at 79: min(raw deduction score 79, 79) = 79.
**Review Date**: 2026-11-07
**Review Mode**: full-file
**Reviewer**: headless (bmad-loop, epic-search-baseline release gate)

---

Note: This review audits existing tests; it does not generate tests.
Coverage mapping and coverage gates are out of scope here. Use `trace` for coverage decisions.

## Executive Summary

**Overall Assessment**: Acceptable

**Recommendation**: Request Changes
**Verdict Rule**: Critical = 0 and High > 0 => Request Changes (4 High).

**Context Basis**: pr_diff

**Context Waivers Applied**: 0

**Execution Mode**: sequential

### Key Strengths

✅ Assertions check values, not shapes: ranks, scores, outcomes, spans and rendered rows are compared to exact expectations, and type checks always sit beside a value check.

✅ Known defects stay visible instead of disabled: the one `xfail` is `strict=True` with the product defect named, and every `skipif` names the missing tool (`helm`, `openssl`, `git`).

✅ The cluster checks poll with deadlines and report the last observed state on failure rather than failing on a fixed timeout.

### Advisory Observations

ℹ️ `tests/unit/test_page_expanded.py:268` records a live product defect as a strict xfail: a 405 on `/` lists only `GET` in `Allow`. It belongs on the epic's open-items list until fixed.

ℹ️ `tests/unit/test_ingest_jira.py:331` and `tests/unit/test_release.py:63` pass by not raising. Asserting on the return value (the parsed exclusion set, the downloaded file's path and bytes) would also show what the call produced.

ℹ️ `tests/smoke/test_gateway.py:600` catches `AssertionError` inside the trace poll. It is safe because the final attempt re-asserts outside the `try`, but a predicate that returns a bool would make that clearer.

ℹ️ `tests/unit/test_modes.py:21` checks the registry wiring by class only; also asserting the built retriever ranks a known fixture query would cover the registry end to end.

### Summary

The epic's 37 test files are disciplined: value-level assertions throughout, fixtures and factories for issue data, documented skip guards and no focused or silently disabled tests. The verdict is Request Changes because of four HIGH determinism findings. Three tests put assertions behind a filter or a loop that can match nothing, so they would pass on an empty input. One cluster smoke test orders polling with `time.sleep`. Context was the epic file named by the invocation. The review was scoped to the epic, not to a single story, and coverage against the epic's criteria is left to `trace`.

---

## Quality Criteria Assessment

| Criterion                            | Status  | Violations | Basis    | Notes                                                                         |
| ------------------------------------ | ------- | ---------- | -------- | ----------------------------------------------------------------------------- |
| Disabled or Focused Tests            | ✅ PASS | 0          | Absolute | Skips are tool guards with reasons; the one xfail is strict and documented    |
| Hard Waits (sleep, waitForTimeout)   | ❌ FAIL | 1          | Absolute | `time.sleep` poll intervals in the kind smoke suite                            |
| Determinism (assertions always run)  | ❌ FAIL | 3          | Absolute | Assertions behind a filter or a loop that may run zero times                  |
| Isolation (cleanup, no shared state) | ✅ PASS | 0          | Absolute | Class-level fake state is reset at the start of its only test                 |
| Explicit Assertions                  | ✅ PASS | 0          | Absolute | No tautologies, no self-mock assertions, no shape-only checks                 |
| Test Length (≤1000 lines)            | ✅ PASS | 0          | Absolute | Longest file 726 lines (`tests/smoke/test_gateway.py`); 7,809 lines in total  |
| Test Duration (≤1.5 min)             | ➖ Not measured | -  | Not measured | A static read cannot time a run                                          |
| Flakiness Patterns                   | ❌ FAIL | 4          | Absolute | The hard wait and the three conditional assertions above                      |

**Total Violations**: 0 Critical, 4 High, 0 Medium, 1 Low

**Convention Baseline**: unavailable: the epic's review set is every test file in the repository, so no test file remains outside it to measure.

---

## Quality Score Breakdown

```text
Starting Score:          100
Critical Violations:     -0 × 10 = -0
High Violations:         -4 × 5 = -20
Medium Violations:       -0 × 2 = -0
Low Violations:          -1 × 1 = -1

Bonus Points:
  Comprehensive Fixtures: +0
  Data Factories:        +0
  Network-First:         +0
  Perfect Isolation:     +0
  All Test IDs:          +0
                         --------
Total Bonus:             +0

Raw Deduction Score:     79/100
Score Cap:               79/100 (HIGH)
Effective Score:         79/100
Grade:                   C
```

---

## Critical Issues (Must Fix)

No critical issues detected. ✅

---

## Recommendations (Should Fix)

### 1. Polling ordered by `time.sleep` in the kind smoke suite

**Severity**: P1 (High)
**Location**: `tests/smoke/test_gateway.py:495`
**Row**: H1

**Issue**: The backup wait sleeps 5 s between status reads. The trace poll (line 608) and the Grafana port-forward wait (line 704) use the same pattern. Each loop has a deadline, but the step order still depends on a fixed timer, and the three loops each hand-roll the same poll.

**Fix**: Extract one `poll_until(predicate, timeout, interval)` helper in `tests/target.py` that returns the last observed value and fails with it, and route the three waits through it. Where an API exists, wait on the condition itself (for example `kubectl wait --for=jsonpath='{.status.phase}'=completed backup/<name>`).

### 2. Log-heavy fixture check asserts only inside a filter

**Severity**: P1 (High)
**Location**: `tests/unit/test_snapshot.py:140`
**Row**: H3

**Issue**: `test_fixture_log_heavy_issues_use_jira_blocks` asserts only under `if kinds[...] == "log_heavy"` inside a loop over the fixture. If the fixture lost its log-heavy issues, or `fixture_kinds()` returned none, the test would pass without asserting anything.

**Fix**: Select first, assert the selection is non-empty, then check each one:

```python
heavy = [line for line in _lines() if kinds[line["number"]] == "log_heavy"]
assert heavy, "fixture holds no log-heavy issue"
for line in heavy: ...
```

### 3. Default-render exposure check asserts only on matching documents

**Severity**: P1 (High)
**Location**: `tests/unit/test_chart_telemetry.py:91`
**Row**: H3

**Issue**: The default-values half of `test_nothing_of_the_traces_pipeline_is_exposed` asserts only when a rendered document names a telemetry workload. If those workloads were renamed or dropped from the default render, the check would pass without asserting anything.

**Fix**: Collect the matching documents, assert there are as many as `TELEMETRY_NAMES` expects, then assert none is a `LoadBalancer`.

### 4. Retrieval-span attribute check loops over possibly empty attributes

**Severity**: P1 (High)
**Location**: `tests/unit/test_telemetry_expanded.py:203`
**Row**: H3

**Issue**: `test_only_ticketscope_and_gen_ai_attributes_on_the_retrieval_span` iterates `retrieval.attributes or {}`. A span with no attributes passes the test, which is exactly the regression where instrumentation stops setting them.

**Fix**: Assert the attribute set is non-empty (or contains the attributes the span contract requires) before checking every key's prefix.

### 5. Unexplained fixture number floor

**Severity**: P3 (Low)
**Location**: `tests/unit/test_app.py:34`
**Row**: L6

**Issue**: `assert result.issue.number >= 900000` encodes the synthetic fixture's number range with no name or comment, so a reader cannot tell why the bound matters.

**Fix**: Name it (`FIXTURE_NUMBER_FLOOR = 900_000  # synthetic issues sit above real Mojang ids`) or import the bound from the fixture module.

---

## Decision

**Recommendation**: Request Changes

---

## Reviewed Files

- tests/integrated/test_done_when.py
- tests/smoke/test_gateway.py
- tests/unit/test_app.py
- tests/unit/test_chart_backup.py
- tests/unit/test_chart_backup_expanded.py
- tests/unit/test_chart_pin.py
- tests/unit/test_chart_telemetry.py
- tests/unit/test_chart_telemetry_expanded.py
- tests/unit/test_contract.py
- tests/unit/test_derive.py
- tests/unit/test_derive_jira.py
- tests/unit/test_derive_jira_expanded.py
- tests/unit/test_golden_queries.py
- tests/unit/test_ingest_jira.py
- tests/unit/test_ingest_mask.py
- tests/unit/test_ingest_notes.py
- tests/unit/test_ingest_version.py
- tests/unit/test_integrated_check_expanded.py
- tests/unit/test_integrated_golden.py
- tests/unit/test_layer_imports.py
- tests/unit/test_load_expanded.py
- tests/unit/test_load_main.py
- tests/unit/test_modes.py
- tests/unit/test_page.py
- tests/unit/test_page_expanded.py
- tests/unit/test_postgres_corpus_meta.py
- tests/unit/test_postgres_store.py
- tests/unit/test_postgres_store_expanded.py
- tests/unit/test_publish_script.py
- tests/unit/test_refactor_sweep_expanded.py
- tests/unit/test_release.py
- tests/unit/test_release_expanded.py
- tests/unit/test_settings.py
- tests/unit/test_snapshot.py
- tests/unit/test_telemetry.py
- tests/unit/test_telemetry_expanded.py
- tests/unit/test_v1_contract_expanded.py

## Review Context

- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml
