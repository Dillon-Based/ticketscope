---
workflowType: 'testarch-test-review'
runScope: 'epic'
runKey: 'epic-3'
---

# Test Quality Review: epic-hybrid-retrieval (epic 3) test suite

**Quality Score**: 68/100 (D - Needs Improvement)
**Raw Deduction Score**: 68/100
**Score Cap**: 79/100
**Score Override Rule**: Highest severity HIGH caps effective score at 79: min(raw deduction score 68, 79) = 68.
**Review Date**: 2026-11-10
**Review Mode**: full-file
**Reviewer**: headless (bmad-loop, epic-hybrid-retrieval release gate)

---

Note: This review audits existing tests; it does not generate tests.
Coverage mapping and coverage gates are out of scope here. Use `trace` for coverage decisions.

## Executive Summary

**Overall Assessment**: Needs Improvement

**Recommendation**: Request Changes
**Verdict Rule**: Critical = 0 and High > 0 => Request Changes (6 High).

**Context Basis**: pr_diff

**Context Waivers Applied**: 0

**Execution Mode**: sequential

### Key Strengths

✅ Dense scoring is checked against a fixed oracle: `tests/dense_oracle.py` gives hand-computed cosine scores and an order, and both the in-memory store (`tests/unit/test_dense.py:53`) and Postgres (`tests/postgres/test_dense_postgres.py:56`) must reproduce them within a stated tolerance.

✅ Unit tests run with no model and no database. The deterministic `HashEmbedder` fake and the fake stores carry the retriever, fusion, load and eval tests, and hybrid fusion is checked on hand-computed rankings, ties and exclusions (`tests/unit/test_hybrid.py`).

✅ Cluster checks wait on conditions, not timers. Tempo traces and readiness use `eventually(..., timeout=60, interval=2)`. The model-mismatch check restores `corpus_meta` in a `finally` block (`tests/integrated/test_hybrid_check.py:102`).

✅ Known defects stay visible. The single `xfail` is `strict=True` and names the product defect. Every `skipif` names the missing tool (`helm`, `git`) or the missing pin.

### Advisory Observations

ℹ️ `tests/unit/test_eval_embedder_expanded.py:332` records a live product defect as a strict xfail: `EMBEDDINGS_COMPUTE=1` in `scripts/kind-up.sh` resets `HELM_TIMEOUT` to 50m after the eval branch set 60m. `tests/unit/test_dense_expanded.py:242` asserts `--timeout 50m`, so it pins the defective value. Both belong on the epic's open-items list until the script is fixed.

ℹ️ `tests/unit/test_embedding_asset.py:261` skips when no embeddings pin is merged. The 2026.11.1 pin has been merged since story 3.4, so the guard is now dead. Worse, if someone cleared the pin, the check would quietly skip instead of failing.

ℹ️ The hybrid gateway checks (`tests/integrated/test_dense_kind.py:198` and `tests/integrated/test_hybrid_check.py:72`) assert only that each outcome has a status. The dense gateway check (`tests/integrated/test_dense_kind.py:81`) compares every outcome to its row in `issue`, and the hybrid checks could do the same.

ℹ️ `tests/unit/test_hybrid_check_38_expanded.py:22` and `tests/integrated/test_hybrid_check.py:62` derive the expected default mode with the same expression the chart test uses. A fixed expected value (`hybrid`, from the committed baseline) would catch an error in that expression.

ℹ️ `tests/integrated/test_dense_kind.py:59` and `:186` branch on the test's own environment (`PINNED`, `TICKETSCOPE_DENSE_ENABLED`), and every path asserts. Since the pin was merged, the 503 branch can no longer run in CI.

### Summary

The epic's 21 test files (3,792 lines) are well built. Dense and hybrid ranking is pinned to oracles. Fakes keep the unit tier free of models and databases. The cluster checks poll with deadlines, and no test is focused or silently disabled. The verdict is Request Changes because of six HIGH findings:

- Four tests put assertions inside a loop over data that can be empty, so they would pass with nothing checked.
- Two tests constrain only the type or presence of a value.

One MEDIUM finding is the kind budget check, which bundles five unrelated subjects into one test. The review set is the test files that epic 3's stories created or changed: commits 684c8f4 to 9c6efe0, with helper modules read as context. Context was the epic file named by the invocation and its ticket list. Coverage against the epic's requirements is left to `trace`.

---

## Quality Criteria Assessment

| Criterion                            | Status         | Violations | Basis                    | Notes                                                                        |
| ------------------------------------ | -------------- | ---------- | ------------------------ | ---------------------------------------------------------------------------- |
| Disabled or Focused Tests            | ✅ PASS        | 0          | Absolute                 | Skips are tool or pin guards with reasons; the one xfail is strict           |
| Hard Waits (sleep, waitForTimeout)   | ✅ PASS        | 0          | Absolute                 | Cluster waits go through `eventually` and `kubectl wait`                     |
| Determinism (assertions always run)  | ❌ FAIL        | 4          | Absolute + Applicability | Assertions inside loops over data that may be empty                          |
| Isolation (cleanup, no shared state) | ✅ PASS        | 0          | Absolute                 | Cluster mutation restored in `finally`; fakes are built per test             |
| Fixture Patterns                     | ✅ PASS        | 0          | Applicability            | Setup comes from pytest fixtures (`db`, `asset`, `loaded`, `pg_conninfo`)    |
| Data Factories                       | ✅ PASS        | 0          | Applicability            | No domain payload is built inline three or more times                        |
| Explicit Assertions                  | ❌ FAIL        | 2          | Absolute + Applicability | Two checks constrain only the type or presence of a value                    |
| Test Length (≤1000 lines)            | ✅ PASS        | 0          | Absolute                 | Longest file 494 lines (`tests/unit/test_dense.py`); 3,792 lines in total    |
| Test Duration (≤1.5 min)             | ➖ Not measured | -          | Not measured             | A static read cannot time a run                                              |
| Flakiness Patterns                   | ❌ FAIL        | 4          | Absolute + Applicability | The four loop-guarded assertions above                                       |

**Total Violations**: 0 Critical, 6 High, 1 Medium, 0 Low

**Convention Baseline**: 53 test files outside the review set; 8 sampled (`tests/unit/test_app.py`, `test_chart_telemetry_expanded.py`, `test_derive.py`, `test_eval_score_expanded.py`, `test_ingest_mask.py`, `test_layer_imports.py`, `test_modes.py`, `test_postgres_corpus_meta.py`). Convention: dataFactories (4 of 8 sampled, established, `tests.factories` builders). Convention: fixtures (7 of 8 sampled, established, pytest fixtures). Convention: priorityMarkers (0 of 8 sampled, absent). Convention: testIds (0 of 8 sampled, absent). Convention: networkFirst (0 of 8 sampled, absent). Convention: playwrightUtils (0 of 8 sampled, absent). Convention: assertionStyle (8 of 8 sampled, established, bare `assert` with `pytest.approx`/`pytest.raises`).

---

## Quality Score Breakdown

```text
Starting Score:          100
Critical Violations:     -0 × 10 = -0
High Violations:         -6 × 5 = -30
Medium Violations:       -1 × 2 = -2
Low Violations:          -0 × 1 = -0

Bonus Points:
  Comprehensive Fixtures: +0
  Data Factories:        +0
  Network-First:         +0
  Perfect Isolation:     +0
  All Test IDs:          +0
                         --------
Total Bonus:             +0

Raw Deduction Score:     68/100
Score Cap:               79/100 (HIGH)
Effective Score:         68/100
Grade:                   D
```

---

## Critical Issues (Must Fix)

No critical issues detected. ✅

---

## Recommendations (Should Fix)

### 1. Pod restart and OOM checks inside a loop that may match no pod

**Severity**: P1 (High)
**Location**: `tests/integrated/test_dense_kind.py:145`
**Row**: H3

**Issue**: The restart-count and `OOMKilled` assertions run once per pod and once per container status. If the label selector `app.kubernetes.io/component=api` matches no pod, or a pod has no `containerStatuses` yet (`.get(..., [])`), the loop body never runs. The budget check then passes without proving that `api` survived dense inference under its memory limit (R5).

**Fix**: Assert the list sizes before the loop, for example `assert len(pods["items"]) == 1` and `assert statuses, pod["metadata"]["name"]`.

### 2. Record-field check passes when the asset holds no records

**Severity**: P1 (High)
**Location**: `tests/unit/test_embedding_asset.py:101`
**Row**: H3

**Issue**: `test_every_record_holds_only_issue_model_and_vector` asserts the field set inside `for line in record_lines`. If `write_asset` wrote the manifest and dropped the record, the loop would run zero times and the test would pass.

**Fix**: Unpack the single record the test wrote, `[record_line] = record_lines`, then assert its fields.

### 3. Environment-file override check passes when no file matches

**Severity**: P1 (High)
**Location**: `tests/unit/test_embedding_asset.py:268`
**Row**: H3

**Issue**: `test_no_environment_file_overrides_the_embeddings_pin` asserts only inside `for env_file in CHART_VALUES.parent.glob("values-*.yaml")`. If `values-kind.yaml` were renamed or moved, the glob would match nothing and the guard against a per-environment override of the pin (AD-25) would pass with nothing checked.

**Fix**: Collect the glob into a list and assert it is not empty, or name the expected files (`values-kind.yaml`) and assert that set.

### 4. Default-mode comment check passes on an empty baseline

**Severity**: P1 (High)
**Location**: `tests/unit/test_chart_defaults.py:27`
**Row**: H3

**Issue**: `test_default_mode_comment_records_the_number_it_chose_by` checks the `values.yaml` comment once per mode in `eval/baseline.json`. If `modes` were empty or lost a mode, fewer numbers would be checked or none, and the test would still pass.

**Fix**: Assert `set(modes) == {"keyword", "dense", "hybrid"}` before the loop.

### 5. Dense and hybrid metric values checked for type only

**Severity**: P1 (High)
**Location**: `tests/eval/test_eval_kind.py:219`
**Row**: H10

**Issue**: For dense and hybrid, Recall@1, @5, @10 and MRR@10 are asserted only to be `float`. A NaN, a negative value, a recall above 1, or Recall@10 below Recall@1 would all pass. The keyword check in the same file (`:93`–`:96`) already bounds each value to [0, 1] and checks the order Recall@1 ≤ @5 ≤ @10 and MRR@10 ≤ Recall@10.

**Fix**: Apply the keyword check's range and order assertions to every mode, for example by moving them into a helper called for each mode.

### 6. Baseline check asserts only that a key is present

**Severity**: P1 (High)
**Location**: `tests/unit/test_hybrid_check_38_expanded.py:45`
**Row**: H10

**Issue**: `test_baseline_file_is_json_with_modes` asserts `"modes" in ...`. A baseline whose `modes` is empty, `null` or missing a mode passes.

**Fix**: Assert the value: `set(json.loads(...)["modes"]) == {"keyword", "dense", "hybrid"}`. Alternatively, drop the test, because `test_baseline_modes_cover_every_kind` already indexes each mode.

### 7. One kind test checks five unrelated subjects

**Severity**: P2 (Medium)
**Location**: `tests/integrated/test_dense_kind.py:121`
**Row**: M3

**Issue**: `test_dense_corpus_readiness_and_api_budget` checks five things in one test:

- the corpus counts and model id in Postgres;
- the load Job log;
- the Deployment's memory limit and ready replicas;
- pod restarts and OOM kills;
- `/readyz` and peak memory.

A failure names the test, not which of R1, R5 or readiness broke. `tests/integrated/test_hybrid_check.py` cites this one test for both R1 and R5.

**Fix**: Split it into three tests: one for the corpus and load, one for readiness, and one for resource budget and restarts. Then update the docstring in `test_hybrid_check.py` so each Done when line names its own check.

---

## Decision

**Recommendation**: Request Changes

---

## Reviewed Files

- `tests/eval/test_eval_kind.py` (231 lines)
- `tests/integrated/test_dense_kind.py` (211 lines)
- `tests/integrated/test_hybrid_check.py` (135 lines)
- `tests/postgres/test_dense_postgres.py` (154 lines)
- `tests/postgres/test_eval_reuse_postgres.py` (59 lines)
- `tests/postgres/test_load_asset_postgres.py` (147 lines)
- `tests/unit/test_chart_defaults.py` (46 lines)
- `tests/unit/test_chart_defaults_expanded.py` (93 lines)
- `tests/unit/test_chart_embeddings.py` (186 lines)
- `tests/unit/test_dense.py` (494 lines)
- `tests/unit/test_dense_expanded.py` (249 lines)
- `tests/unit/test_dense_oracle_pinned.py` (31 lines)
- `tests/unit/test_embedder_concurrency.py` (116 lines)
- `tests/unit/test_embedding_asset.py` (312 lines)
- `tests/unit/test_eval_embedder_expanded.py` (354 lines)
- `tests/unit/test_hybrid.py` (195 lines)
- `tests/unit/test_hybrid_check_38_expanded.py` (46 lines)
- `tests/unit/test_hybrid_expanded.py` (100 lines)
- `tests/unit/test_load_asset.py` (325 lines)
- `tests/unit/test_publish_script.py` (205 lines)
- `tests/unit/test_refactor_sweep_37_expanded.py` (103 lines)

## Context Read

- `_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/epic-hybrid-retrieval.md`
- `_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/tickets.toml`
