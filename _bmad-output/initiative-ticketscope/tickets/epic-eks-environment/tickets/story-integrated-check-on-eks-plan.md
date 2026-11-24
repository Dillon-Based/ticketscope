---
title: 'Integrated check on EKS (env-check.yml)'
type: 'feature'
ticket: '11'
created: '2026-11-24'
status: done
baseline_revision: 'fe5a8eebdd56a8e32ebb32663f1e745b11e2c860'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
operator_actions:
  - Merge the story-5-11 pull request so env-check.yml is on main (gh workflow run needs the workflow on the default branch).
  - In the lighter month, dispatch it from a ref the eks environment admits with `gh workflow run env-check.yml --ref main`, with no other environment running, and read each of its three runs with scripts/run-summary.sh.
  - Fill the Runs table in docs/drills/env-check.md from that run (env-check, env-up time, env-down, leftover check) and commit it.
  - Add to the epic's Notes the env-check run URL as the CI evidence, links to the restore, failure and recreate drill records, and the month's billing figure, raw from Cost Explorer (AWS only) and amortised (plus the domain's annual fee from the Cloudflare invoice divided by 12), under $10 (R5).
  - Run scripts/failure-drill.sh in the December window and commit docs/drills/failure-drill.md (R10 is unproven until then), then close the epic once every Done when line has a story's evidence.
---

<intent-contract>

## Intent

**Problem:** The epic's Done when asks for an integrated check on the cluster: a dispatched run of `env-up`, its smoke check, `env-down` and the leftover check that ends clean. No workflow runs them in sequence on one SHA, and there is no results record.

**Approach:** Add `env-check.yml`, which dispatches the existing `env-up` and `env-down` with `gh`, waits for each, runs a final leftover check, and is green only when all pass and `env-up`'s recorded time is under 30 minutes. Add a results-record skeleton. The live dispatch, the epic's Notes and the billing figure are done after merge.

## Boundaries & Constraints

**Always:** No AWS credential in the workflow; only the final read-only job assumes the deploy role through OIDC. `env-down` runs whenever `env-up` was dispatched. Every `run` step is `bash -eo pipefail`.

**Never:** Edit `env-up.yml`, `env-down.yml` or any ticket file. Hand-write a run URL, a time or a billing figure into the record.

</intent-contract>

## Code Map

- `.github/workflows/env-check.yml` -- new; jobs up, down, leftover, verdict
- `scripts/dispatch-and-watch.sh` -- new; dispatch a workflow, find its run, `gh run watch --exit-status`
- `tests/unit/test_env_check_workflow.py` -- new; wiring tests, tagged `ticketscope--e5-s11--AC-n`
- `docs/drills/env-check.md` -- new; record skeleton ("not run yet"), filled from the live run
- `.github/workflows/env-up.yml`, `env-down.yml` -- reused unchanged; `env-up-stages` artifact carries `verdict` and `total_seconds`

## Tasks & Acceptance

**Execution:**
- [x] `.github/workflows/env-check.yml` -- dispatch-only orchestrator -- the integrated check
- [x] `scripts/dispatch-and-watch.sh` -- shared dispatch and wait -- keeps the workflow's shell short and shellchecked
- [x] `tests/unit/test_env_check_workflow.py` -- wiring tests -- no live run is possible before merge
- [x] `docs/drills/env-check.md` -- results record skeleton -- filled by the post-merge run

**Acceptance Criteria:**
- Given `env-check.yml` is on `main`, when it is dispatched on a SHA, then env-up, env-down and a leftover check run in that order, and the run is green only when all three passed.
- Given env-up failed or its smoke check failed, when env-check continues, then env-down still runs.
- Given env-up's recorded total is 1800 seconds or more, when env-check reads it, then the run fails.
- Given the workflow file, when it is read, then it holds no AWS credential and only the leftover job assumes the role.

## Implementation Notes

Written before this plan file, in the same session: the route was decided as full by the size rule but implemented directly. env-up and env-down are dispatched rather than called as reusable workflows, because `tests/unit/test_env_up_workflow.py` pins env-up to `workflow_dispatch` only. After env-down passes, env-check cancels env-up's run so the `expire` job does not sleep for nothing. The live run cannot happen before merge (`gh workflow run` needs the workflow on the default branch), and it spends about 1.5 environment-hours of a month that already holds many.

## Plan Change Log

## Review Triage Log

### 2026-11-24 — Review pass
- verdicts: 5 findings — high 1, medium 0, low 3, false 0, maybe-false 0 (one finding graded medium: see row 3)
- findings:
  - `[high]` `[patch]` up job waited for env-up's whole run, including the `expire` sleep, so env-down was delayed to the expiry and the cancel step did nothing — fixed: `WATCH_JOB="env"` in scripts/dispatch-and-watch.sh ends the wait at env-up's `env` job; the cancel step now stops the sleeping `expire` job; test added.
  - `[low]` `[reject]` run lookup could match another dispatch of the same workflow — a concurrent env-down on the same ref needs a second person or a stale expire, and the epic allows one environment at a time; a unique-id fix adds an input and more complexity.
  - `[medium]` `[patch]` criterion tags did not match the plan's ACs — retagged AC-1 to AC-4 and left the expiry-input test untagged.
  - `[low]` `[reject]` tests pin text — the repo's other workflow tests do the same, and the live run is the behavioural check.
  - `[low]` `[patch]` leftover job skipped when env-down failed — now runs whenever env-down was dispatched (condition on its run id).

## Verification

**Commands:**
- `scripts/check.sh` -- expected: `check: all passed`
- `uv run pytest tests/unit/test_env_check_workflow.py -q` -- expected: all pass

## Auto Run Result

Status: awaiting-operator

- Summary: added env-check.yml, a dispatch-only workflow that dispatches env-up (waiting for its `env` job, failing on a total of 1800 s or more), then env-down, then a read-only leftover check, with a verdict job green only when all three pass; env-down still runs after a failed env-up.
- Files: `.github/workflows/env-check.yml` (the check), `scripts/dispatch-and-watch.sh` (dispatch, find the run, wait), `tests/unit/test_env_check_workflow.py` (wiring tests), `docs/drills/env-check.md` (results record skeleton, "not run yet").
- Review: 1 high and 1 medium patched, 1 low patched, 2 low rejected (reasons in the triage log). Follow-up review recommended: false.
- Verification: `scripts/check.sh` passed (ruff, pyright, lint-imports, pytest, README table, terraform, actionlint, shellcheck).
- Residual risk: nothing here ran against GitHub. The `gh run view --json jobs` job-name match (`env`) and the `env-up-stages` artifact read are first exercised by the live dispatch.
- Owed to an operator: see `operator_actions` above.
