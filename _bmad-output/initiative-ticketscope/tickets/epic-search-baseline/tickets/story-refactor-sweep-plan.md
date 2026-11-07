---
title: 'Refactor sweep'
type: 'refactor'
ticket: '10'
created: '2026-11-07'
status: done
baseline_revision: '93c43443de12bc3d2ca6f94370019a57309f6db7'
route: 'full'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** The epic left cleanup behind. Core still carries the retired GitHub (schema v1) snapshot shapes and outcome rules, which no snapshot feeds any more. Smoke test (3) fails when it runs right after an in-place `kind-up.sh` upgrade (ledger DW-2). The deferred-work ledger still lists two items that later stories settled: the missing `Chart.lock` and DW-1.

**Approach:** Delete the v1 shapes and GitHub rules, and move their kind tests onto v2 issues. Make smoke (3) force a reload when the newest load was a no-op. Make `kind-up.sh` roll the api pods when it rebuilt the image under an unchanged tag. Drop the dead "no Chart.lock" fallback from CI and `kind-up.sh`. Close the settled ledger entries. `/v1` responses do not change.

## Boundaries & Constraints

**Always:** Leave `derivation_version()` and `preprocessing_version()` unchanged (`pre1.kind2-t3.outcome3`), so a deploy does not reload. Keep every v2 rule and its tests. Keep the dict-literal `V1_LINE` tests in `tests/unit/test_snapshot.py`; they prove that v1 lines are refused. Keep ruff, pyright, import-linter and pytest green.

**Never:** Do not change the `issue.state_reason` column, the migration, `IssueRow`, the `/v1` contract or the chart values. Do not fix ingest provenance (the OS user-folder paths that story 1.5 found); that is new scope, so it becomes a new story. Do not edit ticket files or the architecture spine.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Golden queries | `eval/golden-queries.json` queries posted to `/v1/search` keyword on kind, before and after | Identical `results` (number, rank, score, outcome) and `corpus_version` | No error expected |
| Smoke (3) after an in-place upgrade | Newest Succeeded load pod logged `no-op` with no report line | Test forces a reload (stale `preprocessing_version` + `_upgrade()`), then checks the fresh report, and `corpus_meta` ends current | Assertion failure if still no report |
| Smoke (3) on a fresh deploy | Newest load logged a report | Checks it without reloading | — |
| `kind-up.sh` re-run with FORCE_BUILD=1, release exists | Same HEAD tag, image rebuilt | `rollout restart deploy/ticketscope-api` before `rollout status` | — |
| `kind-up.sh` on a fresh cluster or with no rebuild | — | No restart | — |

</intent-contract>

## Code Map

- `src/ticketscope/core/snapshot.py` -- delete `SCHEMA_VERSION`, `Label`, `Comment`, `TimelineEvent`, `SnapshotIssue`, and the v1 parts of the module docstring. Keep `_Frozen`, `JiraComment`, `DuplicateLink` and `SnapshotIssueV2`. `jobs/ingest/main.py` defines its own `SCHEMA_VERSION = 2`.
- `src/ticketscope/core/derive.py` -- delete the GitHub constants (`DUPLICATE_LABEL`, `STALE_LABELS`, `SUPPORT_LABEL`, `MAINTAINER_ASSOCIATIONS`, `_PR_EVENTS`), `_github_outcome`, `_event_key`, `_duplicate`, `_fixed`, `_not_planned`, `_stale`, `_comment_key` and `_answered`. `derive_outcome` and `derive_kind` take only `SnapshotIssueV2`. `derive_kind` always applies `jira_to_fences`, and the module docstring drops the v1 wording. Keep the rule-version constants unchanged.
- `tests/unit/test_derive.py` -- delete the GitHub outcome and determinism tests and the v1 factories. Keep the kind and derivation-version tests, building issues as v2 (copy `make_jira_issue` from `tests/unit/test_derive_jira_expanded.py:71`, or import it). Note that `{code}` now converts for every issue, but the kind tests use backtick fences and log lines, so their expectations hold.
- `tests/unit/test_derive_jira_expanded.py` -- delete `make_github_issue`, the `SnapshotIssue` import and `test_v1_issue_keeps_github_rules`. Change `test_v1_body_jira_toggles_are_not_fences` so it asserts only the v2 case, or delete it if `test_toggles_*` already covers it.
- `tests/smoke/test_gateway.py` -- (3) `test_load_log_has_the_report` at line ~321. Reuse `_sql`, `_upgrade`, `_corpus_meta`, `_load_log` and the stale-version trick from (5) at line ~348, ideally through a small shared `_force_reload()` helper that both use. Update the module docstring if it changes.
- `scripts/kind-up.sh` -- `build()` at line ~51 records whether it built the app image. Before step 6, note whether the `ticketscope` release exists (`helm --kube-context "$KCTX" status ticketscope -n "$APP_NS"`). After `helm upgrade`, when both hold, run `k -n "$APP_NS" rollout restart deploy/ticketscope-api` before the existing `rollout status`. Also drop the `Chart.lock`-missing branch: run `helm dependency build` only.
- `.github/workflows/ci.yml` -- `charts` job, about lines 51-56: drop the missing-lock warning branch and run `helm dependency build` only.
- `_bmad-output/initiative-ticketscope/deferred-work.md` -- the Chart.lock entry: committed in cdffdfe (story 1.9), so remove it or mark it resolved. DW-1: `status: resolved`, because ingest keeps only Duplicate-mapped links (`jobs/ingest/jira.py` `is_duplicate_linktype`). DW-2: `status: resolved` by this story.

## Tasks & Acceptance

**Execution:**
- [x] `src/ticketscope/core/snapshot.py`, `src/ticketscope/core/derive.py` -- retire the v1 shapes and GitHub rules -- the epic allows the sweep to retire them, and no snapshot feeds them
- [x] `tests/unit/test_derive.py`, `tests/unit/test_derive_jira_expanded.py` -- drop the GitHub tests, and port the kind and version tests to v2 -- keep the kind rule covered
- [x] `tests/smoke/test_gateway.py` -- make (3) reload when the newest load was a no-op -- DW-2
- [x] `scripts/kind-up.sh` -- restart api after a rebuild under an existing release; build dependencies from the lock only -- DW-2 and the Chart.lock entry
- [x] `.github/workflows/ci.yml` -- build dependencies from the lock only -- dead branch
- [x] `_bmad-output/initiative-ticketscope/deferred-work.md` -- close the Chart.lock entry, DW-1 and DW-2 -- ledger hygiene

**Acceptance Criteria:**
- Given the change, when `grep -rnE "SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS" src tests` runs, then it finds nothing.
- Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.
- Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.
- Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.

## Implementation Notes

- Implemented by the full-route subagent, as the plan describes. Ledger entries are closed with `status: done 2026-11-07` plus a `resolution:` line, not with `resolved`. The ledger format (`.claude/skills/bmad-loop-sweep/deferred-work-format.md`) accepts only `open` or `done <date>`.
- `spike-choose-the-jira-corpus-findings/convert.py` and `test_spike.py` still import the removed `SnapshotIssue`. They are frozen spike evidence, outside pytest's paths and the lint and type checks, and the plan forbids editing ticket files, so they were left as they are.
- The kind baseline had to be redeployed first, because the cluster ran story 1.8's image. The first baseline `kind-up.sh` timed out waiting for the Gateway to report Programmed: Envoy was healthy, but Envoy Gateway's status was stale. Restarting `deploy/envoy-gateway` in `platform` cleared it. This is environmental and predates this change; it was not fixed here.
- I/O matrix coverage: the golden-query rows were checked by diffing captured `/v1/search` responses on kind (identical). The two smoke (3) rows are covered by the smoke test itself, which passed on the first run after an in-place upgrade. The `kind-up.sh` rows were checked from the run log ("restarting api" on the same-tag rebuild); a fresh cluster and a new tag skip the restart by construction.

## Plan Change Log

## Review Triage Log

### 2026-11-07 — Review pass
- verdicts: 1 findings — high 0, medium 0, low 1, false 0, maybe-false 0
- findings:
  - `[low]` `[patch]` `scripts/kind-up.sh` restarted api after any app-image build under an existing release, so an in-place re-run on a new commit rolled api twice: once from Helm's tag change, then again from the redundant restart. — Patched: the script reads the deployed api image before the upgrade, and restarts only when the image was rebuilt and the deployed image equals `ticketscope-app:${TAG}`. Re-verified on kind: the restart fired on a same-tag `FORCE_BUILD=1` run.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `uv run python -c "from ticketscope.core.derive import preprocessing_version as p; assert p()=='pre1.kind2-t3.outcome3', p()"` -- expected: exit 0
- `helm lint deploy/charts/platform -f deploy/charts/platform/values-kind.yaml` after `helm dependency build deploy/charts/platform` -- expected: pass
- `bash -n scripts/kind-up.sh` -- expected: exit 0
- On kind: capture the golden-query responses on the baseline deploy, commit, run `FORCE_BUILD=1 scripts/kind-up.sh`, capture them again, and diff -- expected: identical. Then run `uv run pytest -m kind tests/smoke` once -- expected: all pass, (3) included.

## Auto Run Result

Status: built

**Summary.** The cleanup the epic deferred. Core no longer carries the GitHub (schema v1) snapshot shapes and outcome rules; the epic allowed the sweep to retire them, and no snapshot feeds them. Derivation and preprocessing versions are unchanged (`pre1.kind2-t3.outcome3`), so no reload happens and `/v1` responses do not change. Smoke (3) forces a reload when the newest load was a no-op (DW-2). `kind-up.sh` restarts api when it rebuilds the image under the deployed tag. The dead missing-`Chart.lock` fallback is gone from CI and `kind-up.sh`, and the ledger closes the Chart.lock entry, DW-1 and DW-2.

**Files changed.**
- `src/ticketscope/core/snapshot.py`: removed `SCHEMA_VERSION`, `Label`, `Comment`, `TimelineEvent` and `SnapshotIssue`.
- `src/ticketscope/core/derive.py`: removed the GitHub rules and constants; `derive_outcome` and `derive_kind` now take only v2 issues.
- `tests/unit/test_derive.py`: removed the GitHub outcome tests; the kind and version tests now use v2 issues.
- `tests/unit/test_derive_jira_expanded.py`: removed the v1 factory and the dispatch test; the toggle test now checks only the v2 case.
- `tests/smoke/test_gateway.py`: added a shared `_force_reload()`; (3) reloads after a no-op load, and (5) uses the helper.
- `scripts/kind-up.sh`: api restarts after a rebuild under the deployed tag; dependencies build only from the lock.
- `.github/workflows/ci.yml`: dependencies build only from the lock.
- `_bmad-output/initiative-ticketscope/deferred-work.md`: removed the Chart.lock entry; closed DW-1 and DW-2.

**Review.** Quick lens, one pass, one finding: a low, patched (the redundant api restart on a new tag). Nothing was deferred or rejected. Patched by verdict: high 0, medium 0, low 1.

**Follow-up review recommended:** false. No high was patched, and fewer than two mediums.

**Verification.**
- ruff check and format: pass. pyright: 0 errors. lint-imports: 7 contracts kept. pytest: 656 passed, 1 xfailed.
- `preprocessing_version()` returns `pre1.kind2-t3.outcome3`. The AC grep finds nothing. `bash -n scripts/kind-up.sh` passes. Platform `helm lint` passes after `helm dependency build` (subagent run).
- On kind (colima), the golden-query `/v1/search` responses were captured on the baseline deploy (93c4344) and after `FORCE_BUILD=1 scripts/kind-up.sh` with the change, twice: before and after the review patch. Each time they were byte-identical (ranks, scores, outcomes and `corpus_version`); the twins sit at ranks 5 and 9 as recorded.
- After the patched in-place upgrade, `uv run pytest -m kind tests/smoke` passed 22/22 on the first run, (3) included.

**Residual risks.**
- The ticket's verify line asks for `ci.yml` and `_kind-deploy` to pass on the sweep PR. That needs the commit pushed and a PR opened, which this run does not do; the orchestrator owns it. Local kind and unit checks stand in for it here.
- The frozen spike scripts in `spike-choose-the-jira-corpus-findings/` import the removed `SnapshotIssue` and would fail if run.
- Out of scope, and it should become a new story: 1,188 issues in snapshot 2026.11.1 hold OS user-folder paths that often contain real names (found in story 1.5). This needs an ingest fix and a republish.
