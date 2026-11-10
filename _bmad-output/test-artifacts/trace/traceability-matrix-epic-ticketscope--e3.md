---
workflowType: 'testarch-trace'
runScope: 'epic'
runKey: 'epic-ticketscope--e3'
gateType: 'epic'
workflowStatus: 'completed'
stepsCompleted: ['step-01-load-context', 'step-02-discover-tests', 'step-03-map-criteria', 'step-04-analyze-gaps', 'step-05-gate-decision']
lastStep: 'step-05-gate-decision'
lastSaved: '2026-11-10'
sourceSha: '9c6efe0d0d4fa957afde1b4152357bfc5e7e488b'
oracleGranularity: 'requirements'
collectionMode: 'contract_static'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/epic-hybrid-retrieval.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/story-hybrid-search-fuses-keyword-and-dense-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/spike-choose-the-embedding-model-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/story-embeddings-load-from-a-published-release-asset-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/story-ci-scores-keyword-dense-and-hybrid-side-by-side-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/story-chart-defaults-carry-the-model-s-needs-and-the-best-mode-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/story-refactor-sweep-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/story-integrated-check-on-kind-plan.md
  - _bmad-output/test-artifacts/test-design/test-design-epic-3.md
  - _bmad-output/test-artifacts/nfr/nfr-assessment-epic-3.md
  - _bmad-output/test-artifacts/test-review/test-review-epic-3.md
  - _bmad-output/test-artifacts/live-verification-results.json
---

# Traceability Matrix & Gate Decision — Epic 3: Dense and hybrid retrieval, scored against keyword

## Gate Decision: FAIL

**Rationale:** P0 coverage is 0% (required: 100%). Three critical requirements (R1, R2, R4) are below FULL coverage: all three are PARTIAL. Overall FULL coverage is 20% (minimum 80%), and P1 is 50% (minimum 80%).

Of the 28 criteria, 21 are FULL. The other seven are PARTIAL or NONE because a clause in each rests on a CI run or a person-run step, and no test or live verification record carries it:

- story 1: AC-4, AC-6 and AC-7;
- spike: AC-1 and AC-3;
- story 4: AC-5;
- story 7: verify.

**Date:** 2026-11-10. **Evaluator:** Claude Code / Master Test Architect. **Source:** `9c6efe0d0d4fa957afde1b4152357bfc5e7e488b` (`main`, level with `origin/main`). **Gate type:** epic. This is the first trace for this key.

**What the FAIL means.** Every P0 behaviour the code implements has passing tests: the ranking oracles, embedding state against `corpus_meta`, the asset load, and the asset's content. Each P0 requirement fails only because it shares a contributor criterion whose clause is a process observation:

- a PR's CI passing with the baseline unchanged;
- a person publishing the Release;
- an image embedding with the network disabled;
- the eval Job left untraced.

A requirement is FULL only when every contributor is FULL. Trace never records live verification itself, and `live-verification-results.json` holds no epic 3 records. So these clauses cannot count.

**How to close it:**

1. Record live verification results for the process criteria at this commit (story 1 AC-7, story 4 AC-5, story 7 verify, spike AC-3), with CI run evidence. These alone move R1, R2 and R4 toward FULL, but live-only evidence caps the run at CONCERNS.
2. Add three small static tests:
   - the eval Job emits no spans (story 1 AC-4);
   - the app image embeds a text under `docker run --network none` (story 1 AC-6);
   - the spike findings name image-size impact, the cut test, and per-issue and total embedding time (spike AC-1).

## Coverage Summary

| Priority | Total | FULL | Coverage |
| --- | ---: | ---: | ---: |
| P0 | 3 | 0 | 0% |
| P1 | 2 | 1 | 50% |
| P2 | 0 | 0 | 100% |
| P3 | 0 | 0 | 100% |
| Overall | 5 | 1 | 20% |

Gate rows: 1 FULL, 4 PARTIAL, 0 NONE.

Criteria: 21 FULL, 6 PARTIAL, 1 NONE (75% FULL).

Accepted evidence: 58 test references across 18 files: 32 unit, 7 API (TestClient over `/v1` and `/readyz`), 3 integration (Postgres), 14 e2e (kind, smoke, eval), 2 other (static file checks). Kind, Postgres and eval tests are accepted as static evidence under `collection_mode: contract_static`. This trace did not run them. Their latest CI results are informational:

- `ci` run 42910706544 (PR #54): `integrated-check / deploy` success.
- `eval` runs 42891461582 and 42903014546: success.

Local sanity run at HEAD (informational, not counted): `uv run pytest` 1101 passed, 16 skipped, 1 xfailed; `uv run lint-imports` 7 kept, 0 broken.

**Oracle.** The oracle is the formal epic requirements R1 to R5, at requirement granularity: a v7 epic with `R<n>` lines and no duplicate ids. Criteria come from each plan's Acceptance Criteria:

- story 1, spike 3, story 4, story 5 and story 6 have Acceptance Criteria;
- stories 2, 7 and 8 have none, so their `tickets.toml` `verify` line is the criterion (`-verify`).

Declared links come from the `(R<n>)` tags in each ticket's `verify` text. Where an AC names no requirement, its ticket's `covers` applies.

Criterion priorities are inferred from `test-design-epic-3.md`'s coverage plan:

- P0: rows (A)–(D), the ranking oracles, embedding state and asset content;
- P1: contract, readiness, drift, resources, integrated check and sweep;
- P2: findings, cost and default mode.

A requirement takes the highest priority among its contributors.

**Supporting audits:**

- NFR: `nfr-assessment-epic-3.md` (CONCERNS: cross-machine embedding parity is unevidenced).
- Test quality: `test-review-epic-3.md` (68/100, Request Changes).

**Live results.** `live-verification-results.json` holds 26 records, all for epics 1 and 2, recorded at `424291f`. None names an epic 3 criterion, and none is counted.

## Requirement Oracle Mapping

| ID | Kind | Requirement | Priority | Coverage |
| --- | --- | --- | --- | --- |
| ticketscope--e3--R1 | requirement | Every loaded issue has an embedding from the chosen model in `issue_embedding`, loaded from a precomputed Release asset pinned in `values.yaml`. Met when `load` on kind fills the table from the pinned asset without computing any embedding, and `corpus_meta` records the model id. | P0 | PARTIAL |
| ticketscope--e3--R2 | requirement | Dense and hybrid retrieval are modes in the core registry, served by `/v1/search`. Met when a vague query and a log-heavy query each return ranked issues with outcomes in dense and in hybrid mode on kind. | P0 | PARTIAL |
| ticketscope--e3--R3 | requirement | The embedding model is chosen by a scored eval. Met when a committed record compares the candidate models on Recall@10, MRR@10 by ticket kind, embedding time and memory, and names the one chosen. | P1 | PARTIAL |
| ticketscope--e3--R4 | requirement | The CI eval table shows keyword, dense and hybrid side by side, split by ticket kind, and is published whatever it shows. Met when the committed baseline and the README table carry all three modes from a CI run. | P0 | PARTIAL |
| ticketscope--e3--R5 | requirement | The chosen model's CPU, memory and embedding-time needs and the default retrieval mode are chart defaults in `values.yaml`. Met when `api` runs Ready and answers a dense search on kind within those defaults, and a request that omits `mode` is served by the default mode. | P1 | FULL |

## Detailed Mapping

### ticketscope--e3--R1 (P0, requirement): PARTIAL

Source: `epic-hybrid-retrieval.md`, Requirements, R1. Contributors: s1 AC-1 to AC-7, s4 AC-1 to AC-5, s8 verify.

Gaps: s1 AC-6 and AC-7 and s4 AC-5 are PARTIAL. Every behaviour the requirement line states is covered by FULL contributors:

- load from the pinned asset: s4 AC-1 and s8;
- nothing computed: s4 AC-1;
- the model id in `corpus_meta`: s4 AC-1 and s1 AC-3.

The requirement is PARTIAL only through those process contributors.

### ticketscope--e3--R2 (P0, requirement): PARTIAL

Source: `epic-hybrid-retrieval.md`, Requirements, R2. Contributors: s1 AC-1 to AC-7, s2 verify, s7 verify, s8 verify.

Gaps: s1 AC-4, AC-6 and AC-7 and s7 verify are PARTIAL. Every stated behaviour is covered: a vague query and a log-heavy query, each in dense and in hybrid on kind, with outcomes (s1 AC-1, s2 verify and s8).

### ticketscope--e3--R3 (P1, requirement): PARTIAL

Source: `epic-hybrid-retrieval.md`, Requirements, R3. Contributors: spike AC-1 to AC-3, s8 verify.

Gaps: spike AC-1 is PARTIAL and spike AC-3 is NONE. The requirement's own behaviours, comparing candidates on Recall@10, MRR@10 by kind, embedding time and memory, and naming the choice, are asserted by `test_model_choice_record_names_the_chosen_model`.

### ticketscope--e3--R4 (P0, requirement): PARTIAL

Source: `epic-hybrid-retrieval.md`, Requirements, R4. Contributors: s2 verify (its "no change to `jobs.eval`" clause is tagged R4), s5 AC-1 to AC-4, s7 verify, s8 verify.

Gaps: s7 verify is PARTIAL. Every stated behaviour is covered: the committed baseline and the README carry all three modes by kind, from a CI run (s5 AC-1 and AC-3, s8).

### ticketscope--e3--R5 (P1, requirement): FULL

Source: `epic-hybrid-retrieval.md`, Requirements, R5. Contributors: s6 AC-1 to AC-3 and s8 verify, all FULL.

Every stated behaviour is covered: Ready and a dense answer within the defaults (s6 AC-1), the omitted mode served by the default (s6 AC-2), and the measured needs recorded (s6 AC-3).

#### ticketscope--e3-s1--AC-1 (P1): FULL

Given kind with `computeOnKind` set and a fresh load, `mode=dense` for a vague query and for a log-heavy query returns 200 with ranked issues, `score_kind` `cosine`, and outcomes. Links: R1, R2.

- e2e `tests/integrated/test_dense_kind.py:50` `test_dense_gateway_queries_and_tempo[vague, log-heavy]`. It asserts 10 ranked results, `cosine`, and outcomes equal to the `issue` rows. Since the pin, dense is enabled from the asset rather than the flag.
- unit `tests/unit/test_dense.py:188` `test_dense_search_returns_ranked_cosine_results`

#### ticketscope--e3-s1--AC-2 (P1): FULL

With `computeOnKind` off, `dense` is unavailable (503 problem+json), keyword is unchanged, and `api` is Ready. Links: R1, R2.

- api `tests/unit/test_dense.py:202` `test_dense_is_503_problem_json_when_unavailable`
- unit `tests/unit/test_dense_expanded.py:119` `test_dense_is_unavailable_without_an_embedder`
- unit `tests/unit/test_dense.py:344` `test_load_with_the_flag_off_computes_nothing`
- api `tests/unit/test_dense.py:213` `test_readiness_without_a_configured_model_is_ready_on_a_keyword_only_corpus`

Note: the kind test's flag-off branch (`test_dense_kind.py:59`) can no longer run in CI, because the asset is pinned. This criterion is carried by the API-level tests.

#### ticketscope--e3-s1--AC-3 (P1): FULL

`/readyz` returns 503 when the model id differs from `corpus_meta` or `corpus_meta` holds null, and Ready when they match. Links: R1, R2.

- api `tests/unit/test_dense.py:225` `test_readiness_fails_naming_both_ids_when_they_differ[other, None]`
- api `tests/unit/test_dense.py:218` `test_readiness_is_ready_when_the_model_ids_match`
- e2e `tests/integrated/test_hybrid_check.py:97` `test_readiness_fails_on_a_model_mismatch`

#### ticketscope--e3-s1--AC-4 (P1): PARTIAL

In a Tempo trace, `retrieval dense` has a child `embeddings {model}` span with `gen_ai.request.model`, and `/readyz` and eval stay untraced. Links: R1, R2.

- e2e `tests/integrated/test_dense_kind.py:83` (Tempo poll inside `test_dense_gateway_queries_and_tempo`)
- api `tests/unit/test_dense.py:258` `test_dense_search_emits_an_embeddings_span_under_retrieval_dense`
- api `tests/unit/test_dense.py:276` `test_probes_stay_untraced_with_a_model_configured`

Missing: no test asserts that the eval Job emits no spans.

#### ticketscope--e3-s1--AC-5 (P0): FULL

The unit suite runs with the hash fake and no model or database, covering the cosine oracle (order 1, 2, 3, 4; `1 - distance`), exclusion keeping `k` slots, and a load rollback leaving the previous corpus. Links: R1, R2.

- unit `tests/unit/test_dense.py:53` `test_cosine_oracle_order_and_scores`
- unit `tests/unit/test_dense.py:62` `test_cosine_is_not_a_distance_or_an_inner_product`
- unit `tests/unit/test_dense.py:78` `test_exclusion_keeps_k_slots`
- unit `tests/unit/test_dense.py:382` `test_an_embedder_failure_exits_1_and_the_previous_corpus_answers`
- unit `tests/unit/test_dense_oracle_pinned.py:25` `test_the_cosine_oracle_is_unchanged_since_it_was_committed`
- integration `tests/postgres/test_dense_postgres.py:56` `test_the_cosine_oracle_through_sql`

#### ticketscope--e3-s1--AC-6 (P1): PARTIAL

The built app image embeds a text with the network disabled, and `ruff`, `pyright`, `lint-imports` and the full `pytest` pass. Links: R1, R2.

- other `tests/unit/test_chart_embeddings.py:105` `test_the_image_reads_hugging_face_only_in_a_build_stage_and_runs_offline` (a static Dockerfile check)
- unit `tests/unit/test_import_linter_enforcement.py` (import-linter contracts)

Missing: no test runs the image with the network disabled. The kind dense test runs it with `HF_HUB_OFFLINE=1` on a networked cluster. The lint and type-check clauses are CI `checks` job steps, not tests.

#### ticketscope--e3-s1--AC-7 (P1): PARTIAL

On the PR, `ci.yml` (including `integrated-check`) and `eval.yml` pass with `eval/baseline.json` unchanged. Links: R1, R2.

Evidence: the integrated suite exists and can be re-run (`tests/integrated/`). Missing: the clause about PR #36 is a CI observation with no live verification record.

#### ticketscope--e3-s2--verify (P0): FULL

Fakes pass a hand-computed fusion case, a tie broken by issue number, an excluded issue never scoring with no slot lost, and `k` larger than either side (R2). On kind, `mode=hybrid` returns ranked issues with outcomes for both queries (R2). Registering hybrid needs no change to `jobs.eval` (R4).

- unit `tests/unit/test_hybrid.py:39` `test_a_known_pair_of_rankings_fuses_to_a_known_order`
- unit `tests/unit/test_hybrid.py:56` `test_ties_break_on_issue_number`
- unit `tests/unit/test_hybrid.py:62` `test_an_excluded_issue_never_scores_and_costs_no_slot`
- unit `tests/unit/test_hybrid.py:74` `test_k_larger_than_either_side_returns_the_union`
- unit `tests/unit/test_hybrid.py:89` `test_fusion_is_reproducible`
- api `tests/unit/test_hybrid.py:160` `test_v1_serves_hybrid_with_ranked_issues_and_outcomes`
- e2e `tests/integrated/test_dense_kind.py:177` `test_hybrid_gateway_queries_and_tempo[vague, log-heavy]`
- unit `tests/unit/test_eval_main.py:218` `test_a_mode_registered_after_import_is_scored_with_no_job_change`

#### ticketscope--e3-s3--AC-1 (P2): PARTIAL

The findings file holds, for every candidate, Recall@10 and MRR@10 by kind and overall, embedding time per issue and in total, peak memory, image-size impact, and the cut test. Links: R3.

- e2e `tests/integrated/test_hybrid_check.py:116` `test_model_choice_record_names_the_chosen_model`. It asserts the chosen model, Recall@10, MRR@10, `short`, `log_heavy`, "Embed time", "Memory", and at least two candidates.

Missing: image-size impact, the cut test, and the split between per-issue and total embedding time are not asserted.

#### ticketscope--e3-s3--AC-2 (P2): FULL

If the pick differs from bge-small-en-v1.5, the findings state the one-line change. Links: R3.

- unit `tests/unit/test_embedding_asset.py:250` `test_the_pinned_model_is_the_findings_decision_and_the_dockerfile_s`. The pin equals `BAAI/bge-small-en-v1.5`, so the condition does not hold, and the test asserts it does not.

#### ticketscope--e3-s3--AC-3 (P2): NONE

The spike run changed no tracked file outside `scripts/embedding_spike.py` and the findings file. Links: R3.

No test covers this. For information only: commit 6227978 touches the findings file, the spike plan, the epic's Notes and `scripts/embedding_spike.py`. That is a history observation, not test evidence.

#### ticketscope--e3-s4--AC-1 (P0): FULL

Given the pin, `load` on kind gives `issue_embedding` one row per issue, with no embedding computed. Links: R1.

- unit `tests/unit/test_load_asset.py:135` `test_pinned_load_writes_one_embedding_per_issue_and_computes_nothing`
- integration `tests/postgres/test_load_asset_postgres.py` (asset load through Postgres)
- e2e `tests/integrated/test_dense_kind.py:121` `test_dense_corpus_readiness_and_api_budget`. It asserts embeddings equal issues, the model in `corpus_meta`, and no `embedding_seconds` in the load log.

#### ticketscope--e3-s4--AC-2 (P0): FULL

A second `load` is a no-op. Links: R1.

- unit `tests/unit/test_load_asset.py:175` `test_a_second_load_is_a_no_op`

#### ticketscope--e3-s4--AC-3 (P0): FULL

A wrong checksum fails the load with its reason and leaves the corpus unchanged. Links: R1.

- unit `tests/unit/test_load_asset.py:206` `test_a_wrong_checksum_fails_with_its_reason_and_changes_nothing`
- integration `tests/postgres/test_load_asset_postgres.py:123` `test_a_bad_asset_fails_the_load_and_keeps_the_previous_corpus`

#### ticketscope--e3-s4--AC-4 (P1): FULL

The timed load stays under 600 s. Links: R1.

- e2e `tests/smoke/test_time_load.py:45` `test_pinned_asset_alone_loads_within_budget`

#### ticketscope--e3-s4--AC-5 (P1): PARTIAL

A person runs the publish script. The Release shows the asset, its checksum and notes with attribution, and a person merges the pin (person-run). Links: R1.

- unit `tests/unit/test_publish_script.py:181` `test_the_embedding_phase_embeds_the_verified_snapshot_and_attaches_with_the_guards`
- unit `tests/unit/test_publish_script.py:169` `test_a_published_embedding_asset_name_stops_the_run_before_anything_is_uploaded`
- unit `tests/unit/test_embedding_asset.py:257` `test_a_pinned_asset_is_whole_and_matches_the_snapshot_pin`

Missing: no live verification record shows the published Release (asset, checksum, notes).

#### ticketscope--e3-s5--AC-1 (P1): FULL

The eval artifact holds Recall@1, @5 and @10, MRR@10 and p95 for keyword, dense and hybrid, split short, log-heavy and overall, with the lineage's model id. Links: R4.

- e2e `tests/eval/test_eval_kind.py:203` `test_dense_and_hybrid_are_scored_beside_keyword_on_every_pair` (marker `ticketscope--e3-s5--AC-1`)
- unit `tests/unit/test_eval_main.py:394` `test_an_embedder_scores_dense_and_hybrid_beside_keyword_on_every_pair`

Note: the test review flags that this kind test checks the dense and hybrid metric values for type only (H10).

#### ticketscope--e3-s5--AC-2 (P1): FULL

The gate passes with the updated baseline and fails a deliberately regressed dense ranking. Links: R4.

- unit `tests/unit/test_eval_gate.py:248` `test_a_regressed_dense_ranking_fails_once_dense_is_in_the_baseline`
- unit `tests/unit/test_eval_gate.py:89` `test_any_drop_passes_when_baseline_changed_and_equals_run`

#### ticketscope--e3-s5--AC-3 (P1): FULL

The README check passes and shows all three modes. Links: R4.

- unit `tests/unit/test_readme_table.py:67` `test_committed_readme_equals_render_of_committed_baseline`
- unit `tests/unit/test_readme_table_expanded.py:128` `test_committed_readme_lists_every_baseline_mode_and_kind`
- e2e `tests/integrated/test_hybrid_check.py:125` `test_committed_baseline_and_readme_carry_all_three_modes`

#### ticketscope--e3-s5--AC-4 (P2): FULL

The run's wall-clock cost is in the job summary and under the Job deadline. Links: R4.

- unit `tests/unit/test_eval_main.py:307` `test_the_job_summary_shows_cost_pair_counts_and_metrics`
- e2e `tests/eval/test_eval_kind.py:228` `test_the_run_fits_inside_the_job_deadline` (marker `ticketscope--e3-s5--AC-4`)

#### ticketscope--e3-s6--AC-1 (P1): FULL

Under the new limits, `api` stays Ready during dense searches with no OOM kill. Links: R5.

- e2e `tests/integrated/test_dense_kind.py:121` `test_dense_corpus_readiness_and_api_budget`. It asserts the 512Mi limit, `readyReplicas` 1, no restarts, no `OOMKilled`, and `/readyz` ready.
- e2e `tests/integrated/test_dense_kind.py:98` `test_concurrent_dense_requests`

Note: the test review flags that the restart and OOM assertions sit inside a loop that could match no pod (H3).

#### ticketscope--e3-s6--AC-2 (P2): FULL

A `POST /v1/search` with no `mode` is served by the default mode, which has the best overall MRR@10 in `eval/baseline.json`. Links: R5.

- e2e `tests/integrated/test_hybrid_check.py:53` `test_omitted_mode_is_served_by_the_chart_default`
- unit `tests/unit/test_chart_defaults.py:13` `test_default_mode_is_the_best_overall_mrr_in_the_baseline` (default mode equals best overall MRR@10, hybrid on a tie)

#### ticketscope--e3-s6--AC-3 (P2): FULL

`values.yaml` comments name the measured memory and embedding time. Links: R5.

- other `tests/unit/test_chart_defaults.py:43` `test_values_comments_name_the_measured_memory_and_embedding_time`

#### ticketscope--e3-s7--verify (P1): PARTIAL

On a PR, the eval check passes with `eval/baseline.json` unchanged, `ci.yml` and its `integrated-check` pass, and import-linter keeps every contract. Links: R2, R4.

- unit `tests/unit/test_refactor_sweep_37_expanded.py` (the sweep's behaviour-preservation checks)
- unit `tests/unit/test_import_linter_enforcement.py`

Missing: the PR #52 CI pass is a CI observation with no live record. That PR's diff contains no `eval/baseline.json` (`git show --stat 3c0cddd`), but this is history, not test evidence.

#### ticketscope--e3-s8--verify (P1): FULL

On a fresh kind cluster, the `integrated-check` passes in CI and covers each Done when line of the epic. Links: R1, R2, R3, R4, R5.

- e2e `tests/integrated/test_hybrid_check.py`: one named check per Done when line, as its docstring maps them.
- unit `tests/unit/test_hybrid_check_38_expanded.py:31` `test_docstring_references_existing_tests`

## Invalid and Unlinked Criteria

None. Story 7's ticket has `covers = []`, but its verify text tags R2 and R4, and those tags are used as its links.

## Gaps & Recommendations

| # | Priority | Gap | Closes | Action |
| --- | --- | --- | --- | --- |
| 1 | P0 (via R1, R2, R4) | Process clauses with no live record: s1 AC-7, s4 AC-5, s7 verify, spike AC-3 | R1, R2, R4, R3 | Record live verification results at this commit, citing CI runs and the published embeddings Release. This caps the run at CONCERNS. |
| 2 | P1 | The eval Job is not shown to be untraced (s1 AC-4) | R1, R2 | Add a unit test that the eval Job's tracer provider exports no spans |
| 3 | P1 | No image embed with the network disabled (s1 AC-6) | R1, R2 | Add an `images` CI step or test: `docker run --network none <app image> python -c '<embed one text>'` |
| 4 | P2 | Findings completeness (spike AC-1) | R3 | Extend `test_model_choice_record_names_the_chosen_model` with image size, the cut test, and per-issue and total embedding time |
| 5 | P1 | Cross-machine embedding parity (NFR R-004, not an epic criterion) | — | See `nfr-assessment-epic-3.md`. Not a gate input. |

## Waiver Register Review

`_bmad-output/test-artifacts/gate-waivers.md` has no entry for `ticketscope--e3`. No waiver is filed, and none is applied.

## Next Actions

1. Record live verification results for the four process criteria, and add the three tests above. Then re-run `bmad-tea-trace` for `epic-ticketscope--e3`.
2. Address the test review's six HIGH findings, which touch criteria counted FULL here: s5 AC-1 (H10) and s6 AC-1 (H3).
