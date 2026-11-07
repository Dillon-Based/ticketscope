---
title: 'Integrated check on kind'
type: 'feature'
ticket: '11'
created: '2026-11-07'
status: done
baseline_revision: '9b291e39239a90c08f649b0c40a812bf55f20d58'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** The epic's Done when is checked piecemeal by the smoke suite, and nothing gates on relevance: no kind check asserts that each golden query's expected issue comes back (test design R-004), nor that the loaded corpus is the pinned asset validated against the committed schema v2. There is no single CI job named for the epic's integrated check.

**Approach:** Add `tests/integrated/test_done_when.py` (marker `kind`) with exactly five checks, in order: (1) schema — the pinned asset validates against `snapshot/schema-v2.json` and the loaded corpus is that asset; (2) kind/outcome — every loaded issue has a valid kind and outcome; (3) `/v1` and page — each golden query returns its expected issue in the top-k with outcomes, through `/v1/search` and the page, a recorded known keyword miss reported but not gated; (4) trace — one search reaches Tempo in the AD-10 tree; (5) backup — an on-demand backup completes to SeaweedFS. Rename ci.yml's `kind-deploy` job to `integrated-check`; its `_kind-deploy` check runs the integrated suite first, then the smoke suite, on the same cluster.

## Boundaries & Constraints

**Always:** One kind cluster per PR (no second `_kind-deploy` job). Read k, mode, pin and entries from `eval/golden-queries.json`; never hard-code query text or issue numbers. Each check is one test function, so a broken check fails exactly that test. The known-miss verdict is a pure function, unit-tested in the default (non-`kind`) pytest run. Report golden results (rank or "absent") in the pytest output and, when `GITHUB_STEP_SUMMARY` is set, as a table appended to it. Keep ruff, pyright, import-linter and pytest green.

**Never:** No sabotage knobs or env switches in test or product code to break a check; breaking on purpose is done by hand during verification. Do not change `src/`, the charts, `_kind-deploy.yml`, `kind-up.sh`, `eval/golden-queries.json` or the `/v1` contract. Do not weaken or drop existing smoke tests. Do not edit ticket files or the spine.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Twin found | entry `known_keyword_miss: false`, expected number in top-k | verdict `pass`, rank reported | No error expected |
| Twin absent, gated | `known_keyword_miss: false`, expected number absent | verdict `fail` | test fails naming the entry id and the returned numbers |
| Known miss, still absent | `known_keyword_miss: true`, absent | verdict `known-miss`, reported, not gated | warning, test passes |
| Known miss now found | `known_keyword_miss: true`, present | verdict `pass` with a "known miss now found" note | reported, test passes |
| Result without outcome | any result with empty/unknown-to-contract outcome status | check (3) fails | assertion names the issue |
| Page lacks twin | `/v1` has the twin, page rows have no href ending in the expected key | check (3) fails (gated entries only) | assertion names the entry id |

</intent-contract>

## Code Map

- `tests/smoke/test_gateway.py` -- source of the cluster helpers: `_gateway`, `_post_search`/`_search`, `_sql`, `_corpus_meta`, `_page` + `_Rows` (page rows carry `href`, `rank`, `data-outcome`), `_secret_data`, backup (`_backup_status`, `_bucket_listing`, body of `test_on_demand_backup_completes_to_seaweedfs` line ~468), trace (`_search_with_traceparent`, `_poll_trace`, `_tempo`, `_assert_ad10_tree`), constants `OUTCOMES`, `PIN`, `GOLDEN`, `CLUSTER`, `NAMESPACE`. Extract the backup test body into `_assert_on_demand_backup_completes()` that the smoke test calls; otherwise leave smoke behaviour unchanged. The integrated module imports these underscore helpers (pytest collects only `test_*`, so never import a `test_*` name into the new module).
- `tests/target.py` -- `REPO`, `snapshot_pin()` (version, sha256, baseUrl).
- `src/ticketscope/adapters/release.py:45` -- `fetch_snapshot(base_url, version, dest_dir, sha256, *, timeout)`, checksum-verified download; reuse for check (1). `tests/unit/test_golden_queries.py` shows the pattern.
- `tests/unit/test_snapshot.py` -- `Draft202012Validator` usage against `snapshot/schema-v2.json` (jsonschema is in the dev group that `uv sync --locked` installs).
- Issue table: columns `number`, `kind`, `outcome_status`; `corpus_meta.snapshot_version`. Kinds are `short`/`log_heavy`.
- `tests/integrated/__init__.py`, `tests/integrated/golden.py` (new) -- pure `twin_verdict(known_keyword_miss: bool, expected: int, ranked: list[int]) -> Verdict` (status `pass`/`fail`/`known-miss`, rank or None, note) and a summary-table formatter.
- `tests/integrated/test_done_when.py` (new) -- the five checks, module docstring mapping each to the epic Done when and stories (13, 5 / 5 / 5, 6, 7 / 9 / 8).
- `tests/unit/test_integrated_golden.py` (new) -- unit tests for every matrix verdict row and the table.
- `.github/workflows/ci.yml` -- job `kind-deploy` (last job) → `integrated-check`, check `uv run pytest -m kind tests/integrated tests/smoke`; update the header comment. No branch protection names the old job.

## Tasks & Acceptance

**Execution:**
- [x] `tests/integrated/golden.py` -- verdict and report helpers -- the known-miss rule is testable without a cluster
- [x] `tests/unit/test_integrated_golden.py` -- cover every I/O-matrix verdict row and the summary table -- edge cases
- [x] `tests/smoke/test_gateway.py` -- extract `_assert_on_demand_backup_completes()`; smoke (7) calls it -- shared by check (5)
- [x] `tests/integrated/__init__.py`, `tests/integrated/test_done_when.py` -- the five checks -- Done when together
- [x] `.github/workflows/ci.yml` -- rename the kind job to `integrated-check` and run integrated then smoke -- one job on every PR

**Acceptance Criteria:**
- Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank. (R1, R2, R3, R4, R5, R6, R7)
- Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again. (R1, R2, R3, R4, R5, R6, R7)
- Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass. (R7)

## Design Notes

Integrated runs before smoke so its verdict is on the freshly deployed state, before smoke's upgrades and forced reloads. Check (1) is "the loaded snapshot is the pinned asset": every asset line validates against the committed schema, `corpus_meta.snapshot_version` equals the pin, and the loaded issue numbers equal the asset's, compared cheaply as count plus `md5(string_agg(number::text, ',' ORDER BY number))` against the same digest computed locally. Page check matches the expected issue by its key at the end of a row's `href` (`…/browse/MCD-6467`); confirm the page's k equals the file's k, else assert against the page's own row count.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `TICKETSCOPE_GATEWAY_URL=… TICKETSCOPE_GATEWAY_HOST=… uv run pytest -m kind tests/integrated -v` on the local kind cluster (values from `scripts/kind-up.sh` output, or its port-forward) -- expected: 5 passed
- `uv run pytest -m kind tests/smoke` on the same cluster -- expected: all pass (backup extraction kept smoke green)
- `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"` or `uv run python` equivalent -- expected: parses; job `integrated-check` present

**Manual checks:**
- Each of the five break-on-purpose runs fails only its own check; record the break used and the failing test in Implementation Notes.

## Implementation Notes

- `tests/integrated/golden.py` also holds two small pure helpers, `results_without_outcome` and `page_rank`, so the matrix's "result without outcome" and "page lacks twin" rows are unit-tested too. The verdict table reports the `/v1` verdict; a page miss is a separate failure line naming the entry id.
- Check (1) keeps the checksum-verified asset in pytest's cache (`.pytest_cache/d/ticketscope-snapshot`), so local reruns skip the download; CI downloads it once per run.
- The backup helper takes a name label (`smoke` default, `integrated` for check 5) so the two Backup objects never share a name.
- Local kind run (Gateway port-forward `http://127.0.0.1:18080`): `pytest -m kind tests/integrated -v` 5 passed (vague rank 5, log-heavy rank 9); `pytest -m kind tests/integrated tests/smoke` 27 passed.
- Break-on-purpose runs (each reverted, suite green again afterwards):
  1. Schema: added a required `integrated_break` property to `snapshot/schema-v2.json` -> only `test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2` failed (line 1, issue 11313).
  2. Kind/outcome: dropped `issue_kind_check` and NOT NULL, `UPDATE issue SET kind = NULL WHERE number = 11313` -> only `test_every_loaded_issue_has_a_valid_kind_and_outcome` failed (`11313 NULL fixed`); value, NOT NULL and constraint restored.
  3. `/v1` and page: in `eval/golden-queries.json` set vague's expected number to 1 and log-heavy's expected key to `MCL-999999` -> only `test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page` failed, naming both entries (absent from `/v1` with returned numbers; page lacking the key). Marking both entries `known_keyword_miss: true` passed with a warning and a "known miss now found" note; the `GITHUB_STEP_SUMMARY` table was written. File restored with `git checkout`.
  4. Trace: `kubectl -n platform scale statefulset tempo --replicas=0` -> only `test_one_search_reaches_tempo_as_the_ad10_tree` failed (no endpoints for service tempo); scaled back to 1.
  5. Backup: patched ObjectStore `ticketscope-backup` to `s3://ticketscope-missing-bucket/` -> only `test_an_on_demand_backup_completes_to_seaweedfs` failed (SeaweedFS auto-creates the bucket, so the Backup completes, but its base backup is absent from `ticketscope-backups`: listing 404). Path restored, the stray Backup object and bucket deleted.

## Plan Change Log

## Review Triage Log

### 2026-11-07 — Review pass
- verdicts: 3 findings — high 0, medium 1, low 2, false 0, maybe-false 0
- findings:
  - `[medium]` `[patch]` Check (3) skipped the page twin check when the twin's `/v1` rank exceeded the page's row count, so a gated twin missing from a shorter page passed silently. — Patched: for a gated entry whose twin `/v1` found, the twin must be on the page regardless of row count (page `PAGE_K` and the file's k are both 10 today, so a divergence now fails loudly).
  - `[low]` `[patch]` The golden table was reported only after the loop, so any in-loop assert lost the whole report and the CI summary. — Patched: the loop runs in `try`, and `finally` reports the rows collected so far; `assert not failures` still follows.
  - `[low]` `[reject]` A `known_keyword_miss: true` entry whose query returns zero page rows would fail on `assert page.rows`. — Rejected: real but unlikely (no known misses are recorded, and a full ticket text returning zero BM25 hits is implausible), and the fix adds a branch; the requirement that results carry outcomes still applies to every entry.

## Auto Run Result

Status: built

**Summary.** The epic's integrated check. `tests/integrated/test_done_when.py` holds exactly five `kind` checks, one test each: (1) the pinned asset validates against the committed `snapshot/schema-v2.json` and the loaded corpus is that asset (version, count and an md5 over the sorted issue numbers); (2) every loaded issue has a valid kind and outcome; (3) each golden query returns its expected issue in the top-k with outcomes through `/v1/search` and the page, a recorded known keyword miss reported but not gated, with a verdict table in the pytest output and the GitHub job summary; (4) one search reaches Tempo as the AD-10 tree; (5) an on-demand backup completes to SeaweedFS. ci.yml's kind job is renamed `integrated-check` and runs the integrated suite, then smoke, on one cluster.

**Files changed.**
- `.github/workflows/ci.yml`: `kind-deploy` → `integrated-check`; check runs `tests/integrated` then `tests/smoke`.
- `tests/integrated/__init__.py`, `tests/integrated/golden.py`: pure verdict (`twin_verdict`), outcome and page-row helpers, and the summary table.
- `tests/integrated/test_done_when.py`: the five checks.
- `tests/smoke/test_gateway.py`: backup body extracted to `_assert_on_demand_backup_completes(label)`, shared with check (5).
- `tests/unit/test_integrated_golden.py`: unit tests for every I/O-matrix row and the table.

**Review.** Quick lens, one pass, three findings: one medium and one low patched, one low rejected (reason in the triage log). Nothing deferred. Patched by verdict: high 0, medium 1, low 1.

**Follow-up review recommended:** false. No high was patched, and fewer than two mediums.

**Verification.**
- ruff check and format: pass. pyright: 0 errors. lint-imports: 7 contracts kept. pytest: 699 passed, 27 deselected, 1 xfailed.
- Local kind cluster, after the patches: `pytest -m kind tests/integrated tests/smoke` — 27 passed (integrated 5/5; vague twin rank 5, log-heavy twin rank 9).
- Break-on-purpose: each of the five checks broken by hand, one at a time, failed only its own test, and the suite was green again after each revert (see Implementation Notes). The cluster's constraints, Tempo and ObjectStore path were confirmed restored.
- Matrix audit: every I/O-matrix row is covered by a unit test in `tests/unit/test_integrated_golden.py`, run in the default pytest run.

**Residual risks.**
- "Passes on a PR" is shown on the local kind cluster with the exact CI check command; the GitHub-hosted `integrated-check` run happens when this branch is pushed and a PR opens (not done here: no push).
- Check (1) downloads the pinned asset from GitHub Releases in CI (timeout 300 s), adding network dependence and some minutes to the kind job; backup and trace now run twice per job (integrated and smoke).
- The page-twin break after the patch was not re-run on purpose; the unit test for `page_rank` and the earlier break run (3) cover it.
