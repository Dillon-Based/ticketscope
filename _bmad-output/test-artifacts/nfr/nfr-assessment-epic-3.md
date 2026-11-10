---
runScope: 'epic'
runKey: 'epic-3'
workflowStatus: 'completed'
stepsCompleted: ['step-01-load-context', 'step-02-define-thresholds', 'step-03-gather-evidence', 'step-04-evaluate-and-score', 'step-04e-aggregate-nfr', 'step-05-generate-report']
lastStep: 'step-05-generate-report'
lastSaved: '2026-11-10'
workflowType: 'testarch-nfr-assess'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/epic-hybrid-retrieval.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/tickets.toml
  - _bmad-output/test-artifacts/test-design/test-design-epic-3.md
  - knowledge/adr-quality-readiness-checklist.md
  - knowledge/ci-burn-in.md
  - knowledge/test-quality.md
  - knowledge/playwright-config.md
  - knowledge/error-handling.md
  - knowledge/playwright-cli.md
---

# NFR Evidence Audit - epic-hybrid-retrieval (epic 3): Dense and hybrid retrieval, scored against keyword

**Date:** 2026-11-10
**Story:** n/a (epic scope, run key `epic-3`)
**Overall Status:** CONCERNS ⚠️

---

Note: This audit summarizes existing evidence; it does not run the CI workflows. The NFR thresholds come from the epic's test design (`test-design-epic-3.md`, section NFR Planning), which is the primary source per step 2. Two local re-runs on 2026-11-10 check that the evidence is current:

- `uv run lint-imports`: 7 contracts kept, 0 broken.
- `uv run pytest`: 1101 passed, 16 skipped, 53 deselected (kind, postgres and eval tests), 1 xfailed.

**Execution mode:** sequential. All four domains were evaluated in this session, with no subagents.

## Executive Summary

**Assessment:** 13 PASS, 1 CONCERNS, 0 FAIL

**Blockers:** 0

**High Priority Issues:** 0

**Recommendation:** CONCERNS. Nothing blocks release. Every security, performance and maintainability criterion has evidence. One reliability criterion is only partly evidenced. Rankings reproducing across runs is shown by repeated passing eval gates on CI. Reproduction across machines is not shown: the planned parity checks are missing (the asset's vectors against a recompute in the CI image, two fresh processes embedding identical bytes, and the F5 reload comparison).

**Scope note:** the cluster-side evidence comes from CI on the epic's own pull requests, all `success`:

- `ci` run 42910706544 on PR #54 (story 3.8): `checks`, `charts` and `integrated-check / deploy`.
- `eval` runs 42891461582 (story 3.6), 42903014546 (story 3.7) and 42891445428 (eval speedups).
- `eval` run 42835557994, whose results are committed as `eval/baseline.json` (#47).

PR #54's own `eval` run took 11 s: the eval job runs only when a score can move, and that change could not move one. `main` is at 9c6efe0, level with `origin/main`. An open PR, "api: cap onnxruntime threads at the CPU limit", is not on `main`, and this audit does not count it.

---

## Security Assessment

Domain status: **PASS**

### Embedding assets hold no text or person identifier

- **Status:** PASS ✅
- **Threshold:** Embedding assets hold no text or person identifier (Provenance)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** An asset record holds only `issue`, `model` and `vector`. A record with any text field is refused when parsed, and a built asset contains no title, URL, mention, masked marker or link.
- **Evidence:** tests/unit/test_embedding_asset.py
- **Supports:** `test_a_built_asset_carries_no_text_or_identifier` and `test_a_record_with_a_text_field_is_refused` pass, and `test_every_record_holds_only_issue_model_and_vector` checks the record field set. The test review flags that this last test loops over records with no length check (H3).

### api and eval read issue_embedding as ticketscope_ro and cannot write it

- **Status:** PASS ✅
- **Threshold:** `api` and `eval` read `issue_embedding` as `ticketscope_ro` and cannot write it (AD-7)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** Postgres tests check that the role can read the table and that a write as `ticketscope_ro` raises `InsufficientPrivilege`. The cluster eval check confirms that the eval Job's only secret reference is the read-only role.
- **Evidence:** tests/postgres/test_dense_postgres.py
- **Supports:** `test_the_read_only_role_reads_and_cannot_write` reads 4 rows and has a write refused
- **Evidence:** tests/eval/test_eval_kind.py
- **Supports:** `test_eval_job_reads_as_ticketscope_ro` checks that the Job's secret refs are exactly the ro secret, with username `ticketscope_ro`

### The Hugging Face source is read at build time only

- **Status:** PASS ✅
- **Threshold:** Hugging Face read at build time only; the image runs with no network for the model
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** The model is downloaded in a build stage. The runtime stage sets `HF_HUB_OFFLINE=1` and reads the model only from `/models`.
- **Evidence:** images/app.Dockerfile
- **Supports:** runtime sets `HF_HUB_OFFLINE=1`, and the model is read from `/models` only
- **Evidence:** tests/unit/test_chart_embeddings.py
- **Supports:** `test_the_image_reads_hugging_face_only_in_a_build_stage_and_runs_offline` passes

---

## Performance Assessment

Domain status: **PASS**

### Dense and hybrid p95 reported, never gated

- **Status:** PASS ✅
- **Threshold:** p95 reported for every mode, not gated (AD-12)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** `eval/baseline.json`, committed from CI run 42835557994, reports `p95_latency_ms` for every mode and ticket kind:

  | Mode    | Overall | Short    | Log-heavy |
  | ------- | ------- | -------- | --------- |
  | Keyword | 18.4 ms | 17.4 ms  | 54.2 ms   |
  | Dense   | 118.1 ms | 99.3 ms | 182.4 ms  |
  | Hybrid  | 135.4 ms | 117.4 ms | 213.1 ms |

  The gate does not act on p95.
- **Evidence:** eval/baseline.json
- **Supports:** `p95_latency_ms` is present and positive for keyword, dense and hybrid in short, log-heavy and overall
- **Evidence:** tests/eval/test_eval_kind.py
- **Supports:** the all-modes check asserts `p95_latency_ms > 0` for every mode and kind

### load stays under 600 s with the asset

- **Status:** PASS ✅
- **Threshold:** `load` under 600 s with the pinned asset (story 3.4, publish guard)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** With the pinned asset, `load` finished in 16 s on kind within its 512Mi limit (recorded in story 3.6). The publish script keeps its timed-load guard.
- **Evidence:** deploy/charts/ticketscope/values.yaml
- **Supports:** the `jobs` comment records that load completed in 16 s on kind with the pinned asset
- **Evidence:** tests/unit/test_publish_script.py
- **Supports:** the publish script's guards (clean main, never overwrite, timed load) are tested

### api and Job resources come from measurement

- **Status:** PASS ✅
- **Threshold:** `api` and Job resources set from measured needs (R-002; stories 3.3, 3.6)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** The `api` limits are 1 CPU and 512Mi, about 1.9× the measured peak of 288 MB. The comments record 35.7 ms per issue for embedding and 80–134 ms per dense search. The cluster check asserts the 512Mi limit, no restarts, no OOM kill, and Ready.
- **Evidence:** deploy/charts/ticketscope/values.yaml
- **Supports:** the `api.resources` comment names the measured peak memory and embedding time
- **Evidence:** tests/unit/test_chart_defaults.py
- **Supports:** `test_values_comments_name_the_measured_memory_and_embedding_time` and `test_api_resources_set_cpu_and_memory_requests_and_limits` pass
- **Evidence:** tests/integrated/test_dense_kind.py
- **Supports:** `test_dense_corpus_readiness_and_api_budget` passed in `integrated-check`, run 42910706544

### The eval run fits the Job deadline

- **Status:** PASS ✅
- **Threshold:** The eval run's wall clock fits the eval Job's `activeDeadlineSeconds`, raised if needed (story 3.5)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** The deadline was raised from 1800 s to 2700 s. The committed baseline run took 1822.3 s, which is under the new deadline but would have exceeded the old one. The cluster check asserts that `wall_seconds` is under the deadline.
- **Evidence:** eval/baseline.json
- **Supports:** `wall_seconds` 1822.3
- **Evidence:** deploy/charts/ticketscope/values.yaml
- **Supports:** `eval.activeDeadlineSeconds: 2700`, with a comment citing the 1475 s measured in story 3.5
- **Evidence:** tests/eval/test_eval_kind.py
- **Supports:** `test_the_run_fits_inside_the_job_deadline` (criterion `ticketscope--e3-s5--AC-4`)

---

## Reliability Assessment

Domain status: **CONCERNS**

### Rankings reproduce across runs and machines within the 0.005 tolerance

- **Status:** CONCERNS ⚠️
- **Threshold:** Rankings reproduce across runs and machines within the 0.005 tolerance. Planned checks: two fresh-process embeds, a parity check of asset vectors against a recompute in the CI image, and the F5 reload comparison (R-004).
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** Reproducibility across CI runs is shown in practice. Asset vectors built on a person's machine and query vectors embedded on CI runners passed the 0.005-tolerance gate against the committed baseline in three later `eval` runs (42891445428, 42891461582, 42903014546). The ranking components are deterministic in unit tests:
  - the dense cosine oracle, pinned by digest;
  - fusion is reproducible and breaks ties by issue number;
  - Postgres fetches with tied scores are stable across `k`.

  None of the planned parity checks exists in `tests/`: no recompute in the CI image, no two-process byte comparison, and no F5 reload comparison.
- **Evidence:** tests/unit/test_dense_oracle_pinned.py
- **Supports:** `test_the_cosine_oracle_is_unchanged_since_it_was_committed`
- **Evidence:** tests/unit/test_hybrid.py
- **Supports:** `test_fusion_is_reproducible`
- **Evidence:** tests/postgres/test_eval_reuse_postgres.py
- **Supports:** a shorter keyword or dense fetch is the head of a longer one, with tied scores across the cuts
- **Findings:** Repeated green gates are a sample, not a guarantee. A runner with a different CPU or architecture (AD-16 builds amd64 and arm64) could flip ranks near a tie, and nothing would catch it before the required `eval` check flapped.
- **Recommendation:** Add the R-004 parity row: recompute about 200 sampled asset vectors inside the CI image (cosine ≥ 0.9999), have two fresh processes embed the same 20 texts to identical bytes, and run the F5 two-reload comparison for dense and hybrid.

### A load is all-or-nothing and idempotent

- **Status:** PASS ✅
- **Threshold:** A load is all-or-nothing and idempotent (AD-22)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** A second load is a no-op. A wrong checksum fails with its reason and changes nothing. Bad coverage fails and keeps the previous corpus. A manifest whose count disagrees with its records is refused, and so is an asset for another preprocessing version or snapshot. Postgres tests run the asset load against a real database.
- **Evidence:** tests/unit/test_load_asset.py
- **Supports:** `test_a_second_load_is_a_no_op`, `test_a_wrong_checksum_fails_with_its_reason_and_changes_nothing`, `test_bad_coverage_fails_the_load_and_keeps_the_previous_corpus`
- **Evidence:** tests/postgres/test_load_asset_postgres.py
- **Supports:** the asset load against Postgres

### api is Ready only on a matching model

- **Status:** PASS ✅
- **Threshold:** `api` fails readiness when its model id differs from `corpus_meta.embedding_model_id` (AD-21)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** On kind, changing `corpus_meta` to another model makes `/readyz` return 503 with "embedding model mismatch". Restoring it returns `api` to Ready. This passed in `integrated-check`, run 42910706544.
- **Evidence:** tests/integrated/test_hybrid_check.py
- **Supports:** `test_readiness_fails_on_a_model_mismatch`

---

## Maintainability Assessment

Domain status: **PASS**

### core imports no embedding runtime

- **Status:** PASS ✅
- **Threshold:** `core` imports no embedding runtime (AD-1, import-linter)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** `uv run lint-imports` on 2026-11-10: 7 contracts kept, 0 broken. The `checks` job passed in run 42910706544.
- **Evidence:** .importlinter
- **Supports:** the layer contracts, kept on 2026-11-10

### One source of truth for the model id and preprocessing version

- **Status:** PASS ✅
- **Threshold:** One source of truth for the model id and preprocessing version
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Actual:** The asset builder names the asset from `core`'s preprocessing version. The pinned model in `values.yaml` must equal the Dockerfile's `EMBEDDING_MODEL_ID`. A change to the search-text rule changes the preprocessing version.
- **Evidence:** tests/unit/test_embedding_asset.py
- **Supports:** `test_the_builder_names_the_asset_from_core_s_preprocessing_version`, `test_the_pinned_model_is_the_findings_decision_and_the_dockerfile_s`
- **Evidence:** tests/unit/test_load_expanded.py
- **Supports:** `test_preprocessing_version_changes_with_the_search_text_rule`

### New modes need no change to jobs.eval

- **Status:** PASS ✅
- **Threshold:** Registering a mode needs no change to `jobs.eval` (AD-19)
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Evidence:** tests/unit/test_eval_main.py
- **Supports:** `test_a_mode_registered_after_import_is_scored_with_no_job_change`

### No time.sleep in tests/

- **Status:** PASS ✅
- **Threshold:** No `time.sleep` in `tests/`
- **Threshold Source:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Evidence:** tests/unit/test_no_sleep_in_tests.py
- **Supports:** `test_tests_never_call_time_sleep` scans `tests/`, including references such as `wait=time.sleep`

---

## Evidence Gaps

1 evidence gap identified - action required:

- **reliability-rankings-reproduce-across-runs-and-machines-within-the-0-005-tolerance:** Rankings reproduce across runs and machines within the 0.005 tolerance: no supplied implementation evidence for the cross-machine parity checks (asset against recompute, two fresh processes, F5 reload comparison)

---

## Recorded-Only NFR Criteria

These criteria were preserved without automated assessment.

| ID | Category | Label | Declared threshold | Threshold source | Assessment mode |
| --- | --- | --- | --- | --- | --- |
| scalability-vector-index-trigger | Scalability & Availability | The p95 at which a vector index is added (C-4) | UNKNOWN (dense is an exact scan until p95 demands an index) | _bmad-output/test-artifacts/test-design/test-design-epic-3.md | RECORDED ONLY |
| deployability-image-size-growth | Deployability | Maximum image size growth from the baked model | UNKNOWN | _bmad-output/test-artifacts/test-design/test-design-epic-3.md | RECORDED ONLY |
| qos-default-mode-tie-width | QoS/QoE | Tie width for choosing the default mode (C-4) | UNKNOWN (hybrid wins an exact tie; baseline overall MRR@10 hybrid 0.5936, dense 0.5787, keyword 0.5505) | _bmad-output/test-artifacts/test-design/test-design-epic-3.md | RECORDED ONLY |

---

## Recommended Actions

### Short-term (Next Milestone) - MEDIUM Priority

1. **Add the R-004 embedding parity row** - MEDIUM - medium - epic-hybrid-retrieval follow-up
   - Recompute about 200 sampled asset vectors in the CI app image and require cosine ≥ 0.9999 with identical top-10 lists, have two fresh processes embed the same 20 texts to identical bytes, and run the F5 two-reload comparison for dense and hybrid.

2. **Fix the `HELM_TIMEOUT` override in `scripts/kind-up.sh`** - LOW - small - epic-hybrid-retrieval follow-up
   - With `EMBEDDINGS_COMPUTE=1`, the script resets the eval branch's 60m Helm timeout to 50m. A strict xfail records this (`tests/unit/test_eval_embedder_expanded.py:332`). It affects local runs that compute embeddings, not CI.

### Long-term (Backlog) - LOW Priority

1. **Watch the eval wall clock against its deadline** - LOW - epic-eval-gate
   - The committed run took 1822 s of a 2700 s deadline. A larger pair set or a slower runner narrows that margin, so keep reporting the timing in the job summary.

---

## Gate YAML Snippet

```yaml
nfr_assessment:
  date: '2026-11-10'
  story_id: 'n/a (epic-3)'
  feature_name: 'epic-hybrid-retrieval: Dense and hybrid retrieval, scored against keyword'
  audited_domains:
    security: 'PASS'
    performance: 'PASS'
    reliability: 'CONCERNS'
    maintainability: 'PASS'
  overall_status: 'CONCERNS'
  critical_issues: 0
  high_priority_issues: 0
  medium_priority_issues: 1
  concerns: 1
  blockers: false
  quick_wins: 1
  evidence_gaps: 1
  recommendations:
    - 'Add the R-004 embedding parity row (asset vs recompute in the CI image, two fresh processes, F5 reload comparison)'
    - 'Fix the EMBEDDINGS_COMPUTE override of HELM_TIMEOUT in scripts/kind-up.sh'
    - 'Keep the eval wall clock in the job summary against the 2700 s deadline'
```

---

## Related Artifacts

- **Epic:** _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/epic-hybrid-retrieval.md
- **Test Design:** _bmad-output/test-artifacts/test-design/test-design-epic-3.md
- **Evidence Sources:**
  - CI results: `ci` run 42910706544 (PR #54: `checks`, `charts`, `integrated-check / deploy`, all success); `eval` runs 42891445428, 42891461582 and 42903014546 (all success)
  - Eval baseline: `eval/baseline.json` from `eval` run 42835557994 (lineage `BAAI/bge-small-en-v1.5`, `pre1.kind2-t3.outcome3.emb1`, snapshot 2026.11.1)
  - Spike findings: _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/spike-choose-the-embedding-model-findings.md
  - Test quality: _bmad-output/test-artifacts/test-review/test-review-epic-3.md

---

## Sign-Off

**NFR Evidence Audit:**

- Overall Status: CONCERNS ⚠️
- Critical Issues: 0
- High Priority Issues: 0
- Concerns: 1
- Evidence Gaps: 1

**Gate Status:** CONCERNS ⚠️

**Generated:** 2026-11-10
**Workflow:** testarch-nfr v5.0
