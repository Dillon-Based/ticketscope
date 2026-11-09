---
title: 'A regressing PR cannot merge'
type: 'feature'
ticket: '3'
created: '2026-11-08'
status: done
baseline_revision: '9a62dbceb82950119c6c881e080e4293e6900f1c'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** CI produces eval scores (story 2.2) but nothing compares them to a committed baseline, so a PR that worsens retrieval still merges.

**Approach:** Commit `eval/baseline.json` (a CI run's full results JSON, lineage included). A pure gate function compares the PR run's per-mode, per-kind Recall@10 and MRR@10 to it and fails on a drop over 0.005 unless the same diff changes the baseline. The gate runs in `eval.yml` after the eval check, finding that diff against the PR base commit.

## Boundaries & Constraints

**Always:** Tolerance 0.005 absolute, inclusive, compared with `round(..., 6)` or `Decimal` (0.400−0.395 is 0.0050000000000000044 in float). Gated: Recall@10 and MRR@10, per mode, per kind (short, log_heavy; overall too). Recall@1/5 and p95 are reported, never gated. A changed baseline must equal this run's results within tolerance. Lineage (snapshot_version, embedding_model_id, preprocessing_version) must match unless the baseline changed; null, "none" and "" embedding ids are equal. A gated mode missing from the run fails unless the baseline changed; a new mode passes and is reported. Kind floor: run `log_heavy.pairs_scored` < 200 fails unless baseline carries `kind_floor_decision` with a date and a reason. Every failure names mode, kind, metric or field. New workflow inputs have defaults (ci.yml also calls `_kind-deploy.yml`).

**Decisions (user, 2026-11-08):** A missing `eval/baseline.json` passes with a "no baseline" report; a follow-up PR commits the CI artifact (so this PR does not add baseline.json, and the final task and the "worsens ranking" E2E move to that follow-up). The gate runs inside `eval.yml`'s `check:` after pytest, reading the results file before upload.

**Never:** Gate p95. Write or run anything that merges, or set branch protection (a person's step, HITL). Hand-write baseline numbers: they come from a CI results artifact. Touch `ci.yml`'s integrated check behaviour.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Within tolerance | R@10 drop exactly 0.005 | pass | none |
| Over tolerance | drop 0.0051; or log-heavy MRR −0.006 while overall rises | fail naming mode/kind/metric | exit 1 |
| Reported only | R@1/R@5 −0.1; p95 ×100 | pass, p95 in report | none |
| Baseline updated | any drop, baseline changed and equals run | pass | none |
| Baseline hand-edited | changed baseline differs from run by >0.005 | fail | exit 1 |
| Lineage drift | snapshot / model id / preprocessing differs, baseline unchanged | fail naming field | exit 1 |
| Null model id | null in both files | match | none |
| Mode set | gated mode missing / new mode | fail unless baseline changed / pass, reported | exit 1 |
| Kind floor | 199 log-heavy, no decision / with dated reason / 200 without | fail / pass / pass | `kind_floor_decision` missing date or reason fails |
| Diff detection | head changes `eval/baseline.json` vs base commit | updated=true, else false | base unavailable fails loudly |

</frozen-after-approval>

## Code Map

- `src/ticketscope/jobs/eval/main.py:39-72` -- builds the results line and `lineage`; reuse the schema, do not change it.
- `src/ticketscope/jobs/eval/score.py:40-51` -- `modes.<m>.{short,log_heavy,overall}` with `recall@1/5/10`, `mrr@10`, `p95_latency_ms`, `pairs_scored`.
- `tests/eval/conftest.py:40-94` -- writes `reports/eval-results.json` (sorted keys, indent 2); the gate reads it.
- `.github/workflows/eval.yml` -- only `pull_request`, `check:` runs pytest; add the gate to `check:` after pytest.
- `.github/workflows/_kind-deploy.yml:40` -- plain checkout (depth 1); add a defaulted `base_sha` input that fetches it (pattern: `ci.yml` evidence job, `git fetch --no-tags --depth=1 origin`).
- `pyproject.toml` -- scripts, pytest markers, lint-imports contracts; check the new module fits a contract.
- `tests/unit/test_eval_workflow.py` -- workflow parse test; extend for the base-commit fetch.
- `eval/baseline.json` -- does not exist; new.

## Tasks & Acceptance

**Execution:**
- [ ] `src/ticketscope/jobs/eval/gate.py` -- pure `check(baseline, results, baseline_changed)` returning failure and report lines, plus CLI (`--baseline`, `--results`, `--base-sha`) that detects the diff with `git diff --name-only <base> HEAD -- eval/baseline.json` -- the gate
- [ ] `tests/unit/test_eval_gate.py` -- the 15-case decision table, provenance, mode-set cases, and diff detection on a temporary git repo (no sleeps) -- I/O matrix
- [ ] `tests/unit/test_eval_workflow.py` -- assert the base commit is fetched and the gate step is wired -- R-003
- [ ] `.github/workflows/eval.yml`, `_kind-deploy.yml` -- pass `base_sha`, fetch it, run the gate; write the report to `$GITHUB_STEP_SUMMARY` -- gate in CI

**Acceptance Criteria:**
- Given a PR that worsens keyword ranking, when eval runs, then the gate step fails with the metric named (R3).
- Given the same PR also updates `eval/baseline.json` to its run's results, then the gate passes (R3).
- Given a preprocessing-version change with no baseline update, then the gate fails with a lineage message (R3).
- Given `ruff`, `pyright`, `lint-imports` and `pytest tests/unit`, then all pass (R3).
- Given the merged workflow, a person makes `eval` required in branch protection (checked by the person, R3).

## Implementation Notes

## Plan Change Log

## Review Triage Log

- medium / patch -- deleting `eval/baseline.json` passed as "no baseline". Verified in `main()`. Fixed: `baseline_existed` checks the base commit; a deleted baseline fails; test added.
- low / defer -- `base.sha` can be stale on a rerun after main advanced, so a baseline update from main may count as this PR's. Real only on reruns; recorded in deferred-work.md.
- low / rejected -- a changed baseline that still lists a missing mode fails. Intended: a changed baseline must equal the run; the fix would add a branch.
- low / rejected -- non-object JSON raises `AttributeError`. The gate still exits non-zero; a guard adds complexity for a case CI cannot produce.
- info -- worsening-PR E2E and branch protection need CI and a person; deferred by the plan's decision.

## Design Notes

Baseline numbers must come from CI, and the gate step runs in the same job that produces them, so the first PR cannot already carry a matching baseline.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports` -- expected: clean
- `uv run pytest tests/unit` -- expected: pass, including the new gate tests

**Manual checks (if no CLI):**
- Throwaway PRs: a worsening PR fails `eval`, passes after a baseline update; record the run URLs.
- GitHub shows `eval` as required on main (person's step).
