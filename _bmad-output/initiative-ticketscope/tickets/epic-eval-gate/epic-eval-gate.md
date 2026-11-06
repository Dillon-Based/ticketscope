---
type: epic
title: "Retrieval is scored on every PR and regressions block the merge"
parent: initiative-ticketscope
covers: [R6, R7]
sources: []
companions: []
after: []
refined: false
risk: high
---

# Retrieval is scored on every PR and regressions block the merge

## Description

Labelled duplicate pairs are extracted from the corpus that epic 1 stored. An eval job scores every retrieval mode the API offers by Recall@k, MRR and p95 latency, split short versus log-heavy. It runs on every PR in its own workflow, blocks regressions, and generates the README results table from CI output. Epic 3's modes are scored by it, and epic 8 publishes its table.

## Outcome

A reviewer sees retrieval scores that CI produced on labelled data, and a regressing PR cannot merge (initiative R6, R7; brief Success Criteria 1).

## Done when

- A labelled set of duplicate pairs exists, with its size reported separately for short and log-heavy tickets (R6).
- The eval job scores keyword retrieval by Recall@k, MRR and p95 latency, split by ticket kind, and picks up any new mode with no change to the job (R6).
- The eval runs on every PR, and a PR that lowers a score fails the required check (R7).
- The README results table is generated from CI output and committed as-is (R7).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Adding dense and hybrid modes belongs to epic-hybrid-retrieval; this epic only scores them.
- There is no target score: the gate blocks regressions, not misses (brief Success Criteria 1).

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R6, R7)

## Notes

- Waits on epic-search-baseline because: it needs the ingested corpus with labels and comments, the retrieval API's mode parameter, and the CI workflow layout.
