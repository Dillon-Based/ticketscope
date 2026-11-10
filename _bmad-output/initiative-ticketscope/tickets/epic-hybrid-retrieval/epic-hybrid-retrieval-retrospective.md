---
epic: epic-hybrid-retrieval
date: 2026-11-10
verdict: rejected
criteria: declared
headless: true
---

# Retrospective: epic-hybrid-retrieval (epic 3), Dense and hybrid retrieval, scored against keyword

## Epic summary

`tickets.py status` lists 8 tickets, all with `status: done` and `state: done`:

- 3.1 Tracer: dense search answers through /v1 on kind
- 3.2 Hybrid search fuses keyword and dense
- 3.3 (spike) Choose the embedding model
- 3.4 Embeddings load from a published Release asset
- 3.5 CI scores keyword, dense and hybrid side by side
- 3.6 Chart defaults carry the model's needs and the best mode
- 3.7 Refactor sweep
- 3.8 Integrated check on kind

`pending_tickets` is empty, and no ticket is still at `built`.

**Plan ranges.** Each range runs from the plan's `baseline_revision` to the next baseline, oldest first. The `git_evidence.py` pre-pass ran once per range.

| Ticket | Range | Commits | Files | Lines added |
| --- | --- | ---: | ---: | ---: |
| 3.1 | 6b6e234..684c8f4 | 1 (#36) | 43 | 2,761 |
| 3.2 | 684c8f4..90364f5 | 4 (#37, plus 3 unrelated: #38, #39, #40) | 22 | 716 |
| 3.3 | 90364f5..9e6b6e7 | 4 (spike commits and a merge of `origin/main`) | 4 | 706 |
| 3.4 | 9e6b6e7..e504101 | 3 (#42, #43, #44) | 27 | 1,938 |
| 3.5 | e504101..dd20e0c | 5 (#46, #48, #47, #49, plus epic 4's #45) | 28 | 85,911 (mostly `eval/baseline.json` ranks and epic 4 planning) |
| 3.6 | dd20e0c..6752efe | 2 (#50, #51) | 13 | 686 |
| 3.7 | 6752efe..3c0cddd | 1 (#52) | 13 | 289 |
| 3.8 | 3c0cddd..9c6efe0 | 1 (#54) | 4 | 261 |

The 3.8 range ends at `HEAD` and is inferred, not recorded. The whole epic is 6b6e234..9c6efe0: 18 commits, 108 files, 0 merges measured on the first-parent spine.

**Evidence inventory**

- Read:
  - the epic file;
  - `tickets.toml`;
  - the 8 plans, each with its frontmatter, Design and Implementation Notes, Review Triage Log and Auto Run Result;
  - `test-design-epic-3.md`;
  - the spike findings;
  - `_bmad-output/initiative-ticketscope/deferred-work.md`;
  - the previous retrospective, `epic-eval-gate/epic-eval-gate-retrospective.md`;
  - the CI run list (`gh run list`).
- Release-gate reports, produced before this retro and committed together as `test(tea): epic-hybrid-retrieval release gate`:
  - `_bmad-output/test-artifacts/test-review/test-review-epic-3.md`
  - `_bmad-output/test-artifacts/nfr/nfr-assessment-epic-3.md`
  - `_bmad-output/test-artifacts/trace/traceability-matrix-epic-ticketscope--e3.md`
  - `_bmad-output/test-artifacts/trace/gate-decision-epic-ticketscope--e3.json`
- Missing or not present:
  - The epic folder has no story files: no entry was pulled, so `description` and `verify` come from `tickets.toml`.
  - The epic folder has no run folders (`<type>-*/`). The epic file lists no companions.
  - Session logs: no session transcripts were read. The bmad-loop run folders under `.bmad-loop/runs/` were not opened. Process-lesson analysis therefore rests on the plans' triage logs only, and is **narrowed**.

## Findings

### Release gate (cited evidence)

- **G1. The trace gate is FAIL.** Source: `gate-decision-epic-ticketscope--e3.json`. P0 requirement coverage is 0%, with R1, R2 and R4 all PARTIAL. P1 is 50% and overall is 20%. 21 of 28 criteria are FULL.

  Every P0 behaviour the code implements has passing tests. The PARTIAL requirements each share a contributor whose clause is a CI-run or person-run observation with no live verification record (`live-verification-results.json` holds no epic 3 records):
  - 3.1 AC-7: PR #36's CI passed with the baseline unchanged.
  - 3.4 AC-5: a person published the Release.
  - 3.7 verify: PR #52's CI passed with the baseline unchanged.
  - 3.3 AC-3: no tracked file changed outside the spike's.

  Three clauses lack a test:
  - 3.1 AC-4: the eval Job is never shown to be untraced.
  - 3.1 AC-6: the app image is never run under `--network none` in a test.
  - 3.3 AC-1: the findings test does not check image size, the cut test, or per-issue and total embedding time.

  Disposition: **fix now** (A1, A2). Prevention: P1.
- **G2. The NFR audit is CONCERNS.** Source: `nfr-assessment-epic-3.md`. Of 14 criteria, 13 PASS. The cross-machine ranking reproducibility criterion (R-004) has no evidence: no parity check of asset vectors against a recompute in the CI image, no two-fresh-process byte comparison, and no F5 reload comparison. Repeated green `eval` gates (runs 42891445428, 42891461582, 42903014546) show reproducibility across runs only. Disposition: **defer**, tracked (A6). It overlaps DW-3 and DW-6.
- **G3. The test review is 68/100, Request Changes, with 6 HIGH findings.** Source: `test-review-epic-3.md`.
  - Four tests assert inside loops that can run zero times: `tests/integrated/test_dense_kind.py:145`, `tests/unit/test_embedding_asset.py:101` and `:268`, and `tests/unit/test_chart_defaults.py:27`.
  - Two assert only a type or presence: `tests/eval/test_eval_kind.py:219` and `tests/unit/test_hybrid_check_38_expanded.py:45`.
  - One MEDIUM is a multi-subject kind test, `test_dense_kind.py:121`.

  Two of the HIGH findings sit on criteria the trace counts as FULL: 3.5 AC-1 and 3.6 AC-1. Disposition: **fix now** (A5).

### Diff-scope review (cross-ticket boundaries)

`bmad-review` was not invoked. Its lenses (adversarial, edge-case, verification gap) ran inline, **narrowed** to the seams between tickets and to the plans' deferred items.

- **F1. Story 3.5 and story 3.1 disagree on the Helm timeout.** Source: `scripts/kind-up.sh:121–133`. Story 3.5 (d1a1911) sets `HELM_TIMEOUT=60m` under `EVAL_ENABLED`. Story 3.1's later block (684c8f4) then resets it to `50m` under `EMBEDDINGS_COMPUTE`. With both flags on, the eval hook's 2700 s deadline gets a 50-minute Helm wait. No single session saw both blocks.

  A strict xfail records the defect (`tests/unit/test_eval_embedder_expanded.py:332`). Meanwhile `tests/unit/test_dense_expanded.py:242` asserts `--timeout 50m`, which pins the wrong value. This affects local runs only, since CI never computes embeddings. Disposition: **fix now** (A4). Prevention: a cross-ticket check on any script that more than one story edits (P2).
- **F2. The Postgres tier never runs in CI.** Source: DW-5 (`deferred-work.md:41`, open) and `tests/postgres/conftest.py:22,42`. Nothing in `.github/workflows/ci.yml` sets `TICKETSCOPE_TEST_PG_IMAGE`. The epic's only real-SQL tests are therefore skipped on every PR:
  - `test_dense_postgres.py`: the cosine oracle through SQL, and the read-only role's write refusal;
  - `test_load_asset_postgres.py`;
  - `test_eval_reuse_postgres.py`.

  The trace and the NFR audit count them as static evidence. They pass locally (3.1 plan, triage line 209) but carry no CI result. Disposition: **fix now** (A3).
- **F3. Story 3.4's pin made story 3.1's flag-off kind path unreachable.** Source: `tests/integrated/test_dense_kind.py:24–27,59,186`, and `tests/unit/test_embedding_asset.py:261`. With `PINNED` true, the 503 branch and the "no pin yet" skip never run in CI. The flag-off behaviour is still covered at API level (`tests/unit/test_dense.py:202,213`). Disposition: **accept as-is**, with the dead skip guard removed under A5.
- **F4. The eval run would have broken the deadline the epic first set.** Sources:
  - `eval/baseline.json`: `wall_seconds` 1822.3;
  - `deploy/charts/ticketscope/values.yaml:96–100`: `activeDeadlineSeconds: 2700`;
  - epic Constraints: "the deadline is raised if needed".

  Story 3.5 raised the deadline from 1800 s, as the epic allows, after a 1475 s local measurement (3.5 plan, line 51). The committed CI run took 1822 s and exceeded the old value. Disposition: **accept as-is**, as an intended deviation. Prevention: keep the job-summary timing (already done in c930d0b).

### Aggregate views

- **Architecture delta.** `uv run lint-imports` reports 7 contracts kept and 0 broken at HEAD. `core` gained `modes.py` (+84), `ports.py` (+27, the `Embedder` port) and `fakes.py` (+55), and imports no embedding runtime. No new layering violation. *Narrowed:* no before/after dependency-graph diff was run; the evidence is the import-linter contracts.
- **Size growth.** The largest product-code churn (`git_evidence.py`, full range):

  | File | Net lines in the epic | Lines now |
  | --- | ---: | ---: |
  | `src/ticketscope/jobs/load/main.py` | +222 | 396 |
  | `src/ticketscope/jobs/eval/score.py` | +173 | 332 |
  | `src/ticketscope/adapters/postgres.py` | +68 | 317 |

  `load/main.py` now carries keyword load, compute-on-kind embedding with spooling, and asset load. It is a candidate to watch, not yet a god-class: three load paths in about 400 lines. Disposition: **defer**. Watch it when epic 4 or 5 adds a load path.
- **Duplication.** Story 3.7 consolidated the retriever and Postgres helpers (3.7 plan, Implementation Notes). It deliberately left the `CorpusStore` issue-lookup methods alone (epic Notes, decision of 2026-11-10). No new duplication was found. *Narrowed:* this view was taken from the 3.7 plan plus a read of `core/modes.py`; no clone detector was run.
- **Pattern divergence.** Story 3.5 adopted `@pytest.mark.criterion` markers in `tests/eval/test_eval_kind.py:202,227`, but no other epic 3 test file did. This is why the trace had to map 26 of 28 criteria by reading. Disposition: **defer**, folded into P1.
- **Spec-to-implementation reconciliation.**
  - R1–R5 are each met in the as-built system, per the trace's FULL contributors and CI run 42910706544's `integrated-check`.
  - The plans' acceptance criteria carry no `(R<n>)` tags, even though the epic 2 retro asked for them (action 6). Links had to come from `tickets.toml` `verify` text and `covers`.
  - Story 3.7 has `covers = []` while its verify text names R2 and R4.

  Disposition: spec reconciliation **proposed** (A7). DW-4 ("kind run, Tempo, OOM and api memory not run") is still `open`, although stories 3.6 and 3.8 now evidence it (`values.yaml:62–69`, `test_dense_kind.py:121`, run 42910706544). Disposition: propose closing it (A8).

## Behavior verification

Runtime behaviour changed (new `/v1` modes, readiness, load, eval), but this headless run **did not exercise it end to end**: no kind cluster was brought up. The closest evidence:

- `ci` run 42910706544 on PR #54: `integrated-check / deploy` success. It runs `tests/integrated` and `tests/smoke` on a fresh kind cluster, including dense and hybrid answers, readiness on a model mismatch, and the omitted-mode default.
- `eval` runs 42891461582 and 42903014546: success.
- A local `uv run pytest` at 9c6efe0: 1101 passed, 16 skipped, 1 xfailed. The 16 skips include the Postgres tier (F2).

These are reported as CI observations, not as a behaviour check by this run.

## Previous-retro follow-through

Source: `epic-eval-gate/epic-eval-gate-retrospective.md`, Action items.

1. **Remediate W-001: record the six criteria as superseded, then re-trace epic 1** (Dillon, through `bmad-agent-po`). **Partly landed.** Commit 5ae01de recorded the superseded notes, for example `story-derive-kind-and-outcome-in-core-plan.md:83`. There is no re-trace: `trace/gate-decision-epic-ticketscope--e1.json` is still dated 2026-11-08.
2. **Re-file the 2.5 plan** (Sofia). **Landed** in 5ae01de: `plan-2-5-refactor-sweep.md` was removed and `story-refactor-sweep-plan.md` updated.
3. **Record the R3 end-to-end run, or add a static test** (Dillon / TEA). **No evidence found.** `live-verification-results.json` has no regressing-PR record, and no branch-protection test was found.
4. **Decide on `enforce_admins`** (Dillon). **Not landed.** `gh api .../protection/enforce_admins` returns `false`, and no record says that R3 binds non-admins only.
5. **Mark stories done on merge** (user, bmad-loop). **Partly landed.** `.bmad-loop/policy.toml:95` sets `mark_done = "auto"`, but stories 3.3, 3.4 and 3.5 were still marked by hand (#44, #49).
6. **Enforce R ids in the plan template** (Sofia / Smithy). **Not landed.** Epic 3's plan acceptance criteria carry no `(R<n>)` tags, for example `story-tracer-dense-search-answers-through-v1-on-kind-plan.md:17–23`.
7. **Carry the unlanded epic 1 process actions** (user). **No evidence found** in `.bmad-loop/policy.toml` or the commit history.
8. **Merge `worktree-mark-epic2-done`** (user). **Landed** in 5bcc6e4 (#33).

## Action items

All are proposed; none was applied.

**Fix now**

1. **A1. Close the process clauses with live verification results** (Dillon / TEA). Record results at 9c6efe0 for:
   - 3.1 AC-7: CI on PR #36;
   - 3.4 AC-5: the embeddings Release `2026.11.1`, with its checksum and notes;
   - 3.7 verify: CI on PR #52, with `eval/baseline.json` unchanged;
   - 3.3 AC-3: commit 6227978's file list.

   Then re-run `bmad-tea-trace` for `epic-ticketscope--e3`. Live-only evidence caps the gate at CONCERNS. Closes G1, in part.
2. **A2. Add the three missing tests** (dev loop):
   - the eval Job exports no spans (3.1 AC-4);
   - a CI step embeds a text with the app image under `docker run --network none` (3.1 AC-6);
   - the findings test checks image size, the cut test, and per-issue and total embedding time (3.3 AC-1).

   Closes G1, together with A1.
3. **A3. Run `tests/postgres` in CI** (dev loop): set `TICKETSCOPE_TEST_PG_IMAGE` in `ci.yml` from the Postgres image the workflow already builds (`ci.yml:115–118`). Closes F2 and DW-5.
4. **A4. Fix the `HELM_TIMEOUT` order in `scripts/kind-up.sh`** (dev loop): the compute branch must not lower the eval branch's timeout. Then remove the strict xfail at `test_eval_embedder_expanded.py:332` and correct `test_dense_expanded.py:242`. Closes F1.
5. **A5. Fix the test review's 6 HIGH findings and 1 MEDIUM finding** (dev loop):
   - guard the loops with length assertions;
   - give the dense and hybrid metrics in `test_eval_kind.py` the keyword check's range and order assertions;
   - assert the `modes` value, not just its key;
   - split `test_dense_corpus_readiness_and_api_budget`;
   - remove the dead skip guard at `test_embedding_asset.py:261`.

   Closes G3 and F3.

**Defer (tracked)**

6. **A6. Add the R-004 embedding parity row** (Dillon / TEA): recompute about 200 asset vectors in the CI image and require cosine ≥ 0.9999, check that two fresh processes give identical bytes, and run the F5 two-reload comparison. Closes G2. Addresses DW-3 and DW-6.

**Spec reconciliation and ledger, awaiting human application through `bmad-agent-po`**

7. **A7. Tag the epic 3 plans' acceptance criteria with the requirements they prove, and set 3.7's `covers` to `["R2", "R4"]`** (Sofia). Carries epic 2 action 6.
8. **A8. Close DW-4** as resolved by 3.6's measurement and 3.8's integrated check, citing `values.yaml:62–69` and run 42910706544 (Sofia, or a `bmad-loop-sweep` run).

**Carried from epic 2, still open**

9. **A9.** Re-trace epic 1 after W-001 (Dillon / TEA). This is epic 2's action 1, second half.
10. **A10.** Decide on `enforce_admins` (Dillon). This is epic 2's action 4.

**Process lessons (prevention)**

- **P1. A process criterion needs an evidence path when it is written.** Write a criterion such as "CI passes on the PR" or "a person publishes" together with how it will be evidenced: a live verification record, or a `criterion` marker on a test. Owner: Sofia / Smithy, in the plan template.
- **P2. A script that two stories edit gets a cross-ticket review.** A ticket that edits a shared script (`scripts/kind-up.sh`) another ticket in the same epic already changed should get the thorough review, or a line in the integrated-check story listing the interacting flags. Owner: user (`.bmad-loop/policy.toml`, `thorough_review`).

## Decision records

Headless: proposed only, none written.

- **Proposed: `adr-pgvector-values-travel-as-text-literals.md`.** Vectors are sent to Postgres as `'[...]'` text literals through `COPY` and `%s::vector`, instead of through the `pgvector` Python adapter, so no new dependency is added. Source: 3.1 plan, Design Notes, "Vector transport"; commit 684c8f4. The plan gives the reason ("avoids a new dependency"). Approval: pending, since this run is headless.
- **Proposed: `adr-eval-job-deadline-is-2700-seconds.md`.** The eval Job's `activeDeadlineSeconds` was raised from 1800 s to 2700 s, because scoring three modes measured 1475 s locally, too close to 1800 s for a slower runner. Source: 3.5 plan, Implementation Notes, line 51; commit d1a1911. The committed CI run then took 1822 s (`eval/baseline.json`). Approval: pending.

The readiness rule (`api` is not Ready when its model id differs from `corpus_meta`) was considered and not proposed: the architecture spine's AD-21 already states it as a decision.

## Acceptance verdict

**Machine verdict: rejected.** The criteria are **declared**: the epic file's Requirements R1–R5 and its Done when list.

The verdict is bounded by the release gate. The trace gate decision is **FAIL** (`_bmad-output/test-artifacts/trace/gate-decision-epic-ticketscope--e3.json`, `gate_status: FAIL`), and per this run's instructions a FAIL makes the verdict `rejected`.

On the substance, the epic's outcome is delivered:

- all 8 tickets are done;
- the CI eval table compares keyword, dense and hybrid by kind (`eval/baseline.json`; README);
- the model is chosen by a scored spike (bge-small-en-v1.5; hybrid MRR@10 0.594 against keyword 0.550);
- `integrated-check` passes on a fresh kind cluster (run 42910706544).

The rejection rests on evidence the gate requires and does not yet have:

- three P0 requirements depend on process clauses with no live record (G1);
- the Postgres tier the trace counts never runs in CI (F2);
- the NFR audit is CONCERNS (G2);
- the test review asks for changes (G3).

A1–A3 are the shortest path to a re-trace. A human may override this verdict. No human decision was taken in this run.

## Open questions

- Should the process clauses (A1) be recorded as live results, or rewritten as test-backed criteria? Recording them lifts the gate only to CONCERNS. Rewriting them changes the plans. This is the user's call through `bmad-agent-po`.
- Should epic 4 start before A3 lands? Epic 4's by-key lookup (4.4) extends `PostgresCorpusStore`, whose real-SQL tests do not run in CI (F2).
- Is a 2700 s deadline enough on GitHub-hosted runners as the pair set grows (F4)? The committed run used 1822 s of it.

## Assumptions

- The invocation's `epic-hybrid-retrieval` was resolved to `_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/` with `tickets.py status`. `pending_tickets` is empty, so unfinished work did not force the verdict.
- The machine verdict **rejected** was rendered with no human decision. It follows the trace gate FAIL, as instructed for this run.
- The previous epic was taken as `epic-eval-gate`, the epic whose retrospective sits in the sibling folder.
- `bmad-review` and `bmad-party-mode` were not invoked. The diff-scope lenses ran inline, narrowed to the seams between tickets and the plans' deferred items. Phase 3 was skipped, as headless runs require.
- Session logs were not read, and the bmad-loop run folders were not opened. Process lessons come from the plans' triage logs only.
- Every action item (A1–A10) and both decision records are proposals. Nothing was applied: no status changed, and no plan, ticket, epic or ledger file was edited.
