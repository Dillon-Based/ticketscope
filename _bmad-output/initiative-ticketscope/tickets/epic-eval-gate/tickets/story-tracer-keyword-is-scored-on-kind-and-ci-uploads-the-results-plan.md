---
title: 'Tracer: keyword is scored on kind and CI uploads the results'
type: 'feature'
ticket: '1'
created: '2026-11-08'
status: 'built'
baseline_revision: '42ac66fa2e2e165a6acf0ea4572d06088c696eab'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md'
  - '{project-root}/_bmad-output/test-artifacts/atdd/atdd-checklist-ticketscope--e2-s1.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** No retrieval score is produced by CI. Epic 2 needs a tracer from the pinned snapshot to a CI artifact before metrics, the gate, and the README table can build on it.

**Approach:** Derive AD-26 pairs in `core` and commit `eval/pairs/2026.11.1.jsonl`. Add `jobs.eval`, which scores every available registry mode with target-only Recall@10 and MRR@10 as `ticketscope_ro` and emits a results JSON with corpus lineage. Run it as a chart Job (behind `eval.enabled`) after load on kind, through a new `eval.yml` that uploads the results.

## Boundaries & Constraints

**Always:** one pair per duplicate issue whose `core.duplicate_target` is in the snapshot, under `derive_kind`; the pairs file is sorted by query, holds only `query`/`target`/`kind`, and regenerates byte-identical. Eval reads `REGISTRY` at call time, skips unavailable modes, searches with `k=10` and `exclude={query}`, and uses the query issue's title + description (no comments). Results carry `snapshot_version`, `embedding_model_id`, `preprocessing_version` from `corpus_meta`. The eval Job is rendered only when `eval.enabled`, uses the `ticketscope-db-ro` Secret only, and runs after load. `ci.yml`'s integrated-check call stays unchanged.

**Never:** edit `tests/eval_oracle.py` (or change what `tests/unit/test_eval_oracle.py` asserts); cluster relevance, R@1/R@5, p95, per-kind splits or skipped-mode lists (story 2.2); any gate or baseline (2.3); `time.sleep` in tests; changes to `PostgresCorpusStore`'s per-call connections.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Pair, normal | Duplicate issue, target in snapshot | One pair, target = `duplicate_target` | — |
| Target outside snapshot | Duplicate whose target is not loaded | No pair | — |
| Not a duplicate | `Fixed` issue carrying duplicate links | No pair | — |
| Two links | "duplicates" + "duplicated_by", or two "duplicates" | One pair: the "duplicates" target; the lowest number | — |
| Oracle | `tests/eval_oracle.py` fixture | R@10 3/5, MRR@10 43/150, pairs_scored 5 | — |
| Pairs file missing | No `eval/pairs/<corpus_meta version>.jsonl` | Job exits 1, logs the path | `run` returns 1 |
| No corpus loaded | `read_corpus_meta` returns None | Job exits 1 | `run` returns 1 |

</frozen-after-approval>

## Code Map

- `src/ticketscope/core/derive.py:194` `duplicate_target`, `:273` `derive_kind` (threshold 3) -- reuse; never re-implement (AD-26).
- `src/ticketscope/jobs/ingest/jira.py:317-343` `report()` -- the counting rule the pairs function must match.
- `src/ticketscope/jobs/load/main.py:39` `read_snapshot(path)` and `src/ticketscope/adapters/release.py:45` `fetch_snapshot(base_url, version, dest_dir, sha256, timeout=)` -- read and fetch the pinned asset; pin at `deploy/charts/ticketscope/values.yaml:27-30`, read in tests via `tests/target.py:37` `snapshot_pin()`; cache pattern `tests/smoke/test_time_load.py:45-55`.
- `src/ticketscope/adapters/postgres.py:72` `PostgresCorpusStore(conninfo)`, `:204` `read_corpus_meta(conninfo) -> CorpusMeta | None` -- the store and lineage; no adapter change.
- `src/ticketscope/settings.py` `Settings` (prefix `TICKETSCOPE_`, `conninfo()`) -- the role comes from injected `DB_USER`.
- `src/ticketscope/jobs/load/main.py:116-170` -- `main()`/`run(settings)` pattern: `telemetry.setup(SERVICE_JOBS, …)`, `job_span`, `log.exception`, return 1.
- `deploy/charts/ticketscope/templates/jobs.yaml:39-85` (load hook, weight "0") and `templates/api.yaml:30-44` (ro env inline) -- patterns for the eval Job.
- `scripts/kind-up.sh:114-119` -- the helm call (env-var driven, `--timeout 25m`, blocks on hooks).
- `.github/workflows/_kind-deploy.yml` (inputs `check`, `upgrade_check`; `if: always()` upload of `reports/`, L134-140) and `.github/workflows/ci.yml:68` (`charts` job's explicit test list), `:109-116` (integrated-check call).
- `images/app.Dockerfile` and `.dockerignore` (whitelist) -- must ship `eval/pairs/`.
- `tests/unit/test_chart_backup.py` (`_template`/`_render`/`_docs`, skipif no helm), `tests/unit/test_integrated_check_expanded.py:19,65-71` (workflow text asserts), `tests/smoke/test_gateway.py:85-131` (`_kubectl`, `_sql` via CNPG primary, Job log read) -- test patterns.
- `tests/unit/test_eval_oracle.py`, `tests/eval_oracle.py` -- red scaffold (seam: `ticketscope.jobs.eval.score(store, pairs)` → `results["modes"][name]` with `recall@10`, `mrr@10`, `pairs_scored`). Oracle file is read-only.

## Tasks & Acceptance

**Execution:**
- [x] `src/ticketscope/core/pairs.py` -- `Pair` (query, target, kind), `derive_pairs(issues) -> list[Pair]` sorted by query, `pairs_jsonl(pairs) -> bytes` (fixed key order, `\n`-terminated), `count_by_kind` -- pure, AD-26.
- [x] `scripts/derive_pairs.py` -- fetch the pinned asset (`fetch_snapshot`, pin from `values.yaml`), write `eval/pairs/<version>.jsonl`, print total/short/log-heavy; `--check` compares bytes with the committed file and exits 1 on difference.
- [x] `eval/pairs/2026.11.1.jsonl` -- generated by the script; counts 10,473 / 10,164 / 309.
- [x] `src/ticketscope/jobs/eval/{__init__,score,main}.py` -- `score(store, pairs)` (re-exported from `__init__`); `main()`/`run(settings)` reads `corpus_meta`, loads `<pairs_dir>/<snapshot_version>.jsonl`, scores, logs one `ticketscope-eval results: <json>` line with lineage, `pairs_file`, and `wall_seconds`.
- [x] `src/ticketscope/settings.py` -- `eval_pairs_dir: Path = Path("eval/pairs")`.
- [x] `pyproject.toml` -- `ticketscope-eval = "ticketscope.jobs.eval.main:main"`.
- [x] `images/app.Dockerfile`, `.dockerignore` -- copy `eval/pairs` to `/app/eval/pairs`.
- [x] `deploy/charts/ticketscope/templates/jobs.yaml`, `values.yaml` -- `eval.enabled: false`, `eval.activeDeadlineSeconds: 1800`; Job `ticketscope-eval` under `{{ if .Values.eval.enabled }}`, hook `post-install,post-upgrade` weight `"10"`, `before-hook-creation`, ro env, OTLP env, `command: ["ticketscope-eval"]`.
- [x] `scripts/kind-up.sh` -- `EVAL_ENABLED=1` adds `--set eval.enabled=true` and raises helm `--timeout` to 40m.
- [x] `.github/workflows/_kind-deploy.yml` -- input `eval_enabled` (boolean, default false) passed to kind-up as `EVAL_ENABLED`.
- [x] `.github/workflows/eval.yml` -- on `pull_request`; calls `_kind-deploy.yml` with `eval_enabled: true`, `check: uv run pytest -m kind tests/eval --junitxml=reports/eval.xml`.
- [x] `tests/eval/` -- kind tests: a session fixture reads the eval Job's log and writes `reports/eval-results.json` first; then: Job Complete, keyword `recall@10`/`mrr@10` present with `pairs_scored == 10473`; lineage equals `corpus_meta` via `_sql`; Job env uses `ticketscope-db-ro`; artifact has no Secret value; `derive_pairs.py --check` passes and prints the Release counts.
- [x] `tests/unit/` -- pair-rule matrix rows and `pairs_jsonl` format; `run()` with fake store/meta (missing pairs file, no corpus → 1; results line carries lineage); query text excludes comments; chart render (off by default, on → command, ro Secret only, weight > load, deadline set); workflow text (eval.yml on pull_request calls `_kind-deploy.yml`; new input has a default; `ci.yml` call unchanged; kind-up off by default). Add the chart test file to `ci.yml:68`.
- [x] `tests/unit/test_eval_oracle.py` -- remove only the skip block.

**Acceptance Criteria:**
- Given the oracle fixture, when the scaffold runs, then it passes, and `git diff b7be713 -- tests/eval_oracle.py` is empty.
- Given a PR, when `eval.yml` runs, then the eval Job completes after load as `ticketscope_ro`, and the `reports-kind` artifact holds `eval-results.json` with keyword's Recall@10 and MRR@10 over 10,473 pairs and lineage equal to `corpus_meta`.
- Given a step after the results are written fails, when the workflow ends, then the artifact is still uploaded.
- Given the same PR, when `ci.yml` runs, then integrated-check passes.
- Given the pinned snapshot, when the pairs are regenerated, then the file is byte-identical and the printed counts are 10,473 / 10,164 / 309.

## Implementation Notes

- **Seam as built:** `ticketscope.jobs.eval.score(store, pairs)` accepts `Pair`s or parsed pair mappings and returns `{"k": 10, "relevance": "target", "modes": {name: {"recall@10", "mrr@10", "pairs_scored"}}}`. The oracle scaffold is used unchanged (only its skip block removed). The query issue's text is fetched once per pair and searched once per available mode. A query issue missing from the corpus raises, and `run` returns 1, so it never scores as a silent zero.
- **Results line:** `run` adds `lineage` (`snapshot_version`, `embedding_model_id`, `preprocessing_version`), `pairs_file` and `wall_seconds`. The kind conftest parses it from the JSON log (`results_from_log`; the format is unit-tested through `telemetry.JsonFormatter`).
- **Eval Job:** `backoffLimit: 0`, because the run is deterministic. A failed Job fails the helm hook, so kind-up fails before the check, and no `eval-results.json` exists for that run (Diagnostics still dumps the pod log).
- **derive_pairs.py:** caches the asset in `--snapshot-dir` (default `snapshots/`, now gitignored). It carries its own copy of the values.yaml pin parser, because scripts do not import `tests/`.
- **Local evidence (not CI):** the pinned asset loaded into the in-repo Postgres image; `ticketscope-eval` as `ticketscope_ro` exited 0 with keyword R@10 0.1753, MRR@10 0.0854, 10,473 pairs, and wall_seconds 116.7 on a dev Mac (R-006 input). `derive_pairs.py --check` with `PYTHONHASHSEED=4242` was byte-identical: 10473 / 10164 / 309.

## Plan Change Log

## Review Triage Log

**Pass 1 (quick lens).** Counts: high 0, medium 1, low 4, false 2, maybe-false 1. One finding rejected because its fix edits the plan.

| # | Finding | Verdict | Route | Evidence |
|---|---------|---------|-------|----------|
| 1 | `_kind-deploy.yml` 45-min job limit can cut the eval hook off (Helm allows 40m, the Job's deadline is 30m); a cancelled job skips Diagnostics | maybe-false (medium if true) | defer | Depends on the eval run time on a GitHub runner, which is UNKNOWN (R-006; 117 s locally). The first `eval.yml` run's `wall_seconds` and job duration settle it. |
| 2 | Runner-fit "kind-up start to api Ready" includes the whole eval when `eval_enabled` | low | patch | Confirmed: `kind-up.sh` takes `READY_EPOCH` after `helm upgrade`, which blocks on the weight-10 hook. Every `eval.yml` summary would mislabel the number. The fix is one summary line when `inputs.eval_enabled`. |
| 3 | About 21,000 eval connections each emit psycopg spans into one job trace | medium | patch | Confirmed: `telemetry.setup` instruments psycopg (`telemetry.py:66-83`), and `main.run` scores without `telemetry.untraced()` (`telemetry.py:154`). Spans overflow the batch queue and add export cost to a timed run. The fix is to wrap the `score` call in `untraced()`; `job_span` stays. |
| 4 | AC "artifact uploaded even when a later step fails" has no execution evidence | low | reject | The fix is to add the forced-failure run to this plan's Verification. It is carried as a manual CI check in step 5 instead. |
| 5a | No Postgres-container integration test of the `ticketscope_ro` reads | low | reject | Every `eval.yml` run covers it on kind (the Job succeeds with the ro Secret only; `test_eval_job_reads_as_ticketscope_ro`). The repo has no Postgres-container unit tier, so the fix adds new infrastructure. |
| 5b | Byte-identity is not tested under a different `PYTHONHASHSEED` | false | reject | Output order comes from `sorted()` over an ordered dataclass, and the JSON key order is fixed. The only set is used for membership tests, so the hash seed cannot change any bytes. |
| 5c | The kind tests read the Job status once instead of `kubectl wait` | false | reject | `kind-up` returns only after Helm's blocking post-install hooks have completed (a failed hook fails `helm upgrade`), so the Job is already Complete when the tests run. |
| 6 | The autouse `eval_results` fixture makes the regeneration test error when the results line is missing | low | patch | Confirmed (`tests/eval/conftest.py`). The fix is direct: drop `autouse` and have the tests that read the results request the fixture. The results file is still written before the first test that reads it. |
| 7 | `scripts/derive_pairs.py` duplicates `tests/target.py`'s pin parser | low | reject | Drift is unlikely and both copies fail loudly on a malformed pin; merging them is a refactor. Left for story 2.5's sweep, which is scoped from this epic's review findings. |

## Design Notes

- **Hook, not workflow-started:** Helm blocks on post-install hooks, so a weight-10 hook runs after load (weight 0) inside kind-up with no extra orchestration. Only `eval.yml`'s cluster sets `eval.enabled`, so ci.yml's smoke upgrade never reruns it.
- **Results via the Job log:** the pod's filesystem is gone after completion; one prefixed log line is read with `kubectl logs` (as `_load_log` does) and written to `reports/` before any assertion, so the always() upload carries it.
- **Pairs chosen by `corpus_meta`'s version:** eval scores the loaded snapshot's own pairs file, so lineage and ground truth cannot disagree.
- **Regeneration runs in `eval.yml`** (test design's contingency): it needs the Release asset, and the kind check already depends on it; `checks` stays offline.
- **Time budget is UNKNOWN** (R-006): about 21,000 short connections. `wall_seconds` is recorded for story 2.2.

## Verification

**Commands:**
- `uv run pytest tests/unit/test_eval_oracle.py` -- expected: passes (red scaffold green).
- `uv run pytest tests/unit` -- expected: all pass (helm-gated tests may skip without helm).
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports` -- expected: clean, 7+ contracts kept.
- `uv run python scripts/derive_pairs.py --check` -- expected: exit 0, prints `10473 pairs: 10164 short, 309 log_heavy`.
- `git diff b7be713 -- tests/eval_oracle.py` -- expected: empty.

**Manual checks (if no CLI):**
- PR run of `eval.yml`: Job Complete, `reports-kind` artifact holds `eval-results.json`; `ci.yml` integrated-check green on the same head.
