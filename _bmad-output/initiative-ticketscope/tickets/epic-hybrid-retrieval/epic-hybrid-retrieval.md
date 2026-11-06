---
type: epic
title: "Dense and hybrid retrieval, scored against keyword"
parent: initiative-ticketscope
covers: [R2, R6]
sources: []
companions: []
after: []
refined: false
risk: medium
---

# Dense and hybrid retrieval, scored against keyword

## Description

Issues are embedded with a small CPU model into an embedding column and index that this epic owns in pgvector. The retrieval API offers dense and hybrid modes beside keyword, under epic 1's contract and span conventions. Epic 2's gate scores all three in CI, and the results are published whatever they show. The model's CPU and memory needs set the chart values that epic 5 sizes nodes for, and the final numbers feed epic 8.

## Outcome

The eval table compares keyword, dense and hybrid retrieval on short and log-heavy tickets, testing the brief's hybrid hypothesis (initiative R2, R6).

## Done when

- Every ingested issue has an embedding from the chosen CPU model in pgvector (R2).
- A vague query and a log-heavy query each return ranked issues with outcomes in the dense and hybrid modes (R2).
- The CI eval table shows keyword, dense and hybrid side by side, split by ticket kind, and is published whatever it shows (R6).
- The model's CPU, memory and embedding-time needs are recorded in the chart values on kind.
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Scoring and the gate belong to epic-eval-gate. The API contract and span contract are epic-search-baseline's; this epic extends them and does not change them.
- Out: model fine-tuning and any second vector store (initiative Boundaries).

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R2, R6)

## Notes

- Waits on epic-search-baseline because: it needs the pgvector extension, the retrieval API's mode parameter and the span contract.
- Waits on epic-eval-gate because: the eval job and CI gate score the new modes.
