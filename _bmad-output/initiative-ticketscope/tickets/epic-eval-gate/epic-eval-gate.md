---
type: epic
title: "Retrieval is scored on every PR and regressions block the merge"
parent: initiative-ticketscope
covers: [R6, R7]
sources: []
companions: [_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md]
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

- **Hit definition:** a query's relevant set is its duplicate cluster, the connected component over every in-subset `duplicate_links` entry of every issue, in both directions, minus the query itself. Recall@k counts a hit when any member is in the top k. MRR@10 uses the first member's rank, and 0 past 10. Overall metrics are computed over all queries, not as the mean of the two kind means. The query issue is excluded from its own results (core's `Retriever.search` takes `exclude`).
- **Queries:** one pair per duplicate issue whose `core.duplicate_target` is in the snapshot, counted under the duplicate issue's kind (spine AD-26); 10,473 on snapshot 2026.11.1 (10,164 short, 309 log-heavy), matching the Release notes. The full set is scored on every PR.
- **Metrics:** Recall@10 and MRR@10 are gated; Recall@1 and Recall@5 are reported, not gated. p95 latency is reported and never gated (spine AD-12).
- **Gate tolerance:** 0.005 absolute, per metric, per mode, per ticket kind, inclusive: a drop of exactly 0.005 passes.
- **Mode-set changes:** a gated mode missing from the run fails unless the same diff updates the baseline; a mode new to the run passes and is reported.
- **Baseline provenance:** a changed `eval/baseline.json` must equal the PR's own CI results within the tolerance, so the baseline and README only carry numbers a CI run produced.
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
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1, AD-2, AD-4, AD-6, AD-7, AD-8, AD-12, AD-17, AD-19, AD-21, AD-22, AD-26
- test design — _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md, Test Coverage Plan (the Owner column names the story that writes each test), Independent Oracles, Risk Assessment (R-001, R-003, R-005)

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
- Decision (was an assumption, confirmed by user 2026-11-08): The query text is the query issue's title and description, the text a triage engineer would paste; comments are left out.
- Decision (was an assumption, confirmed by user 2026-11-08): The README table is rendered from the committed `eval/baseline.json`, which is the CI results artifact committed by a baseline update. The README check compares against that render.
- Decision: Stories planned (5 entries). Story 1, "Tracer: keyword is scored on kind and CI uploads the results", is the tracer bullet: snapshot to pairs, then the eval Job on kind, then eval.yml's artifact. The stories run in one lane, because each touches jobs.eval, the eval Job or eval.yml. The refactor sweep closes the epic (user, 2026-11-08).
- Decision: Story 1 scores against the linked target only. Story 2 replaces that with the Hit definition's cluster relevance, so the Hit definition binds from story 2 onward (user, 2026-11-08).
- Decision: The gate (story 3) is the least certain story, but it needs story 2's per-kind metrics, so story 2 stays second (user, 2026-11-08).
- Decision: Kind floor: the gate fails below 200 log-heavy pairs unless `eval/baseline.json` carries a `kind_floor_decision` with the author's dated reason (user, 2026-11-08).
- Decision: `eval/baseline.json` is the full CI results JSON, so it carries lineage and every reported metric for the README table (user, 2026-11-08).
- Decision: No separate closing integrated-check story. `eval.yml` on kind is this epic's integrated check, and every story keeps ci.yml's integrated-check passing (user, 2026-11-08).
- Decision: Waiver W-001's remediation is checked at this epic's closure; owner Dillon, per the waiver (user, 2026-11-08).
- Decision: Story 1 is likely over 800 added lines. It is flagged for the independent review rather than split further (epic-search-baseline retro, finding Z4) (user, 2026-11-08).
- Decision: The TEA test design `test-design-epic-2.md` is adopted as a companion (PR #21). Each story writes the tests the design assigns it, and its Proposed Story Updates are applied to stories 1–5 (user, 2026-11-08).
- Decision: The pair rule follows spine AD-26: one pair per duplicate issue whose `core.duplicate_target` is in the snapshot. The earlier "one query per in-subset duplicate link" wording contradicted AD-26 and is replaced. The counts are unchanged (test design C-1; user, 2026-11-08).
- Decision: The test design's clarifications are settled as stated. The cluster uses every in-subset link in both directions (C-2). A missing gated mode fails unless the same diff updates the baseline, and a new mode passes and is reported (C-3). The tolerance is inclusive (C-4). README numbers use three fixed decimals (C-5) (user, 2026-11-08).
- Decision: A changed `eval/baseline.json` must equal the PR's own CI results within the tolerance (test design R-004) (user, 2026-11-08).
- Decision: Before story 1's build, a `bmad-tea-automate` red-mode session commits the hand-computed oracle fixture and failing P0 tests; before story 2's build, it adds the cluster oracle. The independent review on story 1 checks that the oracle fixture is unchanged since its red commit (test design R-005) (user, 2026-11-08).
