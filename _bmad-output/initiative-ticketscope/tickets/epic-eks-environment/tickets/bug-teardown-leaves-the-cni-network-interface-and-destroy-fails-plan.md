---
title: "env-down fails at terraform destroy because a VPC CNI network interface is left behind"
type: 'bugfix'
ticket: '14'
created: '2026-11-20'
status: 'built'
baseline_revision: 'f0f247a981ca86bc2d43de908d2d2da5e73cb14d'
route: 'full'
route_source: 'auto'
risk: 'high'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/bug-teardown-leaves-the-cni-network-interface-and-destroy-fails.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A detached ENI made by the VPC CNI (`eks:eni:owner=amazon-vpc-cni`, no `environment` or `elbv2.k8s.aws/cluster` tag) stays in the VPC after the nodes go, so `terraform destroy` fails with `DependencyViolation` on a subnet and the node security group, and `env-down` ends red (R3). The ENI wait and the leftover check select by those two tags only and never see it.

**Approach:** `eks-teardown.sh` deletes detached CNI ENIs of the environment's VPC (a sweep before the destroy and a loop alongside it, because the nodes only go during the destroy), the wait and the leftover check also name CNI ENIs by the CNI's own tags, and the deploy role gains `ec2:DeleteNetworkInterface` limited to CNI-tagged interfaces. A person re-applies bootstrap. Chosen from the ticket's open question (delete, not a longer wait), because a wait gave no sign of ending in run 44619309245.

## Boundaries & Constraints

**Always:** The sweep selects `status=available` interfaces with `eks:eni:owner=amazon-vpc-cni` in the environment's VPC and nothing else. An unreadable listing, or a VPC lookup that errors, fails the job and is never read as clean. AD-24 order, and the DNS step after the destroy, are unchanged. The agent runs no AWS write command outside the workflows.

**Never:** No force-deleting an attached ENI, no ENI selection by name or description alone, no wildcard resource beyond `network-interface/*` with the tag condition, no `-target` on the destroy, no hand-written baseline or README table.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Leaked CNI ENI | `available`, CNI owner tag, in the VPC, no env tags | deleted by the sweep; the wait and leftover check would name it | No error |
| Attached CNI ENI | attached, CNI owner tag | never selected | n/a |
| Another VPC | `available`, CNI owner tag, other VPC id | never selected | n/a |
| Listing unreadable | `aws ec2 describe-network-interfaces` errors | the ENI wait times out, exit 1; leftover check exits 2 | job red |
| No VPC found | `describe-vpcs` empty (cluster-less rerun) | sweep skipped, logged | No error |

</frozen-after-approval>

## Code Map

- `scripts/eks-teardown.sh` -- `eni_volume_gone` (wait, tag legs only), stage `terraform-destroy`; add `cni_orphans`/`sweep_cni_enis`, call once before the wait and as a background loop during the destroy (killed afterwards); AWS calls use `$REGION`.
- `scripts/leftover-check.sh`, `scripts/leftover_check.py` -- add a listing filtered by `tag:cluster.k8s.amazonaws.com/name=$CLUSTER_NAME`; `leftovers()` also matches an ENI whose `eks:eni:owner` is `amazon-vpc-cni` and whose cluster tag is the cluster's; `confirm` already handles `ec2:network-interface`.
- `tests/unit/test_eks_teardown.py` -- stub `aws` (`AWS_BODY`) needs `describe-vpcs`, VPC-filtered `describe-network-interfaces`, `delete-network-interface`; harness `_run`.
- `tests/unit/test_leftover_check.py` -- recorded `NetworkInterfaces` JSON of the leaked ENI (tags per the bug's step 3).
- `infra/bootstrap/policies/deploy-permissions.json.tftpl` -- new statement; `tests/unit/test_infra_bootstrap.py` renders it (mirror `e5-s12` test). No new template variables, so `bootstrap-drift` needs no change.
- `docs/runbooks/env-down.md` (steps list, ~line 49; re-apply note ~89), `_bmad-output/initiative-ticketscope/deferred-work.md` (ENI tag entry, ~line 102) -- update/close.
- Do not touch: `infra/env`, `eval/baseline.json`, the kind path.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/unit/test_leftover_check.py`, `tests/unit/test_eks_teardown.py`, `tests/unit/test_infra_bootstrap.py` -- red first: leaked-ENI listing is a leftover; sweep deletes only available CNI ENIs of the VPC (filter asserted); unreadable listing fails; rendered policy allows only `ec2:DeleteNetworkInterface` on `network-interface/*` with the CNI tag condition
- [ ] `scripts/leftover_check.py`, `scripts/leftover-check.sh` -- CNI-tag match and listing
- [ ] `scripts/eks-teardown.sh` -- sweep, wait leg for CNI ENIs, background sweep during destroy
- [ ] `infra/bootstrap/policies/deploy-permissions.json.tftpl` -- scoped delete right
- [ ] `docs/runbooks/env-down.md`, `deferred-work.md` -- runbook, bootstrap re-apply first, close the ENI-tag entry

**Acceptance Criteria:**
- Given a detached CNI ENI with neither environment tag, when the wait and the leftover check run, then both name it (bug AC 2).
- Given the sweep, when it deletes, then only `available` CNI-tagged interfaces of the environment's VPC are selected and the role's right is limited by tag (AC 3).
- Given an unreadable listing, when teardown or the check runs, then the job still fails (AC 4).
- Given `scripts/check.sh`, then it passes. Live (AC 1): after a bootstrap re-apply, a dispatched `env-up`/`env-down` ends green with no ENI left; not run here.

## Implementation Notes

## Plan Change Log

## Review Triage Log

- high, patch (found by the orchestrator reading the diff; no separate review subagent ran): the new CNI leg of the ENI wait had no `status=available` filter, so at the wait, with nodes still up, attached CNI ENIs would stall every `env-down` for 10 minutes. Added the filter in `eks-teardown.sh` and asserted it in `test_a_cni_interface_that_remains_stops_the_run_before_terraform`.

## Design Notes

AC 1 reads "no ENI remains when `terraform destroy` starts", but the leaked ENI is made when the destroy terminates the nodes, so it cannot exist earlier. The sweep therefore also runs alongside the destroy; the ENI is deleted before Terraform reaches the subnet. IAM cannot limit the delete to detached ENIs or one VPC, so the tag condition is the IAM limit and the script filter does the rest; EC2 refuses to delete an attached ENI.

## Verification

**Commands:**
- `uv run pytest tests/unit/test_eks_teardown.py tests/unit/test_leftover_check.py tests/unit/test_infra_bootstrap.py -q` -- expected: pass
- `scripts/check.sh` -- expected: pass
