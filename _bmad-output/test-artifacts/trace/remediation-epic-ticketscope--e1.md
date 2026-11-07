---
artifactType: trace-remediation
runScope: epic
runKey: epic-ticketscope--e1
date: 2026-11-07
sourceAssessment: traceability-matrix-epic-ticketscope--e1.md
gateReevaluated: false
---

# Epic 1 trace remediation

The source criteria now name the epic requirements they support. This addresses the missing-link finding; it does not establish fresh CI, manual verification, or a passing release gate. The previous trace matrix and gate JSON remain the recorded assessment of their original inputs.

## Requirement links repaired

Added parenthesized `(R...)` annotations to 39 criteria across ten plans and the authoritative Jira-corpus spike ticket. Criterion behavior and ordering are unchanged. These are explicit source annotations, not inheritance from ticket `covers`. The installed story-identity contract selects the spike ticket's four criteria, so its three plan criteria were left untouched.

| Source story | Criteria linked | Epic requirements |
| --- | --- | --- |
| s1: tracer / deployment | AC-1–AC-4 | R7 |
| s12: Jira-corpus spike ticket | AC-1–AC-4 | R1 |
| s14: Jira derivation | AC-1, AC-3 | R2 |
| s13: Jira ingest | AC-1–AC-4 | R1; AC-3 also R2 |
| s5: pinned load | AC-1–AC-5 | R2, R3, R4, R5, R7 according to each criterion |
| s6: API contract | AC-1–AC-3 | R3; layer-boundary AC-2 → R7 |
| s7: page | AC-1–AC-3 | R4; smoke AC-2 also R7; API parity AC-3 → R3 |
| s8: backup | AC-1–AC-3 | R5; CI AC-1 also R7 |
| s9: tracing | AC-1–AC-4 | R6; toolchain AC-2 also R7 |
| s10: sweep | AC-1–AC-4 | R7 for maintenance/CI; R2 for preprocessing/load; R3/R4 for response parity |
| s11: integrated check | AC-1–AC-3 | All R1–R7 for five checks/fault injection; default no-cluster run AC-3 → R7 |

The spike-terms verify criterion already names R1 through its permitted verify-only `covers` rule. The expected new source inventory therefore has 40 linked criteria and six historical exceptions, rather than the previous one linked criterion and 45 exceptions. This is a metadata count, not a coverage score. Fresh trace must verify the selected inventory and reaggregate requirements from actual criterion evidence.

## Finding disposition

| Original findings | Change or remaining work |
| --- | --- |
| R1–R7: no explicit contributing criteria | Source links repaired as above. Reuse existing assertions already mapped to those criteria; do not create duplicate E2E tests solely to repair a metadata gap. |
| Historical s3 AC-1–AC-3, s4 AC-1–AC-2, s14 AC-2 | Retained verbatim and unlinked. These require the owner's explicit reconciliation of completed GitHub acceptance criteria after the approved Jira switch and sweep. Current Jira tests cannot prove GitHub URL, rate-limit, `snapshot.yml`, or retired GitHub outcome behavior. No waiver or retirement was invented here. |
| s1 AC-1/AC-2, s8 AC-1, R7 | Need CI at the final source commit: checks, charts, native image builds where the image filter requires them, and integrated-check. Existing earlier run references do not establish this revision. |
| s1 AC-3, s6 AC-2 | Added `tests/unit/test_import_linter_enforcement.py`: runs the real lint-imports CLI on disposable copies of source/config with caching disabled. A clean copy keeps all seven contracts; planted core→adapter and contract→core imports fail with the specific broken contract and import edge. Three cases pass locally. The checkout source is never modified by these tests. |
| s1 AC-4 | Need runner summary evidence containing peak used memory, free disk and kind-up-to-api-Ready time; local pytest cannot establish runner fit. |
| s12 AC-1–AC-4 | Existing spike notes, samples, CSVs, timed-load record and dated author decision are document/manual evidence. Record them through a matching live manifest or use an explicitly supported artifact evidence collection mode. They are not new pytest scenarios. |
| s13 AC-3, s5 AC-5 | The remediation executed the real `scripts/time-load.sh` on the pinned asset: 32,153 issues, 7.2 s wall duration, exit 0, within 600 s. See `../automate/remediation-live-evidence.md`. The separate v2 fixture invocation remains unexecuted; faked database tests do not prove it. |
| s13 AC-4 | Publishing is a person-run step with restored data and external Release effects. Record the actual version, checksum, release notes, subset/count/pairs/kinds, attribution and measured load time; do not republish merely to fabricate coverage. |
| s6 AC-3, s7 AC-3, s10 AC-3 | Need baseline and final responses on the same pinned corpus, with a JSON comparison and both revisions identified. Two calls on the current revision prove determinism, not historical before/after parity. |
| s9 AC-2, s10 AC-2, s11 AC-3 | The remediation run's actual checks can supply evidence, including default pytest deselection. Keep command output and verified source identity; no recursive pytest test is needed. |
| s9 AC-3 | Need deployed API logs after a known traced request: every nonempty log line parses as a JSON object and request-correlated records contain that trace id. Unit formatter checks stay unit-only. |
| s9 AC-4 | Grafana datasource API coverage remains useful, but opening the same trace in Explore is the stated human visual check. Record the observation; do not relabel an API response as visual verification. |
| s10 AC-4 | Need the first smoke invocation after an in-place upgrade, with the fresh load report check passing. A retry or forced-reload helper alone cannot establish first-run behavior. |
| s11 AC-2 | Need one recorded failure for each deployed break (schema, kind/outcome, golden twin, Tempo, backup), restoration after each, and the final passing run. Existing narrative is supporting history until matched to a verified source SHA. |
| NFR: read-only API role not exercised | Added and executed the real API-container role check on kind: SELECT succeeds and INSERT/UPDATE/DELETE fail with SQLSTATE 42501. Final integrated plus smoke run: 28 passed; see ../automate/remediation-live-evidence.md. |
| NFR: stale GitHub source-access and timed-load design | Test-design NFR Planning now describes local restored Jira ingest and person-run timed load. Historical GitHub test rows remain labeled as retired design history. Search p95 remains unthresholded and owned by epic 2, as AD-12 specifies. |

## Verification sequence

Run the existing checks against the final edits:

```sh
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run lint-imports
uv run pytest
```

On the intended local kind cluster, refresh the deployment and run integrated checks before smoke mutations:

```sh
scripts/kind-up.sh
uv run pytest -m kind tests/integrated tests/smoke -v
```

Use the gateway variables printed by kind-up where required. Preserve the full output, including the golden verdict/rank table. In CI, run the existing `ci.yml` workflow on a PR for the final commit; that workflow calls `_kind-deploy` with integrated then smoke checks.

Any live-results producer must record `schema_version` in supported major version `0`, a verified `source_sha`, `observed_at`, `producer`, and unique result records containing `id`, qualified `requirement_id` (for example `ticketscope--e1-s11--AC-1`), `status` (`pass`, `fail`, `blocked` or `skipped`), and `evidence`. Evidence attaches to criterion IDs, never `ticketscope--e1--R7` or ambiguous local `AC-1`. Record only actual observations. Do not label the uncommitted remediation worktree as verified merely because its parent HEAD has a SHA.

Finally start a fresh `/bmad-tea-trace` run for `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline`, providing any actual live-results artifact. Resume would restore the old frozen oracle without these source annotations. Repeat the test review and NFR assessment after execution to produce new scores; no scores were recomputed in this remediation document.
