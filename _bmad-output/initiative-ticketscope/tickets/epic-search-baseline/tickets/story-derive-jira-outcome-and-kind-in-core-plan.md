---
title: 'Derive Jira outcome and kind in core'
type: 'feature'
ticket: '14'
created: '2026-11-06'
status: done
baseline_revision: '1cb2bf3b5057252a9e2f66e841cdc566a79ff760'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus-findings/outcome-mapping.md'
warnings: ['oversized']
deferred:
  - summary: >-
      duplicate_target does not check link_type, so a non-Duplicate link in duplicate_links could become the duplicate target and /v1 ref.
    evidence: |-
      Unverified (maybe-false). AD-26 names "any Duplicate-mapped link"; the spike filters by jira_issue_linktype_mapping.json. Harmless if story 13's ingest writes only Duplicate-mapped links into duplicate_links; settle in story 13 by filtering at ingest or by having core check link_type.
    location: >-
      src/ticketscope/core/derive.py duplicate_target
    severity: medium (unverified)
---

<intent-contract>

## Intent

**Problem:** Core's kind and outcome rules read GitHub signals (labels, merged PRs, `author_association`), so every Mojang Jira issue would load as `unknown` and `{code}`/`{noformat}` log blocks would not count. Story 13's schema v2 and story 5's load need core to own the v2 snapshot model and the Jira rules (AD-6, AD-8, AD-26).

**Approach:** Add a v2 snapshot model to `core.snapshot` (the AD-6 field list), and make `derive_outcome` / `derive_kind` dispatch on the model type: v2 issues use the Jira resolution mapping, the answered rule and Jira-block fences; v1 issues keep story 4's GitHub rules unchanged. Add `duplicate_target` (AD-26) and bump the derivation version.

## Boundaries & Constraints

**Always:**
- `core` imports only stdlib and pydantic (AD-1); functions are pure and deterministic, independent of the order of comments or duplicate links.
- Outcome mapping exactly per `outcome-mapping.md` (the table in spike `measure.py`'s `RESOLUTION_OUTCOME`), matched on `resolution.strip().lower()`. No resolution → `unknown`; an unmapped value → `unknown`.
- Answered rule: `issue_type` contains "question" or "support" (case-insensitive), a resolution is set, `resolved_at` is set, and at least one comment with `from_reporter` false has `created_at <= resolved_at`. It turns only a `fixed`-class or unmapped resolution into `answered`; duplicate, not_planned, stale and answered resolutions keep their class.
- `/v1` source: duplicate → `label`; answered → `closing_comment`; fixed, not_planned, stale, unknown → `None`. Duplicate `ref` = `https://bugs.mojang.com/browse/<target_key>` of `duplicate_target(issue)`, else `None`. All other refs `None`.
- Derivation version differs from story 4's `kind1-t3.outcome2` (bump both rule versions).
- Story 4's tests in `tests/unit/test_derive.py` keep passing unmodified, except a version-string assertion that must move with the bump.

**Never:**
- No change to `jobs/ingest`, `jobs/load`, `snapshot/schema-v1.json`, `snapshot/fixture*`, migrations, `/v1` contract (`contract/`, `core/model.py` Literals), or `SCHEMA_VERSION` — story 13 owns the v2 JSON Schema, ingest and the load path; story 5 owns the threshold.
- No reporter/author identity field in the v2 model.
- No new runtime dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Duplicate | resolution `Duplicate`, link `duplicates` → MCL-7 | duplicate, `label`, ref `https://bugs.mojang.com/browse/MCL-7` | No error expected |
| Duplicate, no link | resolution `Duplicate`, no links | duplicate, `label`, ref `None` | No error expected |
| Fixed | `Fixed` | fixed, source `None` | No error expected |
| Not planned | `Won't Fix` | not_planned, `None` | No error expected |
| Stale | `Timed out` | stale, `None` | No error expected |
| Answered by resolution | `Answered` | answered, `closing_comment` | No error expected |
| Unresolved | resolution `None`, state open | unknown, all `None` | No error expected |
| Unmapped | `Triaged` | unknown | No error expected |
| Trim/case | ` fixed ` | fixed | No error expected |
| Question answered | type Question, `Done`, non-reporter comment before `resolved_at` | answered, `closing_comment` | No error expected |
| Question not answered | same, only reporter comments, or the non-reporter comment after `resolved_at` | fixed | No error expected |
| Support duplicate | type Support, `Duplicate`, non-reporter comment | duplicate | No error expected |
| Kind below/at threshold | `{code}`/`{noformat}` blocks + log lines scoring `t-1` / `t` | short / log_heavy | `threshold < 1` → `ValueError` |
| Parameterised toggle | `{code:java}` vs `{code}` | same score | No error expected |
| State invariant | `state` closed without resolution, or open with one | — | pydantic `ValidationError` |

</intent-contract>

## Code Map

- `src/ticketscope/core/snapshot.py` -- add `JiraComment(body, created_at, from_reporter: bool)`, `DuplicateLink(target_number: int ≥1, target_key: str, direction: Literal["duplicates", "duplicated_by"], link_type: str)`, `SnapshotIssueV2(schema_version: Literal[2], number: int ≥1, key: str, url, title, body: str | None, issue_type: str, state: Literal["open","closed"], resolution: str | None, created_at, resolved_at: datetime | None, comments: list[JiraComment], duplicate_links: list[DuplicateLink])` on the existing `_Frozen` base, plus a `model_validator` enforcing `state == "closed"` iff `resolution is not None`. Leave `SnapshotIssue`, `SCHEMA_VERSION = 1` and the v1 classes untouched; update the module docstring.
- `src/ticketscope/core/derive.py` -- `derive_outcome(issue: SnapshotIssue | SnapshotIssueV2)` and `derive_kind(...)` dispatch via `isinstance`; current v1 bodies move to private `_github_outcome` with identical behaviour. Add `RESOLUTION_OUTCOME` (copy the spike's dict verbatim), `duplicate_target(issue: SnapshotIssueV2) -> DuplicateLink | None`, `jira_to_fences(body)`, `MOJANG_BROWSE_URL = "https://bugs.mojang.com/browse/"`. `KIND_RULE_VERSION = "kind2"`, `OUTCOME_RULE_VERSION = "outcome3"`. Reuse `Outcome`, `UNKNOWN`, `kind_score`, `_check_threshold`.
- `tests/unit/test_derive_jira.py` -- NEW: the matrix above plus test-design rows "Jira outcome derivation in core" (12 cases) and "Jira kind rule in core" (3 cases), with a `make_jira_issue(**overrides)` helper.
- `tests/unit/test_derive.py` -- story 4's suite; only touch a hard-coded version string if one exists.
- `tests/unit/test_layer_imports.py`, `.importlinter` -- already cover every `core` module; no change.
- Spike reference (read-only): `_bmad-output/.../spike-choose-the-jira-corpus-findings/measure.py` (`RESOLUTION_OUTCOME`, `is_answered`, `derive_outcome`, `jira_to_fences`, `duplicate_target`).

## Tasks & Acceptance

**Execution:**
- [x] `src/ticketscope/core/snapshot.py` -- add the v2 model classes and state validator -- AD-6 field list, the shape story 13's schema v2 mirrors
- [x] `src/ticketscope/core/derive.py` -- Jira outcome, answered rule, `duplicate_target`, Jira-fence kind, dispatch, version bump -- AD-8, AD-26, epic Jira outcome and Kind rule
- [x] `tests/unit/test_derive_jira.py` -- one named test per matrix row and test-design case, plus order independence of comments/links and the version differing from `kind1-t3.outcome2` -- R2 verify

**Acceptance Criteria:**
- Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.
- Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.
- Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.

## Implementation Notes

- **Unclosed toggle.** An unclosed `{code}` / `{noformat}` counts once, exactly like an unclosed ``` fence (`test_unclosed_toggle_counts_once`). The test design marks this UNKNOWN; the sources do not say.
- **Log lines inside blocks.** Story 4's `kind_score` counts log-like lines inside a fence as well as the fence opening, so a `{noformat}` block of log lines scores like the same fenced block. Kept unchanged; pinned by `test_kind_log_lines_inside_block_count_like_fenced_logs`.
- **Answered via unmapped resolution.** A Question/Support issue with an unmapped resolution that passes the answered rule reads `answered`, summary `"Answered before resolution (<resolution>)"`, per the spike's rule.
- **Duplicate target tie-break.** Equal `target_number` falls back to `(target_key, direction, link_type)` so the choice stays order-independent.
- `tests/unit/test_derive.py` needed no change: its version assertion is built from `KIND_RULE_VERSION` / `OUTCOME_RULE_VERSION`.

## Plan Change Log

## Review Triage Log

### 2026-11-06 — Review pass
- verdicts: 4 findings — high 0, medium 0, low 1, false 1, maybe-false 2
- findings:
  - `[maybe-false]` `[defer]` `duplicate_target` never checks `link_type`, so a non-Duplicate link reaching `duplicate_links` could become the target and `/v1` ref — harmless if story 13's ingest writes only Duplicate-mapped links into `duplicate_links` (as the field name implies); settled by story 13 either filtering at ingest with the spike's link-type map or asking core to check `link_type`. Medium if true (unverified); deferred.
  - `[false]` `[reject]` `duplicate_target` picks the lowest `target_number` instead of the spike's list order — AD-26's stated rule is direction precedence ("duplicates" first, then any Duplicate-mapped link), which the code follows; no contract fixes a within-direction order, the lowest-number tie-break is the plan's deliberate choice for order independence, and story 13 recomputes the Release-note counts with this one function, so no caller diverges.
  - `[low]` `[patch]` naive and aware datetimes could meet in `_is_answered` and raise `TypeError` — patched: `JiraComment.created_at`, `SnapshotIssueV2.created_at` and `resolved_at` are now `AwareDatetime`, matching RFC 3339 UTC and JSON Schema `date-time`; `test_naive_datetimes_are_invalid` added.
  - `[maybe-false]` `[reject]` a closed issue with `resolved_at=None` silently reads `fixed` rather than `answered` — this matches the spike's measured `is_answered`, and AD-6 does not tie `resolved_at` to state; if true it only misreads a rare Question/Support issue (low). Story 13 can settle it by counting resolved Mojang issues without a `resolutiondate`.

## Design Notes

- **Non-reporter-comment flag.** The ticket and epic name an issue-level flag; the amended spine (AD-6) fixes it as per-comment `from_reporter`, which carries the same fact without identity and lets core apply the "at or before resolution" cut. Core derives the flag; ingest never writes it.
- **Duplicate target (AD-26).** Only for a duplicate-class resolution: among links with `direction == "duplicates"` the one with the lowest `target_number`; failing that, the lowest `target_number` of any link. Lowest-number (not list order) keeps it order-independent.
- **Kind.** `jira_to_fences` replaces every `\{(?:code|noformat)(?::[^}\n]*)?\}` (case-insensitive) with `"\n```\n"`, then `kind_score`. An unclosed toggle counts once, like an unclosed fence (the test design marks this UNKNOWN; record it in Implementation Notes).
- **Summaries.** `"Duplicate of MCL-7"` / `"Resolved as duplicate"`; class outcomes `"Resolved as <stripped resolution>"`; rule-derived answered `"Answered before resolution (<resolution>)"`; unknown has no summary.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `uv run pytest tests/unit/test_derive_jira.py tests/unit/test_derive.py -v` -- expected: every case named in the ACs passes

## Auto Run Result

**Summary.** Core now owns the schema v2 (Mojang Jira) snapshot model and derives Jira outcome and kind from it. `derive_outcome` and `derive_kind` choose the Jira rules for a v2 issue and keep story 4's GitHub rules for v1. The outcome comes from the `resolution` mapping in spike 12, plus the answered rule, which reads each comment's `from_reporter` flag. `duplicate_target` (AD-26) builds the duplicate `ref`. Jira `{code}`/`{noformat}` toggles count as fences. The derivation version moves to `kind2-t3.outcome3`, so a load reloads.

**Files changed.**
- `src/ticketscope/core/snapshot.py`: adds `JiraComment`, `DuplicateLink` and `SnapshotIssueV2`, with aware datetimes and the rule that an issue is closed exactly when it has a resolution.
- `src/ticketscope/core/derive.py`: adds the Jira outcome mapping, the answered rule, `duplicate_target`, `jira_to_fences`, schema-version dispatch and the rule version bump.
- `tests/unit/test_derive_jira.py`: new. One test per matrix row and per test-design case, plus tests that comment and link order don't change the result.
- This plan.

**Review.** Quick lens, 4 findings:
- 1 low finding patched: naive datetimes are now rejected.
- 1 maybe-false finding deferred: the `link_type` check, for story 13 to settle.
- 1 false finding rejected: the duplicate tie-break follows AD-26's direction precedence.
- 1 maybe-false finding rejected: a missing `resolved_at` matches the spike's rule and would only be low if true.

Patched counts: high 0, medium 0, low 1. Follow-up review recommended: false.

**Verification.** All passed:
- Ruff lint and format checks.
- Pyright: 0 errors.
- lint-imports: 6 contracts kept.
- `uv run pytest`: 212 passed, 4 deselected.
- `uv run pytest tests/unit/test_derive_jira.py tests/unit/test_derive.py`: 101 passed.

Every I/O matrix row has a passing test.

**Residual risks.**
- Nothing outside the tests uses the v2 model yet. Story 13 wires ingest, the v2 JSON Schema and the load path.
- Story 13 must write only Duplicate-mapped links into `duplicate_links` (deferred finding).
- An unclosed `{code}` toggle counts once. The sources do not say how it should count.
- Log lines inside Jira blocks count toward kind, as they do in fenced blocks. Story 5 should weigh this when it sets the threshold.
