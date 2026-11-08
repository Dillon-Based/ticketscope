---
workflowType: 'testarch-test-review'
runScope: 'system'
runKey: 'system'
workflowStatus: 'completed'
stepsCompleted: ['step-01-load-context', 'step-02-discover-tests', 'step-03-quality-evaluation', 'step-03f-aggregate-scores', 'step-04-generate-report']
lastStep: 'step-04-generate-report'
lastSaved: '2026-11-07'
inputDocuments:
  - _bmad/config.toml
  - _bmad/custom/config.user.toml
  - /Users/dillonheffernan/.claude/skills/bmod-tea/knowledge/test-quality.md
  - /Users/dillonheffernan/.claude/skills/bmod-tea/knowledge/data-factories.md
  - /Users/dillonheffernan/.claude/skills/bmod-tea/knowledge/test-levels-framework.md
  - /Users/dillonheffernan/.claude/skills/bmod-tea/knowledge/selective-testing.md
  - /Users/dillonheffernan/.claude/skills/bmod-tea/knowledge/test-healing-patterns.md
  - /Users/dillonheffernan/.claude/skills/bmod-tea/knowledge/selector-resilience.md
  - /Users/dillonheffernan/.claude/skills/bmod-tea/knowledge/timing-debugging.md
---

# Test Quality Review: Full Suite

**Quality Score**: 71/100 (C - Acceptable)
**Raw Deduction Score**: 71/100
**Score Cap**: 79/100
**Score Override Rule**: Highest severity HIGH caps effective score at 79: min(raw deduction score 71, 79) = 71.
**Review Date**: 2026-11-07
**Review Mode**: full-file
**Reviewer**: Dillon Baseden

---

Note: This review audits existing tests; it does not generate tests.
Coverage mapping and coverage gates are out of scope here. Use `trace` for coverage decisions.

## Executive Summary

**Overall Assessment**: Acceptable

**Recommendation**: Request Changes
**Verdict Rule**: Critical = 0 and High > 0 => Request Changes (2 High).

**Context Basis**: none

**Context Waivers Applied**: 0

**Execution Mode**: subagent

### Key Strengths

✅ Every test asserts a result that a regression would break. No test is missing an assertion, and none checks only type or presence. The two tests that previously had no assertion, and the four that previously checked only type or presence, now pin exact values.

✅ No test uses a bare timer. Cluster polling goes through `tests/waiting.py`, which waits on a condition, retries only on assertion failures and stops at a monotonic deadline. Port-forward readiness waits on the process's output rather than on a delay.

✅ The process-bootstrap leaks are gone:
- The real telemetry `setup()` runs in a child process.
- An autouse guard restores the tracer-provider registration, the httpx2 logger level and psycopg instrumentation.
- Snapshotting process state around each of the 725 local tests confirmed this.

### Advisory Observations

ℹ️ The `needs_platform_deps` chart tests in `tests/unit/test_chart_backup_expanded.py` and the other helm-gated files skip honestly when the chart archives are missing. But the CI charts job runs only `test_chart_backup.py` and `test_chart_telemetry.py` (`.github/workflows/ci.yml:60`), so those tests never run in CI. Add them to the charts job.

ℹ️ In `tests/smoke/test_gateway.py`, `test_load_log_has_the_report` branches on the cluster's own state before asserting the report. Every path asserts, but forcing the reload unconditionally, or splitting the test, would make it take the same path every run.

ℹ️ `tests/integrated/test_done_when.py` appends to `$GITHUB_STEP_SUMMARY` and caches the pinned asset under pytest's cache directory. Both writes are deliberate and don't affect any outcome: the cache is checked against the pinned checksum.

ℹ️ OpenTelemetry caches its semantic-convention mode once per process, and nothing resets it. It initializes the same way whichever test runs first, so no outcome depends on order today. It would matter only if the opt-in value varied between tests.

ℹ️ Local execution: `uv run pytest --durations=5 -q` at `ce9a742` returned **725 passed, 28 deselected in 12.64s**; the slowest item took 0.97s. The 28 `kind`-marked smoke and integrated tests were reviewed by reading only; they were not run. Recording `pytest -m kind --durations=10` in CI would let Test Duration be measured. Details are in [review-evidence-system.json](review-evidence-system.json).

### Summary

The remediation pass took the suite from 13 to 71. All Critical findings, every hard wait, both earlier global-state leaks and all earlier shape-only assertions are fixed.

Two High findings remain, and both make results depend on test order. The autouse guard meant to restore the semantic-convention environment variable leaves it set when it started unset. And a smoke-test trace id is cached in a module global that two tests share.

The Medium findings come from an unfinished move to the new payload builders: a few files still build search, outcome and snapshot-issue payloads inline instead of using them. The Low findings are three unnamed domain numbers.

---

## Quality Criteria Assessment

| Criterion                            | Status          | Violations | Basis                                                   | Notes                                                                                  |
| ------------------------------------ | --------------- | ---------: | ------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Disabled or Focused Tests            | ✅ PASS         |          0 | Absolute                                                | Environment skips carry true reasons; no xfail remains.                                |
| Hard Waits (sleep, waitForTimeout)   | ✅ PASS         |          0 | Absolute                                                | Polling goes through the bounded `eventually()` and `wait_for_output()` helpers.       |
| Determinism (assertions always run)  | ✅ PASS         |          0 | Absolute + Applicability                                | No conditional, swallowed or live-clock-governed assertion.                            |
| Isolation (cleanup, no shared state) | ❌ FAIL         |          2 | Absolute                                                | One leaked env var; one module-global trace id shared between two smoke tests.         |
| Fixture Patterns                     | ⚠️ WARN         |          8 | Applicability: constructs domain request/model payloads | The eight Data Factories findings, counted once in the total.                          |
| Data Factories                       | ⚠️ WARN         |          8 | Applicability: constructs domain payloads               | Inline payloads bypass `tests/factories.py`; snapshot-issue builder copied three times. |
| Explicit Assertions                  | ✅ PASS         |          0 | Absolute + Applicability                                | Every test asserts a value the system produced.                                        |
| Test Length (≤1000 lines)            | ✅ PASS         |          0 | Absolute                                                | 14–791 lines per file                                                                  |
| Test Duration (≤1.5 min)             | ➖ Not measured |          - | Not measured                                            | A static read cannot time a run                                                        |
| Flakiness Patterns                   | ❌ FAIL         |          2 | Absolute + Applicability                                | The two isolation findings above, counted once.                                        |

**Total Violations**: 0 Critical, 2 High, 8 Medium, 3 Low

**Convention Baseline**: unavailable: Suite review includes every test file; no eligible tests remain outside the review set.

---

## Quality Score Breakdown

```text
Starting Score:          100
Critical Violations:     -0 × 10 = -0
High Violations:         -2 × 5 = -10
Medium Violations:       -8 × 2 = -16
Low Violations:          -3 × 1 = -3

Bonus Points:
  Comprehensive Fixtures: +0
  Data Factories:        +0
  Network-First:         +0
  Perfect Isolation:     +0
  All Test IDs:          +0
                         --------
Total Bonus:             +0

Raw Deduction Score:     71/100
Score Cap:               79/100 (HIGH)
Effective Score:         71/100
Grade:                   C
```

---

## Critical Issues (Must Fix)

No critical issues detected. ✅

---

## Recommendations (Should Fix)

### 1. Restore the semantic-convention opt-in variable when it started unset

**Severity**: P1 (High)
**Location**: `tests/unit/test_app.py:21`
**Row**: H4

**Issue**: The `client` fixture calls `create_app`, which writes `OTEL_SEMCONV_STABILITY_OPT_IN` into `os.environ`. When the variable starts unset, the autouse guard in `tests/unit/conftest.py:32` calls `monkeypatch.delenv(opt_in, raising=False)`. On a missing variable that call records nothing to undo, so the value the app writes outlives the test.

So the first test that calls `create_app`, `load.main`, `migrate.main` or `setup` changes the environment for every later test. A snapshot taken around each test showed `test_app.py::test_best_match` taking it from unset to `gen_ai_latest_experimental,database,http`. A standalone `MonkeyPatch` reproduction confirmed that `delenv(..., raising=False)` on an absent key does not undo a later write.

**Fix**: Make the guard restore the variable either way, for example:

```python
before = os.environ.get(opt_in)
try:
    yield
finally:
    if before is None:
        os.environ.pop(opt_in, None)
    else:
        os.environ[opt_in] = before
```

Or call `monkeypatch.setenv(opt_in, "placeholder")` and then `monkeypatch.delenv(opt_in)`; that pair does register an undo.

### 2. Replace the module-global trace id with a fixture

**Severity**: P1 (High)
**Location**: `tests/smoke/test_gateway.py:698`
**Row**: H4

**Issue**: `_TRACE_ID: list[str] = []` is filled inside a test by `_traced_search()` and never reset. The Tempo test (8) and the Grafana test (8b) share whichever search ran first. Run alone, 8b makes its own search; run after 8, it reuses 8's trace. So what 8b checks, and how long the trace has had to arrive in Tempo, depend on which tests run and in what order.

**Fix**: Declare the shared search as a module-scoped fixture so pytest owns its lifetime:

```python
@pytest.fixture(scope="module")
def traced_search_id() -> str:
    return _search_with_traceparent()
```

Or have each test make its own traced search.

### 3. Use the search-payload factory in the contract tests

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_contract.py:9`
**Row**: M2

**Issue**: The `/v1/search` request is written as an inline dict five times (lines 9, 16, 25, 93, 99). `tests.factories.search_payload` builds exactly this shape and takes overrides, so a request-schema change now has to be made at every one of these lines.

**Fix**: Use `search_payload("q")`, `search_payload("q", mode="nope")`, `search_payload("q", future=1)` and `search_payload("q", k=k)`. Keep the case that deliberately omits the query (line 20) as a literal.

### 4. Use the outcome factory in the v1 response-shape test

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_contract.py:46`
**Row**: M2

**Issue**: The outcome is written inline as `{"status": "unknown", "summary": None, "source": None, "ref": None}`, which is exactly what `outcome_payload()` returns. The same file already imports and uses that factory elsewhere.

**Fix**: Replace the literal with `outcome_payload()`. The round-trip assertion compares against the same body object, so the test checks the same thing.

### 5. Add an issue-payload builder for the contract tests

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_contract.py:38`
**Row**: M2

**Issue**: The contract `issue` object (number, title, url, kind, state and more) is built inline four times (lines 38, 72, 104, 121), and no builder exists for it.

**Fix**: Add `issue_payload(number, **overrides)` to `tests/factories.py` with neutral defaults. Each test then passes only the fields it is about, such as `body`, `key` or an unknown field.

### 6. Use the search-payload factory in the integrated golden check

**Severity**: P2 (Medium)
**Location**: `tests/integrated/test_done_when.py:162`
**Row**: M2

**Issue**: The integrated check posts `{"query": entry["query"], "mode": mode, "k": k}` inline instead of calling `search_payload`. The remediation missed this file.

**Fix**: Use `json=search_payload(str(entry["query"]), mode=mode, k=k)`.

### 7. Use the outcome factory in the page result builder

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_page_expanded.py:46`
**Row**: M2

**Issue**: `_result` writes the outcome as an inline dict, `{"status": status, "summary": summary, "source": "label", "ref": ref}`, although `outcome_payload` builds this shape with overrides.

**Fix**: Use `Outcome.model_validate(outcome_payload(status=status, summary=summary, source="label", ref=ref))`.

### 8. Encode page form bodies through the form factory

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_page_expanded.py:241`
**Row**: M2

**Issue**: Search-form bodies are hand-written as raw strings: `content="q=quokka"` (line 241) and `content="q=x"` (lines 264 and 271). The same file builds other bodies with `urlencode(form_payload(...))`.

**Fix**: Use `content=urlencode(form_payload("quokka"))` and `urlencode(form_payload("x"))`. Leave the malformed raw-body parser cases elsewhere in the file as literals.

### 9. Share one snapshot-issue factory (test_derive_jira.py)

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_derive_jira.py:31`
**Row**: M2

**Issue**: `make_jira_issue` rebuilds the full 13-field `SnapshotIssueV2` payload. The public `make_issue` builder at `tests/unit/test_derive.py:26` already does this, and other modules reuse it.

**Fix**: Move `make_issue` into `tests/factories.py` as `snapshot_issue(**overrides)`. Keep `make_jira_issue` only as a one-line wrapper that sets its 100 / MCL-100 defaults.

### 10. Share one snapshot-issue factory (test_derive_jira_expanded.py)

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_derive_jira_expanded.py:70`
**Row**: M2

**Issue**: This file holds a third copy of the `SnapshotIssueV2` builder, with 200 / MCL-200 defaults. A change to one schema field must be made in three places.

**Fix**: Import the shared `snapshot_issue` builder from finding 9, and keep `answered_question` as a thin wrapper over it for its scenario.

### 11. Name the legacy receiver ports

**Severity**: P3 (Low)
**Location**: `tests/unit/test_chart_telemetry.py:45`
**Row**: L6

**Issue**: The test asserts that `"6831"` (Jaeger thrift-compact) and `"9411"` (Zipkin) are absent, but writes them as bare strings: no constant or comment says which receiver each port belongs to.

**Fix**: Use `LEGACY_RECEIVER_PORTS = {"jaeger": "6831", "zipkin": "9411"}` and put the receiver name in each failure message.

### 12. Derive the import-linter contract count

**Severity**: P3 (Low)
**Location**: `tests/unit/test_import_linter_enforcement.py:50`
**Row**: L6

**Issue**: `"Contracts: 7 kept, 0 broken."` hard-codes how many contracts `.importlinter` defines. Adding a contract breaks this clean-control test with no hint why.

**Fix**: Count the `[importlinter:contract:*]` sections of the copied config with `configparser`, then assert `f"Contracts: {expected} kept, 0 broken."`.

### 13. Name the COPY row width

**Severity**: P3 (Low)
**Location**: `tests/unit/test_postgres_corpus_meta.py:145`
**Row**: L6

**Issue**: `len(conn.copied[0]) == 14` asserts the `IssueRow` column count as a bare number with no explanation.

**Fix**: Assert `len(conn.copied[0]) == len(dataclasses.fields(IssueRow))`, or use the adapter's column list if it exposes one.

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
- tests/unit/test_import_linter_enforcement.py
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
- tests/unit/test_waiting.py

## Review Context

none
