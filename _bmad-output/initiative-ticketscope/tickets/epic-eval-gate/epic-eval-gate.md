---
type: epic
title: "Retrieval is scored on every PR and regressions block the merge"
parent: initiative-ticketscope
covers: [R6, R7]
sources: []
companions: []
after: []
refined: true
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

## Requirements

- R1 (parent R6): Labelled duplicate pairs are derived deterministically from the pinned snapshot's in-subset duplicate links and committed per snapshot version. It is met when the committed pairs file regenerates byte-identical from the snapshot, with its pair counts reported for short and log-heavy queries.
- R2 (parent R6): An eval job scores every available mode in the core registry through the real Postgres adapter as the read-only role. It reports Recall@1, Recall@5, Recall@10, MRR@10 and p95 latency, split short versus log-heavy. It is met when the job on kind scores keyword over the full pair set, and a newly registered mode is scored with no change to the job.
- R3 (parent R7): The eval runs on every PR as a required check. A Recall@10 or MRR@10 regression against the committed baseline blocks the merge, unless the same diff updates the baseline. It is met when a deliberately regressing PR fails the check, and passes once its diff updates the baseline.
- R4 (parent R7): The README results table is generated from CI output and committed as-is, whatever it shows. It is met when a check fails if the README table differs from the table rendered from the committed CI results.

## Constraints

- **Hit definition:** a query's relevant set is its duplicate cluster, the connected component over in-subset duplicate links, minus the query itself. Recall@k counts a hit when any member is in the top k. MRR@10 uses the first member's rank, and 0 past 10. The query issue is excluded from its own results (core's `Retriever.search` takes `exclude`).
- **Queries:** one query per in-subset duplicate link, from its duplicate side; 10,473 on snapshot 2026.11.1 (10,164 short, 309 log-heavy). The full set is scored on every PR.
- **Metrics:** Recall@10 and MRR@10 are gated; Recall@1 and Recall@5 are reported, not gated. p95 latency is reported and never gated (spine AD-12).
- **Gate tolerance:** 0.005 absolute, per metric, per mode, per ticket kind.
- **Baseline lineage:** `eval/baseline.json` records the snapshot version, the embedding model id and the preprocessing version. A PR that changes any of them, or intentionally moves scores, updates it in the same diff (spine AD-12).
- **Kind floor:** a change to the kind threshold reports the pairs by kind. Below about 200 log-heavy pairs, the change needs the author's decision before it merges (spine AD-12).
- **Determinism:** pair derivation is a pure core function of the snapshot; the same snapshot always yields the same file.
- **Workflow:** `eval.yml` runs on PRs through `_kind-deploy.yml`, then the eval Job in the `ticketscope` release, then the gate and a results artifact (spine AD-13, AD-17). Making it a required check is a person's step in GitHub branch protection.

## Done when

- Labelled duplicate pairs are committed as `eval/pairs/<snapshot>.jsonl`, with the set's size reported separately for short and log-heavy tickets (R6).
- The eval job scores keyword retrieval by Recall@k, MRR and p95 latency, split by ticket kind. It picks up any mode registered in the core registry with no change to the job, and excludes each pair's query issue from its own results (R6).
- The eval runs on every PR. A PR that lowers Recall@k or MRR below `eval/baseline.json` fails the required check, unless that PR updates the baseline in the same diff (R7).
- The README results table is generated from CI output and committed as-is (R7).
- Delivered on the cluster, with an integrated check passing in CI.
- Waiver W-001 is remediated: epic-search-baseline's six superseded GitHub-era criteria are recorded as superseded in the ticket tree, and a fresh epic 1 trace honours them (`_bmad-output/test-artifacts/gate-waivers.md`).

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
- Decision: Refined with Sofia's picks (user, "take your picks", 2026-11-08). Hits count the query's whole duplicate cluster. Recall@10 and MRR@10 are gated; Recall@1 and Recall@5 are reported. The full pair set is scored on every PR. The gate tolerance is 0.005. p95 is reported, never gated, which closes epic-search-baseline's open search-latency row.
- Decision: The log-heavy margin was checked against story 1.5's final kind threshold of 3: there are 309 log-heavy pairs, above the floor of about 200 (Release `snapshot-2026.11.1`; `core/derive.py:16`) (2026-11-08).
- Decision: Waiver W-001's remediation is a Done when line, made as a ticket-tree and TEA tooling change outside the build loop, not a product story (user, 2026-11-08).
- Decision: Stories land through a branch and a PR each, so the required check gates them. PR #20 merges before the epic starts (user, 2026-11-08; epic-search-baseline retro actions 6 and 11).
- Decision: Every story's verify names the R ids it proves (epic-search-baseline retro action 7; user, 2026-11-08).
- Assumption: The query text is the query issue's title and description, the text a triage engineer would paste; comments are left out.
- Assumption: The README table is rendered from the committed `eval/baseline.json`, which is the CI results artifact committed by a baseline update. The README check compares against that render.
