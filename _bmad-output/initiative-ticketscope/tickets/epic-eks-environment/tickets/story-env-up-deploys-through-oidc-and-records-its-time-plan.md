---
title: 'env-up deploys through OIDC and records its time'
type: 'feature'
ticket: '3'
created: '2026-11-18'
status: 'built'
baseline_revision: 'bd99bab4950762e35ada8e48960d39d03d15d414'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-tracer-the-page-and-mcp-answer-over-https-on-the-fixed-hostn-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The environment is only brought up by hand with an admin identity, so the 30-minute target (R1), the no-stored-key deploy (R6) and the expiry tag (R4) are unproven, and multi-arch images (AD-16) have never been built.

**Approach:** `env-up.yml`, a dispatched workflow that assumes the deploy role through OIDC. An untimed job builds and pushes the multi-arch images; timed jobs apply `infra/env` with an expiry tag, run `scripts/eks-deploy.sh`, and run a smoke check from `tests/`. The clock runs from the start of `terraform apply` to the smoke check passing, and each stage's time goes to the job summary and an artifact.

## Boundaries & Constraints

**Always:** No AWS credential in repo secrets or variables; the role comes from `vars.AWS_ROLE_ARN` on the `eks` environment. Inputs are a git SHA and expiry hours (default 4). The build job skips when both images exist for the SHA and is outside the clock. A failed smoke check fails the run and leaves the environment up for the expiry sweep. Reuse `scripts/eks-deploy.sh`, `eks-crds.sh` and the story-2 chart values. The smoke check compares the loaded issue count with the pinned snapshot's published count. `dns_visible` is measured against the zone's name servers before the public resolver is polled. Account ids and ARNs stay masked in logs and artifacts.

**Decisions (user, 2026-11-18):** (1) The live run is after merge, dispatched from `main`; `main` is added to the `eks` environment's branch rule by the user. No push trigger on `env-up.yml`. (2) The deploy-role widening is in this story: a runbook step, applied by the author through bootstrap before the first dispatch, with the denied actions recorded in Implementation Notes.

**Never:** No `env-down` (story 5.4), no auth, no backups (5.6). Do not change kind behaviour (`kind-up.sh`, `values-kind.yaml`, `_kind-deploy.yml`). The agent never applies Terraform, pushes images or dispatches the workflow against AWS itself. No wait that only serves a test. Never move the 30-minute target without the user.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Happy path | SHA, no images, no env | build, apply, deploy, smoke pass; summary and artifact list every stage | n/a |
| Images exist | both tags in ECR | build job skipped | n/a |
| Smoke fails | page or `/mcp` or count wrong | run red, environment left up | summary still written |
| Slow run | total 30 min or more | stage times show where | record a Decision in the epic Notes |
| Bad input | SHA not 40 hex or hours not 1 to 24 | run fails before any AWS call | message names the input |

</frozen-after-approval>

## Code Map

- `.github/workflows/aws-oidc-check.yml` -- OIDC pattern to copy: `environment: eks`, `id-token: write`, `configure-aws-credentials@v4` with `vars.AWS_ROLE_ARN`.
- `scripts/eks-deploy.sh` -- stage timer (`stage`, `summary`), five required flags, polls HTTPS in `https-answers`. Add the DNS stages before it. `scripts/eks-crds.sh` and `scripts/eks-env.sh` (hand path, do not edit).
- `infra/env/{versions,variables,outputs}.tf` -- `default_tags` and variables; add `expires_at`. Backend bucket `ticketscope-<account id>` is passed at init.
- `infra/bootstrap/policies/deploy-permissions.json.tftpl` -- the role has IAM, ECR push, EKS and Describe only. A full `env` apply also needs EC2 (VPC, subnets, security groups, launch templates, tags), the OIDC provider, `ecr:DescribeImages`, and whatever the first run denies. Applied by the author (bootstrap), not the workflow.
- `tests/mcp/test_search_tool.py`, `tests/smoke/test_gateway.py`, `tests/kind.py` -- MCP client and search helpers to reuse; they read `gateway()` for kind. `tests/target.py` `snapshot_pin()`.
- Release `snapshot-<version>` body holds `Issues: N`; there is no manifest file. The load Job's log line `load report: issues=N`.
- `.github/workflows/ci.yml` -- add the new tests and an `actionlint`-style static check.
- `tests/unit/test_infra_env.py`, `test_eks_tracer_findings.py` -- static-test style; tag `5.3--AC-n`.

## Tasks & Acceptance

**Execution:**
- [ ] `infra/env/{variables,versions}.tf` -- `expires_at` variable and tag via `default_tags` -- R4
- [ ] `infra/bootstrap/policies/deploy-permissions.json.tftpl` -- widen the deploy role to what the apply needs, scoped by name or tag; stays out of `bootstrap/` state paths -- R6
- [ ] `scripts/eks-deploy.sh` -- stages `dns_visible` (authoritative name servers of the zone) then `dns_public`, before `https-answers`; keep the usage and idempotence
- [ ] `tests/eks/test_public_smoke.py` -- over `TICKETSCOPE_PUBLIC_URL`: page search, MCP `tools/list` and `search_similar_issues`, load-job issue count equals the Release count; new `eks` marker excluded by default
- [ ] `.github/workflows/env-up.yml` -- inputs validated; `images` job (buildx, amd64 and arm64, skip if present); `env` job (clock file, apply, kubeconfig, deploy, smoke, summary and artifact)
- [ ] `tests/unit/test_env_up_workflow.py` -- no secrets or keys, OIDC, input validation, skip rule, clock starts at apply and stops after smoke, expiry tag wired
- [ ] `docs/runbooks/env-up.md` -- dispatch, the hand teardown in AD-24 order, the bootstrap re-apply
- [ ] Plan `## Implementation Notes` -- the live run's stage times and verdict (human step)

**Acceptance Criteria:**
- Given a dispatch on a SHA, when it finishes, then the page and `/mcp` answer over HTTPS with the corpus loaded, and the time from the start of `terraform apply` is under 30 minutes.
- Given the run, then the summary and artifact list each stage, `dns_visible` before the public resolver stage.
- Given the repo settings, then no AWS credential exists and the run assumed the role through OIDC.
- Given the input hours, then the environment carries the matching expiry tag.
- Given a failing smoke check, then the run is red and the environment remains.
- Given images already pushed for the SHA, then a second dispatch skips the build job.

## Implementation Notes

- Static slice done by the agent; the live run, the bootstrap re-apply and the stage times are human steps and not yet recorded.
- Deploy-role widening (static, first guess): EC2 write actions on `arn:aws:ec2:<region>:<account>:*` (plus the AMI arn for `RunInstances`), the cluster OIDC provider create/delete/tag, IAM policy get/list/tag, `ecr:DescribeImages`, `iam:GetOpenIDConnectProvider`/`ListOpenIDConnectProviders`. Denied actions from the first dispatch: `iam:GetRole` on `role/ticketscope-deploy`, read by the EKS module's `aws_iam_session_context` data source during `terraform plan` (added as `DeployRoleSelfRead`); `ssm:GetParameter` on the public `/aws/service/eks/*` parameters, read by the node group module for the AMI release (added as `EksPublicParameters`); and, added ahead of the apply, the EKS `access-entry` ARN so the access entries and policy associations are authorised. Third, in the apply: `CreateNodegroup` failed validating the service-linked role, `iam:GetRole` on `AWSServiceRoleForAmazonEKSNodegroup` (added as `ServiceLinkedRoleRead`, with the EKS and Auto Scaling service-linked roles read ahead of need). The partial environment was reused for the next dispatch, so that run's time is not a cold R1 measurement. More to record.
- Deviation: the EC2 write statement is scoped to the account and region, not by name or tag, because EC2 create actions have no name prefix to scope on and the denied set is found only by live runs. Tightening it with `aws:RequestTag` and `aws:ResourceTag` conditions is a follow-up once the first dispatch shows the real action list (review triage, 2026-11-18).
- Deviation: `tests/unit/test_infra_bootstrap.py` allows the OIDC provider ARN pattern in the IAM-write scoping test, since a provider is named by cluster id and cannot carry the `ticketscope-env-` prefix.
- Deviation: images build on native runners per arch (matrix) and are joined by an `images` job, instead of one QEMU buildx job, following ci.yml's AD-16 choice; the `build` and `images` jobs are both skipped when the SHA's images exist.
- The hostname, zone id and certificate ARN are read from AWS in the `env` job (zone named `ticketscope.*`, issued certificate for it), because the deploy role never reads bootstrap state and no repo variable besides the role ARN may exist. `eks-deploy.sh` reads the zone's name servers from Route53 (`aws` and `dig` now required there).
- A run at or over 1800 s stays green and is flagged in the summary; it is the person's Decision to record.
- Tooling added to CI: an `actionlint` and `shellcheck` job (`workflows`).

\n- Live run, 2026-11-18, dispatch from `main` at 12b0150, run 44368083253, through OIDC with no stored key. Succeeded: page, `/mcp` and the issue-count check passed over the public hostname. This run continued a partly applied environment (the VPC, IAM and EKS control plane came from the previous failed run), so it is not the cold R1 measurement. Stage times (s): terraform_apply 176, kubeconfig 1, deploy.crds 19, deploy.platform 142, deploy.ticketscope 71, deploy.api-mcp-ready 2, deploy.dns_visible 2, deploy.dns_public 0, deploy.https-answers 0, smoke 6; total from apply start to smoke pass 420. The cold run (control plane about 12.5 minutes in the tracer) is still to record after a hand teardown and a fresh dispatch.
\n## Plan Change Log

## Review Triage Log

Pass 1 (quick): 1 medium, 3 low patched, 4 low rejected, 1 low rejected with a note, 1 false.

| Finding | Verdict | Route | Evidence |
|---------|---------|-------|----------|
| Smoke step exits before writing its `smoke` row or `clock-end` when pytest fails | medium | patch | `env-up.yml` smoke step runs under `bash -e`; the `printf` lines follow the pytest call, so a failed smoke leaves no row. Matrix says the summary is still written. |
| `deploy.*` rows appended after `smoke` in the summary and `stages.json` | low | patch | Rows are added only in the last step; the order disagrees with the runbook and AC-2. |
| Release count fetched from the unauthenticated GitHub API | low | patch | `test_public_smoke.py::_release_count` sends no token; shared runner IPs can hit the 60/hour limit and turn a good run red. |
| `eks-deploy.sh` tool check omits `aws` | low | patch | The check lists `dig` but not `aws`, which the script now calls when `ZONE_NAME_SERVERS` is unset. |
| Test for the failed-smoke case does not check the `smoke` row | low | patch | Same root cause as the first row; test assertion added with its fix. |
| EC2 statement not scoped by name or tag | low | rejected | Real deviation from "scoped by name or tag", but EC2 create actions have no name prefix to scope on, the account is single-purpose, and the fix (RequestTag and ResourceTag conditions) is found only by live denials. Recorded as a deviation in Implementation Notes. |
| Hostname, zone and certificate found by naming heuristic | low | rejected | More than one `ticketscope.*` zone fails the check loudly; the certificate match is on the exact hostname and bootstrap holds one. The fix adds branches. |
| Partial image push leaves one tag | low | rejected | The next dispatch rebuilds both and `imagetools create` overwrites; harmless. |
| `actionlint` installed by an unpinned remote script | low | rejected | CI job has `contents: read` only and no secrets; the fix adds checksum handling. |
| Runbook teardown uses `$TICKETSCOPE_ZONE_ID` undocumented | false | rejected | Runbook line 72 runs `eval "$(scripts/eks-env.sh ...)"` before the teardown block. |

## Design Notes

- Slice order: static pieces (Terraform variable, script, tests, workflow) first, then the human-run bootstrap re-apply, then the first dispatch.
- The issue count has no public endpoint. The smoke check reads the load Job's report line through the kubeconfig, and the Release body's `Issues:` line for the pinned version.

## Verification

**Commands:**
- `uv run pytest tests/unit/test_env_up_workflow.py tests/unit/test_infra_env.py` -- expected: pass
- `uv run pytest --ignore=tests/postgres --ignore=tests/image` -- expected: pass
- `uv run lint-imports` and `python3 scripts/render_readme_table.py --check` -- expected: pass
- `terraform -chdir=infra/env fmt -check`, `init -backend=false`, `validate`; same for `infra/bootstrap` -- expected: pass
- `shellcheck scripts/eks-deploy.sh` and `helm lint` for both charts -- expected: pass

**Manual checks (person):**
- Add `main` to the `eks` environment's branch rule, merge, re-apply bootstrap, dispatch `env-up`, read the summary and artifact, confirm no AWS secret or variable besides the role ARN, tear down by hand in AD-24 order.
