---
title: 'Spike 1.12: Choose the Jira corpus'
type: 'chore'
ticket: '12'
created: '2026-11-06'
status: 'built'
baseline_revision: 'b5cc98405a346144ee88181ec23bc6e2b0fa3a3c'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The first Kubernetes snapshot has 21 duplicates, none with a target, which is too little ground truth for epic-eval-gate. Kubernetes issues are also a weak fit for support tickets. Story 5 and epic-eval-gate both wait on a decision about the corpus.

**Approach:** Restore the Public Jira Dataset v7 into a throwaway MongoDB and measure every instance on the four parts of the decision rule: terms, in-subset duplicate pairs by kind, unknown-outcome share, and load time. Then measure projects in the leading instances, recommend a subset, and prove it with a timed load and samples. The evidence goes beside the ticket. The author makes the final call.

## Boundaries & Constraints

**Always:** Spike scripts live with the evidence, outside `src/`. They may import `ticketscope.core.derive.kind_score`, read-only. The extended kind rule maps Jira `{code…}` and `{noformat}` toggles onto fences, then calls `kind_score` with the current threshold of 3. An in-subset duplicate pair is an issue resolved `Duplicate` with a "duplicates"-type link (by `jira_issue_linktype_mapping.json`) to an issue in the same subset; each pair counts once. Kind is the duplicate issue's kind. The data ends at its 2022 collection date; say so.

**Never:** No product-code changes, schema changes, or snapshot publishing. Nothing is written to the ticket file or its epic until the author signs off. No Decision line written in the author's name without their sign-off.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Instance measured | an instance collection | one CSV row: issues, pairs short/log_heavy, outcome shares, type mix, hygiene counts | none |
| Duplicate link points outside the subset | link target not in the scope | not counted as an in-subset pair | counted separately as `pairs_out_of_scope` |
| Duplicate with no link | resolution Duplicate, no link | outcome `duplicate`, no pair | counted as `dup_no_target` |
| Unmapped resolution value | e.g. a custom resolution | outcome `unknown` | listed in the CSV's `unmapped_resolutions` column |
| Converted snapshot | subset issues | schema-v1 lines + kinds sidecar that `scripts/time-load.sh` loads | load failure is recorded as a finding, not patched in product code |

</frozen-after-approval>

## Code Map

- `src/ticketscope/core/derive.py` -- `kind_score` and `DEFAULT_KIND_THRESHOLD=3`; reuse, do not change
- `snapshot/schema-v1.json`, `src/ticketscope/core/snapshot.py` -- the shape the converter must emit: integer `number`, `url`, RFC 3339 `Z` timestamps, `author_association` enum, `state_reason` enum
- `scripts/time-load.sh <dir> <version>` -- times migrate + load; needs `<version>.jsonl.gz` and `<version>-kinds.json`; prints the seconds on the last stdout line
- Dump: `~/Downloads/2025-06-23 ThePublicJiraDataset.zip`, restored into the container `jira-spike-mongo` (mongo:7, volume `jira-spike-mongo`, `127.0.0.1:27017`), database `JiraReposAnon`, one collection per instance. Instance URLs are in `0. DataDefinition/jira_data_sources.json`, and the link-type mapping is in `jira_issue_linktype_mapping.json`.
- Evidence folder: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus-findings/`

## Tasks & Acceptance

**Execution:**
- [ ] `…-findings/measure.py` -- per-scope metrics (instance, then project for the top instances) → `instances.csv`, `projects.csv` -- AC 1
- [ ] `…-findings/outcome-mapping.md` -- `resolution` → duplicate/fixed/not_planned/stale/answered/unknown table plus the "answered" rule: a Question/Support-type issue resolved after a comment by someone other than the reporter (by masked id)
- [ ] `…-findings/test_spike.py` -- pytest over the pure functions in `measure.py`/`convert.py` on hand-built Jira dicts, one test per I/O matrix row (in-subset pair, out-of-scope link, duplicate with no link, unmapped resolution, converted line validates against `SnapshotIssue` and the kinds sidecar matches the extended kind rule) -- the matrix needs tests
- [ ] `…-findings/convert.py` -- recommended subset → schema-v1 `jira-<subset>.jsonl.gz` + kinds sidecar (kept out of git, in a temporary directory); run `scripts/time-load.sh` and record the seconds
- [ ] `…-findings/samples-<candidate>.md` -- 20 sampled issues per leading candidate (Mojang included) with an empty "author judgement" column, plus 10 sampled duplicate pairs from the recommended subset, each checked against the changelog (resolution set to Duplicate, link added)
- [ ] `…-findings/terms.md` -- each candidate instance's site terms on republishing issue text, plus the draft attribution line
- [ ] `…-findings/findings.md` -- the per-instance and per-project tables, the recommendation against the decision rule, the load time, and the proposed Decision line plus the Corpus scope/terms amendments, as a draft for the author

**Acceptance Criteria:**
- Given the restored dump, when `measure.py` runs, then `instances.csv` has one row per instance in the dump, and `projects.csv` covers the leading instances' projects.
- Given the recommended subset, when it is converted and timed, then `time-load.sh` exits 0 and the findings record the seconds against 600.
- Given the findings, when the author reads the samples and the draft, then they can sign the Decision line. The epic edit happens only after that sign-off.

## Design Notes

Hygiene counts per scope: issues with wiki markup (`{code`, `{noformat`, `{quote`, `h1.`, `[text|url]`), mentions (`[~accountid:…]`, `[~user]`), email-shaped strings, token/key-shaped strings (the same patterns as `jobs/ingest/mask.py`), and NUL characters.

## Verification

**Commands:**
- `uv run pytest <findings>/test_spike.py` -- expected: all pass
- `uv run python <findings>/measure.py --scope instance` -- expected: `instances.csv` with one row per collection
- `scripts/time-load.sh $CLAUDE_JOB_DIR/tmp/snap <version>` -- expected: exit 0, seconds < 600

**Manual checks (if no CLI):**
- The author reads the samples and signs the Decision line (hitl)

## Implementation Notes

- The dump holds all 16 instances (2,686,282 documents restored, none failed), answering the ticket's open question.
- `findings.md` was written by the orchestrating session, because subagents may not write report files. Its tables are rendered by `tables.py` from the CSVs.
- `measure.py` also imports `_EMAIL`, `_PEM_BLOCK` and `_SECRETS` from `ticketscope.jobs.ingest.mask` (read-only), so the hygiene counts use ingest's patterns.
- The scripts need `uv run --with pymongo`; pymongo is not a project dependency.
- Reruns: `measure.py --scope instance` reproduced `instances.csv` byte for byte. `time-load.sh` on `jira-mojang-mcl-realms-mcd-open` took 3.0 s (the first run took 3.9 s).
- Left for the author: the judgement columns, the ruling on Mojang's terms, and the Decision line. The ticket and epic are untouched.

## Review Triage Log

Pass 1 (quick lens, 9 findings): high 0, medium 2, low 6, false 1, maybe-false 0. All surviving entries were routed to patch, so there was no loopback.

| # | Finding | Verdict | Route | Evidence / action |
|---|---|---|---|---|
| 1 | Reversed-direction fallback links are counted in `pairs` without disclosure | low | patch | Pairs are unordered, so the count is unchanged; only the kind attribution moves. Disclosed the counts (58 / 156 / 268 / 153) in the findings' Method section. |
| 2 | Pair samples skip open-target pairs, and the denominator counts per issue | medium | patch | Confirmed in `_pair_samples` (`by_key` holds resolved issues only). The implementer fixed it and regenerated the sample: 10 of 10,466 pairs, all confirmed in the changelog. |
| 3 | Sidecar writing is untested | medium | patch | The test only recomputed `extended_kind`. Added `test_convert_writes_a_sidecar_keyed_by_number_with_the_extended_kind`. |
| 4 | The sidecar kind uses masked text, measure uses raw text | false | reject | The resolved-only sidecar has 811 log-heavy issues, equal to `subsets.csv` `log_heavy` 811. |
| 5 | The `convert.py` docstring says "in-subset" duplicate links | low | patch | `to_snapshot` emits an event for any Duplicate-mapped link; corrected the docstring. |
| 6 | `write_samples` filters before the first-wins dedupe | low | patch | Confirmed; reordered to dedupe first, as `Scope.add` does. |
| 7 | The decision-rule table mislabels variants | low | patch | Every column is + open targets except SPARK's load, which is resolved-only (35,034 issues). Relabelled. |
| 8 | Validation of the recommended `-open` snapshot is not stated | low | patch | Validated 32,154 of 32,154 lines, with unique numbers, and recorded it. |
| 9 | "522 → 535" cannot be traced | low | patch | Recomputed with `kind_extension_effect.py` (MCL Duplicate-resolved 522 → 535; SPARK 385 → 506) and recorded it alongside the script. |
