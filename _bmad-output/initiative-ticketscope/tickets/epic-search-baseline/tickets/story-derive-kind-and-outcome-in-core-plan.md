---
title: 'Derive kind and outcome in core'
type: 'feature'
ticket: '4'
created: '2026-11-06'
status: done
baseline_revision: 'a595c2f7518d9fadbec27c52e51c168e2fc1a156'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** `load` stores a kind from a hand-written sidecar and every outcome as `unknown`. AD-8 requires one pure `core` function for each derived field, so the load (story 5), the ingest report (story 3) and the eval all agree.

**Approach:** Add `ticketscope.core.derive` with `derive_outcome(issue)` (the epic's precedence and outcome terms, returning the `/v1` outcome shape) and `derive_kind(issue, threshold)` (fenced blocks plus log-like lines against a threshold parameter), plus a derivation version for story 5's reload check. Unit tests on synthetic issues cover every branch, the precedence ties and both sides of the threshold.

## Boundaries & Constraints

**Always:**
- Pure functions over `SnapshotIssue`; `core` imports only stdlib and pydantic (AD-1), so `tests/unit/test_layer_imports.py` and `lint-imports` stay green.
- Precedence, first match wins: duplicate → fixed → not_planned → stale → answered → unknown.
- `source` by branch: duplicate `label`, fixed `linked_pr`, answered `closing_comment`; not_planned, stale and unknown `None`.
- Maintainer = `author_association` in {OWNER, MEMBER, COLLABORATOR}; support issue = label `kind/support`.
- Deterministic: same issue in, same result out, independent of the order of labels, comments or timeline events.
- `kind` is `log_heavy` when the score (fenced blocks + log-like lines) is ≥ `threshold`, else `short`. The threshold is a parameter with a module default.
- A derivation version string that changes whenever the threshold, the kind rule or the outcome rule changes.

**Never:**
- No change to `jobs/load`, the schema, migrations or the sidecar — story 5 wires the functions in and sets the final threshold.
- No GitHub API calls, no regex dependency beyond stdlib `re`.
- `state_reason == "duplicate"` alone does not make an issue duplicate (the epic names only the event and the label).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Duplicate by event | `marked_as_duplicate` event with `source_url` | `duplicate`, source `label`, ref = that URL | No error expected |
| Duplicate by label | `triage/duplicate`, no event | `duplicate`, source `label`, ref `None` | No error expected |
| Duplicate + merged PR | both | `duplicate` | No error expected |
| Fixed | `closed` or `cross-referenced` event, `source_is_pull_request` and `source_merged` true | `fixed`, source `linked_pr`, ref = PR URL | No error expected |
| Unmerged PR | cross-referenced PR, `source_merged` false/None | not `fixed` (falls through) | No error expected |
| Not planned | `state_reason: not_planned` (also with a stale label) | `not_planned`, source `None` | No error expected |
| Stale | `lifecycle/stale` or `lifecycle/rotten` | `stale`, source `None` | No error expected |
| Answered | `kind/support`, maintainer comment at or before `closed_at` | `answered`, source `closing_comment` | No error expected |
| Not answered | `kind/support`, only comment after `closed_at` is CONTRIBUTOR | `unknown` | No error expected |
| Unknown | none of the above | `unknown`, summary/source/ref `None` | No error expected |
| Kind boundary | score `threshold-1` / `threshold` | `short` / `log_heavy` | `threshold < 1` raises `ValueError` |
| Empty body | `body` `None` or `""` | `short` | No error expected |

</intent-contract>

## Code Map

- `src/ticketscope/core/snapshot.py` -- `SnapshotIssue`, `Label`, `Comment`, `TimelineEvent` (read-only). Timeline events carry `source_number`, `source_url`, `source_is_pull_request`, `source_merged`.
- `src/ticketscope/core/model.py` -- `Kind`, `OutcomeStatus`, `OutcomeSource` Literals; reuse them, do not redefine.
- `src/ticketscope/core/derive.py` -- NEW: `Outcome` (frozen dataclass: `status`, `summary`, `source`, `ref`), `derive_outcome`, `derive_kind`, `kind_score`, `DEFAULT_KIND_THRESHOLD`, `KIND_RULE_VERSION`, `OUTCOME_RULE_VERSION`, `derivation_version(threshold=DEFAULT_KIND_THRESHOLD) -> str`.
- `tests/unit/test_derive.py` -- NEW: the matrix, built from a small `make_issue(**overrides)` helper over `SnapshotIssue`.
- `tests/unit/test_layer_imports.py` -- already scans every `core` module; no change.
- `snapshot/fixture.jsonl` -- 8 synthetic issues. Log-heavy ones have one fenced block of 6–11 lines of klog/stack text; short ones are one plain line. Do not edit.

## Tasks & Acceptance

**Execution:**
- [x] `src/ticketscope/core/derive.py` -- implement the functions and constants above -- AD-8, epic Constraints (Outcome precedence, Outcome terms, Kind rule, Derivation version)
- [x] `tests/unit/test_derive.py` -- one test per matrix row and per test-design case (story 4 rows: 9 outcome cases, 2 kind cases), plus order-independence and `derivation_version` changing with the threshold

**Acceptance Criteria:**
- Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.
- Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).

**Superseded (waiver W-001, recorded 2026-11-09):** AC-1 and AC-2 above describe story 4's GitHub outcome and kind rules, replaced by story 14's Jira derivation (`kind2-t3.outcome3`). Their intent is carried by story 14 AC-1 and AC-3. They are left as built, not rewritten. Register: `_bmad-output/test-artifacts/gate-waivers.md`.

## Implementation Notes

- Fixture kinds checked by hand at the default threshold (3): `kind_score` gives 900001 0, 900002 7, 900003 5, 900004 0, 900005 6, 900006 0, 900007 0, 900008 4. All eight `derive_kind` results match `snapshot/fixture-kinds.json`. Not committed as a test (story 5 owns it).
- Fixture outcomes for reference: 900001 fixed (#900101), 900005 not_planned, 900006 answered (MEMBER), 900007 duplicate (#900001), the rest unknown.
- Kind boundary tests pass an explicit threshold (2, 5, 10 below; 1, 5, 10 at), so they keep holding when story 5 moves the default.
- Fence lines are not also scored as log-like. A closing fence must use the same character as its opening.
- Not_planned and stale carry a fixed summary ("Closed as not planned", "Closed as stale (<labels>)"); source and ref stay `None`.

## Plan Change Log

- `DEFAULT_KIND_THRESHOLD` is 1, not the 5 in the Design Notes example. Under the listed log-like patterns, fixture issue 900008 (one fence of three `Error from server (Forbidden)` lines) scores 1, so the "fixture kinds match at the default threshold" AC holds only at threshold 1. The listed patterns were kept as they are. Story 5 sets the final threshold against the real corpus and may need a kubectl-error pattern (for example `^Error from server`) to make a higher threshold work. The derivation version is now `kind1-t1.outcome1`.
- Superseded in the parent's verify pass: a threshold of 1 makes any fenced block (a pasted YAML manifest, say) `log_heavy`. Added the log-like pattern `^\s*(?:[Ee]rror|Warning)\b[^:]*:` for kubectl-style error lines, so 900008 scores 4, and set `DEFAULT_KIND_THRESHOLD = 3` (short fixtures score 0, log-heavy 4–7). The derivation version is `kind1-t3.outcome1`. Story 5 still sets the final threshold against the real corpus.

## Review Triage Log

### 2026-11-06 — Follow-up review pass
- verdicts: 1 finding — high 0, medium 1, low 0, false 0, maybe-false 0
- findings:
  - `[medium]` `[patch]` Equal-key duplicate mark and unmark events depended on timeline order — the snapshot permits equal timestamps and source fields; the mark now wins an otherwise identical tie, both orders have a regression test, and the outcome rule version is bumped.

### 2026-11-06 — Review pass
- verdicts: 6 findings — high 0, medium 2, low 2, false 2, maybe-false 0
- findings:
  - `[false]` `[reject]` `_fixed` treats any merged cross-referenced/connected PR as fixed, so a not_planned issue merely mentioned by a merged PR becomes fixed — the ticket's test design (story 4 row, case 9: "a cross-referenced PR that was not merged does not make an issue fixed") and fixture 900001 (only a merged cross-referenced PR, intended fixed) define cross-referenced + merged as the fixed signal; the code matches that reading. Story 5 sees the real outcome split.
  - `[medium]` `[patch]` `_duplicate` ignores `unmarked_as_duplicate`, so an unmarked issue stays duplicate and hides its real outcome — fixed: the event signal counts only when the latest mark/unmark event is a mark; the label still counts alone. Tests added for marked→unmarked, unmarked→re-marked, unmarked + label.
  - `[low]` `[patch]` `_duplicate` drops events without `source_url`, losing a known number and letting an older event win — fixed: the latest mark is used regardless of URL; ref may be `None`. Tests added.
  - `[medium]` `[patch]` the kubectl-error pattern and `^\s+at ` match ordinary prose ("Error handling …: …", "  at the moment …"), inflating `log_heavy` — fixed: tightened to `^\s*(?:[Ee]rror|Warning)(?: from server)?(?: \([^)]*\))?:` and `^\s+at [\w$.<>]+\(`; negative tests added; fixture kinds still match at threshold 3.
  - `[low]` `[patch]` `kind_score` closes a fence on a line with an info string (```` ```yaml ````) — fixed: only a bare marker of the same character and at least the opening length closes; tests added that fail under the old rule.
  - `[false]` `[reject]` order-independence test lacks tie-break cases (equal `created_at` comments, closed vs later cross-referenced PR in reverse order) — the reviewer confirms both are handled by `_comment_key` and the `(event == "closed", …)` key; no wrong output occurs, only a missing test.

## Design Notes

- **Fixed.** "Closed by a merged linked PR" is read from timeline events whose `event` is `closed`, `cross-referenced` or `connected` with `source_is_pull_request is True and source_merged is True`. Prefer a `closed` event; otherwise the latest by `created_at`, ties by `source_number`. Summary `"Fixed by #<n>"` (or `"Fixed by a merged PR"` without a number).
- **Duplicate ref.** Use the `marked_as_duplicate` event's `source_url` when present (latest event), else `None`. Summary `"Duplicate of #<n>"` or `"Marked as duplicate"`.
- **Answered.** The latest maintainer comment with `created_at <= closed_at`; `closed_at is None` → not answered. `ref` is `None` (comments carry no URL). Summary is a fixed template naming the association, not comment text.
- **Kind score.** Count fence openings (lines starting with ``` or ~~~ after optional indent; an unclosed fence still counts once) plus log-like lines anywhere in the body: klog prefixes (`E1105 10:00:01`), ISO/RFC3339 timestamps at line start, `level=`, `panic:`, `goroutine N [`, `Traceback`, `File "...", line N`, Go/Java stack frames (`\.go:\d+`, `^\s+at `), and `ERROR|FATAL|WARN(ING)?` tokens. Lines matching several patterns count once.
- **Derivation version** example: `"kind1-t5.outcome1"`. Bump `KIND_RULE_VERSION` / `OUTCOME_RULE_VERSION` whenever the rule changes.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `uv run pytest tests/unit/test_derive.py -v` -- expected: every case named in the ACs passes

## Auto Run Result

**Summary.** Core derives kind and outcome with the epic's precedence and exposes a version for reloads. This follow-up makes duplicate mark/unmark ties deterministic and bumps the outcome rule version to `outcome2`.

**Files changed.** `src/ticketscope/core/derive.py` implements the derivations and tie-break; `tests/unit/test_derive.py` covers the rules and both event orders; this plan records the review.

**Review.** Quick follow-up: one medium finding patched, none deferred or rejected. Patched counts: high 0, medium 1, low 0. Follow-up review recommended: false.

**Verification.** Ruff lint and format, pyright, and all six import contracts passed. `uv run pytest` passed 102 tests with 4 deselected; `uv run pytest tests/unit/test_derive.py -v` passed 63 tests.

**Residual risks.** The default kind threshold remains provisional until story 5 measures the real corpus. Merged cross-referenced PRs count as fixed under the existing plan's interpretation.
