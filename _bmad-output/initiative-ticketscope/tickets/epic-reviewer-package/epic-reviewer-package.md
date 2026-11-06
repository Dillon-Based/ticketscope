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

The README has:

- an architecture diagram
- epic 2's CI eval table, with epic 3's final numbers
- a recorded clip of Claude Desktop using ticketscope, from epic 6
- a trace screenshot, from epic 4
- epic 5's live URL and recorded CloudNativePG drills
- two or three decision records

Every supported claim has a backed row in the claims ledger, and the wording follows the claim discipline.

## Outcome

A hiring manager verifies the project's three claims from the README within 5 minutes (initiative R12, R13; brief Success Criteria 4, 6).

## Done when

- The README holds the architecture diagram, the CI eval table, the clip, the trace screenshot and two or three decision records (R12).
- Every claim the README makes has a claims-ledger row backed by a repo or CI record (R13).
- The README passes the claim-discipline check: "a personal project, deployed and operated on Kubernetes", never production, and no "vector database" without a ledger row (initiative Constraints).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Generating the eval table belongs to epic-eval-gate; this epic places it.
- If epic-eks-environment is cut, this epic records the CloudNativePG restore and failure drills on kind, and the README links the kind deployment through the tunnel.
- Out: handover work (initiative Boundaries).
- Touch point: the author's claims ledger — rows added outside this repo; owner: epic-reviewer-package

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R12, R13)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1, AD-2, AD-11, AD-12, AD-15, AD-18, AD-24; the spine's diagrams seed the README's architecture diagram

## Notes

- Waits on epic-hybrid-retrieval because: the CI table needs the final keyword, dense and hybrid numbers.
- Waits on epic-mcp-server because: it needs the end-to-end trace to screenshot, and the named tunnel the README links if epic 5 is cut.
- Waits on epic-eks-environment because: it needs the live URL and the recorded CloudNativePG drills. If epic 5 is cut, this edge is dropped and this epic records the drills on kind.
- Waits on epic-mcp-oauth because: the clip records an authenticated Claude Desktop session. If epic 6 is cut, this edge is dropped and the clip is unauthenticated.
- Decision: Adopted the architecture spine. If epic 5 is cut, this epic records the CloudNativePG drills on kind and links the tunnel deployment; it now waits on epic-mcp-server for the trace (user, 2026-11-05).
