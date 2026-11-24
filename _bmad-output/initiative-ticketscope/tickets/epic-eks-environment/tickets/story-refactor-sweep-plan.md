---
title: 'Refactor sweep (epic 5)'
type: 'refactor'
ticket: '10'
created: '2026-11-24'
status: done
baseline_revision: '67252bcf744c3006b2aa44617a12b06d762d12d8'
route: 'oneshot'
route_source: 'auto'
risk: 'low'
review: quick
review_source: pinned
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** The epic's stories left the same code copied in places: the platform chart's templates each spell the same two labels, `eks-deploy.sh` and `eks-teardown.sh` each carry an identical stage timer, and both drill scripts define the same `x` helper.

**Approach:** Cleanup only. Move each copy to one definition, with rendered chart output, script output, values keys and teardown order unchanged.

</intent-contract>

## Implementation Notes

Oneshot: a small, mechanical change (about 60 lines moved), checked by diff of rendered output.

- `deploy/charts/platform/templates/_helpers.tpl` (new): `platform.labels`, used by `gateway.yaml` (2), `loadbalancerconfiguration.yaml`, `targetgroupconfiguration.yaml`, `storageclass.yaml`, `barman-cloud-tls.yaml`. `helm template` of `gateway`, `loadbalancerconfiguration`, `targetgroupconfiguration` and `storageclass` with `values-eks.yaml` and `values-kind.yaml` is byte-identical before and after (the full render is not, because subcharts generate random secrets and certificates).
- `scripts/lib/stages.sh` (new): `log`, `stage`, `summary`, sourced by `eks-deploy.sh` and `eks-teardown.sh`, which set `STAGES_TITLE` so their `--- <title> stage times ---` header is unchanged. `scripts/lib/x.sh` (new): `x`, sourced by `restore-drill.sh` and `failure-drill.sh`. Both are listed in `scripts/check.sh` and `ci.yml`'s shellcheck step, which `tests/unit/test_check_script.py` requires to match.
- Tests that encoded the old layout follow it: `test_chart_tunnel_listener.py` copies `_helpers.tpl` into its scratch chart; `test_infra_env.py` looks for the stage-times text in `lib/stages.sh`.
- Looked at and left alone: the env workflows' repeated OIDC and bootstrap-facts steps (a composite action changes what the deploy role's trust sees and needs a live `env-up`/`env-down` to prove), `infra/env` and `infra/bootstrap` (their provider blocks differ in tags and backend key on purpose), and `restore-drill.sh`'s own `stage` (it records pairs for the record, not a timer log).
- Live `env-up`/`env-down` dispatch from the ticket's verify line is not run here: a person dispatches it, and nothing it exercises besides `eks-deploy.sh`'s and `eks-teardown.sh`'s sourcing of `stages.sh` changed (covered by their stubbed script tests).

## Verification

- `scripts/check.sh` passes (ruff, pyright, lint-imports, pytest, README table, both terraform stacks, `actionlint`, `shellcheck` including the two new libs).
- `helm template` of both platform values files renders; the four deterministic templates are byte-identical to the baseline.

## Review Triage Log

### 2026-11-24 — Review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings:
  - none: the quick lens reported no findings.

### 2026-11-24 — Follow-up review pass

- verdicts: 3 findings — high 0, medium 2, low 1, false 0, maybe-false 0
- findings:
  - [medium] [reject] Live acceptance evidence is outstanding. The story branch has no recorded PR or workflow runs. This is an orchestrator verification item outside the build pass. Closing it requires successful live runs.
  - [low] [patch] The ten expanded tests lacked criterion metadata. The module now carries the story marker, and all ten JUnit cases report it.
  - [medium] [patch] The label check rendered only the Gateway and GatewayClass. It now renders all five consuming templates with EKS values and checks the metadata labels on all eight resulting objects, including both TLS Secrets and both target groups.

## Auto Run Result

The build retains shared platform labels, the deploy and teardown stage timer, and the drill command helper. This follow-up changed the criterion metadata and chart assertions in `tests/unit/test_shared_helpers_expanded.py`. The accompanying automation summary and result describe the preceding test expansion.

The quick review produced two test patches (one medium and one low). The remaining finding tracks outstanding live verification, which the orchestrator owns. No items were deferred. Follow-up code review recommended: false.

Local verification passed. `scripts/check.sh` reported 1,701 pytest cases passed, 85 deselected, both Terraform configurations valid, and all static checks passed. Both charts rendered with each environment file and sample deployment inputs. The four deterministic platform templates rendered byte-identically to the baseline in each environment. All ten expanded tests passed and reported the story criterion in JUnit.

Final acceptance still requires passing PR runs of `ci.yml` and `mcp-e2e.yml` and a successful hand-run EKS `env-up` and `env-down` pair for this change.
