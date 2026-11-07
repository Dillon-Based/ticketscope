---
epic: epic-search-baseline
date: 2026-11-07
verdict: rejected
criteria: declared
headless: true
---

# Retrospective: epic-search-baseline (Keyword search over Mojang issues, deployed on kind)

## Epic summary

- **Epic:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md` (initiative `initiative-ticketscope`, epic 1, key `ticketscope--e1`). It declares Requirements R1 to R7 and a Done when list.
- **Tickets, in build order** (`tickets.py status`): 1.1, 1.2, 1.3, 1.12, 1.4, 1.14, 1.13, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11. All 14 are `status: done` and `state: done`. None is still at `built`, and `pending_tickets` is empty.
- **Plan ranges** (from each plan's `baseline_revision`, oldest first; `git_evidence.py` run once per range):

  | Ticket | Range | Commits (merges) | Code lines +/− (src, tests, deploy, CI, scripts) |
  | --- | --- | --- | --- |
  | 1.1 | `4ca22e31..a595c2f7` | 18 (4) | +2229 / −8 |
  | 1.4 | `a595c2f7..3791664a` | 4 (2) | +559 / −0 |
  | 1.3 | `3791664a..b5cc9840` | 9 (4) | +5473 / −2 (3,141 of them a recorded-response fixture) |
  | 1.12 | `b5cc9840..1cb2bf3b` | 11 (4) | 0 (spike evidence only) |
  | 1.14 | `1cb2bf3b..f4de1fb5` | 1 (0) | +1071 / −14 |
  | 1.13 | `f4de1fb5..b525b53e` | 2 (1) | +2925 / −5104 (GitHub recordings removed) |
  | 1.5 | `b525b53e..32049eef` | 1 (0) | +1530 / −174 |
  | 1.6 | `32049eef..d29ed1ef` | 1 (0) | +1054 / −53 |
  | 1.7 | `d29ed1ef..88613bdb` | 1 (0) | +924 / −20 |
  | 1.8 | `88613bdb..ffe83d97` | 1 (0) | +962 / −7 |
  | 1.9 | `ffe83d97..93c43443` | 5 (2) | +1812 / −15 |
  | 1.10 | `93c43443..9b291e39` | 1 (0) | +349 / −459 |
  | 1.11 | `9b291e39..e71a5ba` (inferred: ends at the last story commit, before the TEA gate commit `4e0aeaf`) | 1 (0) | +498 / −6 |

  Spike 1.2 (`spike-settle-the-corpus-terms-plan.md`) has no `baseline_revision`, so it has no commit or diff evidence. Every merge in every range was measured (`merges_measured` equals `merge_count`).
- **Evidence inventory:**
  - Available: the epic file; `tickets.toml`; story leaves for 1.1, 1.3, 1.12 and 1.5; all 14 plans; the companion `test-design-epic-1.md`; `deferred-work.md`; bmad-loop run folders `.bmad-loop/runs/20261106-110746-1120`, `20261106-180417-b664` and `20261107-110852-cafa` (each `ATTENTION` log and task `session-lifecycle.jsonl`); GitHub Actions run 42385558996 (PR #19); Release `snapshot-2026.11.1`.
  - Release gate reports (this run): `_bmad-output/test-artifacts/test-review/test-review-epic-1.md`, `_bmad-output/test-artifacts/nfr/nfr-assessment-epic-1.md`, `_bmad-output/test-artifacts/trace/traceability-matrix-epic-ticketscope--e1.md`, and `_bmad-output/test-artifacts/trace/gate-decision-epic-ticketscope--e1.json`.
  - Missing: there are no run folders (`<type>-*/`) inside the epic folder. Session transcripts are absent; only the loop's lifecycle logs survive, so the process lessons rest on those logs and the plans. There is no previous retrospective (this is the initiative's first epic).

## Findings

### Release gate (TEA)

- **G1. The trace gate is FAIL.** `trace/gate-decision-epic-ticketscope--e1.json`: P0 coverage 50% (2 of 4 rows), P1 56.52%, overall 46.15% (24 of 52 rows); the two P0 requirement rows, R5 and R7, are NONE. The main cause is structural: 45 of the 46 ticket criteria name no epic `R` id (the stories link only through `covers`), so six of the seven requirement rows have no contributor (`traceability-matrix-epic-ticketscope--e1.md`, "Gate Decision"). *Disposition:* fix now. *Prevention:* criteria cite their `R` ids at ticket-writing time.
- **G2. NFR audit is CONCERNS.** `nfr-assessment-epic-1.md`: security CONCERNS (the planned `ticketscope_ro` write-refusal test does not exist), performance CONCERNS (search latency threshold UNKNOWN by design), reliability PASS, maintainability PASS. The two GitHub-era rows (read-only token, rate-limit resume) are N/A since the corpus switch. *Disposition:* fix now (write-refusal test); accept as-is (latency belongs to epic-eval-gate).
- **G3. Test quality is 79/100 (C), Request Changes.** `test-review-epic-1.md`: 4 HIGH findings. A `time.sleep` poll sits in `tests/smoke/test_gateway.py:495`. Three assertions sit behind a filter or a possibly empty loop, at `tests/unit/test_snapshot.py:140`, `tests/unit/test_chart_telemetry.py:91` and `tests/unit/test_telemetry_expanded.py:203`. One LOW magic value sits at `tests/unit/test_app.py:34`. *Disposition:* fix now (small test-only changes).

### Spec-to-implementation reconciliation

- **S1. R7 and Done when ("integrated check passing in CI") are not met on a PR.** Stories 1.10 (`9b291e3`) and 1.11 (`e71a5ba`) plus `93c4344` are local commits: `main` is three ahead of `origin/main` (`git status -sb`). `ci.yml` triggers only on `pull_request` and `workflow_dispatch` (`.github/workflows/ci.yml:6-8`). The last CI run of `_kind-deploy`, 42385558996 on PR #19, ran only `pytest -m kind tests/smoke`, before 1.11 added `tests/integrated`. Story 1.11's own plan records this: "the GitHub-hosted `integrated-check` run happens when this branch is pushed and a PR opens (not done here: no push)" (`story-integrated-check-on-kind-plan.md:137`). The same holds for 1.10 (`story-refactor-sweep-plan.md:126`). *Disposition:* fix now. *Prevention:* the loop's per-story commits should land through a PR so CI gates each story.
- **S2. Behavior on kind is otherwise met, locally and in CI up to 1.9.** CI run 42385558996 passed 22 kind smoke tests: two instances, backup completed, Tempo and Grafana trace, load report `within_budget=true`, golden queries through the page. See Behavior verification for this run's local integrated check. *Disposition:* accept.
- **S3. The page answers a 405 on `/` with `Allow: GET` only.** That is a live product defect, kept visible as a strict xfail (`tests/unit/test_page_expanded.py:268`) and reproduced on kind in this run. No ticket owns the fix. *Disposition:* defer, with a backlog item.
- **S4. Keyword relevance is weak but within the agreed bar.** The golden twins rank 5 (vague, MCD-6467) and 9 (log-heavy, MCL-602) of 10, observed in this run and recorded in `story-integrated-check-on-kind-plan.md:94`. R-004 is mitigated, not closed (epic Notes, test-design decision). *Disposition:* accept as-is; epic-hybrid-retrieval owns it.
- **S5. Superseded criteria are still written as open.**
  - Story 1.3's leaf asks for `snapshot.yml`, github.com URLs and recorded GitHub responses (`story-ingest-publishes-a-versioned-corpus-snapshot.md:49-58`), but the corpus switched to Jira and `snapshot.yml` no longer exists (`.github/workflows/` holds only `ci.yml` and `_kind-deploy.yml`).
  - Story 1.4's and 1.14's GitHub-rule test criteria were retired by 1.10 (`git_evidence` for 1.10: `tests/unit/test_derive.py` net −220).
  - The test design's NFR rows still name the GitHub token and rate-limit resume (`test-design-epic-1.md:128-130`).

  These are allowed by the epic's Notes, but the tickets and test design were not reconciled, which inflates the trace denominator with criteria that cannot be met. *Disposition:* spec reconciliation (proposed).
- **S6. The ADR-style layering proof is not re-runnable.** "A deliberate change that makes `core` import an adapter fails import-linter" (`story-tracer-keyword-search-answers-through-the-gateway-on-kind.md:56`) was shown once. `tests/unit/test_layer_imports.py` is an allow-list check, not that negative case (NFR audit, maintainability). *Disposition:* defer to the test-hardening item.

### Aggregate views

- **Architecture delta:** `uv run lint-imports` keeps 7 of 7 contracts on HEAD (run 2026-11-07). The layering held across 14 tickets, and no new cross-layer import appears in the ranges. *Checked and clean.*
- **God-class / size growth:** the largest source files at HEAD are `jobs/ingest/jira.py` (344 lines), `core/derive.py` (285) and `http/app.py` (274). Nothing is near god-class size; `derive.py` shrank by 106 lines in 1.10. The largest test file is `tests/smoke/test_gateway.py` (726 lines), which grew in 1.5, 1.6, 1.8 and 1.9 (+107, …, +127, +220 in their ranges). Watch it, but it is not yet a problem. *Checked.*
- **Duplication map:** three hand-rolled poll loops in `tests/smoke/test_gateway.py` (backup at :490, trace at :595, Grafana port-forward at :693), written by 1.8 and 1.9 in separate sessions. Story 1.11 then moved the backup check into `tests/integrated` while smoke kept its own (`story-integrated-check-on-kind-plan.md:138`: "backup and trace now run twice per job"). *Disposition:* defer; extract one poll helper (pairs with G3).
- **Pattern divergence:** narrowed. Only test structure was compared, through the test review. No production-code divergence was found in the files read; a full convention sweep was not run.

### Diff-scope review

Narrowed. `bmad-review` was not invoked: this session does not spawn reviewer subagents unasked. The edge-case and verification-gap lenses were applied inline to the ticket boundaries the gate reports flagged: 1.8 and 1.9 against 1.11 (the shared backup and trace checks), 1.4 and 1.14 against 1.10 (the retired rules), and 1.5 against 1.10 (the no-op load in smoke (3), DW-2, closed in `deferred-work.md`). The adversarial lens over the full diff was not run. Findings from it: S5, the duplication above, and DW-1 and DW-2, both closed with resolutions recorded in `_bmad-output/initiative-ticketscope/deferred-work.md`.

### Process (from loop logs and plans)

- **P1. The loop committed straight to `main`.** Stories 1.5 to 1.11 are `story 1.x: implemented and reviewed via bmad-loop` commits on `main` (`git log`). 1.5 to 1.9 reached CI only when a person opened PR #19 afterwards, and 1.10 and 1.11 never did (S1). *Prevention:* a loop policy of a branch and PR per story, or per epic.
- **P2. Story 1.8's first dev attempt stalled and left the tree for manual rollback, because auto-rollback is off** (`.bmad-loop/runs/20261106-180417-b664/ATTENTION`, 2026-11-06 22:10, "ACTION REQUIRED — manual rollback needed"). Its lifecycle log also shows a 5-hour rate-limit stop (`tasks/1.8-dev-1/session-lifecycle.jsonl`). *Prevention:* enable `[scm] rollback_on_failure`.
- **P3. Story 1.5 overran its token cap** (2,291,235 weighted against a 2,000,000 cap; `ATTENTION`, 2026-11-06 20:41). The cap is advisory, so 1.5 continued. It is the largest story by spend in the logs.
- **P4. The corpus pivot was handled well.** The first Kubernetes snapshot run failed after 1h16m (Actions run 42261907819) and showed too little duplicate ground truth. Spike 12 measured the alternative, the author decided, and the data lane was replanned with dated Decision lines (epic Notes). The resulting snapshot carries 10,473 in-subset duplicate pairs and loads in 2.6 s (Release `snapshot-2026.11.1`). *Accept; worth repeating.*
- **P5. Trace linkage was never set up in the tickets.** The ticket format (Verify-only leaves, plan criteria without `(R<n>)`) gave the gate nothing to link (G1). *Prevention:* Sofia's ticket template should require `R` ids on criteria.

## Behavior verification

Run on 2026-11-07 against the local kind cluster `kind-ticketscope` (api image tag `ticketscope-app:93c4344…`, rebuilt in place by the 1.10 and 1.11 sessions), through a port-forward to the Envoy Gateway:

- `uv run pytest -m kind tests/integrated -v`: **5 passed**. Checks: pinned asset valid against schema v2 and loaded; every issue has a valid kind and outcome; both golden queries pass through `/v1` and the page (vague rank 5, log-heavy rank 9); one search reaches Tempo as the AD-10 tree; an on-demand backup completes to SeaweedFS.
- `POST /v1/search` (keyword, k=3) on a log-like query returned `corpus_version 2026.11.1` and three ranked Mojang issues, each with a kind and an outcome.
- `PUT /` returned `405` with `allow: GET` (S3 reproduced). A `<script>` query rendered escaped.
- Unit suite: 712 passed, 27 deselected, 1 xfailed. `lint-imports`: 7 kept.

This is local evidence. It does not satisfy "passes on a PR" (S1).

## Previous-retro follow-through

Nothing to follow through: no previous retrospective file exists. This is the first epic in the initiative.

## Action items

All items are proposed; none was applied.

1. **Push and gate on CI.** Push `93c4344`, `9b291e3`, `e71a5ba` (and the gate commit `4e0aeaf`) through a PR and get the `integrated-check` job green on GitHub-hosted kind. Owner: user / operator. Closes S1 and the trace's R5 and R7 evidence gap.
2. **Link criteria to requirements** (spec reconciliation, via `bmad-agent-po`). Give the story leaves numbered criteria that cite `R1`–`R7`, or add `(R<n>)` to the plan acceptance criteria, then re-run `bmad-tea-trace` with gate type `epic`. Owner: Sofia (PO). Closes G1.
3. **Retire superseded criteria** (spec reconciliation, via `bmad-agent-po`). Mark story 1.3's GitHub and `snapshot.yml` criteria, 1.4 AC-1 and 1.14 AC-2 as superseded, and update `test-design-epic-1.md`'s NFR rows for the Jira corpus. Owner: Sofia (PO) and the test design owner. Closes S5.
4. **Test hardening** (remediation, story-shaped). Make the four HIGH and one LOW test-review fixes; add one `poll_until` helper for the smoke and integrated waits; add a committed negative import-linter test and a `ticketscope_ro` write-refusal smoke test. Owner: dev loop. Closes G2, G3, S6 and the duplication finding.
5. **Fix the 405 `Allow` header on `/`** (remediation; flip the strict xfail to a pass). Owner: dev loop (backlog). Closes S3.
6. **Loop policy** (process). Branch and PR per story or epic so CI gates each build; enable `[scm] rollback_on_failure`. Owner: user (bmad-loop config). Closes P1 and P2.
7. **Ticket template** (process). Require `R` ids on every acceptance criterion. Owner: Sofia (PO). Closes P5.

## Decision records

Headless: proposed only, none written. No `adr-*.md` exists in the repository.

- **Proposed: `adr-load-swaps-the-corpus-in-one-transaction.md`.** The load replaces the corpus in one transaction (TRUNCATE, COPY and the `corpus_meta` row), so `api` sees the old corpus or the new one, never a partial one. Source: `story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:38`, commit `32049ee`. It is hard to reverse (epic 3's embedding table will join the same swap) and surprising without context. Not approved (headless).
- **Proposed: `adr-snapshot-ingest-is-person-run.md`.** The Jira ingest and Release publish run on a person's machine against a restored dump, not in CI, because the 5.8 GB dump does not fit a hosted runner. Source: epic Notes (2026-11-06) and `story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md`, commit `aac2796`. Not approved (headless).

## Acceptance verdict

**rejected** (criteria declared: epic Requirements R1–R7 and Done when).

- **Bound by the release gate:** the trace gate decision is **FAIL** (`_bmad-output/test-artifacts/trace/gate-decision-epic-ticketscope--e1.json`: P0 50%, P1 56.52%, overall 46.15%), and by this run's instruction a FAIL means `rejected`.
- **On the criteria themselves:** R1 to R6 are demonstrated, on CI up to story 1.9 and locally for the whole epic (Behavior verification, S2). R7 and the Done when line "Delivered on the cluster, with an integrated check passing in CI" are **not met**: the integrated check has never run in CI (S1).
- **Open but non-blocking:** the NFR audit is CONCERNS (G2), test quality is Request Changes (G3), and S3, S4 and S5 remain.
- **No unfinished tickets:** `pending_tickets` is empty.

The path back to acceptance: action items 1 and 2, then a re-run of the trace gate. With the integrated check green on a PR and the criteria linked, the remaining items fit `accepted-with-open-items`. No human decision overrides this verdict.

## Open questions

- Should criterion-to-requirement linkage be fixed in the tickets (action 2), or should the trace contract count story `covers` for Verify-only stories? The answer decides whether this epic's gate is a ticket fix or a tooling change.
- Is the local kind run acceptable as R7 evidence until the PR runs? The epic's wording ("passes on a PR") says no.
- Do the GitHub-era criteria (S5) leave the denominator by retiring them in the tickets, or by a waiver on the gate?

## Assumptions

- The epic reference `epic-search-baseline` resolved to the folder `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/` through `tickets.py status`. `pending_tickets` was empty, so no verdict was forced by unfinished tickets.
- The machine verdict `rejected` was rendered with no human decision, bounded by the trace FAIL as this run's instructions require.
- 1.11's range end was inferred as `e71a5ba` (the last story commit), excluding the TEA gate commit `4e0aeaf` made in this run.
- The diff-scope review and the pattern-divergence view were narrowed (see their sections). Session transcripts were unavailable, so the process findings rest on loop lifecycle logs and plans.
- Every action item and both decision records are proposals only; nothing was applied, and no ticket, epic or plan was edited or had its status changed.
- The gate reports cited here are the versions committed in `4e0aeaf` (`test(tea): epic-search-baseline release gate`). A concurrent Codex session, started at 12:09 in the `tea` worktree (`~/.supacode/repos/ticketscope/tea`), is writing its own TEA run into the same `_bmad-output/test-artifacts` folder. After that commit it overwrote the working-tree copy of `trace/traceability-matrix-epic-ticketscope--e1.md` with its in-progress run. Read the gate evidence at `4e0aeaf`, not from the working tree, until the two runs are reconciled.
- An earlier system-scope test-review run, interrupted by a usage limit, left `_bmad-output/test-artifacts/test-review/test-review-system.md` and `review-evidence-system.json`. They are outside this epic's gate, were not committed and are not cited.
