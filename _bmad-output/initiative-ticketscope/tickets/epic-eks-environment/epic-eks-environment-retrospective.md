---
epic: epic-eks-environment
date: 2026-11-26
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective: epic-eks-environment

## Epic summary

- Tickets (`tickets.py status`, 14 of 14 `done`, none `built`, `pending_tickets` empty): 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12 (bug), 5.13, 5.14 (bug).
- Retro scope note: the first `status` call in this run showed 5.11 as `blocked`. That was before PR #100 (`e4aa976`) landed. The re-run shows it `done`, so the unfinished-epic path did not apply. The user's going-in focus was not asked, because the question was declined. The analysis was weighted evenly.
- Ranges: each plan records a `baseline_revision`, and the baselines run from `9814559` (2026-11-12) to `fe5a8ee` (2026-11-24). Narrowed: one combined range `9814559..e4aa976` was measured, with 32 commits, no merges and 154 files (`git_evidence.py`). Per-plan ranges were not split. 5.8 and 5.9 share baseline `d43b982`, so the range does not separate their commits. The range also contains an unrelated epic-4 trace artifact commit (`_bmad-output/test-artifacts/trace/*--e4.*`, about 1.5k lines).
- Evidence read: the epic file, including all Notes, `tickets.toml` status, plan frontmatter and Review Triage Logs, `docs/drills/*.md`, `deferred-work.md`, and the unit-test run below. Not read: session logs, which are absent, so process-lesson analysis is skipped. Companions: none are listed. Run folders: none exist. `bmad-review` was not invoked and the diff-scope lenses were not run, so the review is narrowed to the aggregate views and the triage logs. Sub-agents were not used.
- Previous retro: the immediately preceding epic (epic-mcp-server) has no retrospective. Epic 3 (`epic-hybrid-retrieval-retrospective.md`) is the nearest one and was not checked for follow-through.

## Findings

Every finding has a source and a disposition.

1. **R10 is unproven, and the epic closed over it.** `docs/drills/failure-drill.md` reads "Result: not yet run". The epic Notes (closure decision, 2026-11-24) accept the gap, and `deferred-work.md` carries it. The Done when bullet "an instance-failure drill recorded" is unmet, and plugin bug #828 (two instances archiving to one archive) is still an open unknown. Disposition: **defer**, with a December owner. It is the reason for the verdict below.
2. **R11's control recreate was not run.** The epic closure note and the 5.9 acceptance both say the control recreate, without the `serverName` change, was not run. So "no 'Expected empty archive' failure" is shown with the fix in place but never shown to fail without it (`docs/drills/recreate-drill.md`). Disposition: **accept**. The requirement text asks only for the success case.
3. **R5 is month-to-date.** The $2.93 raw and $3.94 amortised figures cover 1 to 24 November only (`docs/drills/env-check.md`). The epic budget is 25 env-hours a month, and the December drills (failure drill, node loss) add more. Disposition: **accept** for R5 as declared ("a month that holds recorded runs"). Re-check the December figure when the failure drill runs.
4. **The teardown path took two live bugs and repeated red `env-down` runs.**
   - Bug 5.12 (stale DNS records) and bug 5.14 (CNI network interface) were both found by live runs, after 5.4 had been accepted.
   - `env-down` ended red on the leftover check after both 5.9 `env-down` runs, because the check had no confirmation path for deleted subnets (Notes, 5.9 decision). That was fixed after 5.8 by `fe5a8ee` (#98).
   - Bug 5.14's live delete was still unobserved at its acceptance (Notes, 2026-11-23). The deferred-work entry for it ("no live env-down has yet deleted a leaked CNI interface") is still open.
   - Disposition: **accept** for the fixes. The unobserved CNI delete is **defer**, to be watched on the next live `env-down`.
5. **Unverified items remain open in `deferred-work.md`.**
   - The ALB's TLS 1.0/1.1 listener policy.
   - ENI tag filters that may match nothing (the leftover check's ENI leg could be vacuous).
   - The CNPG ScheduledBackup that has never fired, with retention prune unexercised.
   - The deploy role's ability to attach managed policies to the `ticketscope-env-*` roles it creates, which is a privilege-escalation path.
   - external-dns writing no TXT ownership records, with the symptom fixed but the cause open.
   - Plugin issue 892 (the plugin's Role reading every Secret in the namespace).
   - Disposition: **defer**. The TLS policy, the escalation path and the ENI tag check are the ones worth doing before a live link is published (epic 8).
6. **Workflow and script size grew.** `env-up.yml` is 529 lines (+553 across 7 commits), `eks-teardown.sh` is 392, `env-down.yml` is 273, and `env-check.yml` is 199 (`git_evidence.py`, `wc -l`). `leftover-check.sh` (164 lines) and `leftover_check.py` (205 lines) coexist as two implementations of the check. Not checked: whether they duplicate logic. Disposition: **defer**. Worth a look at the next sweep.
7. **Tests pin workflow text.** The 5.11 triage rejected a finding that its tests pin text (`story-integrated-check-on-eks-plan.md`, Review Triage Log), with the rationale that the repo's other workflow tests do the same and the live run is the behavioural check. The large unit files (`test_eks_teardown.py` +559, `test_env_up_workflow.py` +446, `test_chart_eks.py` +418) follow that pattern. Disposition: **accept**, with the risk that text-pinning tests pass while the live run fails. Bugs 5.12 and 5.14 show that risk was realised.
8. **A real defect was caught at 5.11 review.** The `up` job waited on env-up's whole run, including the `expire` sleep, so the `env-down` dispatch was delayed to the expiry. It was fixed in the same story, with a test. Source: 5.11 plan Review Triage Log. Disposition: **fixed**.
9. **Status records disagreed temporarily.** The board showed 5.11 `blocked` with a December-window precondition. The epic closure note then closed it on 2026-11-24 with R10 as an accepted exception, and this was reconciled by #100. Disposition: **accept**. It is a note for the next closure: record the exception as an exception, not as the story's blocker.

## Behavior verification

- Exercised: `uv run pytest tests/unit -k "eks or leftover or env_ or drill or infra or chart"`, which passed with no failures.
- Not exercised: `scripts/check.sh` (the full static job set), the kind-marked tests, the postgres and image tests, and any live AWS run. No AWS or cluster command was run, as the repo's agent rules forbid writes.
- Live behavior is evidenced only by recorded runs in `docs/drills/env-check.md`, `restore-drill.md` and `recreate-drill.md`. I read the records and did not re-verify the run URLs. `env-check` run 45486216065 shows `env-up` at 908 s, against a 30-minute target for R1, with the leftover check clean (R3).

## Previous-retro follow-through

Not checked. The previous epic (epic-mcp-server) has no retrospective. Epic 3's retrospective exists but its action items were not compared with this epic. One thing is visible: DW-3 and DW-6 (embedding pin and reference vectors), carried from epic 3, were resolved by story 5.13 on 2026-11-20 (`deferred-work.md`).

## Action items

All items are proposed. None were applied.

1. Run `scripts/failure-drill.sh` in the December window, commit the rendered record to `docs/drills/failure-drill.md`, and re-record the December billing figure. Owner: the operator. Closes finding 1, and finding 3 for December.
2. Watch the next live `env-down` for the CNI interface delete and the ENI tag filters, and close the two deferred entries. Owner: the operator.
3. Before epic 8 publishes a live link, triage the TLS policy, the deploy-role escalation path and the ENI tag check from finding 5. Owner: Sofia (`bmad-agent-po`), as board items.
4. Check `leftover-check.sh` against `leftover_check.py` for duplicated logic (finding 6). Owner: the next refactor sweep.
5. Process: when an epic closes with an unmet Done when line, record it as an accepted exception in the epic file at closure (finding 9). Owner: Sofia.

## Decision records

None proposed and none written. The decisions in the plans are mostly in the epic Notes already (domain delegation, OIDC subject, Gateway deletion before controller uninstall). I did not read the plans' frozen blocks line by line for decision records.

## Acceptance verdict

**accepted-with-open-items**, against the epic's declared Requirements and Done when.

- Met with evidence: R1 (908 s, `env-check.md`), R2 and R11 (recreate drill, with the control recreate not run), R3 and R4 (`env-down` and expiry, live-verified in the Notes), R5 ($3.94 amortised, month-to-date), R6 and R7 (OIDC deploy and the PR check, per the Notes), R8 and R9 (backup and restore drill).
- Not met: R10 (node loss survived, a standby promoted, search answering). The user accepted it as unproven on 2026-11-24 (Notes). It stays open until the December drill.
- No unfinished tickets, so no forced rejection.

## Open questions

- Does plugin bug #828 affect two-instance failover? Only the December drill answers this.
- Does the ScheduledBackup fire and prune correctly on EKS? Not observed.
- Do the two leftover-check implementations (`.sh` and `.py`) duplicate logic? Not checked.

Assumptions (interactive run, recorded because the user did not answer the going-in questions): the user's re-invocation was taken as consent to proceed with the retro, and no focus area was applied.
