---
id: 5
type: story
title: "Load the pinned snapshot with kind and outcome"
parent: epic-search-baseline
covers: [R2]
after: [12, 13, 14]
hitl: false
risk: medium
---

# Load the pinned snapshot with kind and outcome

## Description

The load job puts the real corpus into Postgres with each issue's kind and outcome, computed once in core (AD-8). It replaces story 1's fixture load in every environment, and CI on kind runs on the real snapshot from here on. Unit tests keep the fixture.

- **Pin.**
  - `values.yaml` pins the Jira snapshot version from story 13 and its SHA-256 checksum; it is a product default, not an environment fact (AD-25).
  - `load` downloads that Release asset and refuses one whose checksum differs.
- **Schema v2.** Story 13 already makes `load` read schema v2 snapshots; this story adds the derived kind and outcome.
- **What it stores.**
  - `load` is the only writer (AD-7). It stores every issue with the kind and outcome from story 14's Jira rules in core, replacing story 1's fixture kinds.
  - A unit test shows the computed kind equals each fixture issue's expected kind.
- **Kind threshold.** The builder sets the kind threshold from story 13's Jira snapshot. Spike 12 measured 304 log-heavy duplicate pairs at threshold 3, close to the 200 floor: re-measure before raising it. The PR shows 20 sampled issues from each side of the threshold, so a person can see the split reads right.
- **`corpus_meta`.**
  - `load` writes the row with the snapshot version, the embedding model id (none in this epic), the preprocessing version and `loaded_at` (AD-21).
  - The preprocessing version includes a derivation version from core. That version changes whenever the kind threshold or the outcome rule changes.
- **Idempotent.** When the snapshot, the model and the preprocessing version all match the row, `load` does nothing. A change to any one of them reloads.
- **Never half-loaded.** A reload swaps the corpus in one transaction. `api`, already serving on upgrade, sees the old corpus or the new one, never a mix.
- **Report.** The job log reports the issue count, the share of each kind and of each outcome, and the load time. The load time is checked against the 10-minute budget (stories 3 and 13).
- **Example queries.**
  - The builder picks one vague and one log-heavy query from the real snapshot. Each is committed in a golden-query file with the issue it should return.
  - Each entry records the query text, its kind, how it was chosen, its source issue, and its expected issue. The file records the snapshot version and the `k` it is checked at.
  - The expected issue must exist in the pinned snapshot and differ from the source issue, so the check can't pass by matching the query's own text. A unit test checks both.
  - If no vague query's expected issue ranks in the top-k under keyword, the file marks it a known keyword miss. Story 11 then reports that check without gating it.
  - The person approves them at this story's plan review.
  - Story 7's page check, story 10's sweep check and story 11's integrated check use them.

## Requirements

Verify: On kind in CI the load hook loads the pinned snapshot. Then:

- a SQL check finds no issue without a kind or an outcome,
- the job log reports each kind's and each outcome's share and a load time within 10 minutes,
- a helm upgrade with the same pin logs a no-op,
- a changed derivation version reloads.

A unit test shows a wrong checksum is refused and the old corpus stays in place.

## References

- parent — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md, sections Requirements (R2), Constraints (Jira outcome, Outcome precedence, Outcome terms, Kind rule, Example queries, Corpus scope)
- story 13 — the entry "Ingest publishes the Jira snapshot (schema v2)" in this epic's tickets.toml
- story 3 — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot.md, Description (Publishing, Load-time budget)
- spike 12 — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus-findings/findings.md, Findings for the replan
- story 1 — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind.md, Description (Snapshot)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-6, AD-7, AD-8, AD-12, AD-21, AD-22, AD-25
- test design — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md, rows owned by story 5; Mitigation Plans (R-004)

## Notes

- Decision: The preprocessing version in `corpus_meta` includes a derivation version from core, so a kind-threshold or outcome-rule change reloads (user, 2026-11-06).
- Decision: A reload swaps the corpus in one transaction; `api` never sees a partial corpus (user, 2026-11-06).
- Decision: The example queries live in a committed golden-query file with each query's expected issue, approved at this story's plan review (user, 2026-11-06).
- Epic-eval-gate's baseline records the preprocessing version (AD-12), so a derivation change shows up there as a baseline update.
- Decision: Replanned for spike 12: this story loads story 13's Mojang Jira snapshot with story 14's rules, and waits on 12, 13 and 14 instead of 3 and 4 (user, 2026-11-06).
