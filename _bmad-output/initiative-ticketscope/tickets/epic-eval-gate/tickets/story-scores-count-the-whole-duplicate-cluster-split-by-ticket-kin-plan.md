---
title: 'Scores count the whole duplicate cluster, split by ticket kind'
type: 'feature'
ticket: '2'
created: '2026-11-08'
status: done
baseline_revision: '7ea485ac88979fe18a98500c36a4fb45a9cf79a4'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'thorough'
review_source: 'pinned'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md'
  - '{project-root}/_bmad-output/test-artifacts/atdd/atdd-checklist-ticketscope--e2-s2.md'
warnings: ['oversized']
deferred: []
---

<intent-contract>

## Intent

**Problem:** Story 2.1 scores against the linked target only, with Recall@10 and MRR@10 overall. The gate and README need cluster relevance, Recall@1/5, p95 latency and a short/log-heavy/overall split, and unchanged code must give identical ranks.

**Approach:** Put each query's cluster (`relevant`) in the pairs file, derived in `core` from every in-subset duplicate link in both directions. `jobs.eval.score` counts a hit when any `relevant` member is in the top k, tallies per kind and overall over all queries, times each search, and records first-member ranks, skipped modes and pair counts. The adapter's top-k gets a total order. `run` and the kind check surface the cost.

## Boundaries & Constraints

**Always:** Cluster = connected component over every in-subset `duplicate_links` entry of every issue, both directions; `relevant` = cluster minus the query, sorted ascending; a link to an issue outside the snapshot adds no member. Pair rule (one per duplicate issue, AD-26) and kind (`derive_kind`, the pair's `kind`) are unchanged. Pairs-file line keys, in order: `query`, `target`, `kind`, `relevant`; the file regenerates byte-identical and the counts stay 10,473 / 10,164 / 309. Recall@k is a hit rate (any member in the top k); MRR@10 uses the first member's rank, 0 past 10; `overall` is computed over all queries, never as the mean of the kind means. Per mode the results hold `short`, `log_heavy`, `overall`, each with `recall@1`, `recall@5`, `recall@10`, `mrr@10`, `p95_latency_ms` (nearest-rank 95th percentile of the per-search wall time, `time.perf_counter`, search only, in ms) and `pairs_scored`; plus `first_member_ranks` as `[query, rank or null]` sorted by query. Top level keeps `k`, `lineage`, `pairs_file`, `wall_seconds`, sets `relevance: "cluster"`, and adds `skipped_modes` (sorted names of registry modes whose `available` is false). Eval still reads `REGISTRY` when called, searches `k=10` with `exclude={query}`, and uses title + description. The keyword top-k ties break on issue number, including the inner `LIMIT` of `_KEYWORD_SQL`. The kind step in CI writes the results file first, then appends a markdown summary (wall seconds, pairs by kind, per-mode metrics) to `$GITHUB_STEP_SUMMARY` when set.

**Never:** Edit `tests/eval_oracle.py` or what `tests/unit/test_eval_cluster_oracle.py` asserts (its skip marker and setup/key lookups may be adapted, recorded in Implementation Notes); a gate, baseline or README table (2.3, 2.4); gating or failing on p95; `time.sleep` in tests; changes to `PostgresCorpusStore`'s per-call connections; any change to the Release counts.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Oracle | `tests/eval_oracle.py` cluster fixture | every `CLUSTER_EXPECTED` value, `CLUSTER_PAIRS_BY_KIND`, `FIRST_MEMBER_RANKS` | — |
| Sibling hit | Query 3: target absent, sibling at rank 4 | hit, rank 4 | — |
| Self in results | Retriever returns the query | no hit, R@10 and MRR@10 0 | — |
| Chain / outside link | 13→14→15; 16→999 (999 not loaded) | cluster {13,14,15}; {16} | — |
| Rank 10 / 11 | first member at 10 / absent | RR 1/10 / 0; `null` rank | — |
| Fake second mode | `modes.REGISTRY` replaced after import | appears in results, no job change | — |
| Unavailable mode | `available` false | absent from `modes`, named in `skipped_modes` | — |
| Kind with no pairs | all pairs of one kind | that kind's metrics 0.0, `pairs_scored` 0, `p95_latency_ms` 0.0 | — |
| Pairs line | missing/extra key, unsorted or non-int `relevant` | rejected, names the line | `ValueError` → `run` returns 1 |
| BM25 tie at k-th score | planted ties | same top-k every run | — |

</intent-contract>

## Code Map

- `src/ticketscope/core/pairs.py` -- `Pair` (add required `relevant: tuple[int, ...]`), `derive_pairs`, `pairs_jsonl`, `as_pair`/`read_pairs`, `PAIR_KEYS`; add `duplicate_clusters(issues)` (union-find over in-subset links) for the oracle's `EXPECTED_CLUSTERS`. Reuse `core.derive.duplicate_target`/`derive_kind` (AD-26); do not re-implement.
- `src/ticketscope/core/snapshot.py:23-45` -- `DuplicateLink`(`target_number`, `direction`), `SnapshotIssueV2.duplicate_links`.
- `src/ticketscope/jobs/eval/score.py` -- `score`, `_Tally`, `query_text`, `K`, `RELEVANCE`; `jobs/eval/main.py` -- `run`, results line, `RESULTS_PREFIX`; `jobs/eval/__init__.py` re-exports `score`.
- `src/ticketscope/adapters/postgres.py:33-46` -- `_KEYWORD_SQL` inner `ORDER BY score LIMIT %(k)s` has no tie-break; add `number`. `core/fakes.py` already breaks ties on number.
- `scripts/derive_pairs.py` -- prints counts; no change expected beyond regenerating `eval/pairs/2026.11.1.jsonl`.
- `tests/eval/conftest.py` (`eval_results` fixture, writes `reports/eval-results.json`), `tests/eval/test_eval_kind.py` (asserts `relevance == "target"`: update), `tests/unit/test_eval_main.py`, `tests/unit/test_pairs.py`, `tests/unit/test_eval_oracle.py` (story 2.1's target-only test, retired by this story: remove it, keep its `k`/`exclude`/`pairs_scored` checks in the cluster test), `tests/unit/test_eval_cluster_oracle.py` (remove only the skip block), `tests/unit/test_postgres_store*.py`, `tests/eval_oracle.py` (read-only; use `MEMBERSHIP_*`, `EXPECTED_CLUSTERS`, `SELF_RANKING`).
- `.github/workflows/_kind-deploy.yml:116-141` -- runner-fit summary pattern for `$GITHUB_STEP_SUMMARY`; `deploy/charts/ticketscope/values.yaml` `eval.activeDeadlineSeconds`.

## Tasks & Acceptance

**Execution:**
- [x] `src/ticketscope/core/pairs.py` -- add `relevant` to `Pair` and the file format, `duplicate_clusters`, strict validation (`relevant` sorted, unique, ints, excludes the query, contains the target) -- Hit definition, AD-26.
- [x] `eval/pairs/2026.11.1.jsonl` -- regenerate with `scripts/derive_pairs.py`; counts unchanged.
- [x] `src/ticketscope/jobs/eval/score.py` -- cluster relevance, per-kind and overall tallies, p95 latency, `first_member_ranks`, `skipped_modes`, `relevance: "cluster"`; `main.py` log the same line plus `wall_seconds`.
- [x] `src/ticketscope/adapters/postgres.py` -- total order in the keyword top-k; confirm against the in-repo Postgres image (planted ties, two runs identical) and that the BM25 index is still used (compare `wall_seconds` with story 2.1's 116.7 s).
- [x] `tests/eval/conftest.py`, `tests/eval/test_eval_kind.py` -- write the job summary; assert cluster relevance, per-kind blocks, 10,164 / 309 / 10,473, first-member ranks recomputed independently into the same metrics, empty `skipped_modes`, cost present.
- [x] `tests/unit/` -- activate the cluster oracle; fake second mode; unavailable mode named; empty-kind row; cluster derivation vs `EXPECTED_CLUSTERS`; pairs format and rejection rows; two runs identical; tie-break SQL (and a Postgres tie test where the repo's tier allows); summary writer. Update `test_eval_main.py`/`test_pairs.py` for the new `Pair`.

**Acceptance Criteria:**
- Given the oracle fixture, when the cluster scaffold runs, then every metric short, log-heavy and overall equals `CLUSTER_EXPECTED` (overall differs from the mean of the kind means), a sibling counts as a hit, and the query never scores itself; the fixture still starts with the bytes its red commit `7ea485a` wrote (R2).
- Given `modes.REGISTRY` replaced after import with a fake second mode, when `score` runs, then the mode appears in the results with no change to `jobs.eval`; an unavailable mode is named in `skipped_modes` (R2).
- Given the same corpus scored twice, then the metrics and ranks are identical (R2, R3).
- Given a PR, when `eval.yml` runs, then `reports-kind`'s `eval-results.json` holds, for keyword, every metric split short, log-heavy and overall, pair counts 10,164 / 309 / 10,473, each query's first-member rank (an independent recompute matches), and `wall_seconds`, which the job summary also shows (R2).
- Given the pinned snapshot, when pairs regenerate, then the file is byte-identical and `derive_pairs.py` prints `10473 pairs: 10164 short, 309 log_heavy` (R1).

## Implementation Notes

- `tests/unit/test_eval_cluster_oracle.py`: only the skip block was removed; setup and key lookups were not adapted (the scaffold's seam matched).
- `tests/unit/test_eval_oracle.py` (story 2.1, target-only) deleted; its `k`/`exclude`/`pairs_scored` checks live in the cluster oracle test.
- Keyword tie-break verified on the in-repo Postgres image (`ticketscope-postgres:18-local`, pg_textsearch 1.5.1): 60 tied docs inserted shuffled gave an arbitrary top 10 before, `1..10` three runs running after. `EXPLAIN` still shows `Index Scan using issue_search_bm25_idx` under an Incremental Sort. Wall-time vs 116.7 s is only measurable in the kind run.

## Plan Change Log

## Review Triage Log

### 2026-11-08 — Review pass
- verdicts: 4 findings — high 0, medium 0, low 3, false 1, maybe-false 0
- findings:
  - `[low]` `[reject]` `test_a_latency_is_measured_per_search` patches the shared `time.perf_counter` with a fixed iterator — the patch is scoped by `monkeypatch` to the test body, `InMemoryCorpusStore` and `score` make no other calls, and pytest's own timing uses names bound at import; the test passes in the 822-test run. Switching to an injected clock is a refactor.
  - `[low]` `[reject]` Plan task checkboxes left `[ ]` — bookkeeping, not code; ticked directly in the plan.
  - `[low]` `[reject]` `first_member_ranks` is keyed by query, so a pairs file with a repeated query would disagree with `pairs_scored` — `derive_pairs` emits one pair per duplicate issue and the committed file has 10,473 unique queries; adding validation is new complexity for a state the program cannot reach.
  - `[false]` `[reject]` Byte-identical regeneration and unchanged oracle not confirmed from the diff — the reviewer's own reading of the file and `derive_pairs.py --check` (byte-identical) plus an empty `git diff 7ea485a -- tests/eval_oracle.py` confirm both. The kind-run latency comparison is a manual PR check, not an unmet criterion.

## Design Notes

- **Cluster in the pairs file:** cluster links exist only in the snapshot, not the loaded corpus, so eval cannot derive them; the pairs file, regenerated from the pinned asset, carries `relevant`. Story 2.1's `target`-only path is deleted, not kept behind a flag.
- **Kind** is the pair's `kind` (derived once with `derive_kind`, equal to the kind persisted at load).
- **Not built:** the test design's third-party IR library cross-check (a proposed dev dependency) is deferred; the independent recompute from `first_member_ranks` covers the real run.
- **Rank worked example:** top 10 `[100, 3, 1, ...]` for query 2 with `relevant {1, 3}` gives first-member rank 2; with none in the top 10 the rank is `null` and the reciprocal rank 0.

## Verification

**Commands:**
- `uv run pytest tests/unit/test_eval_cluster_oracle.py tests/unit/test_eval_main.py tests/unit/test_pairs.py` -- expected: pass.
- `uv run pytest tests/unit` -- expected: all pass (helm-gated tests may skip).
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports` -- expected: clean.
- `uv run python scripts/derive_pairs.py --check` -- expected: exit 0, `10473 pairs: 10164 short, 309 log_heavy`.
- `git diff 7ea485a -- tests/eval_oracle.py` -- expected: empty.

**Manual checks (if no CLI):**
- PR run of `eval.yml`: `eval-results.json` and the job summary hold the fields above; `ci.yml` integrated-check green.


### 2026-11-08 — Thorough follow-up review pass

- verdicts: 21 findings — high 0, medium 8, low 10, false 3, maybe-false 0
- findings (lens order; grouped findings retain individual rows):
  - `[low]` `[reject]` Blind: directly constructed invalid `Pair` bypasses mapping validation — only trusted Python callers supply `Pair`; production reads validated JSON and derives cluster-minus-query membership. Scoring self would additionally require a retriever violating `exclude`. Adding validation for this hypothetical misuse adds branches outside everyday operation.
  - `[low]` `[reject]` Blind: repeated query overwrites recorded rank — carried from the prior review: one pair per issue is guaranteed by derivation; the pinned file has 10,473 unique queries. No change or new deferral.
  - `[medium]` `[patch]` Blind: PostgreSQL cutoff ties lack executable behavioral coverage — added `tests/eval/test_postgres_ties.py`, executing the adapter SQL on real pg_textsearch with 60 shuffled tied documents and asserting issues 1–10 three times.
  - `[medium]` `[patch]` Blind: full-corpus cost comparison lacked run evidence — executing kind deployment and full eval; duration and artifact evidence recorded under Auto Run Result.
  - `[medium]` `[patch]` Blind: nonempty kind latency separation is untested — mixed short/log-heavy scripted durations now assert 4 ms short, 10 ms log-heavy and 10 ms overall.
  - `[low]` `[patch]` Blind: mode samples could accidentally share ranks or clocks without detection — added two modes with distinct rankings and 4/20 ms durations and asserted both outputs independently.
  - `[low]` `[patch]` Blind: persisted rank domain is unchecked — kind assertion now requires null or an integer from 1 through 10 before recomputation.
  - `[low]` `[reject]` Blind: duplicate JSON keys are accepted by the standard decoder — generated ground truth always emits each key exactly once; duplicate-key decoding machinery would guard manually corrupted data not produced by this system, with negligible practical harm.
  - `[low]` `[patch]` Blind: pairs module overview describes the old format — corrected the overview to name query, target, kind and relevant members.
  - `[low]` `[patch]` Blind: automation summary filename wrongly names epic 1 — renamed the new untracked artifact to `automation-summary-story-ticketscope--e2-s2.md` and corrected its result-file reference.
  - `[low]` `[reject]` Edge: repeated queries overwrite ranks — carried from the prior review, same claim and unchanged code; derivation guarantees unique query issues and pinned-file uniqueness was confirmed. No change or deferral.
  - `[low]` `[reject]` Edge: self-linked snapshot issue yields a pair that cannot round-trip — no self-links exist among the 32,153 pinned issues; the selected-target rule is AD-26 and remains unchanged. A new guard for hypothetical future malformed input is more than a direct correction and is not justified for this pinned corpus.
  - `[low]` `[reject]` Edge: malformed direct `Pair` can score self — production pairs are validated or derived, and real retrieval honors exclusion; reaching the claim requires two violated caller contracts. Additional guard complexity is unwarranted for this hypothetical misuse.
  - `[medium]` `[patch]` Verification: real PostgreSQL tie ordering has only SQL-text verification — same root cause as Blind's tie finding; executable kind test now checks actual selected numbers, not SQL spelling.
  - `[medium]` `[patch]` Verification: nonempty per-kind p95 values lack distinct assertions — same root cause as Blind's latency finding; scripted mixed-kind test now observes each kind and overall independently.
  - `[medium]` `[patch]` Intent: kind recomputation only checks aggregates from recorded ranks — added a second full-corpus read-only retrieval pass that computes each first-member rank without `score`, its rank helper or its tallies, then compares every query to the artifact.
  - `[medium]` `[patch]` Intent: repeatability coverage uses only a fake corpus — the new tied-cutoff database test and independent full-corpus second pass exercise the real adapter, with exact rank equality; timing is intentionally measured independently.
  - `[false]` `[reject]` Intent: oracle's “every metric” does not include latency — hand-computed ranking quality has a fixed oracle; elapsed latency has no fixed corpus oracle and is covered with a controlled clock and nearest-rank percentile tests. The combined tests observe every requested metric.
  - `[false]` `[reject]` Intent: wall clock can mean wider kind cost — `wall_seconds` has always enclosed scoring; existing workflow separately reports kind-up duration. Both costs remain available, so no required cost surface is lost.
  - `[medium]` `[patch]` Intent: real-corpus artifact evidence was prospective — local kind run and artifact/summary verification now run as part of this follow-up; evidence recorded under Auto Run Result. Hosted PR checks remain the orchestrator's next verification surface because this branch has no PR and this workflow does not push.
  - `[false]` `[reject]` Intent: strict format/empty-kind details go beyond ticket — these details support the required outputs and add no conflicting product behavior; baseline and README remain reserved for stories 3/4.

## Follow-up Implementation Notes

- Preserved the orchestrator-owned `status: built`; did not run `tickets.py mark` or edit a deferred-work ledger.
- All four thorough lenses ran. The environment permits three concurrent child agents, so the fourth launched after the first finished; no findings were triaged until all four completed.
- Patches add verification and correct documentation/artifact naming; scoring semantics and the independent oracle are unchanged.
- Added verification commands: `uv run pytest -m kind tests/eval --junitxml=reports/eval.xml` (including PostgreSQL ties and an independent second full-corpus retrieval pass), with `GITHUB_STEP_SUMMARY` set to a local evidence file; `EVAL_ENABLED=1 scripts/kind-up.sh` supplies the full-set eval Job.


## Auto Run Result

**Summary.** Thorough follow-up of the built cluster-scoring implementation. Added real PostgreSQL cutoff-tie coverage, distinct nonempty kind and mode latency/rank assertions, rank-domain checks, and independent full-corpus rank recomputation through the read-only adapter. Corrected the pairs-format overview and the preceding automation summary's epic identifier. Existing scoring behavior, the hand-computed oracle, ticket status and deferred-work ledgers are preserved.

**Files changed this pass.**
- `src/ticketscope/core/pairs.py` — correct the format overview.
- `tests/unit/test_eval_main.py` — independently observe per-kind latency and separate mode ranks/latencies.
- `tests/eval/test_postgres_ties.py` — execute the adapter query on 60 shuffled BM25 ties and require the same lowest ten numbers across three runs, inside a rolled-back isolated schema.
- `tests/eval/test_eval_kind.py` — validate persisted rank values and independently search every pair again without scorer helpers, comparing all first-member ranks.
- `tests/unit/test_eval_score_expanded.py` — include the preceding automation run's 15 expanded tests in verification and the reviewed change set.
- `_bmad-output/test-artifacts/automate/automation-summary-story-ticketscope--e2-s2.md`, `_bmad-output/initiative-ticketscope/bmad-build-auto-result-2.2-tea.automate-1.md` — preserve automation evidence with the correct epic filename/reference.
- This plan — record four-lens review, per-finding triage and verification evidence; status unchanged.

**Review.** 21 findings: 8 medium, 10 low, 3 false. Eight patch groups (4 medium, 4 low); 0 high; 0 deferred. Duplicate lens findings share their fix. Rejected findings and individual evidence are recorded in the thorough triage log above. No existing deferred-work entry was changed, reopened or resolved.

**Follow-up review recommended:** false (follow-up pass, no high patch group and no identified unverified repair risk).

**Verification evidence.**
- Targeted oracle/eval/pairs suite: 51 passed.
- Full default suite: 838 passed, 41 kind tests deselected.
- Ruff check and format, pyright, import-linter: clean, 7 contracts kept.
- Pair regeneration: byte-identical, 10,473 total / 10,164 short / 309 log-heavy. Oracle diff against `7ea485ac88979fe18a98500c36a4fb45a9cf79a4`: empty.
- Real PostgreSQL shuffled-tie regression: passed before full eval, issues 1–10 on all three searches.
- `EVAL_ENABLED=1 scripts/kind-up.sh`: retry succeeded in 209 seconds, API Ready in 207 seconds. First attempt was interrupted when CNPG rolled the newly tagged database image; after Cluster Ready, rerunning succeeded without a code change.
- Full-set keyword eval cost: **177.4 seconds**, versus story 2.1's recorded 116.7 seconds (about 1.52x; local runs are not a controlled benchmark), well within the existing 1,800-second Job deadline. BM25 index use and tie semantics remain as established by the original implementation experiment; no deadline or full-set decision change is needed.
- `reports/eval-results.json` SHA-256: `9812dfc1b45c96fd70b78624109dbb4f348cca4e301879398ec9448b71dd8bad`. All 10,473 query ranks recorded; lineage `2026.11.1` / null embedding model / `pre1.kind2-t3.outcome3`; no skipped modes. `/tmp/ticketscope-2-2-eval-summary.md` holds matching cost and per-kind metrics. Runtime reports remain local ignored artifacts, not a baseline update.
- Overall Recall@1 / Recall@5 / Recall@10 / MRR@10: 0.4442853050701805 / 0.6950253031605079 / 0.7706483338107515 / 0.5505022362871117. p95 short / log-heavy / overall: 17.559719 / 47.286743 / 18.483871 ms. Pair counts: 10,164 / 309 / 10,473.
- Eval kind suite: **9 passed in 167.88 seconds**, including exact equality of all 10,473 ranks from an independent second read-only retrieval pass and the real PostgreSQL cutoff test. Results and summary writing, counts, lineage and credential checks all passed.
- Integrated suite: 5 passed, including golden API/page results, trace to Tempo and backup to SeaweedFS. An initial invocation supplied the wrong local Host value and returned 404; rerun with chart hostname `ticketscope.kind.internal` passed.

- Full smoke suite: **27 passed in 784.92 seconds**, including forced reload, same-pin no-op, stale preprocessing recovery, backup TLS/credential preservation across upgrades, traces and timed loads. Because the local release retained `eval.enabled=true`, upgrade checks also reran the full eval hook.

**Residual scope.** Hosted PR checks and their uploaded artifacts remain the orchestrator's verification: this branch has no PR, and this run does not push. The local full eval artifact is available under `reports/`; it is not represented as hosted CI evidence. Ticket status remains orchestrator-owned.


### Additional diagnostic: pre-existing index versus controlled reload

- An extra post-smoke comparison against the first local eval found two changed first-member ranks: query 258858 (4 → 5) and 489515 (5 → 6). Initial overall Recall@5 was 0.6950253031605079 versus 0.6949298195359496 after reload; MRR@10 was 0.5505022362871117 versus 0.5504942793183984. The initial index predated this run; equivalence of its complete text/statistics state was not captured. The deployed prior revision was `6400e5ac8e3bb4cadeea8061a5581c33b2b45036`; load/derive code and migrations are unchanged from it.
- Repeated real searches on the current index returned identical numbers and scores for both queries. `REINDEX INDEX public.issue_search_bm25_idx` reduced the physical layout from two segments to one without changing either query's scores or ordering. This was a local diagnostic only, not a product/loader change.
- A subsequent **controlled same-snapshot forced reload**, through the unchanged loader and complete eval Job, produced **exactly the same 10,473 first-member ranks and every per-kind/overall quality metric** as the saved preceding fresh-load eval. Wall time was **173.5 seconds**. Complete controlled results are at `/tmp/ticketscope-2-2-controlled-eval.json`; execution evidence is `/tmp/ticketscope-2-2-controlled-reload.log`.
- `[maybe-false]` `[reject]` Cross-reload reproducibility defect — a historical-state comparison alone does not prove identical retrieval inputs/statistics. Repeated same-index retrieval, the independent complete second pass, real tied-cutoff testing and a controlled fresh-reload comparison all pass. If true, the tiny historical drift is low harm (well below the gate tolerance); adding lifecycle normalization without a reproducible defect is unwarranted. The original historical state is no longer available, so its cause remains unknown. No deferred-work entry was added or altered.
- Final verification totals: **838 default tests, 9 eval kind tests, 5 integrated checks, 27 smoke tests passed**; targeted oracle/eval/pairs suite 51 passed; lint, formatting, typing and seven import contracts clean. Controlled reload equality passed in addition. Hosted PR verification remains with the orchestrator; this run does not push or mark the ticket done.
