---
epic: epic-eval-gate
date: 2026-11-09
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: epic-eval-gate

## Epic summary

Epic 2, "Retrieval is scored on every PR and regressions block the merge" (covers R6, R7 of the initiative; epic requirements R1 to R4). Criteria are declared: the epic file has Requirements and Done when.

| Ticket | Title | Status | Range (from the plan's `baseline_revision`) |
|---|---|---|---|
| 2.1 | Tracer: keyword is scored on kind and CI uploads the results | done | `42ac66f..7ea485a` (6 commits; PR #24 plus unrelated #25, #26 that merged in the window) |
| 2.2 | Scores count the whole duplicate cluster, split by ticket kind | done | `7ea485a..9a62dbc` (PR #27) |
| 2.3 | A regressing PR cannot merge | done | `9a62dbc..17c3dd1` (PRs #28 and #29, the baseline commit) |
| 2.4 | README results table is generated from CI output | done | `17c3dd1..d2313e9` (PR #30) |
| 2.5 | Refactor sweep | done | `d2313e9..3fe91b2`, inferred: the plan has no `baseline_revision` (PR #31) |

- Unfinished tickets when the retro was asked for: 2.1 and 2.3 were at `built` (state review) and 2.5 was `planned`, although PRs #24, #28 and #31 had merged. At the user's instruction Sofia marked all three done (commit `684fe4c`, branch `worktree-mark-epic2-done`). `pending_tickets` is now empty (5 of 5 done). The retro was run from that branch, so main still shows the old statuses until the branch merges.
- The ranges are the evidence of record. The 2.1 range also contains PRs #25 (ATDD red scaffold for 2.2) and #26 (loop plugins), which are not 2.1 work. 2.5's real plan is `_bmad-output/initiative-ticketscope/plan-2-5-refactor-sweep.md` (status `built`).
- **Evidence available:** epic file; all five tickets' entries; four plan files in the tree plus the 2.5 plan outside it; `git_evidence.py` for all five ranges; `test-design-epic-2.md` (companion); the epic 2 trace (`traceability-matrix-epic-ticketscope--e2.md`, `gate-decision-epic-ticketscope--e2.json`); `gate-waivers.md`; `deferred-work.md`; the epic 1 retrospective; the GitHub PR list, run list and branch protection.
- **Evidence missing:** no session logs, so process lessons cover only what the plans record. No run folders (`<type>-*/`) exist in the epic folder. The `bmad-review` lenses were not run over the epic diff (see Narrowing).
- **Narrowing:** Phase 2's diff-scope review is a read of the plans' own review triage logs plus the checks below, not a fresh multi-lens pass. Architecture delta is limited to `lint-imports` (7 contracts kept). Duplication was checked by grep for the repeated constants and helpers the plans name.

## Findings

Each finding has a source and two dispositions: this instance / what would prevent the next.

### Spec-to-implementation reconciliation

- **F1. Done when line 6 is not met: W-001's remediation did not happen.** The epic asks that the six superseded epic 1 criteria "are recorded as superseded in the ticket tree" and that "a fresh epic 1 trace honours them" (`epic-eval-gate.md`, Done when). Evidence against: the epic 1 story plans for 1.3 (`story-ingest-publishes-a-versioned-corpus-snapshot-plan.md`) and 1.14 (`story-derive-jira-outcome-and-kind-in-core-plan.md`) contain no "superseded" text, and the only hit in the 1.4 plan (`story-derive-kind-and-outcome-in-core-plan.md:94`) is about a kind threshold, not these criteria. The epic 1 gate decision was last committed in `5f2844b`, before this epic's work, and is still `WAIVED` by W-001 (`gate-decision-epic-ticketscope--e1.json:12,28`). The epic Notes record that it is "a ticket-tree and TEA tooling change outside the build loop" with owner Dillon, checked at closure. *This instance:* fix now, outside the build loop (action 1). *Prevention:* a Done when line that depends on non-story work needs a ticket or an owner dated in the epic file, or the build loop will never see it.
- **F2. R1 to R4 are demonstrated.** R1: the pairs file regenerates byte-identical with counts 10,473 / 10,164 / 309 (`2.1 plan` Implementation Notes and Verification; `eval/pairs/2026.11.1.jsonl`). R2: keyword is scored per kind with Recall@1/5/10, MRR@10 and p95 in `eval/baseline.json`; a fake second mode is picked up without job changes (2.2 I/O matrix). R3: `gate.py` plus `eval / deploy` as a required status check on main (branch protection API: contexts `checks`, `integrated-check / deploy`, `eval / deploy`). R4: `scripts/render_readme_table.py --check` exits 0 here, wired into `ci.yml`'s `checks` job. Accept, nothing to fix.
- **F3. The R3 proof "a deliberately regressing PR fails the check, and passes once its diff updates the baseline" has no recorded end to end run.** The 2.3 plan's decision moved the worsening-PR run to a follow-up, and its Manual checks ("Throwaway PRs ... record the run URLs") are not recorded anywhere I could find. The gate logic is covered by the unit decision table (`tests/unit/test_eval_gate.py`) and the trace gives R3 FULL partly through live records at `424291f`; the trace itself caps the epic at CONCERNS for this reason (`gate-decision-epic-ticketscope--e2.json`: "R3 ... covered in part only by recorded live verification"). *This instance:* defer, as action 3. *Prevention:* when a decision moves a ticket's end to end proof to a follow-up, name the follow-up ticket.
- **F4. Plan filing of 2.5.** The real plan sits outside the tree's plan convention (`plan-2-5-refactor-sweep.md`, no `ticket` link in the epic folder). When `tickets.py mark` ran for 2.5 it created a 5-line stub plan, `tickets/story-refactor-sweep-plan.md`, with `status: done` and no baseline. The tree is consistent, but the review log and Auto Run Result for 2.5 are not beside the ticket. *This instance:* fix now (action 2). *Prevention:* the loop should write plans at `<type>-<slug>-plan.md` beside the entry for entries without a file.

### Cross-ticket and boundary lenses

- **F5. Cross-reload rank drift is unexplained but below the gate.** After one forced reload, 2 of 10,473 first-member ranks moved (query 258858: 4 to 5; 489515: 5 to 6), shifting overall Recall@5 by about 0.0001 and MRR@10 by about 8e-6 (2.2 plan, "Additional diagnostic"). A controlled same-snapshot reload then reproduced the second state exactly. The committed baseline carries the later value (MRR@10 0.5504942793 in `eval/baseline.json`; the first local run had 0.5505022363), which is well inside the 0.005 tolerance. The plan rejected it as `maybe-false`. *This instance:* accept, recorded so later retros stop re-flagging it. *Prevention:* none beyond the tolerance; if epic 3 adds vector indexes, re-run the reload comparison for each new mode.
- **F6. The gate's stale `base.sha` on reruns.** Already in the ledger: `deferred-work.md:21-22` (source plan 2.3). A rerun after main advanced can count main's baseline update as the PR's. *This instance:* defer, already tracked. *Prevention:* none needed now.
- **F7. The branch protection does not apply to administrators.** `enforce_admins.enabled` is false (branch protection API), so "a regressing PR cannot merge" holds for non-admin merges only. For a single-owner repo this matters in practice: the owner can merge past a red `eval / deploy`. *This instance:* defer (action 4, a user decision). *Prevention:* decide whether R3 means "blocks everyone"; if yes, enable it.
- **F8. Eval Job time budget settled.** The 2.1 review deferred "the 45-minute `_kind-deploy.yml` job limit can cut the eval hook off" pending a first CI run (2.1 plan, Review Triage Log row 1). The latest `eval / deploy` job ran 14 minutes 37 seconds (2026-11-09 01:01:05 to 01:15:42Z, run 42543269379), well inside the limit. Closed, accept.

### Duplication map

- **F9. Duplicates fixed by the sweep, remaining copies are intentional.** The chart snapshot-pin parser now lives once in `ticketscope.adapters.release.read_snapshot_pin` (2.5, `3fe91b2`), and `jobs.eval.gate.KINDS` derives from the scorer (`gate.py:27`). `scripts/render_readme_table.py:23` keeps its own `KINDS` by design (it must run on standard-library Python in CI), and the oracle tests keep independent tuples by design (`test_eval_cluster_oracle.py:36`, `test_eval_kind.py:54`). Accept. The wrappers left in `scripts/derive_pairs.py` and `tests/target.py` were reviewed and rejected by the 2.5 review as harmless.

### Size growth

- **F10. No god-class.** The largest new source modules are `gate.py` (242 lines), `score.py` (159) and `render_readme_table.py` (130). The largest churn is data: `eval/pairs/2026.11.1.jsonl` (10,473 lines, regenerated once in 2.2) and `eval/baseline.json` (41,934 lines). The epic Notes flagged 2.1 as likely over 800 added lines for independent review; the pairs file alone is 10,473 added lines (`r1` evidence for `6281014`), and I did not count the rest. Accept.
- **F11. `eval/baseline.json` is 41,934 lines because it embeds `first_member_ranks` for every query.** It is the full CI results JSON by decision (epic Notes), which keeps README rendering and the provenance check simple but makes a baseline update a very large diff to review. *This instance:* accept. *Prevention:* if reviewers start skimming baseline diffs, move the rank list to the artifact and keep only metrics in the baseline.

### Process lessons

- **F12. Status lagged the merges.** All three plans that stayed at `built` say "ticket plan status preserved for the orchestrator" or "`tickets.py mark` was not run" (2.2, 2.4, 2.5 Auto Run Results). The orchestrator did not mark done after PRs merged, so 2.1, 2.3 and 2.5 stayed unfinished until this retro. *This instance:* fixed by `684fe4c`. *Prevention:* the PR-per-story loop plugin (#26) should mark the story done on merge, or the retro prompt should be run only after a status check (action 5).
- **F13. Plan criteria did not name requirement ids until a re-trace failed.** Epic 1's action 7 asked for R ids on every criterion, and this epic's Notes repeated it ("Every story's verify names the R ids"), yet the first epic 2 trace failed because "plan criteria carry no R ids" (commit message of `c8987c9`). They were added afterward (`8d772e0`). The requirement was recorded twice and not enforced by the plan template. *Prevention:* make the build's plan template reject acceptance criteria without `(R<n>)` (action 6).
- **F14. TEA red-then-green worked.** The oracle fixture was committed red before stories 2.1 and 2.2 (PRs #23, #25) and a pin test now guards its bytes (`tests/unit/test_eval_oracle_pinned.py:34`). The independent second retrieval pass in 2.2 (all 10,473 ranks recomputed without the scorer) caught nothing wrong but gives the baseline a real oracle. Keep.
- **F15. Independent review of story 2.1 is not evidenced.** The epic Notes say 2.1 "is flagged for the independent review" (epic-search-baseline retro action 9). Its plan shows `review: quick`, `lenses_ran: ['quick']`, 7 findings, none from a second reviewer. 2.2 got a four-lens follow-up. *This instance:* accept, since 2.2 added the independent full-corpus second pass and `derive_pairs.py --check` regenerates the pairs file byte-identical in CI. *Prevention:* the size trigger in epic 1 action 9 was not wired into the loop (see follow-through).

## Behavior verification

Runtime behavior changed (CI scoring, gate, README), so I exercised what could be exercised from the worktree at `684fe4c`; I did not run the kind cluster.

- `python3 scripts/render_readme_table.py --check`: exit 0, "README results table matches the baseline".
- `eval/baseline.json`: lineage `2026.11.1` / embedding model none / preprocessing `pre1.kind2-t3.outcome3`; modes `keyword` only; no `kind_floor_decision` (not needed: 309 log-heavy pairs, above the floor of 200). Keyword overall Recall@10 0.7706, MRR@10 0.5505 over 10,473 pairs; log-heavy Recall@10 0.8220, MRR@10 0.6789 over 309.
- `uv run pytest tests/unit`: 895 passed, 17 skipped (the helm-gated tests; the 2.5 plan recorded 910 passed on a machine with helm).
- `uv run lint-imports`: 7 contracts kept, 0 broken.
- CI: `eval.yml` succeeded on PR #31 (run 42532155256) and #32 (run 42543269379); the baseline commit came from run 42526527850. Not exercised here: the kind cluster eval Job, a regressing PR (F3), and a gate run against a stale base (F6).

## Previous-retro follow-through

Source: `epic-search-baseline-retrospective.md`, Action items 1 to 11.

1. Push the gated work and get `integrated-check` green (user/operator): landed. PR #20 merged (`75efbfc`); CI is green on every later PR.
2. Link criteria to requirements (Sofia): landed for epic 2 (`8d772e0`, in `c8987c9`); no evidence found for epic 1's leaves.
3. Retire superseded criteria (Sofia, test design owner): no evidence found. This is F1.
4. Test hardening (dev loop): landed, per the epic 1 retro's own status note and `no-sleep` test (`tests/unit/test_no_sleep_in_tests.py`, 2.5).
5. Fix the 405 `Allow` header (dev loop): landed per the epic 1 retro's status note; no new evidence checked.
6. Loop policy, PR per story (user): partly landed. PRs #24 to #31 were one per story and the plugin is `8f61ee4`/#26; no evidence found that `rollback_on_failure` is on (`.bmad-loop/policy.toml.bak:167` shows `false`, and I did not find the live policy).
7. Ticket template, R ids on criteria (Sofia): not landed in time; F13.
8. Recalibrate story-size signals (user): no evidence found; I did not look for a config change beyond the loop policy file.
9. Trigger independent review by diff size (user): no evidence found; F15.
10. Re-score the test suite (TEA): landed. `test-review-system.md` was re-scored after remediation at 71/100, Request Changes (`5f8f034`).
11. Merge PR #20 (user): landed (`75efbfc`).

## Action items

All are proposed; none was applied.

1. **Remediate W-001** (spec reconciliation / TEA tooling): record the six criteria (1.3 AC-1..3, 1.4 AC-1..2, 1.14 AC-2) as superseded in the epic 1 plans, then re-trace epic 1 so the gate honours them. Owner: Dillon (per the waiver), through `bmad-agent-po`. Closes F1.
2. **Re-file the 2.5 plan**: move `plan-2-5-refactor-sweep.md`'s content into `tickets/story-refactor-sweep-plan.md` (keeping `status: done`) and delete the old file. Owner: Sofia. Closes F4.
3. **Record the R3 end to end run**: one throwaway PR that regresses keyword fails `eval / deploy`, and passes once the diff updates the baseline; record the run URLs in the 2.3 plan or the trace's live records, or add a static test that reads the branch protection and asserts the gate step exit code. Owner: Dillon / TEA. Closes F3 and lifts the trace's CONCERNS cap.
4. **Decide on `enforce_admins`**: turn it on, or record that R3 binds non-admins only. Owner: Dillon. Closes F7.
5. **Mark stories done on merge**: have the PR-per-story plugin run `tickets.py mark ... done` after the PR merges, or gate the retro on a status check. Owner: user (bmad-loop). Closes F12.
6. **Enforce R ids in the plan template**: reject acceptance criteria with no `(R<n>)`. Owner: Sofia / Smithy (toolsmith). Closes F13 and epic 1 action 7.
7. **Carry the unlanded epic 1 process actions** (6's `rollback_on_failure`, 8, 9) into the loop config work, or drop them explicitly. Owner: user. Closes F15 follow-through.
8. **Merge `worktree-mark-epic2-done`** (statuses done plus this retro) so main reflects the tracker. Owner: user.

## Decision records

Candidates tested against "hard to reverse, surprising without context, a real trade-off, not already recorded". No `adr-*.md` exists in the repository and there is no `docs/decisions/` folder.

- **Approved and written: `adr-eval-baseline-is-ci-output-only.md`.** Context: the gate must trust the numbers it compares against. Decision: `eval/baseline.json` is the full CI results JSON, a changed baseline must equal the PR's own CI results within 0.005, and the first baseline was committed in a follow-up PR (#29) because it cannot exist before a CI run produces it. Why: the plan's Boundaries and Design Notes (2.3 plan, `b26574b`, `17c3dd1`). Surprising without context (the gate passes with "no baseline" for one PR) and hard to reverse (README table and gate depend on its shape).
- **Approved and written: `adr-hit-is-the-whole-duplicate-cluster.md`.** Decision: a query's relevant set is its whole duplicate cluster, computed at pair derivation and stored in the pairs file, not at eval time. Why: cluster links exist only in the snapshot, not the loaded corpus (2.2 plan, Design Notes; `9a62dbc`). Changing it changes every score and the baseline.

Both approved by the user on 2026-11-09 and written: `docs/decisions/adr-eval-baseline-is-ci-output-only.md` and `docs/decisions/adr-hit-is-the-whole-duplicate-cluster.md`.

## Acceptance verdict

**accepted-with-open-items** (criteria declared: epic Requirements R1 to R4 and Done when). The user chose this verdict on 2026-11-09, overriding the machine verdict of **rejected**. No ticket is unfinished, so the unfinished-ticket rule does not apply. The machine verdict was rejected for one reason only: Done when line 6, the W-001 remediation, is not met (F1). Everything else is met or tracked:

- R1 to R4 are demonstrated (F2); the epic 2 trace gate is CONCERNS (P0 100%, P1 100%, overall 100%), capped only by R3's reliance on live records (F3).
- "Delivered on the cluster, with an integrated check passing in CI": met. `integrated-check / deploy` and `eval / deploy` are green on PRs #31 and #32.
- Open items (non-blocking if accepted): F3, F6, F7, F11, and the process actions 5 to 7.

F1 is carried as the open item, which matches how epic 1 was closed. Closing the epic is Sofia's call, confirmed by the user.

## Open questions

- Does R3 mean "blocks everyone" or "blocks non-admin merges"? (F7)

## Follow-up applied after the retro (2026-11-09, Sofia)

- **Action 2 done (F4):** the 2.5 plan content now lives in `tickets/story-refactor-sweep-plan.md` with `status: done`; `plan-2-5-refactor-sweep.md` is removed.
- **Action 1 half done (F1):** each of the six superseded criteria now carries a dated "Superseded (waiver W-001)" note in the epic 1 plans for 1.3 (AC-1..3), 1.4 (AC-1..2) and 1.14 (AC-2). The criterion text is untouched. **Still open:** the fresh epic 1 trace that honours the notes is TEA's (`bmad-tea-trace`, gate type `epic`); until it runs, the epic 1 gate stays `WAIVED`.
- Not mine to change, still open: actions 3, 4, 5, 7 (Dillon / the loop config) and 6 (template change, toolsmith).
