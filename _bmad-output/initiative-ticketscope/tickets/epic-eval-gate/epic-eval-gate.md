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

Labelled duplicate pairs are derived from epic 1's corpus snapshot and committed per snapshot version.

- **Scoring.** An eval job scores every mode in the core retriever registry, through the real Postgres adapter and as the read-only role. It reports Recall@k, MRR and p95 latency, split short versus log-heavy.
- **Gate.** It runs on every PR in its own workflow. Recall@k or MRR regressions against a committed baseline block the merge; p95 is reported, not gated.
- **README table.** The results table is generated from CI output.

Epic 3's modes are scored by it, and epic 8 publishes its table.

## Outcome

A reviewer sees retrieval scores that CI produced on labelled data, and a regressing PR cannot merge (initiative R6, R7; brief Success Criteria 1).

## Done when

- Labelled duplicate pairs are committed as `eval/pairs/<snapshot>.jsonl`, with the set's size reported separately for short and log-heavy tickets (R6).
- The eval job scores keyword retrieval by Recall@k, MRR and p95 latency, split by ticket kind. It picks up any mode registered in the core registry with no change to the job, and excludes each pair's query issue from its own results (R6).
- The eval runs on every PR. A PR that lowers Recall@k or MRR below `eval/baseline.json` fails the required check, unless that PR updates the baseline in the same diff (R7).
- The README results table is generated from CI output and committed as-is (R7).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Adding dense and hybrid modes belongs to epic-hybrid-retrieval; this epic only scores them.
- There is no target score: the gate blocks regressions, not misses (brief Success Criteria 1). p95 latency is reported, never gated.
- This is the last epic on the brief's cut list. A cut drops only the required merge check (R7); the eval job, the baseline and the README table (R6) are still built.

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R6, R7)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1, AD-2, AD-4, AD-6, AD-7, AD-8, AD-12, AD-17, AD-19, AD-22

## Notes

- Waits on epic-search-baseline because: it needs the schema-v2 Mojang Jira corpus snapshot with resolutions, comments and duplicate links (story 1.13), the core retriever registry, and the CI workflow layout.
- Decision: Adopted the architecture spine. Pairs come from the snapshot, eval calls the core registry rather than the API's mode parameter, and p95 is reported but not gated (user, 2026-11-05).
- Decision: A cut of this epic drops only the blocking check; R6's eval job and table survive for epics 3 and 8 (user, 2026-11-06).
- Decision: The corpus is now Mojang bug-tracker issues from The Public Jira Dataset v7 (epic-search-baseline spike 12). Labelled pairs come from the Jira duplicate links in story 1.13's schema-v2 snapshot: spike 12 measured 10,466 in-subset pairs (10,162 short, 304 log-heavy at threshold 3), and the author judged 9 of 10 sampled pairs real duplicates. The log-heavy margin is thin; refinement should check it against story 1.5's final kind threshold (user, 2026-11-06).
