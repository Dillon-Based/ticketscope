---
runScope: 'story'
runKey: 'story-ticketscope--e3-s5'
testMode: 'expand'
testEntry: 'bmad-tea-automate'
workflowStatus: 'completed'
storyId: '3.5'
storyKey: 'ticketscope--e3-s5'
lastStep: 'step-04-validate-and-summarize'
lastSaved: '2026-11-10'
---

# Automation summary: story 3.5 (expand, autonomous)

Added `tests/unit/test_eval_embedder_expanded.py` (8 tests: 7 pass, 1 strict xfail). Full `tests/unit`: 1065 passed, 1 xfailed. Ruff and pyright clean. The kind eval tests were not run (they need a cluster).

Covered: `build_embedder` with a model id; model-load failure gives exit 1 and no results line; one embed per pair for each of dense and hybrid; an embedder over a store without embeddings skips dense and hybrid; the workflow and Helm timeouts outlast the 2700 s deadline; `eval.resources` override.

No test defects needed healing.

## Product defect (not changed)
`scripts/kind-up.sh`: with `EVAL_ENABLED=1` and `EMBEDDINGS_COMPUTE=1`, the compute branch resets `HELM_TIMEOUT=50m` after the eval branch set 60m, so Helm may time out before eval's 2700 s deadline plus load. CI does not set both, so the risk is local only. Pinned by the strict xfail `test_embeddings_compute_does_not_shrink_the_eval_helm_timeout`. It will fail loudly (XPASS) once fixed, and the marker should be removed then.

The operator actions in the plan (baseline and README update, AC-2/AC-3) remain untested because they need a CI run.
