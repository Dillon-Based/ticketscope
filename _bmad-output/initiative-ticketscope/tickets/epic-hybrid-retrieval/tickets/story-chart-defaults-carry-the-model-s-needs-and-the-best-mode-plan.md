---
title: 'Chart defaults carry the model''s needs and the best mode'
type: 'feature'
ticket: '6'
created: '2026-11-10'
status: done
baseline_revision: 'dd20e0c51a4179e2354036bf8b01c1d7ad8dfe37'
route: 'oneshot'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/spike-choose-the-embedding-model-findings.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** `values.yaml` still carries provisional api resources and `retrieval.defaultMode: keyword`, so a request that omits `mode` is served by the weakest mode and the chart does not record what the model needs (R5).

**Approach:** Set api's CPU and memory requests and limits from the measured api pod on kind, record the measured memory and embedding time in comments, and set `defaultMode` to the mode with the best overall MRR@10 in `eval/baseline.json` (hybrid on a tie), with the number it chose by. `mcp` gets no mode default.

</intent-contract>

## Tasks & Acceptance

**Acceptance Criteria:**
- Given the chart on kind under the new limits, when dense searches run, then api stays Ready with no OOM kill.
- Given `POST /v1/search` with no `mode`, then its `score_kind` is the default mode's, and that mode has the best overall MRR@10 in `eval/baseline.json`.
- Given `values.yaml`, then comments name the measured memory and embedding time.

## Implementation Notes

Oneshot: a values edit plus one unit test.

- Measured on the kind api pod (cgroup `memory.peak` 288 MB = 275 MiB on a fresh pod after 60 dense searches and a default-mode search (an earlier pod: 239 MB); no OOM events; dense search ~134 ms, hybrid ~82 ms). Spike 3.3: embedding 35.7 ms per issue (1,146 s for the 32,153-issue snapshot, host); eval Job 1475 s on kind.
- Kind load Job (`kubectl get jobs`): ticketscope-load Complete in 16 s within its 512Mi limit with the pinned asset. After `helm upgrade` with the new limits (`cpu: 1`): default-mode search `score_kind` rrf, dense `cosine`, 60 dense searches, peak 288 MB, `oom_kill 0`; latency under the limit dense 80 ms, hybrid 81 ms, keyword 20 ms (mean over 40 requests), with 61 CPU throttle events totalling 2.6 s and no latency regression.
- `values.yaml`: `defaultMode: hybrid` (overall MRR@10 hybrid 0.5936, dense 0.5787, keyword 0.5505); api cpu limit added; comments record the numbers.
- `tests/unit/test_chart_defaults.py`: default mode equals the best-MRR mode in `eval/baseline.json`, and the api resources and measured numbers are in `values.yaml`.

## Plan Change Log

## Review Triage Log

### 2026-11-10 — Review pass
- verdicts: 7 findings — high 0, medium 0, low 3, false 3, maybe-false 0 (one low grouped with the unsupported-numbers claims)
- findings:
  - `[low]` `[patch]` Unsupported "16 s" and keyword "21 ms" figures in comments — both were observed (`kubectl get jobs`, my 40-request timing); recorded in Implementation Notes, keyword figure re-measured at 20 ms and comment updated.
  - `[low]` `[patch]` CPU limit not tied to a measurement, possible throttling — re-measured under the limit: dense 80 ms, hybrid 81 ms, keyword 20 ms, so no regression; comment now says it was measured under the 1-core limit.
  - `[false]` `[reject]` ACs 1 and 2 not evidenced — after the upgrade with the new limits the pod was Ready, default search returned `rrf`, dense `cosine`, peak 288 MB, `oom_kill 0` (Implementation Notes).
  - `[low]` `[reject]` Comment test uses literal strings — rewording would fail it deliberately; the fix adds complexity for no everyday harm.
  - `[low]` `[reject]` Regex brittle against a quoted `defaultMode` — a reformat fails loudly with a clear message and the fix adds parsing complexity.
  - `[false]` `[reject]` `settings.py` default is still `keyword` — the intent sets the default once in `values.yaml` (spine AD-25); the code fallback is outside it and the chart always sets the env var.
  - `[false]` `[reject]` No AGENTS.md/CLAUDE.md rules checked — none exist, nothing to break.

### 2026-11-10 — Follow-up review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings: none. Quick reviewer inspected the complete diff since the baseline, including the expanded chart tests. Other lenses skipped by the pinned quick selection.

## Auto Run Result

Status: built (preserved; the orchestrator owns ticket completion).

**Summary.** Verified the existing chart defaults and incorporated the automation pass's five rendered-chart tests. The default remains hybrid, chosen from overall MRR@10: hybrid 0.5936, dense 0.5787, keyword 0.5505. api requests cpu 100m / memory 256Mi and limits cpu 1 / memory 512Mi; comments record measured memory and embedding time. The pinned load asset uses the existing jobs resources; mcp receives no default mode.

**Files changed since the baseline**
- `deploy/charts/ticketscope/values.yaml` — chosen default, measured api resources and load/embedding measurements (existing implementation).
- `tests/unit/test_chart_defaults.py` — baseline selection, resource keys and measurement comments (existing implementation).
- `tests/unit/test_chart_defaults_expanded.py` — rendered default, override propagation, api-only default, request/limit bounds and memory headroom (automation pass).
- This plan — follow-up review and verification evidence; status retained.
- `_bmad-output/test-artifacts/automate/automation-summary-story-ticketscope--e3-s6.md` and `_bmad-output/initiative-ticketscope/bmad-build-auto-result-3.6-tea.automate-1.md` — existing automation pass records incorporated with its tests.

**Review.** Follow-up quick review: no findings; patched high 0, medium 0, low 0; deferred 0; rejected 0. Prior pass's seven findings and dispositions remain in the triage log above. Existing deferred-work ledger entries were not changed.

**Follow-up review recommended:** false.

**Verification.** `uv run pytest tests/unit`: 1077 passed, 1 xfailed, including all nine chart-default tests. `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`: clean. `uv run lint-imports`: 7 contracts kept. Helm rendered the chart with kind values, local image tags and backup disabled for offline rendering; api receives `TICKETSCOPE_DEFAULT_MODE: hybrid`.

On the existing kind deployment, confirmed the chart's cpu/memory requests and limits and default-mode env. Sixty dense POST requests returned ten results with `score_kind: cosine`; a POST omitting mode returned `mode: hybrid`, `score_kind: rrf`. Afterwards `/readyz` returned ready, the pod remained Ready with zero restarts, and cgroup memory events reported `oom 0`, `oom_kill 0`. This verification run's memory peak was 291160064 bytes (about 278 MiB), below 512Mi; the values comments retain the original sizing measurement. The load Job is Complete in 16 seconds. No upgrade was necessary because the deployed defaults already matched.

**Residual risks.** Measurements are from local kind; epic 5 must confirm node sizing on EKS. The baseline-selection test catches a change in the best mode. No unresolved blocker or human decision remains.

## Verification

**Commands:**
- `uv run pytest tests/unit` -- expected: pass
- `uv run ruff check . && uv run ruff format --check . && uv run pyright` -- expected: clean
- `helm template deploy/charts/ticketscope -f deploy/charts/ticketscope/values-kind.yaml` -- expected: renders with TICKETSCOPE_DEFAULT_MODE "hybrid"
- Kind: upgrade the release, POST `/v1/search` without `mode` -- expected: `score_kind` rrf, no OOM kill
