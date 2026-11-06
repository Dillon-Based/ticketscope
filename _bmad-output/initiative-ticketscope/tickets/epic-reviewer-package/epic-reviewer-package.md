---
type: epic
title: "A reviewer gets ticketscope in 5 minutes"
parent: initiative-ticketscope
covers: [R12, R13]
sources: []
companions: []
after: []
refined: false
risk: low
---

# A reviewer gets ticketscope in 5 minutes

## Description

The README has an architecture diagram, epic 2's CI eval table with epic 3's final numbers, a recorded clip of Claude Desktop using ticketscope from epic 6, a trace screenshot from epic 4, and two or three decision records. Every supported claim has a backed row in the claims ledger, and the wording follows the claim discipline.

## Outcome

A hiring manager verifies the project's three claims from the README within 5 minutes (initiative R12, R13; brief Success Criteria 4, 6).

## Done when

- The README holds the architecture diagram, the CI eval table, the clip, the trace screenshot and two or three decision records (R12).
- Every claim the README makes has a claims-ledger row backed by a repo or CI record (R13).
- The README passes the claim-discipline check: 'a personal project, deployed and operated on Kubernetes', never production, and no 'vector database' without a ledger row (initiative Constraints).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Generating the eval table belongs to epic-eval-gate; this epic places it.
- Out: handover work (initiative Boundaries).
- Touch point: the author's claims ledger — rows added outside this repo; owner: epic-reviewer-package

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R12, R13)

## Notes

- Waits on epic-hybrid-retrieval because: the CI table needs the final keyword, dense and hybrid numbers.
- Waits on epic-eks-environment because: it needs the live URL and the recorded CloudNativePG drills.
- Waits on epic-mcp-oauth because: the clip records an authenticated Claude Desktop session. If epic 6 is cut, this edge is dropped and the clip is unauthenticated.
