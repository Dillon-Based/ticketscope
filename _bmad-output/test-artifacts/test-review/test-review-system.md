---
workflowType: testarch-test-review
runScope: system
runKey: system
workflowStatus: completed
stepsCompleted: [step-01-load-context, step-02-discover-tests, step-03f-aggregate-scores, step-04-generate-report]
lastStep: step-04-generate-report
lastSaved: 2026-11-07
inputDocuments:
- _bmad/config.toml
- _bmad/custom/config.user.toml
- /Users/dillonheffernan/.agents/skills/bmod-tea/knowledge/test-quality.md
- /Users/dillonheffernan/.agents/skills/bmod-tea/knowledge/data-factories.md
- /Users/dillonheffernan/.agents/skills/bmod-tea/knowledge/test-levels-framework.md
- /Users/dillonheffernan/.agents/skills/bmod-tea/knowledge/selective-testing.md
- /Users/dillonheffernan/.agents/skills/bmod-tea/knowledge/test-healing-patterns.md
- /Users/dillonheffernan/.agents/skills/bmod-tea/knowledge/selector-resilience.md
- /Users/dillonheffernan/.agents/skills/bmod-tea/knowledge/timing-debugging.md
---

# Test Quality Review: Full Suite

**Quality Score**: 13/100 (F - Critical Issues)
**Raw Deduction Score**: 13/100
**Score Cap**: 69/100
**Score Override Rule**: Highest severity CRITICAL caps effective score at 69: min(raw deduction score 13, 69) = 13.
**Review Date**: 2026-11-07
**Review Mode**: full-file
**Reviewer**: Codex

This review audits existing tests. Coverage mapping and coverage gates are out of scope; use `trace` for coverage decisions.

## Executive Summary

**Overall Assessment**: Critical Issues
**Recommendation**: Block
**Verdict Rule**: Critical > 0 => Block (2 Critical).
**Context Basis**: none
**Context Waivers Applied**: 0
**Execution Mode**: subagent

### Key Strengths

- Temporary paths, in-memory stores, mocked transports, and provider fixtures keep most unit checks independent of external services.
- Contract tests check exact status codes, response values, and failure cases across the API and ingest paths.
- All 37 test files are below 1000 lines; the largest is 726 lines.

### Advisory Observations

- Local execution: `uv run pytest --durations=10 -q` returned **712 passed, 27 deselected, 1 xfailed in 11.37s**, exit code 0. The 27 cluster cases were reviewed statically and were not executed. The expected failure is a documented strict check of the page route's incomplete HTTP `Allow` header.
- No story or test-design artifact was supplied. The review considered existing tests and the source/support they exercise. Source and test files were left unchanged.
- Discovery measured 37 files, 7,809 lines, and 510 test function definitions. Parameterization accounts for the larger executed case count. Detailed metadata and verification evidence are in [review-evidence-system.json](review-evidence-system.json).

### Summary

The suite passes locally, but several tests accept incomplete or unrelated outcomes, and process bootstrap tests leave shared state behind. Repeated request construction and deep nesting add maintenance cost. The result applies to the full suite under rubric version 5.0; it is a test-quality assessment, not a coverage or release-readiness measurement.

## Quality Criteria Assessment

| Criterion | Status | Violations | Basis | Notes |
| --- | --- | ---: | --- | --- |
| Disabled or Focused Tests | ✅ PASS | 0 | Absolute | Environment skips have current reasons; the strict expected failure remains documented. |
| Hard Waits (sleep, waitForTimeout) | ❌ FAIL | 3 | Absolute | Fixed intervals in bounded smoke polling helpers. |
| Determinism (assertions always run) | ✅ PASS | 0 | Absolute + Applicability | No hidden conditional-assertion or live-clock expiry defects established. |
| Isolation (cleanup, no shared state) | ❌ FAIL | 2 | Absolute | Two verified process-global state leaks. |
| Fixture Patterns | ⚠️ WARN | 9 | Applicability: constructs domain request/model payloads | Repeated payload setup; same nine findings as Data Factories, counted once in the total. |
| Data Factories | ⚠️ WARN | 9 | Applicability: constructs domain payloads | Repeated shapes need small test-only builders with explicit overrides. |
| Explicit Assertions | ❌ FAIL | 6 | Absolute | Two tests without explicit outcome checks and four shape-only result checks. |
| Suite Structure | ⚠️ WARN | 2 | Absolute | Two test bodies nest four blocks deep. |
| Test Length (≤1000 lines) | ✅ PASS | 0 | Absolute | Measured range: 14–726 lines per test file. |
| Test Duration (≤1.5 min) | ➖ Not measured | - | Not measured | The full suite, including cluster cases, was not timed. |
| Flakiness Patterns | ❌ FAIL | 5 | Absolute + Applicability | The three sleep findings and two state leaks already counted above. |

**Total Violations**: 2 Critical, 9 High, 11 Medium, 0 Low

**Convention Baseline**: unavailable: Suite review includes every test file; no eligible tests remain outside the review set.

## Quality Score Breakdown

```text
Starting Score:          100
Critical Violations:     -2 × 10 = -20
High Violations:         -9 × 5 = -45
Medium Violations:       -11 × 2 = -22
Low Violations:          -0 × 1 = -0

Bonus Points:
  Comprehensive Fixtures: +0
  Data Factories:        +0
  Network-First:         +0
  Perfect Isolation:     +0
  All Test IDs:          +0
                         --------
Total Bonus:             +0

Raw Deduction Score:     13/100
Score Cap:               69/100 (CRITICAL)
Effective Score:         13/100
Grade:                   F
```

## Critical Issues (Must Fix)

### 1. Assert the committed exclusion result

**Severity**: P0 (Critical)
**Location**: `tests/unit/test_ingest_jira.py:332`
**Row**: C4

**Issue**: The committed-exclusions test calls read_exclusions but never asserts its returned set or any other observable outcome. It does check that parsing raises no exception, but a regression returning None or ignoring every exclusion still passes.

**Fix**: Assert the parsed frozenset equals the issue keys recorded in the committed exclusion file, including the explicit empty-set case if the file intentionally contains only comments.

**Verification**: In a separate Python process, replacing `read_exclusions` with a function returning `None` and invoking this exact test still returned normally.

### 2. Verify the uppercase-pin download result

**Severity**: P0 (Critical)
**Location**: `tests/unit/test_release.py:65`
**Row**: C4

**Issue**: The case-insensitive-pin test calls fetch_snapshot with SHA.upper() and has no explicit assertion or failure path in the test. It checks that no exception escapes, but a no-op fetch implementation that returns without downloading also passes.

**Fix**: Capture the returned path, assert it names the expected asset and its bytes equal BODY; optionally assert a request was made.

**Verification**: A disposable uv-run Python process replaced test_release.fetch_snapshot with a lambda returning tmp_path / "missing", invoked test_pin_is_compared_case_insensitively(tmp_path) exactly, and observed normal return with asset_exists=False and no files created.


## Recommendations (Should Fix)

### 1. Observe backup completion without a fixed sleep

**Severity**: P1 (High)
**Location**: `tests/smoke/test_gateway.py:495`
**Row**: H1

**Issue**: The backup helper sleeps five seconds between status checks. The loop checks completion, failure, and its deadline correctly, but fixed delays add up to five seconds between observations.

**Fix**: Prefer observing the Backup phase through a Kubernetes watch with a deadline and explicit completed/failed checks, eliminating the bare sleep.

### 2. Centralize bounded trace waiting

**Severity**: P1 (High)
**Location**: `tests/smoke/test_gateway.py:608`
**Row**: H1

**Issue**: The trace helper sleeps three seconds between attempts. It rechecks the complete span tree and exposes final failures at its deadline, but waiting policy and fixed delays are embedded in the assertion helper.

**Fix**: Use an observable trace-ingestion signal if available or a dedicated bounded eventual-assertion utility with explicit retry policy instead of an inline bare timer.

### 3. Wait for port-forward readiness explicitly

**Severity**: P1 (High)
**Location**: `tests/smoke/test_gateway.py:704`
**Row**: H1

**Issue**: Grafana readiness sleeps one second between health probes. Process failure and deadline checks are present, but readiness detection depends on repeated timer-delayed probes.

**Fix**: Wait on the port-forward readiness event/output and retain a bounded health check through a dedicated readiness helper, removing the inline sleep.

### 4. Exercise the retriever returned by the registry

**Severity**: P1 (High)
**Location**: `tests/unit/test_modes.py:21`
**Row**: H10

**Issue**: The registry-builder test checks only that the returned object is a KeywordRetriever instance. An instance with incorrect store wiring or broken search behavior satisfies this bare class assertion, so the factory result has no behavioral value constraint.

**Fix**: Build the retriever against a small known store and assert its search returns the expected issue and score through the object returned by REGISTRY["keyword"].build.

### 5. Verify which issue the pasted log ranks

**Severity**: P1 (High)
**Location**: `tests/unit/test_app.py:122`
**Row**: H10

**Issue**: The pasted-log test verifies the request length and HTTP 200, but its only assertion about the produced search results is truthiness. Returning any unrelated nonempty result list passes the claimed ranking check.

**Fix**: Assert TARGET_NUMBER is the expected top result for the synthetic zephyrcache log, and retain the length/status checks.

### 6. Check the operator query against an expected issue

**Severity**: P1 (High)
**Location**: `tests/smoke/test_gateway.py:222`
**Row**: H10

**Issue**: The operator-character smoke test gets a schema-valid HTTP 200 through _search, but constrains the resulting hits only by nonemptiness. A search that ignores the query and returns unrelated hits passes.

**Fix**: Use a pinned-corpus operator-character query with an independently recorded expected issue and assert that issue occurs at the expected rank or within a stated top-k.

### 7. Check the stack trace against an expected issue

**Severity**: P1 (High)
**Location**: `tests/smoke/test_gateway.py:236`
**Row**: H10

**Issue**: The 4KB stack-trace smoke test verifies request size and HTTP 200 through _search, then checks only that results exist. Any nonempty set of unrelated issues passes the claimed ranking behavior.

**Fix**: Choose or seed a log-heavy query with an independently recorded expected issue and assert its presence/rank in the returned top-k.

### 8. Isolate the global tracer-provider registration

**Severity**: P1 (High)
**Location**: `tests/unit/test_telemetry.py:290`
**Row**: H4

**Issue**: The test invokes real telemetry.setup(), which installs OpenTelemetry's process-global, write-once tracer provider, then shuts the provider down without restoring the global provider or its initialization guard. Later setup() calls keep using the first global provider rather than the provider they create; running this setup test before an app that uses the global provider therefore changes that app's tracing behavior. The same setup path is exercised by the load and migrate main tests.

**Fix**: Run process-bootstrap telemetry setup checks in a subprocess, or provide a fixture that isolates and restores OpenTelemetry global provider/initialization state and instrumentation around every in-process bootstrap test. Keep injected per-test providers for application span tests.

**Verification**: tests/unit/test_telemetry.py:290 calls setup; lines 297-298 only shutdown. src/ticketscope/telemetry.py:91 calls trace.set_tracer_provider. An isolated subprocess invoked this actual test inside MonkeyPatch.context: ProxyTracerProvider before, TracerProvider after, and a subsequent set_tracer_provider(new) logged that overriding is not allowed and retained the old global. No test fixture restores _TRACER_PROVIDER or its once guard.

### 9. Restore the HTTP client logger level

**Severity**: P1 (High)
**Location**: `tests/unit/test_load_expanded.py:246`
**Row**: H4

**Issue**: The logging test calls load.main(), which changes the process-wide httpx2 logger level to WARNING, and leaves that level installed after its MonkeyPatch context exits. The context restores only the database stubs: no fixture saves and restores the logger level. Later tests consequently observe different httpx2 logging and capture behavior depending on whether this test (or another load.main test) ran first.

**Fix**: Save the logger's existing level in a fixture and restore it in teardown for all tests that invoke load.main(); in this test, explicitly establish a non-WARNING starting level before verifying the side effect.

**Verification**: tests/unit/test_load_expanded.py:244-247 patches only _use(db, mp), calls main, and asserts the changed global level after the context. src/ticketscope/jobs/load/main.py:120 sets logging.getLogger("httpx2").setLevel(logging.WARNING). Isolated invocation of the actual test with initial INFO yielded logger_before=20, logger_after=30, info_enabled_after=False.

### 10. Reuse payload construction in test_gateway.py

**Severity**: P2 (Medium)
**Location**: `tests/smoke/test_gateway.py:209`
**Row**: M2

**Issue**: The same three-field search request shape is built inline three times, in the invalid-input table and traced-search setup. A request-schema change requires updating multiple independent construction sites.

**Fix**: Introduce a test-only search-payload builder with query, mode and k overrides; retain the visibly invalid k=0 and k=51 values in the parameter table.

### 11. Reuse payload construction in test_app.py

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_app.py:23`
**Row**: M2

**Issue**: Eight inline query/mode search payloads duplicate the same domain request shape across API scenarios.

**Fix**: Use a small test-only search-payload factory that accepts overrides, leaving invalid modes and edge inputs explicit in each test. Keep response assertions independent of that builder.

### 12. Reuse payload construction in test_contract.py

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_contract.py:45`
**Row**: M2

**Issue**: The four-field outcome payload is constructed inline four times as setup for model-validation tests. All four sites repeat status, summary, source and ref.

**Fix**: Add a test-only raw-outcome builder with explicit overrides for each scenario; keep expected round-trip bodies and invalid enum values visible and independent of production serializers.

### 13. Reuse payload construction in test_integrated_golden.py

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_integrated_golden.py:40`
**Row**: M2

**Issue**: Four entries in the malformed-outcome input matrix reconstruct the same nested issue/outcome payload shape.

**Fix**: Build the common issue/outcome input shape through a small test-only factory or parameterized construction. Keep empty and unknown statuses explicit, keep the omitted-outcome case explicit, and retain the independent expected issue-number list.

### 14. Reuse payload construction in test_page.py

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_page.py:115`
**Row**: M2

**Issue**: The same q form/query payload shape is constructed inline four times, including in the existing _post helper and in GET/POST comparison tests that bypass it.

**Fix**: Centralize q payload construction in a test-only form builder reusable by both GET and POST helpers; keep each query value explicit and keep repeated-q tests using their deliberate list-of-pairs representation.

### 15. Reuse payload construction in test_page_expanded.py

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_page_expanded.py:206`
**Row**: M2

**Issue**: Four tests construct the same q form payload inline before encoding it.

**Fix**: Introduce a small test-only form-payload or encoded-form builder accepting the explicit query. Leave raw-body parser edge cases unmodified so malformed wire inputs remain visible.

### 16. Reuse payload construction in test_telemetry.py

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_telemetry.py:121`
**Row**: M2

**Issue**: Search/page telemetry setup repeats domain request shapes: query-only search bodies three times and q form/query bodies four times.

**Fix**: Reuse test-only search and form payload builders with explicit query overrides. Preserve each privacy-sensitive query in the test and keep telemetry expectations independent of the builders.

### 17. Reuse payload construction in test_telemetry_expanded.py

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_telemetry_expanded.py:92`
**Row**: M2

**Issue**: Telemetry scenarios independently construct the same search and page request shapes throughout the file: query/mode three times, query-only five times, and q five times.

**Fix**: Reuse test-only search/form builders with explicit overrides and a way to deliberately omit mode. Keep invalid k=0 and mode=x values at the call sites and keep all span expectations independent.

### 18. Reuse payload construction in test_v1_contract_expanded.py

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_v1_contract_expanded.py:76`
**Row**: M2

**Issue**: The API tests construct query/mode search payloads four times and query-only payloads three times.

**Fix**: Use a test-only search-payload builder with overrides and deliberate field omission. Keep invalid and boundary values visible, and retain the independent expected response contracts.

### 19. Flatten the page-twin check

**Severity**: P2 (Medium)
**Location**: `tests/integrated/test_done_when.py:193`
**Row**: M7

**Issue**: The golden-query test nests the missing-page-twin branch four blocks deep: try, per-query for, gated/rank if, then missing-page-rank if. Flattening the check would make its failure handling easier to follow.

**Fix**: Extract the per-entry page-twin check into a helper returning an optional failure message, or flatten its guard with a single condition, while retaining the finally report and final failures assertion.

### 20. Extract the nested source scan

**Severity**: P2 (Medium)
**Location**: `tests/unit/test_refactor_sweep_expanded.py:49`
**Row**: M7

**Issue**: The retired-symbol test nests its match body four blocks deep: root traversal, file traversal, line traversal, then match guard.

**Fix**: Extract the file/line scan into a helper returning matching locations, leaving one traversal or comprehension and the final explicit assertion in the test.

## Decision

**Recommendation**: Block

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

none
