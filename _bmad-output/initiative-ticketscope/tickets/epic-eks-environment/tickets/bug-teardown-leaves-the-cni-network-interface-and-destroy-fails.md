---
id: 14
type: bug
title: "env-down fails at terraform destroy because a VPC CNI network interface is left behind"
parent: epic-eks-environment
covers: ["R3"]
after: [4]
assignee: ""
refined: false
hitl: false
risk: high
severity: P1
---

# env-down fails at terraform destroy because a VPC CNI network interface is left behind

## Description

After the ordered teardown, one network interface created by the VPC CNI stays in the environment's VPC, detached. It keeps the node security group and a subnet from being deleted, so `terraform destroy` fails after 30 minutes and `env-down` ends red with the VPC, subnets and security group still in the account. The ENI wait and the ENI leg of the leftover check never see it. The environment should be destroyed completely and `env-down` should end green.

## Reproduction

1. Dispatch `env-up` (1 hour expiry); the `expire` job dispatches `env-down` at expiry (run 44619309245, 2026-11-19).
2. Actual: every ordered stage passes, then `terraform destroy` runs about 30 minutes and fails with `DependencyViolation` on subnet `subnet-095399c21f028da3f` and security group `sg-09a0dbb4887d89c08` (the node shared group). `scripts/eks-teardown.sh` exits before its DNS step.
3. Read-only listing of the VPC's interfaces then shows one: `eni-0de53ed513ef52774`, status `available`, no attachment, description `aws-K8S-i-...`, in that subnet and that group. Tags: `node.k8s.amazonaws.com/instance_id`, `eks:eni:owner=amazon-vpc-cni`, `cluster.k8s.amazonaws.com/name`, `node.k8s.amazonaws.com/createdAt`. It has neither the `environment` tag nor `elbv2.k8s.aws/cluster`.
4. Expected: no interface remains and `terraform destroy` succeeds. The earlier runs 44570082818 and 44579422898 destroyed 52 resources, so this does not happen every time.

## Cause Hypothesis

The nodes are terminated while the VPC CNI still holds a secondary ENI, or the CNI's cleanup of a detached ENI lags past `terraform destroy`. The leftover check and the ENI wait select by the `environment` and `elbv2.k8s.aws/cluster` tags only, which these ENIs lack, so both are vacuous for them (the open deferred entry from story 5.4). Not verified why this run leaked and the earlier two did not.

## Acceptance Criteria

1. **The CNI interface is cleared before the destroy**
   **Given** an environment brought up by `env-up`
   **When** `env-down` runs, dispatched or by expiry
   **Then** no ENI remains in the environment's VPC when `terraform destroy` starts, `terraform destroy` succeeds, and the job is green (R3)
2. **The wait and the leftover check see these interfaces**
   **Given** a detached ENI in the environment's VPC carrying `eks:eni:owner=amazon-vpc-cni` and neither environment tag
   **When** the ENI wait and the leftover check run
   **Then** both name it, shown by a unit test on recorded AWS output (R3)
3. **Only the environment's own interfaces are touched**
   **Given** the fix
   **When** it removes an ENI
   **Then** it removes only `available` (detached) interfaces in the environment's VPC with the CNI owner tag, never one that is attached or in another VPC, shown by a test on the filter; the deploy role's permission is limited the same way (R3)
4. **Tests cover the condition found and fixed**
   **Given** the test suite
   **When** it runs
   **Then** a test that fails on the defect and passes on the fix covers the reproduction, and one covers a listing that cannot be read, which still fails the job
5. **Or: no change is needed, with proof**
   **Given** the reproduction
   **When** it is run on the current code
   **Then** no interface remains and the destroy succeeds, with the evidence in Notes; this supersedes 1 to 4

## References

- parent — `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md`, requirement R3
- plan — `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-env-down-tears-down-in-order-finds-nothing-left-and-expires-plan.md`, Implementation Notes
- deferred — `_bmad-output/initiative-ticketscope/deferred-work.md`, the ENI tag entry from story 5.4
- run — GitHub Actions run 44619309245 (`env-down`)

## Notes

- Decision: A bug in this epic, before story 6, because every environment stories 6 to 9 create can leak the same interface (user, 2026-11-19).
- The interface was deleted by hand by the user after the run, so the next `env-down` could finish.
- Bug 12's live check (the DNS delete) did not run on this run, because the script exits at the failed destroy; it is rerun after the manual delete.
- Open question: Whether to delete the detached interface from the workflow before the destroy, or to wait for the CNI to release it with a longer limit. A new deploy-role right for deleting a network interface, scoped as in criterion 3, means a bootstrap re-apply.
