---
title: 'Tracer: the page and /mcp answer over HTTPS on the fixed hostname from an applied environment'
type: 'feature'
ticket: '2'
created: '2026-11-17'
status: 'built'
baseline_revision: 'e2a48fa2d63687781f9c4c5dc6631207cfd61d12'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing proves the Gateway, ACM certificate and external-dns chain works end to end on EKS, and no `env` stack, EKS values or deploy script exists. Every later story in epic 5 depends on that chain.

**Approach:** Thinnest path through every layer: `infra/env` Terraform, `values-eks.yaml` for both charts, EKS-only platform dependencies and templates, and `scripts/eks-deploy.sh`. The agent writes and statically checks all of it; a person applies it, pushes images, runs the script, times each stage and tears down by hand, and the results are recorded in this plan and as committed aws-output fixtures.

## Boundaries & Constraints

**Always:** Terraform owns AWS resources only; every Helm release is installed by the script. `values-eks.yaml` holds environment facts only (AD-25). Kubernetes 1.36, standard support, no Auto Mode or Fargate. Every env resource carries an `environment` tag; ALB controller default-tag and EBS CSI extra-volume-tag settings are set. EKS API endpoint public and IAM-authenticated; node SGs admit no inbound internet except the ALB listener ports. Install order: Gateway API CRDs, controller CRDs, `platform`, `ticketscope`. Teardown: delete Gateway, wait for the ALB to go, uninstall platform, then `terraform destroy`. Mask account ids, ARNs and resource ids in fixtures; write no person identifiers.

**Never:** No `helm_release` in Terraform, no Ingress, no second ALB, no customer-managed KMS key, no control-plane logging. Do not change kind behaviour (`kind-up.sh`, `values-kind.yaml`, `_kind-deploy.yml`) or the kind release's rendering. The agent never runs `terraform apply`, pushes images, or touches AWS with write access. No embedding computation. No eks-deploy workflow (story 5.3).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Happy path | applied env, images in ECR, kubeconfig, tag | `https://<host>/` serves the page, search returns ranked issues; `/mcp` lists tools and `search_similar_issues` answers; dig shows external-dns record | script prints per-stage times |
| Address not read | external-dns ignores the ALB address | `external-dns.kubernetes.io/target` annotation on the Gateway, recorded | neither works: stop, replan |
| Missing input | no kubeconfig or tag | script exits non-zero with usage | no partial install |
| EKS render | `values-eks.yaml` plus defaults | renders only environment keys; kind release unchanged | override of a product default fails the render test |

</frozen-after-approval>

## Code Map

- `infra/bootstrap/{outputs,versions,variables}.tf` -- outputs to read (`state_bucket`, `certificate_arn`, `zone_id`, `ecr_repository_urls`); version pins (terraform ~> 1.17, aws ~> 6.0); mirror style. Do not edit.
- `deploy/charts/platform/Chart.yaml`, `values.yaml`, `values-kind.yaml`, `templates/gateway.yaml` -- add `aws-load-balancer-controller` and `external-dns` as EKS-only dependencies (condition-gated, off by default); the Gateway has only an HTTP listener today, so EKS needs an HTTPS listener on 443 and a `gateway.tls` switch. Kind render must stay identical.
- `deploy/charts/ticketscope/values.yaml`, `templates/api.yaml`, `mcp.yaml`, `backup.yaml` -- routes already attach by hostname; backup is on with an empty destination (story 5.6 owns it), so EKS values must disable it for now.
- `scripts/kind-up.sh` -- model for helm repo adds, ordering, timestamped `log`; do not edit.
- `.github/workflows/ci.yml` (`charts`, `terraform` jobs) -- extend terraform job to `infra/env`; add the EKS render tests to the chart test list.
- `tests/unit/test_infra_bootstrap.py`, `test_chart_defaults.py`, `tests/target.py` -- patterns for static infra and chart-render tests.
- `tests/fixtures/aws/` (new) -- masked real aws list output, up and after teardown.

## Tasks & Acceptance

**Execution:**
- [ ] `infra/env/{versions,main,vpc,eks,irsa,variables,outputs}.tf` -- VPC (2 AZ public subnets, no NAT), EKS 1.36 via terraform-aws-modules/eks 21, node group 2x t4g.medium arm64, vpc-cni and ebs-csi add-ons, IRSA roles for LB controller and external-dns, S3 backend in the bootstrap bucket, `environment` tag via default_tags, no KMS or control-plane logs -- AD-15, AD-23
- [ ] `deploy/charts/platform/Chart.yaml`, `values.yaml`, `Chart.lock` -- add the two EKS-only dependencies, disabled by default -- AD-13
- [ ] `deploy/charts/platform/templates/{gateway,loadbalancerconfiguration,targetgroupconfiguration}.yaml` -- HTTPS listener, certificate by explicit ARN, internet-facing scheme, target type ip, default tags; all gated off for kind -- AD-14
- [ ] `deploy/charts/platform/values-eks.yaml`, `deploy/charts/ticketscope/values-eks.yaml` -- hostname, ALB gateway class, gp3, replica counts, IRSA annotations, auth off -- AD-25
- [ ] `scripts/eks-deploy.sh` -- install CRDs, platform, ticketscope for a kubeconfig and tag; per-stage timing; usage error on missing input -- story 5.3 will call it
- [ ] `.github/workflows/ci.yml` -- fmt/validate for `infra/env`; run new tests in `charts` -- R7
- [ ] `tests/unit/test_infra_env.py`, `test_chart_eks.py` -- static checks of the Terraform text, env-only keys, kind render unchanged, tag settings, endpoint and SG rules; tag `@pytest.mark.criterion("5.2--AC-n")`
- [ ] `docs/runbooks/eks-tracer.md` -- hand steps: ECR multi-arch push, apply, deploy, smoke, hand teardown, leftover list
- [ ] `tests/fixtures/aws/*.json` -- person-captured masked list output, up and down (human step)
- [ ] Plan `## Implementation Notes` -- record stage times, certificate mode used, target-annotation need (AD-14 question), requests, limits and node memory headroom (human step)

**Acceptance Criteria:**
- Given an applied env and images in ECR, when eks-deploy.sh runs, then `https://<hostname>/` serves search results under the bootstrap certificate and `/mcp` lists tools and answers `search_similar_issues`.
- Given the deploy, when `dig <hostname>` runs, then external-dns's record resolves to the ALB.
- Given the render tests, when values-eks.yaml is rendered, then it holds only AD-25 environment keys and the kind release still renders and passes mcp-e2e.yml.
- Given the env up, when the tag-scoped list runs, then the ALB, a target group, the security group and the volumes appear; after hand teardown nothing is left.
- Given `infra/env`, when ci.yml runs, then `terraform fmt -check` and `validate` pass.

## Implementation Notes

- Deviation: `scripts/kind-up.sh` gained the two new `helm repo add` lines (kind behaviour unchanged); the existing repo-added-before-dependency-build test requires them.
- Deviation: `hostname` is not in `values-eks.yaml` (the domain is untracked); `eks-deploy.sh` sets it with the certificate ARN, IRSA annotations and ECR repositories. Added a gp3 StorageClass template, since EKS ships only gp2.
- Not implemented: the NetworkPolicy and CNPG instance-placement rule (AD-25 / C-4); left to a later story or the tracer's findings.
- Live run, 2026-11-17 (person-run, arm64-only images from a Mac mini; AD-16's multi-arch is story 5.3's CI):
  - Stage times: `terraform apply` 16m28s (48 resources; EKS control plane 12m31s). `eks-deploy.sh` 162s total: crds 12s, platform 73s, ticketscope 75s (migrate and load included), api-mcp-ready 1s, https-answers 1s. About 19 minutes in all, inside R1's 30. The `platform` stage was an upgrade, not a cold install, so the cold margin is still to measure in story 5.3. `terraform destroy` 11m09s (48 destroyed).
  - Certificate mode: explicit ARN from the bootstrap output, in the `LoadBalancerConfiguration`; the ALB's 443 listener took it. `tls.options` with no `certificateRefs` was accepted (the v1.3.0 CRD rejects a `Terminate` listener with neither).
  - external-dns read the ALB address from the Gateway status and wrote A and AAAA alias records; the target annotation was not needed. AD-14's open question is answered. `dig` returned the two ALB addresses.
  - Page: 200 under the bootstrap certificate, and a search returned ranked issues with outcomes. `/mcp`: initialize, `tools/list`, and `search_similar_issues` (hybrid, rrf, corpus 2026.11.1) answered at the public hostname. Not isolated: whether the Gateway is Programmed before any route exists (the routes already existed when the ALB was first created).
  - Sizing: 2x t4g.medium fit. Node 1 requests 35% memory (limits 105%), node 2 requests 25% (limits 93%), about 3.3 GiB allocatable each. No metrics-server, so no live peak.
  - Findings fixed in this story: (1) the IRSA trust names did not match the release-prefixed ServiceAccounts, so AssumeRoleWithWebIdentity returned 403 (chart now pins the names). (2) The controller needs Gateway API v1.6.0, not v1.3.0 (script default bumped, AWS CRDs moved to `gateway.k8s.aws/v1`). (3) The controller must restart after the CRDs change.
  - Findings left open: external-dns wrote no TXT ownership records and so deleted neither record at teardown (deleted by hand; story 5.4 must handle it). The ALB listener uses the default `ELBSecurityPolicy-2016-08` (set a modern policy). The instance-placement rule and NetworkPolicy are not implemented.
  - Teardown and R3: Gateway deleted first and the ALB confirmed gone with the controller running, then `platform` uninstalled, then destroy. After it, the tag-scoped list had 0 resources and by-name checks of load balancers, target groups, ENIs, volumes, security groups, IAM roles and log groups were empty. Fixtures `tests/fixtures/aws/up.json` (34 resources) and `down.json` (0) are masked by `scripts/mask_aws_list.py`.
  - Cost: environment up about 65 minutes, roughly $0.30.

## Plan Change Log

## Review Triage Log

Pass 1 (quick): 1 high, 2 low patched, 1 medium and 1 maybe-false deferred, 3 rejected.

| Finding | Verdict | Route | Evidence |
|---------|---------|-------|----------|
| HTTPS listener `Terminate` without `certificateRefs` | high | patch | Read the v1.3.0 standard CRD: rule "certificateRefs or options must be specified when mode is Terminate" rejects it. Fix: add `tls.options`. |
| override-check test never calls the check | low | patch | `test_the_override_check_would_fail_on_a_product_default` only compares dicts. |
| `shift 2` with a missing flag value | low | patch | Exits under `set -e` with no usage; matrix row "Missing input". |
| `kind-up.sh` edited against the plan | rejected | n/a | Fix would be a plan edit. Needed: the existing repo-added-before-dependency-build test fails without it. Recorded in Implementation Notes. |
| subchart prefixes exempt from override check | rejected | n/a | Low; those subtrees are environment config by nature, and the fix adds branches. |
| Plan tasks/fixtures/notes incomplete | rejected | n/a | `false`: marked human steps in the plan. |
| `Programmed` wait before routes exist | maybe-false | defer | If the ALB is only created once a route attaches, the wait times out. The tracer settles it. |
| LB controller IAM policy vs Gateway path | maybe-false | defer | Module policy is unverified for the Gateway API path. The tracer settles it. |

## Design Notes

- Split at checkpoint (ticket note): the estimate is about 900 lines. Slice 1: `infra/env`, hand-run docs and Terraform CI. Slice 2: values files, chart templates, deploy script and render tests. Slice 1 is not independently provable on the chain, so the recommendation is to keep one story but implement in this order.
- ACM certificate is explicit ARN from bootstrap output, passed as a value at deploy; the ARN is not committed.
- Backup stays disabled in `values-eks.yaml` until story 5.6; the Cluster still runs `instances: 2`.

## Verification

**Commands:**
- `uv run pytest tests/unit/test_infra_env.py tests/unit/test_chart_eks.py` -- expected: pass
- `uv run pytest --ignore=tests/postgres --ignore=tests/image` -- expected: pass
- `uv run lint-imports` and `python3 scripts/render_readme_table.py --check` -- expected: pass
- `terraform -chdir=infra/env fmt -check && terraform -chdir=infra/env init -backend=false && terraform -chdir=infra/env validate` -- expected: pass
- `helm lint` and `helm template` for both charts with kind and EKS values -- expected: pass, kind output unchanged

**Manual checks (person):**
- Apply, deploy, open the page, run an MCP client call, `dig`, time each stage, hand teardown, tag-scoped list empty, fixtures committed with ids masked.
