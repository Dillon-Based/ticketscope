# Proposed Jira `resolution` → outcome mapping

A draft for the author. `measure.py` (`RESOLUTION_OUTCOME`, `derive_outcome`) implements exactly this table and rule; the shares in `instances.csv`, `projects.csv` and `subsets.csv` come from it.

The table covers every `resolution.name` value in the dump (89 values across 16 instances, counted on 2026-11-06), matched case-insensitively after trimming.

## The table

| Outcome | `resolution` values | Issue documents in the dump |
|---|---|---|
| duplicate | Duplicate, Duplicate Issue | 309,106 |
| fixed | Fixed, Done, Complete, Implemented, Resolved, Fixed-Verified, Deployed, Released, Delivered, Partially Completed, Staged, Current Release, Next Release | 1,377,804 |
| not_planned | Won't Fix, Won't Do, Invalid, Incomplete, Incomplete Description, Cannot Reproduce, Works for Me, Not A Problem, Not a Bug (all spellings), Non-Issue, Works As Intended, Works as Designed, Expected Behavior, Rejected, Declined, Out of scope, Obsolete, Out of Date, Gone away, Later, Deferred, Parked, Low Priority, Deprioritized, No Resources, Won't Finish, Will not implement, Canceled, Abandoned, Spam, Incorrectly Filed, Invalid Ticket, Not Applicable, Unactionable, Unsolved Mysteries, EOL, Incorporated, Tracked Elsewhere, Moved, Migrated to another ITS, Resolved at Apache, Upstream, Invalid: Works as Expected, Invalid: Environment Issue, Invalid: Test Error, Invalid: Not Supported | 550,204 |
| stale | Timed out, Awaiting Response, Automatically Closed, Auto Closed, Low Engagement, Pending Closed | 45,013 |
| answered | Answered, Support Request, Handled by Support, Explained, Information Provided, Community Answered, Feedback Received, Sent to Forums, Sent to Docs, Resolved Locally, Workaround | 24,974 (before the rule below adds Question/Support issues) |
| unknown | no resolution (an open or unresolved issue), and every value not listed above | 379,025 unresolved + 156 unmapped |

Values left `unknown` because they say nothing about the outcome: `REMIND`, `Accepted`, `Triaged`, `Errata`, `Known Error`, `Stop Dots`, `BugzillaOrphan`, `Roadmap Candidate`, `Unresolved`. They total 156 issue documents and are listed per scope in the CSVs' `unmapped_resolutions` column.

## The "answered" rule

Jira has no `author_association`, so "a maintainer comment" cannot be read as on GitHub. Instead:

> An issue is **answered** when its type is a Question or Support type (the type name contains "question" or "support", case-insensitive), it is resolved, and at least one comment created at or before the resolution time was written by someone other than the reporter. "Someone" is the masked author id (`key`, else `name`, else `accountId`; the dump keeps these UUID masks consistent per person).

The rule applies to a Question/Support issue whose resolution reads as `fixed` (for example `Done`) or is unmapped. A resolution that already reads as `duplicate`, `not_planned`, `stale` or `answered` keeps that outcome. The reasoning: no code change closes a question, so for those types `Done` means "handled".

## Precedence

Inside one issue the resolution decides; the epic's precedence order (duplicate, fixed, not_planned, stale, answered, unknown) only matters for the answered rule above, which deliberately lets `answered` win over a `fixed`-class resolution on Question/Support issues. That is a change to the epic's precedence for this corpus, and it needs the author's sign-off with the Decision line.

## How the outcomes map onto schema v1 (for the replan)

- `state`: `closed` when a resolution is set, else `open`.
- `state_reason`: `duplicate` for duplicate, `not_planned` for not_planned, `completed` for every other resolved outcome, null when open.
- duplicate: one `marked_as_duplicate` timeline event pointing at the target issue. The current `derive_outcome` in core then reads it as duplicate.
- fixed, stale and answered: core's current rules read GitHub labels, merged PRs and `author_association`. None exist in Jira, so story 4's rules (`fixed` from a merged PR, `stale` from labels, `answered` from `kind/support` plus a maintainer comment) would read these issues as `unknown` or `not_planned`. **A switch needs core's outcome rules (or the schema) to carry the resolution.** That is part of the data-lane replan.

## Measured

Over the resolved issues of every instance, the `unknown` share is under 1% (largest: SecondLife 0.67%). Including the unresolved targets of duplicates (`plus_open_targets_*` columns) raises it to at most 1.2% (Jira). See `instances.csv`.
