---
id: 12
type: bug
title: "env-down ends red and leaves the hostname's A and AAAA records pointing at a dead ALB"
parent: epic-eks-environment
covers: ["R2", "R3", "R4"]
after: [4]
assignee: ""
refined: false
hitl: false
risk: medium
severity: P2
---

# env-down ends red and leaves the hostname's A and AAAA records pointing at a dead ALB

## Description

After an ordered, otherwise clean teardown, the A and AAAA alias records for the fixed hostname stay in the bootstrap zone, so `env-down` exits 3 and the job fails. The next `env-up` then fails its DNS stage until a person deletes the records by hand. An environment that expires on its own therefore never ends clean, and every drill that recreates an environment (stories 6 to 9) trips on it. After teardown the zone should hold no record for the hostname, and `env-down` should end green.

## Reproduction

1. Dispatch `env-up`, then `env-down` (any expiry), with the external-dns settings in `deploy/charts/platform/values-eks.yaml` (`policy: sync`, `registry: txt`).
2. Read the run with `scripts/run-summary.sh <run id>`.
3. Actual: `dns-records` stage prints "the zone still holds records for ticketscope.heffernan.dev (external-dns did not delete them)", lists `A` and `AAAA`, `eks-teardown.sh` exits 3. Run 44579422898 (2026-11-19) shows it; so do runs 44570082818 and 44565053510. Expected: no record remains and the job is green.
4. Also seen on the tracer run (2026-11-17): no TXT ownership records existed in the zone either.

## Cause Hypothesis

external-dns writes no TXT ownership records for alias records at the zone apex, so under `policy: sync` it does not consider the A and AAAA records its own and never deletes them. It may be the registry's handling of alias records (the tracer notes point at v0.23) or a domain-filter or owner-id setting. Not verified.

## Acceptance Criteria

1. **The hostname's records are gone after teardown**
   **Given** an environment brought up by `env-up`
   **When** `env-down` runs, dispatched or by expiry
   **Then** the zone holds no A or AAAA record for the fixed hostname, the `dns-records` stage passes, and the job is green (R3, R4)
2. **The next environment comes up with no hand step**
   **Given** that teardown
   **When** `env-up` runs again with the same hostname
   **Then** its DNS stage passes with no record deleted by hand, and the hostname and certificate are the same as before (R2)
3. **Bootstrap stays untouched**
   **Given** the fix
   **When** it deletes or lets external-dns delete the records
   **Then** only the environment's own hostname records are affected, and the zone, its NS and SOA records and the certificate validation records are never listed for deletion, shown by a test on the filter (R3)
4. **Tests cover the condition found and fixed**
   **Given** the test suite
   **When** it runs
   **Then** a test that fails on the defect and passes on the fix covers the reproduction, and one covers a zone that cannot be read, which still fails the job
5. **Or: no change is needed, with proof**
   **Given** the reproduction
   **When** it is run on the current code
   **Then** the records are removed, with the evidence in Notes; this supersedes 1 to 4

## References

- parent — `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md`, requirements R2, R3, R4
- plan — `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-env-down-tears-down-in-order-finds-nothing-left-and-expires-plan.md`, Implementation Notes (live record 2026-11-19)
- deferred — `_bmad-output/initiative-ticketscope/deferred-work.md`, the two external-dns entries (2026-11-17 tracer run and 2026-11-19 env-down)
- run — GitHub Actions run 44579422898 (`env-down`)

## Notes

- Decision: A bug in this epic, before story 6, not part of 6, because every environment 6 to 9 creates would otherwise end red and need a hand delete (user, "take your picks", 2026-11-19).
- Open question: Whether to make external-dns write ownership records or have `env-down` delete the two records explicitly. Settled in the fix; the agent's AWS access stays read-only, so the delete runs in the workflow under the deploy role, and that role's permission is added in the same change.
