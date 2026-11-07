---
runScope: 'epic'
runKey: 'epic-ticketscope--e1'
targetType: 'epic'
targetId: 'ticketscope--e1'
targetLabel: 'Epic 1: Keyword search over Mojang issues, deployed on kind'
workflowStatus: 'completed'
stepsCompleted: ['step-01-load-context', 'step-02-discover-tests', 'step-03-map-criteria', 'step-04-analyze-gaps', 'step-05-gate-decision']
lastStep: 'step-05-gate-decision'
lastSaved: '2026-11-07'
coverageBasis: 'acceptance_criteria'
oracleResolutionMode: 'formal_requirements'
oracleGranularity: 'requirements'
oracleConfidence: 'high'
oracleSources:
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml
externalPointerStatus: 'not_used'
gateType: 'epic'
sourceSha: 'e71a5ba4bb2851469df4ff665666d3ff5f6f5550'
---

# Traceability Report: Epic 1 (ticketscope--e1), Keyword search over Mojang issues, deployed on kind

## Gate Decision: FAIL 🚫

**Rationale:** P0 coverage is 50.0% (required: 100%). 2 critical requirement(s) below FULL coverage.

The gate ran on the requirement oracle: the epic's seven `R` lines are the gate rows. Each ticket criterion that names no `R` id stays in the gate as its own `unlinked` exception row. Of the epic's 46 ticket criteria, **45 name no `R` id**. The stories reach the requirements only through `covers` in `tickets.toml`, and the ledger rules do not count `covers` for numbered or plan criteria. So **six of the seven requirement rows have no contributor**, and R1's only contributor is spike 1.2's document check. Both P0 requirement rows (R5 and R7) are NONE, and Rule 1 fails the gate.

Two things drive that FAIL, and the next actions keep them apart:

1. **Traceability debt (structural).** The ticket criteria do not cite the requirements they prove. Fixing it changes tickets only, not tests.
2. **Real evidence gaps.** Stories 1.10 and 1.11 have never run in CI: they are local commits, three ahead of `origin/main`. The epic's R7 bar, "the integrated check passes on a PR", rests on a local kind run only. Several criteria were checked by hand (before/after `/v1` diffs, `time-load.sh`, the integrated-check breakage drill, the Grafana Explore view), and no committed test re-proves them.

## Coverage Summary

| Priority | Total | FULL | Coverage |
| --- | ---: | ---: | ---: |
| P0 | 4 | 2 | 50.0% |
| P1 | 23 | 13 | 56.52% |
| P2 | 20 | 8 | 40.0% |
| P3 | 5 | 1 | 20.0% |
| **All rows** | **52** | **24** | **46.15%** |

Gate criteria: P0 100% required (actual 50%, NOT MET); P1 90% target and 80% minimum (actual 56.52%, NOT MET); overall 80% minimum (actual 46.15%, NOT MET).

Test inventory: 37 pytest files, 740 cases (713 run by default, 27 `kind` cases deselected without a cluster). Local run on 2026-11-07: 712 passed, 1 xfailed (strict, documented product defect). The `kind` suites last ran in CI in run 42385558996 (PR #19, stories 1.5 to 1.9): 22 smoke tests passed. `tests/integrated` (story 1.11) has not run in CI. No tests are skipped, fixme or pending in the default run.

## Traceability Matrix

### Requirement Oracle Mapping

| Row | Kind | Priority | Coverage | Contributors | Missing behaviors |
| --- | --- | --- | --- | --- | --- |
| `ticketscope--e1--R1` | requirement | P2 (contributors) | NONE | `ticketscope--e1-s2--verify` (NONE) | a published snapshot validates against the committed JSON Schema; the snapshot holds both short and log-heavy issues |
| `ticketscope--e1--R2` | requirement | P1 (inferred) | NONE | none | no story covers it |
| `ticketscope--e1--R3` | requirement | P1 (inferred) | NONE | none | no story covers it |
| `ticketscope--e1--R4` | requirement | P1 (inferred) | NONE | none | no story covers it |
| `ticketscope--e1--R5` | requirement | P0 (inferred) | NONE | none | no story covers it |
| `ticketscope--e1--R6` | requirement | P1 (inferred) | NONE | none | no story covers it |
| `ticketscope--e1--R7` | requirement | P0 (inferred) | NONE | none | no story covers it |

#### Requirement details

##### ticketscope--e1--R1: An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues.

- Parent: parent R1
- Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:33`
- Coverage: **NONE**, priority P2 (contributors)
- Missing behaviors: a published snapshot validates against the committed JSON Schema; the snapshot holds both short and log-heavy issues

| Contributor | Story | Coverage |
| --- | --- | --- |
| `ticketscope--e1-s2--verify` | ticketscope--e1-s2 | NONE |

##### ticketscope--e1--R2: A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome.

- Parent: parent R1
- Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:34`
- Coverage: **NONE**, priority P1 (inferred)
- Missing behaviors: no story covers it

##### ticketscope--e1--R3: Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes.

- Parent: parent R2
- Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:35`
- Coverage: **NONE**, priority P1 (inferred)
- Missing behaviors: no story covers it

##### ticketscope--e1--R4: One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries.

- Parent: parent R5
- Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:36`
- Coverage: **NONE**, priority P1 (inferred)
- Missing behaviors: no story covers it

##### ticketscope--e1--R5: CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes.

- Parent: parent R3
- Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:37`
- Coverage: **NONE**, priority P0 (inferred)
- Missing behaviors: no story covers it

##### ticketscope--e1--R6: One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace.

- Parent: parent R8
- Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:38`
- Coverage: **NONE**, priority P1 (inferred)
- Missing behaviors: no story covers it

##### ticketscope--e1--R7: Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR.

- Parent: parent R11
- Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:39`
- Coverage: **NONE**, priority P0 (inferred)
- Missing behaviors: no story covers it

### Unlinked criteria (exception rows)

Each row names no epic `R` id, so it is scored on its own tests.

| Row | Priority | Coverage | Tests | Note |
| --- | --- | --- | --- | --- |
| `ticketscope--e1-s1--AC-1` | P0 | FULL | `tests/smoke/test_gateway.py`, `.github/workflows/ci.yml` | kind smoke suite (22 tests) passed in CI run 42385558996 |
| `ticketscope--e1-s1--AC-2` | P2 | NONE | none | CI job only; no test asserts it |
| `ticketscope--e1-s1--AC-3` | P1 | PARTIAL | `tests/unit/test_layer_imports.py` | contracts run in CI; no committed negative test plants the violation |
| `ticketscope--e1-s1--AC-4` | P3 | NONE | none | workflow step only |
| `ticketscope--e1-s3--AC-1` | P1 | PARTIAL | `tests/unit/test_ingest_jira.py` | GitHub ingest superseded by story 13; schema and no-identity checks carried over, github.com URL no longer applies |
| `ticketscope--e1-s3--AC-2` | P2 | FULL | `tests/unit/test_ingest_jira.py` | output set and digest asserted |
| `ticketscope--e1-s3--AC-3` | P1 | PARTIAL | `tests/unit/test_publish_script.py`, `tests/unit/test_ingest_notes.py`, `tests/unit/test_ingest_version.py` | snapshot.yml retired; publish is person-run; notes, versioning and publish guards are unit-tested |
| `ticketscope--e1-s12--AC-1` | P2 | NONE | none | document deliverable (findings.md); spike test_spike.py sits outside testpaths |
| `ticketscope--e1-s12--AC-2` | P2 | NONE | none | document deliverable |
| `ticketscope--e1-s12--AC-3` | P2 | NONE | none | document deliverable (epic Notes) |
| `ticketscope--e1-s12--AC-4` | P3 | NONE | none | human sign-off |
| `ticketscope--e1-s4--AC-1` | P2 | NONE | none | GitHub rules and their tests retired by story 10 (allowed by the epic) |
| `ticketscope--e1-s4--AC-2` | P1 | FULL | `tests/unit/test_snapshot.py` |  |
| `ticketscope--e1-s14--AC-1` | P1 | FULL | `tests/unit/test_derive_jira.py`, `tests/unit/test_derive_jira_expanded.py` |  |
| `ticketscope--e1-s14--AC-2` | P3 | NONE | none | GitHub-rule cases retired by story 10 |
| `ticketscope--e1-s14--AC-3` | P2 | FULL | `tests/unit/test_derive_jira.py`, `tests/unit/test_refactor_sweep_expanded.py` |  |
| `ticketscope--e1-s13--AC-1` | P1 | FULL | `tests/unit/test_ingest_jira.py` |  |
| `ticketscope--e1-s13--AC-2` | P2 | FULL | `tests/unit/test_snapshot.py` |  |
| `ticketscope--e1-s13--AC-3` | P2 | NONE | none | script run by hand; no committed test |
| `ticketscope--e1-s13--AC-4` | P1 | PARTIAL | `tests/unit/test_publish_script.py`, `tests/unit/test_ingest_notes.py` | person-run publish recorded (snapshot-2026.11.1); renderer and guards unit-tested |
| `ticketscope--e1-s5--AC-1` | P1 | FULL | `tests/smoke/test_gateway.py` | passed in CI run 42385558996 |
| `ticketscope--e1-s5--AC-2` | P1 | FULL | `tests/unit/test_load_main.py`, `tests/unit/test_release.py`, `tests/unit/test_postgres_corpus_meta.py` |  |
| `ticketscope--e1-s5--AC-3` | P1 | FULL | `tests/unit/test_snapshot.py`, `tests/unit/test_app.py`, `tests/unit/test_modes.py` |  |
| `ticketscope--e1-s5--AC-4` | P1 | FULL | `tests/unit/test_golden_queries.py` |  |
| `ticketscope--e1-s5--AC-5` | P2 | NONE | none | script run by hand; no committed test |
| `ticketscope--e1-s6--AC-1` | P1 | FULL | `tests/smoke/test_gateway.py`, `tests/unit/test_v1_contract_expanded.py` |  |
| `ticketscope--e1-s6--AC-2` | P1 | PARTIAL | `tests/unit/test_layer_imports.py` | no committed negative test |
| `ticketscope--e1-s6--AC-3` | P2 | NONE | none | manual before/after diff |
| `ticketscope--e1-s7--AC-1` | P1 | FULL | `tests/smoke/test_gateway.py`, `tests/integrated/test_done_when.py` |  |
| `ticketscope--e1-s7--AC-2` | P1 | FULL | `tests/smoke/test_gateway.py` |  |
| `ticketscope--e1-s7--AC-3` | P2 | NONE | none | manual before/after diff |
| `ticketscope--e1-s8--AC-1` | P0 | FULL | `tests/smoke/test_gateway.py`, `tests/unit/test_chart_backup.py` | passed in CI run 42385558996 |
| `ticketscope--e1-s8--AC-2` | P1 | FULL | `tests/smoke/test_gateway.py` |  |
| `ticketscope--e1-s8--AC-3` | P2 | FULL | `tests/smoke/test_gateway.py` |  |
| `ticketscope--e1-s9--AC-1` | P1 | FULL | `tests/smoke/test_gateway.py` |  |
| `ticketscope--e1-s9--AC-2` | P2 | FULL | `tests/unit/test_telemetry.py`, `tests/unit/test_telemetry_expanded.py` |  |
| `ticketscope--e1-s9--AC-3` | P2 | UNIT-ONLY | `tests/unit/test_telemetry.py` | JSON lines with ids asserted in unit; no kind check reads the pod log |
| `ticketscope--e1-s9--AC-4` | P3 | PARTIAL | `tests/smoke/test_gateway.py` | datasource proxy returns the tree; Explore view is manual |
| `ticketscope--e1-s10--AC-1` | P3 | FULL | `tests/unit/test_refactor_sweep_expanded.py` |  |
| `ticketscope--e1-s10--AC-2` | P2 | FULL | `tests/unit/test_refactor_sweep_expanded.py` |  |
| `ticketscope--e1-s10--AC-3` | P2 | NONE | none | manual local diff recorded in the plan; no test; not run in CI |
| `ticketscope--e1-s10--AC-4` | P2 | FULL | `tests/smoke/test_gateway.py` | test_load_log_has_the_report forces a reload after a no-op |
| `ticketscope--e1-s11--AC-1` | P1 | FULL | `tests/integrated/test_done_when.py`, `tests/unit/test_integrated_check_expanded.py` | passed locally (plan); never run in CI |
| `ticketscope--e1-s11--AC-2` | P1 | PARTIAL | `tests/integrated/test_done_when.py` | breakage drill done by hand and recorded; not re-runnable |
| `ticketscope--e1-s11--AC-3` | P2 | FULL | `tests/unit/test_integrated_check_expanded.py` | 27 deselected in the 2026-11-07 local run |

#### Unlinked criterion text

- `ticketscope--e1-s1--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:94`): Given a PR, when ci.yml runs, then ruff, pyright, pytest and lint-imports pass, and _kind-deploy brings up both releases and passes the smoke test.
- `ticketscope--e1-s1--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:95`): Given a PR that changes images/, when ci.yml runs, then both images build for linux/amd64 and linux/arm64.
- `ticketscope--e1-s1--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:96`): Given a one-line change that makes a core module import ticketscope.adapters.postgres, when lint-imports runs, then it fails.
- `ticketscope--e1-s1--AC-4` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:97`): Given a _kind-deploy run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.
- `ticketscope--e1-s3--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:91`): Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's url is its github.com issue URL, and no recorded user.login value appears anywhere in the gzipped output.
- `ticketscope--e1-s3--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:92`): Given a completed run, when the outputs are listed, then <version>.jsonl.gz, <version>.jsonl.gz.sha256 (matching sha256sum -c), <version>-kinds.json and report.json exist.
- `ticketscope--e1-s3--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:93`): Given snapshot.yml is dispatched on main (person's step), when it finishes, then a snapshot-YYYY.MM.N Release holds the asset and checksum, and its notes state window, count, kind split, load seconds <= 600, attribution and the takedown path; a second dispatch publishes N+1 and leaves the first unchanged.
- `ticketscope--e1-s12--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:65`): The instances and leading projects are compared on the decision rule
- `ticketscope--e1-s12--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:67`): The recommended subset is shown to work
- `ticketscope--e1-s12--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:69`): The answer and its consequences are recorded where the waiting tickets read them
- `ticketscope--e1-s12--AC-4` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:78`): The author accepts it
- `ticketscope--e1-s4--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:80`): Given the unit suite, when uv run pytest tests/unit/test_derive.py -v runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at threshold-1 and threshold.
- `ticketscope--e1-s4--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:81`): Given the default threshold, when derive_kind runs over each issue in snapshot/fixture.jsonl, then it returns the kind in snapshot/fixture-kinds.json (checked by hand in Implementation Notes; story 5 owns the committed test).
- `ticketscope--e1-s14--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:91`): Given the unit suite, when uv run pytest tests/unit/test_derive_jira.py -v runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with {code} and {noformat} blocks on either side of the threshold.
- `ticketscope--e1-s14--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:92`): Given story 4's suite, when uv run pytest tests/unit/test_derive.py runs, then every GitHub-rule case still passes.
- `ticketscope--e1-s14--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:93`): Given the defaults, when derivation_version() is called, then it returns kind2-t3.outcome3, not story 4's kind1-t3.outcome2.
- `ticketscope--e1-s13--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:95`): Given the recorded slice, when ingest runs through jira.select and main.write_outputs, then every line validates against schema-v2.json and parses as SnapshotIssueV2, and sha256sum -c passes.
- `ticketscope--e1-s13--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:96`): Given SnapshotIssueV2 changes, when tests run, then the schema drift test fails until python -m ticketscope.jobs.ingest.schema --write is rerun.
- `ticketscope--e1-s13--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:97`): Given the v2 fixture, when scripts/time-load.sh runs on it, then it prints a load time and exits 0.
- `ticketscope--e1-s13--AC-4` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:98`): Given a restored dump on the person's machine after merge, when scripts/publish-snapshot.sh runs, then a snapshot-YYYY.MM.N Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds <= 600 and the attribution line.
- `ticketscope--e1-s5--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:96`): Given the kind CI run, when uv run pytest -m kind tests/smoke runs after kind-up.sh, then checks (1)-(6) pass on snapshot 2026.11.1.
- `ticketscope--e1-s5--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:97`): Given an asset whose checksum differs from the pin, when load runs against a DB already holding a corpus, then it exits 1 and the corpus and corpus_meta are unchanged (unit test with fakes, plus the adapter test).
- `ticketscope--e1-s5--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:98`): Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals fixture-kinds.json, and test_app/test_modes still find TARGET_NUMBER at rank 1.
- `ticketscope--e1-s5--AC-4` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:99`): Given eval/golden-queries.json, when test_golden_queries.py runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.
- `ticketscope--e1-s5--AC-5` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:100`): Given scripts/time-load.sh <dir> 2026.11.1 with only the asset in <dir>, when it runs, then it exits 0 and prints a time under 600.
- `ticketscope--e1-s6--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:96`): Given the kind cluster with this branch's image, when uv run pytest -m kind tests/smoke runs, then every smoke test passes, the new /v1 checks included.
- `ticketscope--e1-s6--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:97`): Given src/ticketscope/core/modes.py imports ticketscope.adapters.postgres, when uv run lint-imports runs, then it fails (the layering is unchanged).
- `ticketscope--e1-s6--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:98`): Given a POST /v1/search response saved before this change, when the same request runs after it, then the body is identical.
- `ticketscope--e1-s7--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:80`): Given the kind cluster running this branch's image, when the vague and the log-heavy query from eval/golden-queries.json are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.
- `ticketscope--e1-s7--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:81`): Given uv run pytest -m kind tests/smoke on that cluster, when it runs, then every smoke test passes, including section (1c).
- `ticketscope--e1-s7--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:82`): Given a POST /v1/search body saved before this change, when the same request runs after it, then the body is identical.
- `ticketscope--e1-s8--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:92`): Given a PR, when ci.yml runs, then the checks and charts jobs pass, and _kind-deploy passes every kind smoke test, including test (7).
- `ticketscope--e1-s8--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:93`): Given scripts/kind-up.sh on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches completed and its objects are listed in the ticketscope-backups bucket.
- `ticketscope--e1-s8--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:94`): Given a second scripts/kind-up.sh run on the same cluster, when it finishes, then the plugin TLS Secrets and ticketscope-backup-s3 carry the same data as before the run.
- `ticketscope--e1-s9--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:96`): Given the kind cluster from scripts/kind-up.sh on this branch, when uv run pytest -m kind tests/smoke runs, then every test passes, including (8) and (8b).
- `ticketscope--e1-s9--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:97`): Given the repo, when uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest runs, then all pass, including test_telemetry.py.
- `ticketscope--e1-s9--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:98`): Given the api pod on kind, when kubectl -n ticketscope logs deploy/ticketscope-api is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's trace_id.
- `ticketscope--e1-s9--AC-4` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:99`): Given Grafana port-forwarded (kubectl -n platform port-forward svc/grafana 3000:80), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).
- `ticketscope--e1-s10--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:69`): Given the change, when grep -rnE "SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS" src tests runs, then it finds nothing.
- `ticketscope--e1-s10--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:70`): Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and preprocessing_version() still returns pre1.kind2-t3.outcome3.
- `ticketscope--e1-s10--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:71`): Given a kind cluster that ran the baseline and then kind-up.sh on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.
- `ticketscope--e1-s10--AC-4` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:72`): Given a cluster that was just upgraded in place, when uv run pytest -m kind tests/smoke runs once, then (3) passes on the first run.
- `ticketscope--e1-s11--AC-1` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:70`): Given the local kind cluster on the pinned snapshot, when uv run pytest -m kind tests/integrated -v runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.
- `ticketscope--e1-s11--AC-2` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:71`): Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.
- `ticketscope--e1-s11--AC-3` (`_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:72`): Given the change, when uv run pytest runs without a cluster, then the integrated module is deselected and the new unit tests pass.

### Advisory: story-level view through `covers` (not gating)

This view is not the gate; it shows where behavioral evidence sits if each story's `covers` were counted.

| Requirement | Stories (covers) | Strongest test evidence | What is still unproven |
| --- | --- | --- | --- |
| R1 snapshot published and valid | 1.2, 1.3, 1.12, 1.13, 1.11 | `tests/unit/test_ingest_jira.py` (schema v2, masking, no identities); `tests/integrated/test_done_when.py` check (1) | Person-run publish, recorded only in the plan and Release notes |
| R2 load stores kind and outcome, reports shares | 1.4, 1.14, 1.5, 1.11 | kind smoke (2), (3) in CI; `tests/unit/test_load_main.py` | none beyond the CI gap for 1.11 |
| R3 `/v1/search` ranks with outcomes | 1.1, 1.6, 1.11 | kind smoke `/v1` checks in CI; `tests/unit/test_v1_contract_expanded.py` | The vague query's twin ranks 5 and the log-heavy one ranks 9 (R-004 is mitigated, not closed) |
| R4 page renders both example queries | 1.7, 1.11 | `test_page_renders_each_golden_query` in CI | The 405 `Allow` header defect (strict xfail) |
| R5 CNPG on kind with backups | 1.1, 1.8, 1.11 | two ready instances and a completed backup, kind smoke in CI | Integrated check (5) not run in CI |
| R6 one trace in Tempo and Grafana | 1.9, 1.11 | Tempo and Grafana datasource smoke tests in CI | Explore view is manual |
| R7 Helm and CI on kind every PR | 1.1, 1.11 | `_kind-deploy` green on PR #19 | `integrated-check` job never run on a PR |

## Gaps & Recommendations

1. **P0. Link criteria to requirements.** Give each story leaf numbered criteria that name the epic `R` ids, or add `(R<n>)` to plan acceptance criteria, then re-run `bmad-tea-trace`. Without this every requirement row stays NONE, whatever the tests prove.
2. **P0. Run the integrated check on a PR.** Push stories 1.9 (confirm), 1.10 and 1.11, open the PR, and get `integrated-check` green on GitHub-hosted kind (R5, R7).
3. **P1. Add committed negative tests** for the layering rule (a planted core-imports-adapter change fails `lint-imports`, criteria 1.1 AC-3 and 1.6 AC-2) and the `ticketscope_ro` write refusal (NFR audit).
4. **P2. Replace manual checks with committed ones:** the before/after `/v1` body diffs (1.6 AC-3, 1.7 AC-3, 1.10 AC-3), `time-load.sh` (1.13 AC-3, 1.5 AC-5) and a pod-log JSON check on kind (1.9 AC-3).
5. **P2. Retire superseded criteria.** 1.3 AC-1 and AC-3 (GitHub ingest and `snapshot.yml`), 1.4 AC-1 and 1.14 AC-2 (GitHub rules retired by the sweep) can no longer be met by design. Mark them superseded in the plans so they leave the denominator honestly.

## Waiver Register Review

No waiver register was found for this target. No waiver was applied; this workflow never applies one.

## Related Reports

- Test quality: `_bmad-output/test-artifacts/test-review/test-review-epic-1.md` (79/100, Request Changes: 4 HIGH determinism findings)
- NFR audit: `_bmad-output/test-artifacts/nfr/nfr-assessment-epic-1.md` (CONCERNS)
- Machine-readable: `_bmad-output/test-artifacts/trace/e2e-trace-summary-epic-ticketscope--e1.json`, `_bmad-output/test-artifacts/trace/gate-decision-epic-ticketscope--e1.json`

## Next Actions

🚫 GATE: FAIL. The epic is not release-ready until coverage improves. Do actions 1 and 2 above, then re-run `bmad-tea-trace` with gate type `epic`.

### Requirement Aggregation

```json
{
  "criterionMatrix": [
    {
      "id": "ticketscope--e1-s1--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s1--AC-2",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s1--AC-3",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s1--AC-4",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s2--verify",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s3--AC-1",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s3--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s3--AC-3",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s12--AC-1",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s12--AC-2",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s12--AC-3",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s12--AC-4",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s4--AC-1",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s4--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s14--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s14--AC-2",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s14--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s13--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s13--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s13--AC-3",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s13--AC-4",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s5--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s5--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s5--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s5--AC-4",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s5--AC-5",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s6--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s6--AC-2",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s6--AC-3",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s7--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s7--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s7--AC-3",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s8--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s8--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s8--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s9--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s9--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s9--AC-3",
      "coverage": "UNIT-ONLY"
    },
    {
      "id": "ticketscope--e1-s9--AC-4",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s10--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s10--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s10--AC-3",
      "coverage": "NONE"
    },
    {
      "id": "ticketscope--e1-s10--AC-4",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s11--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s11--AC-2",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s11--AC-3",
      "coverage": "FULL"
    }
  ],
  "traceabilityMatrix": [
    {
      "id": "ticketscope--e1--R1",
      "kind": "requirement",
      "coverage": "NONE",
      "contributors": [
        {
          "id": "ticketscope--e1-s2--verify",
          "story": "ticketscope--e1-s2",
          "coverage": "NONE"
        }
      ],
      "missingBehaviors": [
        "a published snapshot validates against the committed JSON Schema",
        "the snapshot holds both short and log-heavy issues"
      ]
    },
    {
      "id": "ticketscope--e1--R2",
      "kind": "requirement",
      "coverage": "NONE",
      "contributors": [],
      "missingBehaviors": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R3",
      "kind": "requirement",
      "coverage": "NONE",
      "contributors": [],
      "missingBehaviors": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R4",
      "kind": "requirement",
      "coverage": "NONE",
      "contributors": [],
      "missingBehaviors": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R5",
      "kind": "requirement",
      "coverage": "NONE",
      "contributors": [],
      "missingBehaviors": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R6",
      "kind": "requirement",
      "coverage": "NONE",
      "contributors": [],
      "missingBehaviors": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R7",
      "kind": "requirement",
      "coverage": "NONE",
      "contributors": [],
      "missingBehaviors": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1-s1--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s1--AC-2",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s1--AC-3",
      "kind": "exception",
      "coverage": "PARTIAL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s1--AC-4",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s3--AC-1",
      "kind": "exception",
      "coverage": "PARTIAL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s3--AC-2",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s3--AC-3",
      "kind": "exception",
      "coverage": "PARTIAL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s12--AC-1",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s12--AC-2",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s12--AC-3",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s12--AC-4",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s4--AC-1",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s4--AC-2",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s14--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s14--AC-2",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s14--AC-3",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s13--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s13--AC-2",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s13--AC-3",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s13--AC-4",
      "kind": "exception",
      "coverage": "PARTIAL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s5--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s5--AC-2",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s5--AC-3",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s5--AC-4",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s5--AC-5",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s6--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s6--AC-2",
      "kind": "exception",
      "coverage": "PARTIAL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s6--AC-3",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s7--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s7--AC-2",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s7--AC-3",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s8--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s8--AC-2",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s8--AC-3",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s9--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s9--AC-2",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s9--AC-3",
      "kind": "exception",
      "coverage": "UNIT-ONLY",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s9--AC-4",
      "kind": "exception",
      "coverage": "PARTIAL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s10--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s10--AC-2",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s10--AC-3",
      "kind": "exception",
      "coverage": "NONE",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s10--AC-4",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s11--AC-1",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s11--AC-2",
      "kind": "exception",
      "coverage": "PARTIAL",
      "exception": "unlinked"
    },
    {
      "id": "ticketscope--e1-s11--AC-3",
      "kind": "exception",
      "coverage": "FULL",
      "exception": "unlinked"
    }
  ]
}
```
