---
runScope: epic
runKey: epic-ticketscope--e1
targetType: epic
targetId: ticketscope--e1
targetLabel: 'Epic 1: Keyword search over Mojang issues, deployed on kind'
workflowStatus: completed
stepsCompleted:
- step-01-load-context
- step-02-discover-tests
- step-03-map-criteria
- step-04-analyze-gaps
- step-05-gate-decision
lastStep: step-05-gate-decision
lastSaved: '2026-11-07'
coverageBasis: acceptance_criteria
oracleConfidence: high
oracleResolutionMode: formal_requirements
oracleSources:
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md
- _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md
externalPointerStatus: not_used
oracleGranularity: requirements
collectionStatus: COLLECTED
sourceSha: 6400e5ac8e3bb4cadeea8061a5581c33b2b45036
criterionLedger:
- id: ticketscope--e1-s1--AC-1
  localId: AC-1
  story: ticketscope--e1-s1
  name: Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.
  text: Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test. (R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:94
  priority: P0
  priorityBasis: inferred
  declaredLinks:
  - R7
  validLinks:
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s1--AC-2
  localId: AC-2
  story: ticketscope--e1-s1
  name: Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.
  text: Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`. (R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:95
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R7
  validLinks:
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s1--AC-3
  localId: AC-3
  story: ticketscope--e1-s1
  name: Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.
  text: Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails. (R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:96
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R7
  validLinks:
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s1--AC-4
  localId: AC-4
  story: ticketscope--e1-s1
  name: Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.
  text: Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready. (R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:97
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R7
  validLinks:
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s2--verify
  localId: verify
  story: ticketscope--e1-s2
  name: The epic's Notes hold a dated Decision line that says yes, yes with named conditions, or no, and story 3's entry reflects any conditions.
  text: The epic's Notes hold a dated Decision line that says yes, yes with named conditions, or no, and story 3's entry reflects any conditions.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml:27
  priority: P2
  priorityBasis: inferred
  declaredLinks:
  - R1
  validLinks:
  - R1
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s3--AC-1
  localId: AC-1
  story: ticketscope--e1-s3
  name: Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.
  text: Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:91
  priority: P0
  priorityBasis: inferred
  declaredLinks: []
  validLinks: []
  invalidLinks: []
  exception: unlinked
- id: ticketscope--e1-s3--AC-2
  localId: AC-2
  story: ticketscope--e1-s3
  name: Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.
  text: Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:92
  priority: P1
  priorityBasis: inferred
  declaredLinks: []
  validLinks: []
  invalidLinks: []
  exception: unlinked
- id: ticketscope--e1-s3--AC-3
  localId: AC-3
  story: ticketscope--e1-s3
  name: Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.
  text: Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:93
  priority: P1
  priorityBasis: inferred
  declaredLinks: []
  validLinks: []
  invalidLinks: []
  exception: unlinked
- id: ticketscope--e1-s12--AC-1
  localId: AC-1
  story: ticketscope--e1-s12
  name: The instances and leading projects are compared on the decision rule
  text: '**The instances and leading projects are compared on the decision rule** (R1) Verify: a findings note beside this ticket holds a table per instance and per leading project. Each table gives the issue count, in-subset duplicate pairs by kind, the outcome shares under the proposed mapping, the issue-type mix, and the text-hygiene counts. The CSVs it was built from sit with it.'
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:65
  priority: P2
  priorityBasis: inferred
  declaredLinks:
  - R1
  validLinks:
  - R1
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s12--AC-2
  localId: AC-2
  story: ticketscope--e1-s12
  name: The recommended subset is shown to work
  text: '**The recommended subset is shown to work** (R1) Verify: the findings note names the subset and its expected duplicate-pair count by kind. It shows the subset''s measured load time through story 3''s timed-load script within 600 s, and 20 sampled issues per leading candidate with the author''s judgement of each.'
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:67
  priority: P2
  priorityBasis: inferred
  declaredLinks:
  - R1
  validLinks:
  - R1
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s12--AC-3
  localId: AC-3
  story: ticketscope--e1-s12
  name: The answer and its consequences are recorded where the waiting tickets read them
  text: '**The answer and its consequences are recorded where the waiting tickets read them** (R1) Verify: the epic''s Notes holds a dated Decision line: switch, stay, or switch with named conditions. On switch, the line names:  - the subset; - the `resolution`-to-outcome mapping and the "answered" rule; - the kind rule extended to Jira `{code}` and `{noformat}` blocks, since a kind-rule change needs a reload and a baseline update (epic Constraints, Kind rule); - the attribution line.  It also amends the epic''s Corpus scope (the 20,000 cap and the source) and Corpus terms for the new source, and says the data lane and epic-eval-gate are to be replanned.'
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:69
  priority: P2
  priorityBasis: inferred
  declaredLinks:
  - R1
  validLinks:
  - R1
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s12--AC-4
  localId: AC-4
  story: ticketscope--e1-s12
  name: The author accepts it
  text: '**The author accepts it** (R1) Verify: the Decision line is attributed to the author (user) and dated.'
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:78
  priority: P2
  priorityBasis: inferred
  declaredLinks:
  - R1
  validLinks:
  - R1
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s4--AC-1
  localId: AC-1
  story: ticketscope--e1-s4
  name: Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.
  text: Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:80
  priority: P1
  priorityBasis: inferred
  declaredLinks: []
  validLinks: []
  invalidLinks: []
  exception: unlinked
- id: ticketscope--e1-s4--AC-2
  localId: AC-2
  story: ticketscope--e1-s4
  name: Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).
  text: Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:81
  priority: P1
  priorityBasis: inferred
  declaredLinks: []
  validLinks: []
  invalidLinks: []
  exception: unlinked
- id: ticketscope--e1-s14--AC-1
  localId: AC-1
  story: ticketscope--e1-s14
  name: Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.
  text: Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold. (R2)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:91
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R2
  validLinks:
  - R2
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s14--AC-2
  localId: AC-2
  story: ticketscope--e1-s14
  name: Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.
  text: Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:92
  priority: P1
  priorityBasis: inferred
  declaredLinks: []
  validLinks: []
  invalidLinks: []
  exception: unlinked
- id: ticketscope--e1-s14--AC-3
  localId: AC-3
  story: ticketscope--e1-s14
  name: Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.
  text: Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`. (R2)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:93
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R2
  validLinks:
  - R2
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s13--AC-1
  localId: AC-1
  story: ticketscope--e1-s13
  name: Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.
  text: Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes. (R1)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:95
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R1
  validLinks:
  - R1
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s13--AC-2
  localId: AC-2
  story: ticketscope--e1-s13
  name: Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.
  text: Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun. (R1)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:96
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R1
  validLinks:
  - R1
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s13--AC-3
  localId: AC-3
  story: ticketscope--e1-s13
  name: Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.
  text: Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0. (R1, R2)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:97
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R1
  - R2
  validLinks:
  - R1
  - R2
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s13--AC-4
  localId: AC-4
  story: ticketscope--e1-s13
  name: Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line.
  text: Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line. (R1)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:98
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R1
  validLinks:
  - R1
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s5--AC-1
  localId: AC-1
  story: ticketscope--e1-s5
  name: Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)–(6) pass on snapshot 2026.11.1.
  text: Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)–(6) pass on snapshot 2026.11.1. (R2, R3, R5, R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:96
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R2
  - R3
  - R5
  - R7
  validLinks:
  - R2
  - R3
  - R5
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s5--AC-2
  localId: AC-2
  story: ticketscope--e1-s5
  name: Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).
  text: Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test). (R2)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:97
  priority: P0
  priorityBasis: inferred
  declaredLinks:
  - R2
  validLinks:
  - R2
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s5--AC-3
  localId: AC-3
  story: ticketscope--e1-s5
  name: Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.
  text: Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1. (R2, R3)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:98
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R2
  - R3
  validLinks:
  - R2
  - R3
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s5--AC-4
  localId: AC-4
  story: ticketscope--e1-s5
  name: Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.
  text: Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source. (R3, R4)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:99
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R3
  - R4
  validLinks:
  - R3
  - R4
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s5--AC-5
  localId: AC-5
  story: ticketscope--e1-s5
  name: Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.
  text: Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600. (R2)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:100
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R2
  validLinks:
  - R2
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s6--AC-1
  localId: AC-1
  story: ticketscope--e1-s6
  name: Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.
  text: Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included. (R3)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:96
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R3
  validLinks:
  - R3
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s6--AC-2
  localId: AC-2
  story: ticketscope--e1-s6
  name: Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).
  text: Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged). (R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:97
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R7
  validLinks:
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s6--AC-3
  localId: AC-3
  story: ticketscope--e1-s6
  name: Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.
  text: Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical. (R3)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:98
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R3
  validLinks:
  - R3
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s7--AC-1
  localId: AC-1
  story: ticketscope--e1-s7
  name: Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.
  text: Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome. (R4)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:80
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R4
  validLinks:
  - R4
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s7--AC-2
  localId: AC-2
  story: ticketscope--e1-s7
  name: Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).
  text: Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c). (R4, R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:81
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R4
  - R7
  validLinks:
  - R4
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s7--AC-3
  localId: AC-3
  story: ticketscope--e1-s7
  name: Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.
  text: Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical. (R3)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:82
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R3
  validLinks:
  - R3
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s8--AC-1
  localId: AC-1
  story: ticketscope--e1-s8
  name: Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).
  text: Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7). (R5, R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:92
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R5
  - R7
  validLinks:
  - R5
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s8--AC-2
  localId: AC-2
  story: ticketscope--e1-s8
  name: Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.
  text: Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket. (R5)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:93
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R5
  validLinks:
  - R5
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s8--AC-3
  localId: AC-3
  story: ticketscope--e1-s8
  name: Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.
  text: Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run. (R5)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:94
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R5
  validLinks:
  - R5
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s9--AC-1
  localId: AC-1
  story: ticketscope--e1-s9
  name: Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).
  text: Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b). (R6)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:96
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R6
  validLinks:
  - R6
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s9--AC-2
  localId: AC-2
  story: ticketscope--e1-s9
  name: Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.
  text: Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`. (R6, R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:97
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R6
  - R7
  validLinks:
  - R6
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s9--AC-3
  localId: AC-3
  story: ticketscope--e1-s9
  name: Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.
  text: Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`. (R6)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:98
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R6
  validLinks:
  - R6
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s9--AC-4
  localId: AC-4
  story: ticketscope--e1-s9
  name: Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).
  text: Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual). (R6)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:99
  priority: P3
  priorityBasis: inferred
  declaredLinks:
  - R6
  validLinks:
  - R6
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s10--AC-1
  localId: AC-1
  story: ticketscope--e1-s10
  name: Given the change, when `grep -rnE "SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS" src tests` runs, then it finds nothing.
  text: Given the change, when `grep -rnE "SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS" src tests` runs, then it finds nothing. (R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:69
  priority: P2
  priorityBasis: inferred
  declaredLinks:
  - R7
  validLinks:
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s10--AC-2
  localId: AC-2
  story: ticketscope--e1-s10
  name: Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.
  text: Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`. (R2, R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:70
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R2
  - R7
  validLinks:
  - R2
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s10--AC-3
  localId: AC-3
  story: ticketscope--e1-s10
  name: Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.
  text: Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical. (R3, R4)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:71
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R3
  - R4
  validLinks:
  - R3
  - R4
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s10--AC-4
  localId: AC-4
  story: ticketscope--e1-s10
  name: Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.
  text: Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run. (R2, R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:72
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R2
  - R7
  validLinks:
  - R2
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s11--AC-1
  localId: AC-1
  story: ticketscope--e1-s11
  name: Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.
  text: Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank. (R1, R2, R3, R4, R5, R6, R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:70
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R1
  - R2
  - R3
  - R4
  - R5
  - R6
  - R7
  validLinks:
  - R1
  - R2
  - R3
  - R4
  - R5
  - R6
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s11--AC-2
  localId: AC-2
  story: ticketscope--e1-s11
  name: Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.
  text: Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again. (R1, R2, R3, R4, R5, R6, R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:71
  priority: P2
  priorityBasis: inferred
  declaredLinks:
  - R1
  - R2
  - R3
  - R4
  - R5
  - R6
  - R7
  validLinks:
  - R1
  - R2
  - R3
  - R4
  - R5
  - R6
  - R7
  invalidLinks: []
  exception: none
- id: ticketscope--e1-s11--AC-3
  localId: AC-3
  story: ticketscope--e1-s11
  name: Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.
  text: Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass. (R7)
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:72
  priority: P1
  priorityBasis: inferred
  declaredLinks:
  - R7
  validLinks:
  - R7
  invalidLinks: []
  exception: none
oracleLedger:
- id: ticketscope--e1--R1
  kind: requirement
  requirement: An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues.
  parent: parent R1
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:33
  priority: P1
  priorityBasis: contributors
  contributors:
  - ticketscope--e1-s2--verify
  - ticketscope--e1-s12--AC-1
  - ticketscope--e1-s12--AC-2
  - ticketscope--e1-s12--AC-3
  - ticketscope--e1-s12--AC-4
  - ticketscope--e1-s13--AC-1
  - ticketscope--e1-s13--AC-2
  - ticketscope--e1-s13--AC-3
  - ticketscope--e1-s13--AC-4
  - ticketscope--e1-s11--AC-1
  - ticketscope--e1-s11--AC-2
- id: ticketscope--e1--R2
  kind: requirement
  requirement: A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome.
  parent: parent R1
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:34
  priority: P0
  priorityBasis: contributors
  contributors:
  - ticketscope--e1-s14--AC-1
  - ticketscope--e1-s14--AC-3
  - ticketscope--e1-s13--AC-3
  - ticketscope--e1-s5--AC-1
  - ticketscope--e1-s5--AC-2
  - ticketscope--e1-s5--AC-3
  - ticketscope--e1-s5--AC-5
  - ticketscope--e1-s10--AC-2
  - ticketscope--e1-s10--AC-4
  - ticketscope--e1-s11--AC-1
  - ticketscope--e1-s11--AC-2
- id: ticketscope--e1--R3
  kind: requirement
  requirement: Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes.
  parent: parent R2
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:35
  priority: P1
  priorityBasis: contributors
  contributors:
  - ticketscope--e1-s5--AC-1
  - ticketscope--e1-s5--AC-3
  - ticketscope--e1-s5--AC-4
  - ticketscope--e1-s6--AC-1
  - ticketscope--e1-s6--AC-3
  - ticketscope--e1-s7--AC-3
  - ticketscope--e1-s10--AC-3
  - ticketscope--e1-s11--AC-1
  - ticketscope--e1-s11--AC-2
- id: ticketscope--e1--R4
  kind: requirement
  requirement: One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries.
  parent: parent R5
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:36
  priority: P1
  priorityBasis: contributors
  contributors:
  - ticketscope--e1-s5--AC-4
  - ticketscope--e1-s7--AC-1
  - ticketscope--e1-s7--AC-2
  - ticketscope--e1-s10--AC-3
  - ticketscope--e1-s11--AC-1
  - ticketscope--e1-s11--AC-2
- id: ticketscope--e1--R5
  kind: requirement
  requirement: CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes.
  parent: parent R3
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:37
  priority: P1
  priorityBasis: contributors
  contributors:
  - ticketscope--e1-s5--AC-1
  - ticketscope--e1-s8--AC-1
  - ticketscope--e1-s8--AC-2
  - ticketscope--e1-s8--AC-3
  - ticketscope--e1-s11--AC-1
  - ticketscope--e1-s11--AC-2
- id: ticketscope--e1--R6
  kind: requirement
  requirement: One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace.
  parent: parent R8
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:38
  priority: P1
  priorityBasis: contributors
  contributors:
  - ticketscope--e1-s9--AC-1
  - ticketscope--e1-s9--AC-2
  - ticketscope--e1-s9--AC-3
  - ticketscope--e1-s9--AC-4
  - ticketscope--e1-s11--AC-1
  - ticketscope--e1-s11--AC-2
- id: ticketscope--e1--R7
  kind: requirement
  requirement: Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR.
  parent: parent R11
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:39
  priority: P0
  priorityBasis: contributors
  contributors:
  - ticketscope--e1-s1--AC-1
  - ticketscope--e1-s1--AC-2
  - ticketscope--e1-s1--AC-3
  - ticketscope--e1-s1--AC-4
  - ticketscope--e1-s5--AC-1
  - ticketscope--e1-s6--AC-2
  - ticketscope--e1-s7--AC-2
  - ticketscope--e1-s8--AC-1
  - ticketscope--e1-s9--AC-2
  - ticketscope--e1-s10--AC-1
  - ticketscope--e1-s10--AC-2
  - ticketscope--e1-s10--AC-4
  - ticketscope--e1-s11--AC-1
  - ticketscope--e1-s11--AC-2
  - ticketscope--e1-s11--AC-3
- id: ticketscope--e1-s3--AC-1
  kind: exception
  exception: unlinked
  requirement: Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:91
  priority: P0
  priorityBasis: inferred
- id: ticketscope--e1-s3--AC-2
  kind: exception
  exception: unlinked
  requirement: Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:92
  priority: P1
  priorityBasis: inferred
- id: ticketscope--e1-s3--AC-3
  kind: exception
  exception: unlinked
  requirement: Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:93
  priority: P1
  priorityBasis: inferred
- id: ticketscope--e1-s4--AC-1
  kind: exception
  exception: unlinked
  requirement: Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:80
  priority: P1
  priorityBasis: inferred
- id: ticketscope--e1-s4--AC-2
  kind: exception
  exception: unlinked
  requirement: Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:81
  priority: P1
  priorityBasis: inferred
- id: ticketscope--e1-s14--AC-2
  kind: exception
  exception: unlinked
  requirement: Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.
  source: _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:92
  priority: P1
  priorityBasis: inferred
---

# Traceability Matrix & Gate Decision — Epic 1: Keyword search over Mojang issues, deployed on kind

## Gate Decision: WAIVED (derived: FAIL)

**Override:** W-001 (`_bmad-output/test-artifacts/gate-waivers.md`, valid on every Waiver Scenarios check) applied by Dillon, Product Owner, on 2026-11-07; expires 2027-11-07. It covers the six superseded GitHub-era criteria (s3 AC-1..3, s4 AC-1..2, s14 AC-2). The derived decision below is unchanged: this workflow never applies a waiver.

### Derived Decision: FAIL

**Rationale:** P0 coverage is 67% (required: 100%). 1 critical requirement(s) below FULL coverage. Overall FULL coverage is 69% (minimum 80%); P1 is 70% (minimum 80%, PASS target 90%).

**Date:** 2026-11-07. **Evaluator:** Claude Code / Master Test Architect. **Source:** `6400e5ac8e3bb4cadeea8061a5581c33b2b45036` (previous trace: `53358199a43fee326e8834d0d7c881a2a566b54a`).

## Have the gaps been closed?

Mostly. **42 of 46 criteria are FULL** (18 at the original trace, 26 after the first CI run). This round closed s1 AC-2 (dispatched multi-arch image build), s5 AC-5 and s13 AC-3 (timed loads, new tests), s9 AC-3 (deployed api log correlation, new test), s10 AC-4 (one smoke pass after an in-place upgrade), s11 AC-2 (five fault injections, each failing exactly its own check and passing on restore), and s6/s7/s10 AC-3 (byte-identical /v1/search bodies before and after each change). Evidence: CI runs [42414691589](https://github.com/Dillon-Based/ticketscope/actions/runs/42414691589) (PR) and [42415340129](https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129) (dispatch) at `6400e5a`, whose new evidence job generated the live results, plus local kind runs of `scripts/fault-inject.sh` and `scripts/v1-parity.sh` at the same commit (raw files in `_bmad-output/test-artifacts/automate/live-evidence-6400e5a/`). R2 and R7, both P0, are now FULL, as are R3, R4 and R5.

Since then the author approved the seven human-check records (spike 12 AC-1..4, spike 2, the snapshot-2026.11.1 publish, and the Grafana Explore look for s9 AC-4), closing R1 and R6. Every requirement R1-R7 is now FULL. The gate still FAILS only on the six retired GitHub criteria, s3 AC-1 being P0; the trace contract cannot retire a criterion of a done story, so the remaining path is the waiver in `gate-waivers.md` and a human WAIVED override.

**Gate arithmetic:** 13 rows; R1-R7 FULL, plus s3 AC-2 and s4 AC-2. The other four retired criteria hold P0 at 2 of 3 and P1 at 7 of 10. They are the whole remaining gap.

## Coverage Summary

| Priority | Total | FULL | Coverage |
| --- | ---: | ---: | ---: |
| P0 | 3 | 2 | 67% |
| P1 | 10 | 7 | 70% |
| P2 | 0 | 0 | 100% |
| P3 | 0 | 0 | 100% |
| Overall | 13 | 9 | 69% |

Gate rows: 9 FULL, 3 PARTIAL, 1 NONE, 0 UNIT-ONLY. Criteria: 42 FULL, 3 PARTIAL, 1 NONE, 0 UNIT-ONLY (previous: 18 / 14 / 13 / 1). Accepted evidence: 111 unique test declarations across 22 files; discovery found 530 test functions in 41 files. Sanity run at HEAD: `uv run pytest`: 716 passed, 17 skipped (chart renders needing built Helm dependencies), 32 deselected (kind). Local kind at HEAD: 32 passed. `lint-imports`: 7 kept. Live results: 22 records at this commit, all pass (15 CI/local runs, 7 author-confirmed).## Context and Oracle

Fresh Create run, as the remediation document asked. The previous matrix, summary and gate for this run key were replaced. The oracle is formal epic requirements R1–R7 at high confidence, with requirement granularity (v7 epic with `R<n>` lines and no duplicate ids). The criterion selection is the same 46 criteria as the previous run, including the user's 2026-11-07 decision that s12 uses the ticket's four criteria. The only source change since the previous trace was the addition of `(R…)` annotations: a word diff of the tickets folder shows nothing else. Priorities are unchanged and inferred. Requirement rows take the highest contributor priority, which makes R2 (via s5 AC-2) and R7 (via s1 AC-1) P0.

Supporting artifacts: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md`; NFR audit `_bmad-output/test-artifacts/nfr/nfr-assessment-epic-1.md` (legacy numbered-epic file; predates the role-check remediation); `_bmad-output/test-artifacts/trace/remediation-epic-ticketscope--e1.md`; `_bmad-output/test-artifacts/automate/remediation-live-evidence.md` (local, uncommitted-worktree evidence: supporting context only). Knowledge: test-priorities-matrix, risk-governance, probability-impact, test-quality, selective-testing. No waiver register.

## Requirement Oracle Mapping

| ID | Kind | Requirement | Priority | Coverage | Previous |
| --- | --- | --- | --- | --- | --- |
| ticketscope--e1--R1 | requirement | An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues. | P1 | FULL | NONE |
| ticketscope--e1--R2 | requirement | A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome. | P0 | FULL | NONE |
| ticketscope--e1--R3 | requirement | Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes. | P1 | FULL | NONE |
| ticketscope--e1--R4 | requirement | One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries. | P1 | FULL | NONE |
| ticketscope--e1--R5 | requirement | CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes. | P1 | FULL | NONE |
| ticketscope--e1--R6 | requirement | One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace. | P1 | FULL | NONE |
| ticketscope--e1--R7 | requirement | Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR. | P0 | FULL | NONE |
| ticketscope--e1-s3--AC-1 | exception | Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output. | P0 | PARTIAL | PARTIAL |
| ticketscope--e1-s3--AC-2 | exception | Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist. | P1 | FULL | FULL |
| ticketscope--e1-s3--AC-3 | exception | Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged. | P1 | PARTIAL | PARTIAL |
| ticketscope--e1-s4--AC-1 | exception | Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`. | P1 | PARTIAL | PARTIAL |
| ticketscope--e1-s4--AC-2 | exception | Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test). | P1 | FULL | FULL |
| ticketscope--e1-s14--AC-2 | exception | Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes. | P1 | NONE | NONE |

## Criterion Status Changes Since Previous Trace

| Criterion | Previous | Now | Why |
| --- | --- | --- | --- |
| ticketscope--e1-s1--AC-1 | PARTIAL | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — checks=success, charts=success, images=success, integrated-check=success; unit: 716 passed, 0 failed, 17 skipped; kind: 32 passed, 0 failed, 0 skipped |
| ticketscope--e1-s1--AC-2 | NONE | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — images job success |
| ticketscope--e1-s1--AC-3 | PARTIAL | FULL | `tests/unit/test_import_linter_enforcement.py:69` plants `import ticketscope.adapters.postgres` into a disposable copy of `core/modes.py` (case `core-imports-adapter`) and runs the real lint-imports CLI with caching disabled; `tests/unit/test_import_linter_enforcement.py:78` asserts exit 1, `tests/unit/test_import_linter_enforcement.py:79` asserts the `core imports only stdlib and pydantic` contract is BROKEN, and `tests/unit/test_import_linter_enforcement.py:82` asserts the exact `ticketscope.core.modes -> ticketscope.adapters.postgres` edge. The clean control `tests/unit/test_import_linter_enforcement.py:46` (`tests/unit/test_import_linter_enforcement.py:49`, `tests/unit/test_import_linter_enforcement.py:50`) rules out a broken setup masquerading as enforcement. Closed since the previous trace. |
| ticketscope--e1-s1--AC-4 | NONE | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — runner fit: peak_memory_mib=4197, free_disk=75G, kind_up_to_api_ready_seconds=198 |
| ticketscope--e1-s2--verify | NONE | FULL | Live: epic-search-baseline.md Notes line 108: 'Decision: Corpus terms settled (spike 2): yes, with attribution, no author logins, masking of emails and secrets, and a takedown path ...'; story 3's entry carries the conditions. Confirmed by the author (user) on 2026-11-07: "Is that the dated decision you made for spike 2?" — approved. |
| ticketscope--e1-s12--AC-1 | NONE | FULL | Live: spike-choose-the-jira-corpus-findings/findings.md (per-instance and per-project tables: issue count, in-subset pairs by kind, outcome shares, issue-type mix, hygiene counts) built from instances.csv, projects.csv, subsets.csv beside it. Confirmed by the author (user) on 2026-11-07: "Do the findings tables cover every instance and leading project with all five measures?" — approved. |
| ticketscope--e1-s12--AC-2 | NONE | FULL | Live: findings.md names Mojang MCL + REALMS + MCD: 32,154 issues, 10,466 in-subset pairs (10,162 short, 304 log-heavy), timed load 3.9 s vs 600 s; samples-mojang-mcl-realms-mcd.md (and the Spark/JRASERVER sample files) hold the 20 sampled issues per leading candidate. Confirmed by the author (user) on 2026-11-07: "Do the sample files hold 20 issues per leading candidate, each with your judgement?" — approved. |
| ticketscope--e1-s12--AC-3 | NONE | FULL | Live: epic-search-baseline.md Notes lines 110-112: dated Decision 'Spike 12 decided: switch ... subset Mojang MCL + REALMS + MCD ...', terms accepted, Corpus scope/terms/Jira outcome/Kind rule amended, data lane replanned (stories 13, 14). Confirmed by the author (user) on 2026-11-07: "Does the line name the subset, the resolution-to-outcome mapping and answered rule, the Jira {code}/{noformat} kind rule, and the attribution line?" — approved. |
| ticketscope--e1-s12--AC-4 | NONE | FULL | Live: epic-search-baseline.md Notes line 110 Decision attributed '(user, 2026-11-06)'. Confirmed by the author (user) on 2026-11-07: "Was that decision yours?" — approved. |
| ticketscope--e1-s13--AC-3 | NONE | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — tests.smoke.test_time_load::test_v2_fixture_loads_and_prints_a_time [passed] (kind-upgrade.xml), tests.smoke.test_time_load::test_v2_fixture_loads_and_prints_a_time [passed] (kind.xml) |
| ticketscope--e1-s13--AC-4 | PARTIAL | FULL | Live: https://github.com/Dillon-Based/ticketscope/releases/tag/snapshot-2026.11.1 (published 2026-11-07T00:48:56Z): assets 2026.11.1.jsonl.gz + .sha256; notes state subset (MCL, REALMS, MCD), 32153 issues, 10473 in-subset pairs (10164 short, 309 log-heavy), kind split 31339/814, timed load 2.6 s (budget 600 s), attribution line, built from b525b53. Confirmed by the author (user) on 2026-11-07: "Was this Release produced by scripts/publish-snapshot.sh from your restored dump after merge?" — approved. |
| ticketscope--e1-s5--AC-5 | NONE | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — tests.smoke.test_time_load::test_pinned_asset_alone_loads_within_budget [passed] (kind-upgrade.xml), tests.smoke.test_time_load::test_pinned_asset_alone_loads_within_budget [passed] (kind.xml) |
| ticketscope--e1-s6--AC-2 | PARTIAL | FULL | Same planted import the criterion names: `src/ticketscope/core/modes.py` importing `ticketscope.adapters.postgres`. `tests/unit/test_import_linter_enforcement.py:69` with assertions `tests/unit/test_import_linter_enforcement.py:78` (exit 1), `tests/unit/test_import_linter_enforcement.py:79` (named contract BROKEN), `tests/unit/test_import_linter_enforcement.py:82` (exact import edge); clean control `tests/unit/test_import_linter_enforcement.py:46`. Closed since the previous trace. |
| ticketscope--e1-s6--AC-3 | NONE | FULL | Live: scripts/v1-parity.sh 32049ee d29ed1e on the local kind cluster (snapshot 2026.11.1, each revision deployed with its own kind-up.sh and image tag): vague, log-heavy and plain keyword requests returned status 200 with byte-identical bodies. Saved responses in _bmad-output/test-artifacts/automate/live-evidence-6400e5a/parity-s6/. |
| ticketscope--e1-s7--AC-3 | NONE | FULL | Live: scripts/v1-parity.sh d29ed1e 88613bd on the local kind cluster (snapshot 2026.11.1, each revision deployed with its own kind-up.sh and image tag): vague, log-heavy and plain keyword requests returned status 200 with byte-identical bodies. Saved responses in _bmad-output/test-artifacts/automate/live-evidence-6400e5a/parity-s7/. |
| ticketscope--e1-s8--AC-1 | PARTIAL | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — checks=success, charts=success, images=success, integrated-check=success; kind: 32 passed, 0 failed, 0 skipped; backup test (7) passed |
| ticketscope--e1-s9--AC-2 | PARTIAL | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — checks=success; unit: 716 passed, 0 failed, 17 skipped; test_telemetry.py: 16 passed, 0 failed, 0 skipped |
| ticketscope--e1-s9--AC-3 | UNIT-ONLY | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — tests.smoke.test_gateway::test_api_logs_are_json_lines_carrying_the_request_trace_id [passed] (kind-upgrade.xml), tests.smoke.test_gateway::test_api_logs_are_json_lines_carrying_the_request_trace_id [passed] (kind.xml) |
| ticketscope--e1-s9--AC-4 | PARTIAL | FULL | Live: Author confirmed in Grafana Explore (Tempo datasource, port-forwarded) that the trace shows the ticketscope-api SERVER -> retrieval keyword -> db query span tree. Confirmed by the author (user) on 2026-11-07: "Did Explore show ticketscope-api SERVER -> retrieval keyword -> db query spans for that trace id?" — approved. |
| ticketscope--e1-s10--AC-2 | PARTIAL | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — checks=success; unit: 716 passed, 0 failed, 17 skipped |
| ticketscope--e1-s10--AC-3 | NONE | FULL | Live: scripts/v1-parity.sh 93c4344 9b291e3 on the local kind cluster (snapshot 2026.11.1, each revision deployed with its own kind-up.sh and image tag): vague, log-heavy and plain keyword requests returned status 200 with byte-identical bodies. Saved responses in _bmad-output/test-artifacts/automate/live-evidence-6400e5a/parity-s10/. |
| ticketscope--e1-s10--AC-4 | PARTIAL | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — after a second kind-up.sh on the same cluster, one smoke run: 27 passed, 0 failed, 0 skipped; test (3) passed |
| ticketscope--e1-s11--AC-2 | PARTIAL | FULL | Live: scripts/fault-inject.sh on the local kind cluster at 6400e5ac8e3bb4cadeea8061a5581c33b2b45036: schema broken: only test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2 failed; schema restored: all five passed; kind broken: only test_every_loaded_issue_has_a_valid_kind_and_outcome failed; kind restored: all five passed; golden broken: only test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page failed; golden restored: all five passed; tempo broken: only test_one_search_reaches_tempo_as_the_ad10_tree failed; tempo restored: all five passed; backup broken: only test_an_on_demand_backup_completes_to_seaweedfs failed; backup restored: all five passed. JUnit per run and summary.json in _bmad-output/test-artifacts/automate/live-evidence-6400e5a/fault/. |
| ticketscope--e1-s11--AC-3 | PARTIAL | FULL | Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — default `uv run pytest` (no cluster): 716 passed, 0 failed, 17 skipped; integrated cases collected: 0 |

No criterion lost coverage. Every test the previous matrix cited still exists at HEAD. `test_a_pasted_stack_trace_of_4kb_ranks` was renamed to `test_a_pasted_log_in_a_4kb_request_ranks` with the same intent, and the citations were re-anchored to HEAD line numbers.

## Detailed Mapping

### ticketscope--e1--R1 (P1, requirement): FULL

An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:33`. Contributors:

- ticketscope--e1-s2--verify: FULL
- ticketscope--e1-s12--AC-1: FULL
- ticketscope--e1-s12--AC-2: FULL
- ticketscope--e1-s12--AC-3: FULL
- ticketscope--e1-s12--AC-4: FULL
- ticketscope--e1-s13--AC-1: FULL
- ticketscope--e1-s13--AC-2: FULL
- ticketscope--e1-s13--AC-3: FULL
- ticketscope--e1-s13--AC-4: FULL
- ticketscope--e1-s11--AC-1: FULL
- ticketscope--e1-s11--AC-2: FULL

### ticketscope--e1--R2 (P0, requirement): FULL

A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:34`. Contributors:

- ticketscope--e1-s14--AC-1: FULL
- ticketscope--e1-s14--AC-3: FULL
- ticketscope--e1-s13--AC-3: FULL
- ticketscope--e1-s5--AC-1: FULL
- ticketscope--e1-s5--AC-2: FULL
- ticketscope--e1-s5--AC-3: FULL
- ticketscope--e1-s5--AC-5: FULL
- ticketscope--e1-s10--AC-2: FULL
- ticketscope--e1-s10--AC-4: FULL
- ticketscope--e1-s11--AC-1: FULL
- ticketscope--e1-s11--AC-2: FULL

### ticketscope--e1--R3 (P1, requirement): FULL

Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:35`. Contributors:

- ticketscope--e1-s5--AC-1: FULL
- ticketscope--e1-s5--AC-3: FULL
- ticketscope--e1-s5--AC-4: FULL
- ticketscope--e1-s6--AC-1: FULL
- ticketscope--e1-s6--AC-3: FULL
- ticketscope--e1-s7--AC-3: FULL
- ticketscope--e1-s10--AC-3: FULL
- ticketscope--e1-s11--AC-1: FULL
- ticketscope--e1-s11--AC-2: FULL

### ticketscope--e1--R4 (P1, requirement): FULL

One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:36`. Contributors:

- ticketscope--e1-s5--AC-4: FULL
- ticketscope--e1-s7--AC-1: FULL
- ticketscope--e1-s7--AC-2: FULL
- ticketscope--e1-s10--AC-3: FULL
- ticketscope--e1-s11--AC-1: FULL
- ticketscope--e1-s11--AC-2: FULL

### ticketscope--e1--R5 (P1, requirement): FULL

CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:37`. Contributors:

- ticketscope--e1-s5--AC-1: FULL
- ticketscope--e1-s8--AC-1: FULL
- ticketscope--e1-s8--AC-2: FULL
- ticketscope--e1-s8--AC-3: FULL
- ticketscope--e1-s11--AC-1: FULL
- ticketscope--e1-s11--AC-2: FULL

### ticketscope--e1--R6 (P1, requirement): FULL

One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:38`. Contributors:

- ticketscope--e1-s9--AC-1: FULL
- ticketscope--e1-s9--AC-2: FULL
- ticketscope--e1-s9--AC-3: FULL
- ticketscope--e1-s9--AC-4: FULL
- ticketscope--e1-s11--AC-1: FULL
- ticketscope--e1-s11--AC-2: FULL

### ticketscope--e1--R7 (P0, requirement): FULL

Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:39`. Contributors:

- ticketscope--e1-s1--AC-1: FULL
- ticketscope--e1-s1--AC-2: FULL
- ticketscope--e1-s1--AC-3: FULL
- ticketscope--e1-s1--AC-4: FULL
- ticketscope--e1-s5--AC-1: FULL
- ticketscope--e1-s6--AC-2: FULL
- ticketscope--e1-s7--AC-2: FULL
- ticketscope--e1-s8--AC-1: FULL
- ticketscope--e1-s9--AC-2: FULL
- ticketscope--e1-s10--AC-1: FULL
- ticketscope--e1-s10--AC-2: FULL
- ticketscope--e1-s10--AC-4: FULL
- ticketscope--e1-s11--AC-1: FULL
- ticketscope--e1-s11--AC-2: FULL
- ticketscope--e1-s11--AC-3: FULL

### ticketscope--e1-s3--AC-1 (P0, exception): PARTIAL

### ticketscope--e1-s3--AC-2 (P1, exception): FULL

### ticketscope--e1-s3--AC-3 (P1, exception): PARTIAL

### ticketscope--e1-s4--AC-1 (P1, exception): PARTIAL

### ticketscope--e1-s4--AC-2 (P1, exception): FULL

### ticketscope--e1-s14--AC-2 (P1, exception): NONE

#### ticketscope--e1-s1--AC-1 (P0): FULL

Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test. (R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:94`. Links: R7.

- `tests/smoke/test_gateway.py:171` test_search_serves_the_pinned_snapshot_with_outcomes (e2e)
- `tests/smoke/test_gateway.py:435` test_cluster_has_two_ready_instances (e2e)
- `tests/unit/test_layer_imports.py:42` test_layer_imports_only_stdlib_pydantic_and_itself (unit)
- `:None` PR ci.yml: ruff, pyright, pytest, lint-imports pass; _kind-deploy brings up both releases and passes smoke (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — checks=success, charts=success, images=success, integrated-check=success; unit: 716 passed, 0 failed, 17 skipped; kind: 32 passed, 0 failed, 0 skipped

#### ticketscope--e1-s1--AC-2 (P1): FULL

Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`. (R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:95`. Links: R7.

- `:None` images/ change builds linux/amd64 and linux/arm64 (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — images job success

#### ticketscope--e1-s1--AC-3 (P1): FULL

Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails. (R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:96`. Links: R7.

- `tests/unit/test_layer_imports.py:42` test_layer_imports_only_stdlib_pydantic_and_itself (unit)
- `tests/unit/test_import_linter_enforcement.py:69` test_forbidden_import_breaks_its_named_contract (unit)
- `tests/unit/test_import_linter_enforcement.py:46` test_clean_source_copy_keeps_all_layer_contracts (unit)
- Evidence: `tests/unit/test_import_linter_enforcement.py:69` plants `import ticketscope.adapters.postgres` into a disposable copy of `core/modes.py` (case `core-imports-adapter`) and runs the real lint-imports CLI with caching disabled; `tests/unit/test_import_linter_enforcement.py:78` asserts exit 1, `tests/unit/test_import_linter_enforcement.py:79` asserts the `core imports only stdlib and pydantic` contract is BROKEN, and `tests/unit/test_import_linter_enforcement.py:82` asserts the exact `ticketscope.core.modes -> ticketscope.adapters.postgres` edge. The clean control `tests/unit/test_import_linter_enforcement.py:46` (`tests/unit/test_import_linter_enforcement.py:49`, `tests/unit/test_import_linter_enforcement.py:50`) rules out a broken setup masquerading as enforcement. Closed since the previous trace.

#### ticketscope--e1-s1--AC-4 (P1): FULL

Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready. (R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:97`. Links: R7.

- `:None` _kind-deploy job summary shows peak memory, free disk, kind-up to api Ready wall clock (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — runner fit: peak_memory_mib=4197, free_disk=75G, kind_up_to_api_ready_seconds=198

#### ticketscope--e1-s2--verify (P2): FULL

The epic's Notes hold a dated Decision line that says yes, yes with named conditions, or no, and story 3's entry reflects any conditions.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml:27`. Links: R1.

- `:None` Corpus-terms decision recorded (live)
- Evidence: Live: epic-search-baseline.md Notes line 108: 'Decision: Corpus terms settled (spike 2): yes, with attribution, no author logins, masking of emails and secrets, and a takedown path ...'; story 3's entry carries the conditions. Confirmed by the author (user) on 2026-11-07: "Is that the dated decision you made for spike 2?" — approved.

#### ticketscope--e1-s3--AC-1 (P0): PARTIAL

Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:91`. Links: none (unlinked).

- `tests/unit/test_ingest_jira.py:74` test_output_validates_against_schema_v2_and_the_model (unit)
- `tests/unit/test_ingest_jira.py:249` test_no_identity_appears_in_the_output (unit)
- Gap: Current tests validate schema v2 and identity absence. They do not establish a GitHub-recording ingest or github.com issue URLs: the implementation was superseded by Jira.

#### ticketscope--e1-s3--AC-2 (P1): FULL

Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:92`. Links: none (unlinked).

- `tests/unit/test_ingest_jira.py:95` test_checksum_matches_and_load_reads_the_output (unit)
- `tests/unit/test_ingest_jira.py:111` test_rerun_is_byte_identical (unit)

#### ticketscope--e1-s3--AC-3 (P1): PARTIAL

Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:93`. Links: none (unlinked).

- `tests/unit/test_ingest_notes.py:31` test_notes_state_subset_counts_pairs_kinds_and_load_time (unit)
- `tests/unit/test_ingest_notes.py:43` test_notes_carry_the_attribution_line (unit)
- `tests/unit/test_ingest_version.py:8` test_version_taken_gives_the_next_n (unit)
- `tests/unit/test_ingest_version.py:18` test_n_is_numeric_and_never_reuses_a_gap (unit)
- `tests/unit/test_publish_script.py:111` test_script_never_clobbers_or_deletes (unit)
- Gap: Notes fields, attribution, version advancement and non-clobber behavior have tests. snapshot.yml was retired; a real two-dispatch publish with unchanged earlier assets is not established.

#### ticketscope--e1-s12--AC-1 (P2): FULL

**The instances and leading projects are compared on the decision rule** (R1) Verify: a findings note beside this ticket holds a table per instance and per leading project. Each table gives the issue count, in-subset duplicate pairs by kind, the outcome shares under the proposed mapping, the issue-type mix, and the text-hygiene counts. The CSVs it was built from sit with it.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:65`. Links: R1.

- `:None` Instances and leading projects compared on the decision rule (live)
- Evidence: Live: spike-choose-the-jira-corpus-findings/findings.md (per-instance and per-project tables: issue count, in-subset pairs by kind, outcome shares, issue-type mix, hygiene counts) built from instances.csv, projects.csv, subsets.csv beside it. Confirmed by the author (user) on 2026-11-07: "Do the findings tables cover every instance and leading project with all five measures?" — approved.

#### ticketscope--e1-s12--AC-2 (P2): FULL

**The recommended subset is shown to work** (R1) Verify: the findings note names the subset and its expected duplicate-pair count by kind. It shows the subset's measured load time through story 3's timed-load script within 600 s, and 20 sampled issues per leading candidate with the author's judgement of each.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:67`. Links: R1.

- `:None` Recommended subset shown to work (live)
- Evidence: Live: findings.md names Mojang MCL + REALMS + MCD: 32,154 issues, 10,466 in-subset pairs (10,162 short, 304 log-heavy), timed load 3.9 s vs 600 s; samples-mojang-mcl-realms-mcd.md (and the Spark/JRASERVER sample files) hold the 20 sampled issues per leading candidate. Confirmed by the author (user) on 2026-11-07: "Do the sample files hold 20 issues per leading candidate, each with your judgement?" — approved.

#### ticketscope--e1-s12--AC-3 (P2): FULL

**The answer and its consequences are recorded where the waiting tickets read them** (R1) Verify: the epic's Notes holds a dated Decision line: switch, stay, or switch with named conditions. On switch, the line names:  - the subset; - the `resolution`-to-outcome mapping and the "answered" rule; - the kind rule extended to Jira `{code}` and `{noformat}` blocks, since a kind-rule change needs a reload and a baseline update (epic Constraints, Kind rule); - the attribution line.  It also amends the epic's Corpus scope (the 20,000 cap and the source) and Corpus terms for the new source, and says the data lane and epic-eval-gate are to be replanned.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:69`. Links: R1.

- `:None` Answer and consequences recorded where waiting tickets read them (live)
- Evidence: Live: epic-search-baseline.md Notes lines 110-112: dated Decision 'Spike 12 decided: switch ... subset Mojang MCL + REALMS + MCD ...', terms accepted, Corpus scope/terms/Jira outcome/Kind rule amended, data lane replanned (stories 13, 14). Confirmed by the author (user) on 2026-11-07: "Does the line name the subset, the resolution-to-outcome mapping and answered rule, the Jira {code}/{noformat} kind rule, and the attribution line?" — approved.

#### ticketscope--e1-s12--AC-4 (P2): FULL

**The author accepts it** (R1) Verify: the Decision line is attributed to the author (user) and dated.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:78`. Links: R1.

- `:None` Author accepts it (live)
- Evidence: Live: epic-search-baseline.md Notes line 110 Decision attributed '(user, 2026-11-06)'. Confirmed by the author (user) on 2026-11-07: "Was that decision yours?" — approved.

#### ticketscope--e1-s4--AC-1 (P1): PARTIAL

Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:80`. Links: none (unlinked).

- `tests/unit/test_derive.py:29` test_kind_just_below_threshold_is_short (unit)
- `tests/unit/test_derive.py:36` test_kind_at_threshold_is_log_heavy (unit)
- Gap: Threshold boundaries are tested. The named GitHub outcome branches and tie cases were deliberately removed in story 1.10, so the frozen criterion is only partially established.

#### ticketscope--e1-s4--AC-2 (P1): FULL

Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:81`. Links: none (unlinked).

- `tests/unit/test_snapshot.py:128` test_fixture_records_kinds_outside_the_schema_and_they_hold (unit)

#### ticketscope--e1-s14--AC-1 (P1): FULL

Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold. (R2)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:91`. Links: R2.

- `tests/unit/test_derive_jira.py:51` test_duplicate_points_at_target (unit)
- `tests/unit/test_derive_jira.py:58` test_duplicate_without_link_has_no_ref (unit)
- `tests/unit/test_derive_jira.py:63` test_fixed (unit)
- `tests/unit/test_derive_jira.py:68` test_not_planned (unit)
- `tests/unit/test_derive_jira.py:73` test_stale (unit)
- `tests/unit/test_derive_jira.py:78` test_answered_by_resolution (unit)
- `tests/unit/test_derive_jira.py:83` test_unresolved_is_unknown (unit)
- `tests/unit/test_derive_jira.py:87` test_unmapped_resolution_is_unknown (unit)
- `tests/unit/test_derive_jira.py:91` test_resolution_matched_trimmed_and_case_insensitive (unit)
- `tests/unit/test_derive_jira.py:100` test_question_answered_by_non_reporter_comment (unit)
- `tests/unit/test_derive_jira.py:111` test_question_comment_at_resolution_time_counts (unit)
- `tests/unit/test_derive_jira.py:120` test_question_only_reporter_comments_is_fixed (unit)
- `tests/unit/test_derive_jira.py:127` test_question_non_reporter_comment_after_resolution_is_fixed (unit)
- `tests/unit/test_derive_jira.py:134` test_question_unmapped_resolution_answered (unit)
- `tests/unit/test_derive_jira.py:143` test_bug_type_with_non_reporter_comment_stays_fixed (unit)
- `tests/unit/test_derive_jira.py:150` test_support_duplicate_stays_duplicate (unit)
- `tests/unit/test_derive_jira.py:164` test_support_other_classes_keep_their_class (unit)
- `tests/unit/test_derive_jira.py:241` test_kind_just_below_threshold_is_short (unit)
- `tests/unit/test_derive_jira.py:247` test_kind_at_threshold_is_log_heavy (unit)
- `tests/unit/test_derive_jira.py:258` test_parameterised_toggle_scores_like_plain (unit)

#### ticketscope--e1-s14--AC-2 (P1): NONE

Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:92`. Links: none (unlinked).

- Gap: The GitHub rules were explicitly retired by the sweep; remaining test_derive.py cases test kinds and versions only.

#### ticketscope--e1-s14--AC-3 (P1): FULL

Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`. (R2)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:93`. Links: R2.

- `tests/unit/test_derive_jira.py:226` test_derivation_version_differs_from_story_4 (unit)

#### ticketscope--e1-s13--AC-1 (P1): FULL

Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes. (R1)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:95`. Links: R1.

- `tests/unit/test_ingest_jira.py:74` test_output_validates_against_schema_v2_and_the_model (unit)
- `tests/unit/test_ingest_jira.py:95` test_checksum_matches_and_load_reads_the_output (unit)

#### ticketscope--e1-s13--AC-2 (P1): FULL

Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun. (R1)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:96`. Links: R1.

- `tests/unit/test_snapshot.py:58` test_committed_schema_matches_the_model (unit)
- `tests/unit/test_snapshot.py:64` test_drift_is_detected (unit)

#### ticketscope--e1-s13--AC-3 (P1): FULL

Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0. (R1, R2)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:97`. Links: R1, R2.

- `:None` tagged tests for ticketscope--e1-s13--AC-3 (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — tests.smoke.test_time_load::test_v2_fixture_loads_and_prints_a_time [passed] (kind-upgrade.xml), tests.smoke.test_time_load::test_v2_fixture_loads_and_prints_a_time [passed] (kind.xml)

#### ticketscope--e1-s13--AC-4 (P1): FULL

Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line. (R1)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:98`. Links: R1.

- `tests/unit/test_ingest_notes.py:31` test_notes_state_subset_counts_pairs_kinds_and_load_time (unit)
- `tests/unit/test_ingest_notes.py:43` test_notes_carry_the_attribution_line (unit)
- `tests/unit/test_publish_script.py:73` test_refuses_off_main (unit)
- `tests/unit/test_publish_script.py:82` test_refuses_a_dirty_checkout (unit)
- `tests/unit/test_publish_script.py:91` test_refuses_when_head_is_not_origin_main (unit)
- `tests/unit/test_publish_script.py:100` test_clean_main_passes_the_guards (unit)
- `tests/unit/test_publish_script.py:111` test_script_never_clobbers_or_deletes (unit)
- `:None` Person-run publish produced the snapshot Release (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/releases/tag/snapshot-2026.11.1 (published 2026-11-07T00:48:56Z): assets 2026.11.1.jsonl.gz + .sha256; notes state subset (MCL, REALMS, MCD), 32153 issues, 10473 in-subset pairs (10164 short, 309 log-heavy), kind split 31339/814, timed load 2.6 s (budget 600 s), attribution line, built from b525b53. Confirmed by the author (user) on 2026-11-07: "Was this Release produced by scripts/publish-snapshot.sh from your restored dump after merge?" — approved.

#### ticketscope--e1-s5--AC-1 (P1): FULL

Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)–(6) pass on snapshot 2026.11.1. (R2, R3, R5, R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:96`. Links: R2, R3, R5, R7.

- `tests/smoke/test_gateway.py:171` test_search_serves_the_pinned_snapshot_with_outcomes (e2e)
- `tests/smoke/test_gateway.py:324` test_every_issue_is_loaded_with_a_kind_and_an_outcome (e2e)
- `tests/smoke/test_gateway.py:391` test_load_log_has_the_report (e2e)
- `tests/smoke/test_gateway.py:414` test_upgrade_with_the_same_pin_is_a_no_op (e2e)
- `tests/smoke/test_gateway.py:425` test_stale_preprocessing_version_reloads (e2e)
- `tests/smoke/test_gateway.py:435` test_cluster_has_two_ready_instances (e2e)

#### ticketscope--e1-s5--AC-2 (P0): FULL

Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test). (R2)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:97`. Links: R2.

- `tests/unit/test_load_main.py:212` test_wrong_checksum_exits_1_and_keeps_the_corpus (unit)
- `tests/unit/test_load_main.py:225` test_wrong_checksum_on_download_exits_1_and_keeps_the_corpus (unit)
- `tests/unit/test_postgres_corpus_meta.py:148` test_replace_corpus_rolls_back_when_the_rows_fail_midway (unit)

#### ticketscope--e1-s5--AC-3 (P1): FULL

Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1. (R2, R3)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:98`. Links: R2, R3.

- `tests/unit/test_load_main.py:124` test_computed_fixture_kinds_equal_the_expected_kinds (unit)
- `tests/unit/test_app.py:25` test_best_match (api)
- `tests/unit/test_modes.py:28` test_keyword_ranks_by_overlap_then_number (unit)
- `tests/unit/test_modes.py:48` test_fixture_target_ranks_first (unit)

#### ticketscope--e1-s5--AC-4 (P1): FULL

Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source. (R3, R4)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:99`. Links: R3, R4.

- `tests/unit/test_golden_queries.py:56` test_file_is_pinned_to_the_chart_snapshot (unit)
- `tests/unit/test_golden_queries.py:76` test_expected_issue_differs_from_its_source (unit)
- `tests/unit/test_golden_queries.py:87` test_source_and_expected_issues_exist_in_the_pinned_asset (unit)

#### ticketscope--e1-s5--AC-5 (P1): FULL

Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600. (R2)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:100`. Links: R2.

- `:None` tagged tests for ticketscope--e1-s5--AC-5 (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — tests.smoke.test_time_load::test_pinned_asset_alone_loads_within_budget [passed] (kind-upgrade.xml), tests.smoke.test_time_load::test_pinned_asset_alone_loads_within_budget [passed] (kind.xml)

#### ticketscope--e1-s6--AC-1 (P1): FULL

Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included. (R3)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:96`. Links: R3.

- `tests/smoke/test_gateway.py:193` test_issue_detail_matches_the_search_hit (e2e)
- `tests/smoke/test_gateway.py:203` test_unknown_issue_is_a_404_problem (e2e)
- `tests/smoke/test_gateway.py:217` test_invalid_search_is_a_422_problem (e2e)
- `tests/smoke/test_gateway.py:222` test_operator_characters_rank (e2e)
- `tests/smoke/test_gateway.py:229` test_a_pasted_log_in_a_4kb_request_ranks (e2e)

#### ticketscope--e1-s6--AC-2 (P1): FULL

Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged). (R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:97`. Links: R7.

- `tests/unit/test_layer_imports.py:42` test_layer_imports_only_stdlib_pydantic_and_itself (unit)
- `tests/unit/test_import_linter_enforcement.py:69` test_forbidden_import_breaks_its_named_contract (unit)
- `tests/unit/test_import_linter_enforcement.py:46` test_clean_source_copy_keeps_all_layer_contracts (unit)
- Evidence: Same planted import the criterion names: `src/ticketscope/core/modes.py` importing `ticketscope.adapters.postgres`. `tests/unit/test_import_linter_enforcement.py:69` with assertions `tests/unit/test_import_linter_enforcement.py:78` (exit 1), `tests/unit/test_import_linter_enforcement.py:79` (named contract BROKEN), `tests/unit/test_import_linter_enforcement.py:82` (exact import edge); clean control `tests/unit/test_import_linter_enforcement.py:46`. Closed since the previous trace.

#### ticketscope--e1-s6--AC-3 (P1): FULL

Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical. (R3)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:98`. Links: R3.

- `:None` POST /v1/search body identical before and after the change (live)
- Evidence: Live: scripts/v1-parity.sh 32049ee d29ed1e on the local kind cluster (snapshot 2026.11.1, each revision deployed with its own kind-up.sh and image tag): vague, log-heavy and plain keyword requests returned status 200 with byte-identical bodies. Saved responses in _bmad-output/test-artifacts/automate/live-evidence-6400e5a/parity-s6/.

#### ticketscope--e1-s7--AC-1 (P1): FULL

Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome. (R4)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:80`. Links: R4.

- `tests/smoke/test_gateway.py:303` test_page_renders_each_golden_query (e2e)

#### ticketscope--e1-s7--AC-2 (P1): FULL

Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c). (R4, R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:81`. Links: R4, R7.

- `tests/smoke/test_gateway.py:171` test_search_serves_the_pinned_snapshot_with_outcomes (e2e)
- `tests/smoke/test_gateway.py:184` test_no_match_is_empty_through_the_gateway (e2e)
- `tests/smoke/test_gateway.py:193` test_issue_detail_matches_the_search_hit (e2e)
- `tests/smoke/test_gateway.py:203` test_unknown_issue_is_a_404_problem (e2e)
- `tests/smoke/test_gateway.py:217` test_invalid_search_is_a_422_problem (e2e)
- `tests/smoke/test_gateway.py:222` test_operator_characters_rank (e2e)
- `tests/smoke/test_gateway.py:229` test_a_pasted_log_in_a_4kb_request_ranks (e2e)
- `tests/smoke/test_gateway.py:291` test_page_serves_the_form (e2e)
- `tests/smoke/test_gateway.py:303` test_page_renders_each_golden_query (e2e)
- `tests/smoke/test_gateway.py:315` test_page_escapes_a_script_query (e2e)
- `tests/smoke/test_gateway.py:324` test_every_issue_is_loaded_with_a_kind_and_an_outcome (e2e)
- `tests/smoke/test_gateway.py:391` test_load_log_has_the_report (e2e)
- `tests/smoke/test_gateway.py:414` test_upgrade_with_the_same_pin_is_a_no_op (e2e)
- `tests/smoke/test_gateway.py:425` test_stale_preprocessing_version_reloads (e2e)
- `tests/smoke/test_gateway.py:435` test_cluster_has_two_ready_instances (e2e)

#### ticketscope--e1-s7--AC-3 (P1): FULL

Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical. (R3)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:82`. Links: R3.

- `:None` POST /v1/search body identical before and after the change (live)
- Evidence: Live: scripts/v1-parity.sh d29ed1e 88613bd on the local kind cluster (snapshot 2026.11.1, each revision deployed with its own kind-up.sh and image tag): vague, log-heavy and plain keyword requests returned status 200 with byte-identical bodies. Saved responses in _bmad-output/test-artifacts/automate/live-evidence-6400e5a/parity-s7/.

#### ticketscope--e1-s8--AC-1 (P1): FULL

Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7). (R5, R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:92`. Links: R5, R7.

- `tests/smoke/test_gateway.py:595` test_on_demand_backup_completes_to_seaweedfs (e2e)
- `tests/unit/test_integrated_check_expanded.py:65` test_ci_runs_integrated_then_smoke_in_one_kind_job (unit)
- `:None` PR ci.yml: checks and charts pass; _kind-deploy passes every kind smoke test incl. (7) (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — checks=success, charts=success, images=success, integrated-check=success; kind: 32 passed, 0 failed, 0 skipped; backup test (7) passed

#### ticketscope--e1-s8--AC-2 (P1): FULL

Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket. (R5)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:93`. Links: R5.

- `tests/smoke/test_gateway.py:595` test_on_demand_backup_completes_to_seaweedfs (e2e)

#### ticketscope--e1-s8--AC-3 (P1): FULL

Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run. (R5)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:94`. Links: R5.

- `tests/smoke/test_gateway.py:472` test_upgrades_keep_the_backup_tls_and_credentials (e2e)

#### ticketscope--e1-s9--AC-1 (P1): FULL

Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b). (R6)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:96`. Links: R6.

- `tests/smoke/test_gateway.py:733` test_one_search_yields_one_trace_in_tempo (e2e)
- `tests/smoke/test_gateway.py:782` test_the_trace_is_served_by_grafanas_tempo_datasource (e2e)

#### ticketscope--e1-s9--AC-2 (P1): FULL

Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`. (R6, R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:97`. Links: R6, R7.

- `tests/unit/test_telemetry.py:88` test_search_is_a_server_span_over_a_retrieval_span (unit)
- `tests/unit/test_integrated_check_expanded.py:65` test_ci_runs_integrated_then_smoke_in_one_kind_job (unit)
- `:None` ruff, ruff format, pyright, lint-imports, pytest all pass incl. test_telemetry.py (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — checks=success; unit: 716 passed, 0 failed, 17 skipped; test_telemetry.py: 16 passed, 0 failed, 0 skipped

#### ticketscope--e1-s9--AC-3 (P1): FULL

Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`. (R6)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:98`. Links: R6.

- `tests/unit/test_telemetry.py:242` test_log_line_inside_a_span_carries_its_ids (unit)
- `tests/unit/test_telemetry_expanded.py:330` test_a_log_line_during_a_request_carries_the_request_trace (unit)
- `:None` tagged tests for ticketscope--e1-s9--AC-3 (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — tests.smoke.test_gateway::test_api_logs_are_json_lines_carrying_the_request_trace_id [passed] (kind-upgrade.xml), tests.smoke.test_gateway::test_api_logs_are_json_lines_carrying_the_request_trace_id [passed] (kind.xml)

#### ticketscope--e1-s9--AC-4 (P3): FULL

Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual). (R6)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:99`. Links: R6.

- `tests/smoke/test_gateway.py:782` test_the_trace_is_served_by_grafanas_tempo_datasource (e2e)
- `:None` Grafana Explore shows the same span tree for the smoke trace (manual, human-visual) (live)
- Evidence: Live: Author confirmed in Grafana Explore (Tempo datasource, port-forwarded) that the trace shows the ticketscope-api SERVER -> retrieval keyword -> db query span tree. Confirmed by the author (user) on 2026-11-07: "Did Explore show ticketscope-api SERVER -> retrieval keyword -> db query spans for that trace id?" — approved.

#### ticketscope--e1-s10--AC-1 (P2): FULL

Given the change, when `grep -rnE "SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS" src tests` runs, then it finds nothing. (R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:69`. Links: R7.

- `tests/unit/test_refactor_sweep_expanded.py:49` test_no_source_or_test_names_a_retired_v1_symbol (unit)

#### ticketscope--e1-s10--AC-2 (P1): FULL

Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`. (R2, R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:70`. Links: R2, R7.

- `tests/unit/test_refactor_sweep_expanded.py:95` test_preprocessing_version_is_unchanged_by_the_sweep (unit)
- `:None` ruff, pyright, lint-imports, pytest pass (preprocessing_version asserted in the unit suite) (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — checks=success; unit: 716 passed, 0 failed, 17 skipped

#### ticketscope--e1-s10--AC-3 (P1): FULL

Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical. (R3, R4)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:71`. Links: R3, R4.

- `:None` POST /v1/search body identical before and after the change (live)
- Evidence: Live: scripts/v1-parity.sh 93c4344 9b291e3 on the local kind cluster (snapshot 2026.11.1, each revision deployed with its own kind-up.sh and image tag): vague, log-heavy and plain keyword requests returned status 200 with byte-identical bodies. Saved responses in _bmad-output/test-artifacts/automate/live-evidence-6400e5a/parity-s10/.

#### ticketscope--e1-s10--AC-4 (P1): FULL

Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run. (R2, R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:72`. Links: R2, R7.

- `tests/smoke/test_gateway.py:391` test_load_log_has_the_report (e2e)
- `:None` first smoke run after an in-place kind-up.sh upgrade passes (3) (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — after a second kind-up.sh on the same cluster, one smoke run: 27 passed, 0 failed, 0 skipped; test (3) passed

#### ticketscope--e1-s11--AC-1 (P1): FULL

Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank. (R1, R2, R3, R4, R5, R6, R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:70`. Links: R1, R2, R3, R4, R5, R6, R7.

- `tests/integrated/test_done_when.py:77` test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2 (e2e)
- `tests/integrated/test_done_when.py:120` test_every_loaded_issue_has_a_valid_kind_and_outcome (e2e)
- `tests/integrated/test_done_when.py:147` test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page (e2e)
- `tests/integrated/test_done_when.py:211` test_one_search_reaches_tempo_as_the_ad10_tree (e2e)
- `tests/integrated/test_done_when.py:219` test_an_on_demand_backup_completes_to_seaweedfs (e2e)
- `tests/unit/test_integrated_check_expanded.py:42` test_module_has_exactly_five_checks_in_order (unit)
- `tests/unit/test_integrated_check_expanded.py:74` test_report_appends_table_to_github_step_summary (unit)
- `tests/unit/test_integrated_golden.py:64` test_summary_table_reports_rank_or_absent (unit)

#### ticketscope--e1-s11--AC-2 (P2): FULL

Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again. (R1, R2, R3, R4, R5, R6, R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:71`. Links: R1, R2, R3, R4, R5, R6, R7.

- `tests/unit/test_snapshot.py:64` test_drift_is_detected (unit)
- `tests/unit/test_integrated_golden.py:21` test_twin_absent_on_a_gated_entry_fails (unit)
- `tests/unit/test_integrated_golden.py:25` test_twin_absent_from_an_empty_result_fails (unit)
- `tests/unit/test_integrated_golden.py:59` test_page_lacking_the_twin_has_no_rank (unit)
- `:None` Each of the five integrated checks fails when broken by hand, then passes when restored (live)
- Evidence: Live: scripts/fault-inject.sh on the local kind cluster at 6400e5ac8e3bb4cadeea8061a5581c33b2b45036: schema broken: only test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2 failed; schema restored: all five passed; kind broken: only test_every_loaded_issue_has_a_valid_kind_and_outcome failed; kind restored: all five passed; golden broken: only test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page failed; golden restored: all five passed; tempo broken: only test_one_search_reaches_tempo_as_the_ad10_tree failed; tempo restored: all five passed; backup broken: only test_an_on_demand_backup_completes_to_seaweedfs failed; backup restored: all five passed. JUnit per run and summary.json in _bmad-output/test-artifacts/automate/live-evidence-6400e5a/fault/.

#### ticketscope--e1-s11--AC-3 (P1): FULL

Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass. (R7)  
Source: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:72`. Links: R7.

- `tests/unit/test_integrated_check_expanded.py:58` test_module_is_marked_kind (unit)
- `:None` uv run pytest without a cluster deselects the integrated module and unit tests pass (live)
- Evidence: Live: https://github.com/Dillon-Based/ticketscope/actions/runs/42415340129 — default `uv run pytest` (no cluster): 716 passed, 0 failed, 17 skipped; integrated cases collected: 0

## Invalid and Unlinked Criteria

Six unlinked exception rows, all retired GitHub-era criteria kept verbatim: s3 AC-1 (P0), s3 AC-2, s3 AC-3, s4 AC-1, s4 AC-2 and s14 AC-2. There are no invalid links. These need the owner's explicit reconciliation (retire or waive). Trace cannot do it.

## Gaps & Recommendations

Critical (P0 below FULL): `ticketscope--e1-s3--AC-1`.

High (P1 NONE): `ticketscope--e1-s14--AC-2`. Medium: none. Low: none.

Partial rows are listed in the mapping and lower the FULL percentages.

- **URGENT** Six retired GitHub-era criteria (s3 AC-1..3, s4 AC-1..2, s14 AC-2) stay in the inventory: the trace contract has no superseded disposition, the stories are done, and the PO replan rule forbids rewriting built criteria. Fill the remaining fields of W-001 in _bmad-output/test-artifacts/gate-waivers.md (approver, dates, expiry, owner) so the waiver is reported as valid; a person then applies WAIVED. Longer term, raise a TEA/PO change so superseded criteria leave the gate.
- **DONE** (Approved 2026-11-07) The drafts in _bmad-output/test-artifacts/live-verification-drafts.json (Grafana Explore look for s9 AC-4; spike 12 and spike 2 document evidence; the snapshot-2026.11.1 publish for s13 AC-4) and move them into live-verification-results.json at the final commit. That closes R1 and R6.
- **MEDIUM** Every new commit makes the live records stale. After the final commit, take the CI evidence artifact (live-verification-results) from that commit's run, re-run scripts/fault-inject.sh and scripts/v1-parity.sh locally if the cluster code changed, and re-run /bmad-tea-trace.

## Waiver Register Review

`gate-waivers.md`: 1 filed, 1 valid, 0 invalid. Rule 6: the derived decision above stays the one Rules 1-5 produced; a waiver, valid or not, is never applied by this workflow.

- **W-001** (Retired GitHub-era criteria of stories 1.3, 1.4 and 1.14), covers 6 criteria (highest P0): VALID.

## Next Actions

1. Fill the `{…}` fields of W-001 in `gate-waivers.md` (approver and role, approval date, expiry, fix target, due date, owner) so it validates.
2. With W-001 valid, the approver applies WAIVED over this FAIL; record that override beside this report.
3. Re-run `/bmad-tea-trace` at the final commit with that commit's CI evidence artifact.

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
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s1--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s1--AC-4",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s2--verify",
      "coverage": "FULL"
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
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s12--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s12--AC-3",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s12--AC-4",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s4--AC-1",
      "coverage": "PARTIAL"
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
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s13--AC-4",
      "coverage": "FULL"
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
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s6--AC-1",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s6--AC-2",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s6--AC-3",
      "coverage": "FULL"
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
      "coverage": "FULL"
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
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s9--AC-4",
      "coverage": "FULL"
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
      "coverage": "FULL"
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
      "coverage": "FULL"
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
      "coverage": "FULL",
      "contributors": [
        {
          "id": "ticketscope--e1-s2--verify",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s12--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s12--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s12--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s12--AC-4",
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
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s13--AC-4",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-2",
          "coverage": "FULL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e1--R2",
      "kind": "requirement",
      "coverage": "FULL",
      "contributors": [
        {
          "id": "ticketscope--e1-s14--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s14--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s13--AC-3",
          "coverage": "FULL"
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
          "id": "ticketscope--e1-s5--AC-5",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s10--AC-2",
          "coverage": "FULL"
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
          "coverage": "FULL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e1--R3",
      "kind": "requirement",
      "coverage": "FULL",
      "contributors": [
        {
          "id": "ticketscope--e1-s5--AC-1",
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
          "id": "ticketscope--e1-s6--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s6--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s7--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s10--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-2",
          "coverage": "FULL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e1--R4",
      "kind": "requirement",
      "coverage": "FULL",
      "contributors": [
        {
          "id": "ticketscope--e1-s5--AC-4",
          "coverage": "FULL"
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
          "id": "ticketscope--e1-s10--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-2",
          "coverage": "FULL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e1--R5",
      "kind": "requirement",
      "coverage": "FULL",
      "contributors": [
        {
          "id": "ticketscope--e1-s5--AC-1",
          "coverage": "FULL"
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
          "id": "ticketscope--e1-s11--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-2",
          "coverage": "FULL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e1--R6",
      "kind": "requirement",
      "coverage": "FULL",
      "contributors": [
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
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s9--AC-4",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-2",
          "coverage": "FULL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e1--R7",
      "kind": "requirement",
      "coverage": "FULL",
      "contributors": [
        {
          "id": "ticketscope--e1-s1--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s1--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s1--AC-3",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s1--AC-4",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s5--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s6--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s7--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s8--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s9--AC-2",
          "coverage": "FULL"
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
          "id": "ticketscope--e1-s10--AC-4",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-1",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-2",
          "coverage": "FULL"
        },
        {
          "id": "ticketscope--e1-s11--AC-3",
          "coverage": "FULL"
        }
      ],
      "missingBehaviors": []
    },
    {
      "id": "ticketscope--e1-s3--AC-1",
      "kind": "exception",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s3--AC-2",
      "kind": "exception",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s3--AC-3",
      "kind": "exception",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s4--AC-1",
      "kind": "exception",
      "coverage": "PARTIAL"
    },
    {
      "id": "ticketscope--e1-s4--AC-2",
      "kind": "exception",
      "coverage": "FULL"
    },
    {
      "id": "ticketscope--e1-s14--AC-2",
      "kind": "exception",
      "coverage": "NONE"
    }
  ]
}
```
