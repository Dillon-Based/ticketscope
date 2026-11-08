---
title: 'README results table is generated from CI output'
type: 'feature'
ticket: '4'
created: '2026-11-08'
status: done
baseline_revision: '17c3dd1267782dd5866edb1800b24bce79a8b94a'
route: 'full'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** The README shows no retrieval scores, and nothing stops a hand-typed number from appearing there instead of one a CI run produced.

**Approach:** A stdlib-only script renders the results table from the committed `eval/baseline.json` (the CI results JSON) between generated-section markers in `README.md`. A `ci.yml` step fails when the README section differs from that render or the markers are missing. The table is committed as rendered, whatever it shows.

## Boundaries & Constraints

**Always:** Rows are one per mode (sorted by name) per kind in the order short, log_heavy, overall, from whatever `modes` the baseline holds, so a new mode adds rows with no script change. Columns: Mode, Kind, Pairs (`pairs_scored`, integer), Recall@1, Recall@5, Recall@10, MRR@10, p95 ms; every non-integer number printed `f"{x:.3f}"`. The snapshot version (`lineage.snapshot_version`) appears above the table, inside the generated section. Markers are the HTML comments `<!-- eval-results:start -->` and `<!-- eval-results:end -->`, each exactly once, start before end. Output is deterministic, ends with one newline, and the check compares the README section byte for byte. The script is the only writer of that section.

**Never:** Hand-write numbers in the README. Edit `eval/baseline.json`. Gate or change any eval/gate behaviour. Add dependencies (stdlib only, so CI runs it without extra setup). Pass on an empty comparison: a missing, duplicated or misordered marker fails.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Committed state | README section made by `--write` from the committed baseline | `--check` exits 0 | none |
| Hand-edited number | one digit in the table changed | `--check` exits 1, says README differs, names the fix command | non-zero exit |
| Missing markers | README without start or end marker | `--check` and `--write` exit 1 naming the marker | non-zero exit |
| Duplicated or misordered markers | two start markers, or end before start | exit 1 | non-zero exit |
| Extra mode | baseline fixture with a second mode | extra rows, no code change | none |
| Rounding | 0.0005, 0.12349999, 1 | fixed three decimals, deterministic | none |
| Baseline missing kind or metric | mode lacks `log_heavy` or `recall@10` | exit 1 naming mode and key | non-zero exit |

</intent-contract>

## Code Map

- `eval/baseline.json` -- input: `lineage.snapshot_version`, `modes.<m>.{short,log_heavy,overall}` with `recall@1/5/10`, `mrr@10`, `p95_latency_ms`, `pairs_scored`; also holds large `first_member_ranks` lists to ignore. Read-only.
- `scripts/live_results.py` -- model for a stdlib-only CI script (argparse, `main(argv) -> int`).
- `tests/unit/test_live_results.py:1-25` -- pattern for loading a script as a module via `importlib` and `tests.target.REPO`.
- `tests/unit/test_eval_workflow.py:16-27` -- `_block` helper and workflow-text parse tests, the pattern for the ci.yml test.
- `.github/workflows/ci.yml` -- `checks` job (steps after pytest) gets the README check step.
- `README.md` -- add a `## Retrieval results` section with the markers; section content comes from `--write`.

## Tasks & Acceptance

**Execution:**
- [ ] `scripts/render_readme_table.py` -- `render(results) -> str`, `splice(readme, section) -> str` and `extract(readme) -> str` raising on marker faults, `main(argv)` with `--baseline`, `--readme`, and `--check` (default) / `--write` -- single place that owns the table
- [ ] `README.md` -- add `## Retrieval results` heading, one sentence saying the table is generated from `eval/baseline.json` by `scripts/render_readme_table.py` and not edited by hand, and the markers; then run `--write`
- [ ] `.github/workflows/ci.yml` -- in `checks`, add step `README results table` running `python3 scripts/render_readme_table.py --check` -- fails the PR on drift
- [ ] `tests/unit/test_readme_table.py` -- cover every matrix row, plus: the committed README equals the render of the committed baseline, and the ci.yml `checks` job contains the check command
- [ ] Update the header comment of `ci.yml` to mention the README check

**Acceptance Criteria:**
- Given the committed `eval/baseline.json` and README, when `python3 scripts/render_readme_table.py --check` runs, then it exits 0, and `--write` leaves `git diff` empty.
- Given one digit of the README table changed by hand, when the check runs, then it exits 1.
- Given a README without the generated-section markers, when the check runs, then it exits 1.
- Given `ci.yml`, when parsed as text, then the `checks` job runs the check command.

## Implementation Notes

## Plan Change Log

## Review Triage Log

### 2026-11-08 — Review pass
- verdicts: 2 findings — high 0, medium 0, low 2, false 0, maybe-false 0
- findings:
  - `[low]` `[reject]` ci.yml README step is skipped when pytest fails — a PR with both failures still sees the test failure and fixes the table next; adding `if: always()` is extra complexity for a negligible gain.
  - `[low]` `[reject]` `--write` could change CRLF line endings on Windows — the committed README is LF and CI is ubuntu; guarding newlines adds complexity for an unreached case.

### 2026-11-08 — Follow-up review pass
- verdicts: 1 findings — high 0, medium 1, low 0, false 0, maybe-false 0
- findings:
  - `[medium]` `[patch]` README reads normalized line endings before checking byte equality — reproduced a CRLF table row passing `--check`. Read and write UTF-8 bytes without newline translation; added a regression proving drift fails and regeneration preserves surrounding CRLF text.

## Verification

**Commands:**
- `python3 scripts/render_readme_table.py --check` -- expected: exit 0
- `uv run pytest tests/unit/test_readme_table.py tests/unit/test_eval_workflow.py` -- expected: pass
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports` -- expected: pass
- `uv run pytest` -- expected: pass

## Auto Run Result

Status: built (hand-back; ticket plan status preserved for the orchestrator).

- Summary: reviewed the existing README renderer and CI check, incorporated the prior automation pass's 24 expanded cases, and corrected newline normalization that allowed byte-level table drift to pass.
- Files: `scripts/render_readme_table.py` preserves UTF-8 bytes on README reads/writes; `tests/unit/test_readme_table.py` adds a mixed-line-ending regression; `tests/unit/test_readme_table_expanded.py` covers CLI, invalid inputs, mode pickup and marker handling; automation result and summary retain the prior run's evidence; this plan records review and verification. Existing README and ci.yml changes remain in the reviewed change set since the baseline revision.
- Review: quick lens, 1 medium finding patched; 0 deferred, 0 rejected in this pass. Earlier rejected lows remain recorded in the prior triage log; the earlier write-normalization observation is now addressed by the byte-preserving write. Patched counts: high 0, medium 1, low 0. Follow-up review recommended: false (follow-up pass, no high patch).
- Verification: README `--check` exits 0; `--write` reproduces README byte-identically; focused README/expanded/workflow tests 51 passed; full `uv run pytest` 908 passed, 41 kind tests deselected; ruff check and format, pyright and lint-imports all pass (7 contracts kept).
- Residual risks: GitHub CI and kind integrated checks were not run in this invocation; orchestrator verification remains outstanding. No human decision is required. Existing deferred-work ledger entries and ticket plan status were not modified; `tickets.py mark` was not run.
