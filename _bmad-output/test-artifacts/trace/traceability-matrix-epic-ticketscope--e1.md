---
runScope: "epic"
runKey: "epic-ticketscope--e1"
targetType: "epic"
targetId: "ticketscope--e1"
targetLabel: "Epic 1: Keyword search over Mojang issues, deployed on kind"
workflowStatus: "completed"
stepsCompleted: ["step-01-load-context", "step-02-discover-tests", "step-03-map-criteria", "step-04-analyze-gaps", "step-05-gate-decision"]
lastStep: "step-05-gate-decision"
lastSaved: "2026-11-07"
coverageBasis: "acceptance_criteria"
oracleConfidence: "high"
oracleResolutionMode: "formal_requirements"
oracleSources: ["_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md", "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md"]
externalPointerStatus: "not_used"
oracleGranularity: "requirements"
criterionLedger: [{"id": "ticketscope--e1-s1--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s1", "name": "Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.", "text": "Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:94", "priority": "P0", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s1--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s1", "name": "Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.", "text": "Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:95", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s1--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s1", "name": "Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.", "text": "Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s1--AC-4", "localId": "AC-4", "story": "ticketscope--e1-s1", "name": "Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.", "text": "Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:97", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s2--verify", "localId": "verify", "story": "ticketscope--e1-s2", "name": "The epic's Notes hold a dated Decision line that says yes, yes with named conditions, or no, and story 3's entry reflects any conditions.", "text": "The epic's Notes hold a dated Decision line that says yes, yes with named conditions, or no, and story 3's entry reflects any conditions.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml:27", "priority": "P2", "priorityBasis": "inferred", "declaredLinks": ["R1"], "validLinks": ["R1"], "invalidLinks": [], "exception": "none"}, {"id": "ticketscope--e1-s3--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s3", "name": "Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.", "text": "Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:91", "priority": "P0", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s3--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s3", "name": "Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.", "text": "Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:92", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s3--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s3", "name": "Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.", "text": "Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:93", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s12--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s12", "name": "The instances and leading projects are compared on the decision rule", "text": "**The instances and leading projects are compared on the decision rule** Verify: a findings note beside this ticket holds a table per instance and per leading project. Each table gives the issue count, in-subset duplicate pairs by kind, the outcome shares under the proposed mapping, the issue-type mix, and the text-hygiene counts. The CSVs it was built from sit with it.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:65", "priority": "P2", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s12--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s12", "name": "The recommended subset is shown to work", "text": "**The recommended subset is shown to work** Verify: the findings note names the subset and its expected duplicate-pair count by kind. It shows the subset's measured load time through story 3's timed-load script within 600 s, and 20 sampled issues per leading candidate with the author's judgement of each.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:67", "priority": "P2", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s12--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s12", "name": "The answer and its consequences are recorded where the waiting tickets read them", "text": "**The answer and its consequences are recorded where the waiting tickets read them** Verify: the epic's Notes holds a dated Decision line: switch, stay, or switch with named conditions. On switch, the line names:  - the subset; - the `resolution`-to-outcome mapping and the \"answered\" rule; - the kind rule extended to Jira `{code}` and `{noformat}` blocks, since a kind-rule change needs a reload and a baseline update (epic Constraints, Kind rule); - the attribution line.  It also amends the epic's Corpus scope (the 20,000 cap and the source) and Corpus terms for the new source, and says the data lane and epic-eval-gate are to be replanned.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:69", "priority": "P2", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s12--AC-4", "localId": "AC-4", "story": "ticketscope--e1-s12", "name": "The author accepts it", "text": "**The author accepts it** Verify: the Decision line is attributed to the author (user) and dated.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:78", "priority": "P2", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s4--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s4", "name": "Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.", "text": "Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:80", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s4--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s4", "name": "Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).", "text": "Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:81", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s14--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s14", "name": "Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.", "text": "Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:91", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s14--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s14", "name": "Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.", "text": "Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:92", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s14--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s14", "name": "Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.", "text": "Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:93", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s13--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s13", "name": "Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.", "text": "Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:95", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s13--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s13", "name": "Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.", "text": "Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s13--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s13", "name": "Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.", "text": "Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:97", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s13--AC-4", "localId": "AC-4", "story": "ticketscope--e1-s13", "name": "Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line.", "text": "Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:98", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s5--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s5", "name": "Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)–(6) pass on snapshot 2026.11.1.", "text": "Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)–(6) pass on snapshot 2026.11.1.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s5--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s5", "name": "Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).", "text": "Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:97", "priority": "P0", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s5--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s5", "name": "Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.", "text": "Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:98", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s5--AC-4", "localId": "AC-4", "story": "ticketscope--e1-s5", "name": "Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.", "text": "Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:99", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s5--AC-5", "localId": "AC-5", "story": "ticketscope--e1-s5", "name": "Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.", "text": "Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:100", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s6--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s6", "name": "Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.", "text": "Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s6--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s6", "name": "Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).", "text": "Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:97", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s6--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s6", "name": "Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.", "text": "Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:98", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s7--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s7", "name": "Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.", "text": "Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:80", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s7--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s7", "name": "Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).", "text": "Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:81", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s7--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s7", "name": "Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.", "text": "Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:82", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s8--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s8", "name": "Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).", "text": "Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:92", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s8--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s8", "name": "Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.", "text": "Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:93", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s8--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s8", "name": "Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.", "text": "Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:94", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s9--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s9", "name": "Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).", "text": "Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s9--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s9", "name": "Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.", "text": "Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:97", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s9--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s9", "name": "Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.", "text": "Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:98", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s9--AC-4", "localId": "AC-4", "story": "ticketscope--e1-s9", "name": "Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).", "text": "Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:99", "priority": "P3", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s10--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s10", "name": "Given the change, when `grep -rnE \"SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS\" src tests` runs, then it finds nothing.", "text": "Given the change, when `grep -rnE \"SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS\" src tests` runs, then it finds nothing.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:69", "priority": "P2", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s10--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s10", "name": "Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.", "text": "Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:70", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s10--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s10", "name": "Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.", "text": "Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:71", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s10--AC-4", "localId": "AC-4", "story": "ticketscope--e1-s10", "name": "Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.", "text": "Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:72", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s11--AC-1", "localId": "AC-1", "story": "ticketscope--e1-s11", "name": "Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.", "text": "Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:70", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s11--AC-2", "localId": "AC-2", "story": "ticketscope--e1-s11", "name": "Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.", "text": "Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:71", "priority": "P2", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}, {"id": "ticketscope--e1-s11--AC-3", "localId": "AC-3", "story": "ticketscope--e1-s11", "name": "Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.", "text": "Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:72", "priority": "P1", "priorityBasis": "inferred", "declaredLinks": [], "validLinks": [], "invalidLinks": [], "exception": "unlinked"}]
oracleLedger: [{"id": "ticketscope--e1--R1", "kind": "requirement", "requirement": "An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues.", "parent": "parent R1", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:33", "priority": "P2", "priorityBasis": "contributors", "contributors": ["ticketscope--e1-s2--verify"]}, {"id": "ticketscope--e1--R2", "kind": "requirement", "requirement": "A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome.", "parent": "parent R1", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:34", "priority": "P1", "priorityBasis": "inferred", "contributors": []}, {"id": "ticketscope--e1--R3", "kind": "requirement", "requirement": "Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes.", "parent": "parent R2", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:35", "priority": "P1", "priorityBasis": "inferred", "contributors": []}, {"id": "ticketscope--e1--R4", "kind": "requirement", "requirement": "One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries.", "parent": "parent R5", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:36", "priority": "P1", "priorityBasis": "inferred", "contributors": []}, {"id": "ticketscope--e1--R5", "kind": "requirement", "requirement": "CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes.", "parent": "parent R3", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:37", "priority": "P1", "priorityBasis": "inferred", "contributors": []}, {"id": "ticketscope--e1--R6", "kind": "requirement", "requirement": "One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace.", "parent": "parent R8", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:38", "priority": "P1", "priorityBasis": "inferred", "contributors": []}, {"id": "ticketscope--e1--R7", "kind": "requirement", "requirement": "Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR.", "parent": "parent R11", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:39", "priority": "P1", "priorityBasis": "inferred", "contributors": []}, {"id": "ticketscope--e1-s1--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:94", "priority": "P0", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test."}, {"id": "ticketscope--e1-s1--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:95", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`."}, {"id": "ticketscope--e1-s1--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails."}, {"id": "ticketscope--e1-s1--AC-4", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:97", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready."}, {"id": "ticketscope--e1-s3--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:91", "priority": "P0", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output."}, {"id": "ticketscope--e1-s3--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:92", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist."}, {"id": "ticketscope--e1-s3--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:93", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged."}, {"id": "ticketscope--e1-s12--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:65", "priority": "P2", "priorityBasis": "inferred", "kind": "exception", "requirement": "The instances and leading projects are compared on the decision rule"}, {"id": "ticketscope--e1-s12--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:67", "priority": "P2", "priorityBasis": "inferred", "kind": "exception", "requirement": "The recommended subset is shown to work"}, {"id": "ticketscope--e1-s12--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:69", "priority": "P2", "priorityBasis": "inferred", "kind": "exception", "requirement": "The answer and its consequences are recorded where the waiting tickets read them"}, {"id": "ticketscope--e1-s12--AC-4", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:78", "priority": "P2", "priorityBasis": "inferred", "kind": "exception", "requirement": "The author accepts it"}, {"id": "ticketscope--e1-s4--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:80", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`."}, {"id": "ticketscope--e1-s4--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:81", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test)."}, {"id": "ticketscope--e1-s14--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:91", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold."}, {"id": "ticketscope--e1-s14--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:92", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes."}, {"id": "ticketscope--e1-s14--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:93", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`."}, {"id": "ticketscope--e1-s13--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:95", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes."}, {"id": "ticketscope--e1-s13--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun."}, {"id": "ticketscope--e1-s13--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:97", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0."}, {"id": "ticketscope--e1-s13--AC-4", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:98", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line."}, {"id": "ticketscope--e1-s5--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)–(6) pass on snapshot 2026.11.1."}, {"id": "ticketscope--e1-s5--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:97", "priority": "P0", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test)."}, {"id": "ticketscope--e1-s5--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:98", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1."}, {"id": "ticketscope--e1-s5--AC-4", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:99", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source."}, {"id": "ticketscope--e1-s5--AC-5", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:100", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600."}, {"id": "ticketscope--e1-s6--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included."}, {"id": "ticketscope--e1-s6--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:97", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged)."}, {"id": "ticketscope--e1-s6--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:98", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical."}, {"id": "ticketscope--e1-s7--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:80", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome."}, {"id": "ticketscope--e1-s7--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:81", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c)."}, {"id": "ticketscope--e1-s7--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:82", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical."}, {"id": "ticketscope--e1-s8--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:92", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7)."}, {"id": "ticketscope--e1-s8--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:93", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket."}, {"id": "ticketscope--e1-s8--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:94", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run."}, {"id": "ticketscope--e1-s9--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:96", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b)."}, {"id": "ticketscope--e1-s9--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:97", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`."}, {"id": "ticketscope--e1-s9--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:98", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`."}, {"id": "ticketscope--e1-s9--AC-4", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:99", "priority": "P3", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual)."}, {"id": "ticketscope--e1-s10--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:69", "priority": "P2", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the change, when `grep -rnE \"SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS\" src tests` runs, then it finds nothing."}, {"id": "ticketscope--e1-s10--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:70", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`."}, {"id": "ticketscope--e1-s10--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:71", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical."}, {"id": "ticketscope--e1-s10--AC-4", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:72", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run."}, {"id": "ticketscope--e1-s11--AC-1", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:70", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank."}, {"id": "ticketscope--e1-s11--AC-2", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:71", "priority": "P2", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again."}, {"id": "ticketscope--e1-s11--AC-3", "exception": "unlinked", "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:72", "priority": "P1", "priorityBasis": "inferred", "kind": "exception", "requirement": "Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass."}]
collectionStatus: "COLLECTED"
sourceSha: "53358199a43fee326e8834d0d7c881a2a566b54a"
tempCoverageMatrixPath: "/tmp/tea-trace-coverage-matrix-epic-ticketscope--e1-2026-11-07T17-26-31.307766+00-00.json"
---

# Traceability Matrix & Gate Decision — Epic 1: Keyword search over Mojang issues, deployed on kind

## Gate Decision: FAIL

**Rationale:** P0 coverage is 33% (required: 100%). 2 critical requirement(s) below FULL coverage. Overall FULL coverage is 35% (minimum 80%); P1 is 39% (minimum 80%, PASS target 90%).

This is requirements-to-tests coverage, not a code line coverage percentage or a claim that the product fails to run. Forty-five selected criteria omit explicit epic requirement links. Those criteria remain separate gate rows, while six epic requirements have no contributors. Historical criteria and missing execution evidence also lower coverage.

**Date:** 2026-11-07 (America/New_York). **Evaluator:** Codex / Master Test Architect. **Source:** `53358199a43fee326e8834d0d7c881a2a566b54a`.

## Context and Oracle

Formal epic requirements R1–R7 are the high-confidence coverage oracle. All 14 entries were resolved with tickets.py; 46 selected criteria are frozen in the frontmatter. The gate inventory contains seven requirements plus 45 unlinked criteria. Plan criteria do not inherit a ticket’s covers; only verify-only criteria do, per the installed contract. No requirement IDs are duplicated. All priorities without explicit source annotations were inferred before mapping: P0 for baseline bring-up, snapshot identity hygiene and checksum integrity; P1 for core behavior and deployment integration; P2 for research decisions and fault-injection checks; P3 for human visual Grafana verification.

User resolution (2026-11-07): story 1.12 uses the ticket’s four criteria, not the plan’s three. Other verify-only tickets use their plan criteria when present. Historical GitHub ingest/outcome criteria are retained; the epic explicitly preserved those completed stories and later retired the implementation. They are not silently rewritten to Jira criteria.

Supporting artifacts: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md` (epic companion; canonical test-artifacts location absent); `_bmad-output/test-artifacts/nfr/nfr-assessment-epic-1.md` (legacy numbered-epic audit, CONCERNS; canonical v7-keyed audit absent). Architecture spine and story references provide context, not standalone test evidence. No PRD or tech-spec is present; initiative requirements and epic acceptance criteria apply.

Knowledge: test-priorities-matrix.md, risk-governance.md, probability-impact.md, test-quality.md, selective-testing.md. Execution mode: sequential. Collection: contract_static; no live results are generated by this workflow.


## Coverage Summary

| Priority | Total | FULL | Coverage |
| --- | ---: | ---: | ---: |
| P0 | 3 | 1 | 33% |
| P1 | 41 | 16 | 39% |
| P2 | 7 | 1 | 14% |
| P3 | 1 | 0 | 0% |
| Overall | 52 | 18 | 35% |

Discovery found 510 test declarations in 37 files. Accepted evidence comprises 87 unique test declarations across 20 files; parameter expansions are not separate declarations. The 46 criterion statuses are 18 FULL, 14 PARTIAL, 13 NONE and one UNIT-ONLY. The 52 gate rows are 18 FULL, 14 PARTIAL, 19 NONE and one UNIT-ONLY. No tests or cluster workflows were run by this trace; the absent live manifest supplies zero coverage.

## Requirement Oracle Mapping

| ID | Requirement | Priority | Coverage |
| --- | --- | --- | --- |
| ticketscope--e1--R1 | An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues. | P2 | NONE |
| ticketscope--e1--R2 | A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome. | P1 | NONE |
| ticketscope--e1--R3 | Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes. | P1 | NONE |
| ticketscope--e1--R4 | One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries. | P1 | NONE |
| ticketscope--e1--R5 | CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes. | P1 | NONE |
| ticketscope--e1--R6 | One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace. | P1 | NONE |
| ticketscope--e1--R7 | Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR. | P1 | NONE |
| ticketscope--e1-s1--AC-1 | Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test. | P0 | PARTIAL |
| ticketscope--e1-s1--AC-2 | Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`. | P1 | NONE |
| ticketscope--e1-s1--AC-3 | Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails. | P1 | PARTIAL |
| ticketscope--e1-s1--AC-4 | Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready. | P1 | NONE |
| ticketscope--e1-s3--AC-1 | Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output. | P0 | PARTIAL |
| ticketscope--e1-s3--AC-2 | Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist. | P1 | FULL |
| ticketscope--e1-s3--AC-3 | Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged. | P1 | PARTIAL |
| ticketscope--e1-s12--AC-1 | The instances and leading projects are compared on the decision rule | P2 | NONE |
| ticketscope--e1-s12--AC-2 | The recommended subset is shown to work | P2 | NONE |
| ticketscope--e1-s12--AC-3 | The answer and its consequences are recorded where the waiting tickets read them | P2 | NONE |
| ticketscope--e1-s12--AC-4 | The author accepts it | P2 | NONE |
| ticketscope--e1-s4--AC-1 | Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`. | P1 | PARTIAL |
| ticketscope--e1-s4--AC-2 | Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test). | P1 | FULL |
| ticketscope--e1-s14--AC-1 | Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold. | P1 | FULL |
| ticketscope--e1-s14--AC-2 | Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes. | P1 | NONE |
| ticketscope--e1-s14--AC-3 | Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`. | P1 | FULL |
| ticketscope--e1-s13--AC-1 | Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes. | P1 | FULL |
| ticketscope--e1-s13--AC-2 | Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun. | P1 | FULL |
| ticketscope--e1-s13--AC-3 | Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0. | P1 | NONE |
| ticketscope--e1-s13--AC-4 | Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line. | P1 | PARTIAL |
| ticketscope--e1-s5--AC-1 | Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)–(6) pass on snapshot 2026.11.1. | P1 | FULL |
| ticketscope--e1-s5--AC-2 | Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test). | P0 | FULL |
| ticketscope--e1-s5--AC-3 | Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1. | P1 | FULL |
| ticketscope--e1-s5--AC-4 | Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source. | P1 | FULL |
| ticketscope--e1-s5--AC-5 | Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600. | P1 | NONE |
| ticketscope--e1-s6--AC-1 | Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included. | P1 | FULL |
| ticketscope--e1-s6--AC-2 | Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged). | P1 | PARTIAL |
| ticketscope--e1-s6--AC-3 | Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical. | P1 | NONE |
| ticketscope--e1-s7--AC-1 | Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome. | P1 | FULL |
| ticketscope--e1-s7--AC-2 | Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c). | P1 | FULL |
| ticketscope--e1-s7--AC-3 | Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical. | P1 | NONE |
| ticketscope--e1-s8--AC-1 | Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7). | P1 | PARTIAL |
| ticketscope--e1-s8--AC-2 | Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket. | P1 | FULL |
| ticketscope--e1-s8--AC-3 | Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run. | P1 | FULL |
| ticketscope--e1-s9--AC-1 | Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b). | P1 | FULL |
| ticketscope--e1-s9--AC-2 | Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`. | P1 | PARTIAL |
| ticketscope--e1-s9--AC-3 | Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`. | P1 | UNIT-ONLY |
| ticketscope--e1-s9--AC-4 | Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual). | P3 | PARTIAL |
| ticketscope--e1-s10--AC-1 | Given the change, when `grep -rnE "SnapshotIssue([^V]\|$)\|TimelineEvent\|_github_outcome\|MAINTAINER_ASSOCIATIONS" src tests` runs, then it finds nothing. | P2 | FULL |
| ticketscope--e1-s10--AC-2 | Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`. | P1 | PARTIAL |
| ticketscope--e1-s10--AC-3 | Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical. | P1 | NONE |
| ticketscope--e1-s10--AC-4 | Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run. | P1 | PARTIAL |
| ticketscope--e1-s11--AC-1 | Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank. | P1 | FULL |
| ticketscope--e1-s11--AC-2 | Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again. | P2 | PARTIAL |
| ticketscope--e1-s11--AC-3 | Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass. | P1 | PARTIAL |

## Detailed Mapping

### ticketscope--e1--R1 (P2): An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues.

- **Coverage:** NONE
- **Priority basis:** contributors
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:33`
- **Parent:** parent R1
- **Missing behaviors:** An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope).; The snapshot carries every field the spine's snapshot contract names.; a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues.

| Contributor | Story | Status | Tests |
| --- | --- | --- | --- |
| ticketscope--e1-s2--verify | ticketscope--e1-s2 | NONE | none |

The sole contributor verifies a dated corpus-terms decision; it does not state the publishing, contract-field or short/log-heavy snapshot behaviors.
- **Recommendation:** repair the declared criterion links and cover every missing behavior; no tests map directly to the requirement row.

### ticketscope--e1--R2 (P1): A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:34`
- **Parent:** parent R1
- **Missing behaviors:** A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome.
- **Contributors:** none
- **Gaps:** no story covers it through explicit criterion links. Tests may exist on unlinked criteria below.
- **Recommendation:** repair the declared criterion links and cover every missing behavior; no tests map directly to the requirement row.

### ticketscope--e1--R3 (P1): Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:35`
- **Parent:** parent R2
- **Missing behaviors:** Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes.
- **Contributors:** none
- **Gaps:** no story covers it through explicit criterion links. Tests may exist on unlinked criteria below.
- **Recommendation:** repair the declared criterion links and cover every missing behavior; no tests map directly to the requirement row.

### ticketscope--e1--R4 (P1): One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:36`
- **Parent:** parent R5
- **Missing behaviors:** One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries.
- **Contributors:** none
- **Gaps:** no story covers it through explicit criterion links. Tests may exist on unlinked criteria below.
- **Recommendation:** repair the declared criterion links and cover every missing behavior; no tests map directly to the requirement row.

### ticketscope--e1--R5 (P1): CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:37`
- **Parent:** parent R3
- **Missing behaviors:** CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes.
- **Contributors:** none
- **Gaps:** no story covers it through explicit criterion links. Tests may exist on unlinked criteria below.
- **Recommendation:** repair the declared criterion links and cover every missing behavior; no tests map directly to the requirement row.

### ticketscope--e1--R6 (P1): One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:38`
- **Parent:** parent R8
- **Missing behaviors:** One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace.
- **Contributors:** none
- **Gaps:** no story covers it through explicit criterion links. Tests may exist on unlinked criteria below.
- **Recommendation:** repair the declared criterion links and cover every missing behavior; no tests map directly to the requirement row.

### ticketscope--e1--R7 (P1): Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:39`
- **Parent:** parent R11
- **Missing behaviors:** Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR.
- **Contributors:** none
- **Gaps:** no story covers it through explicit criterion links. Tests may exist on unlinked criteria below.
- **Recommendation:** repair the declared criterion links and cover every missing behavior; no tests map directly to the requirement row.

### ticketscope--e1-s1--AC-1 (P0): Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:94`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The Gateway and two-instance assertions cover bring-up outcomes. Workflow wiring runs checks, but no static assertion proves all CI tools and both releases pass on a PR at this source revision.

Test identities and levels: `test_search_serves_the_pinned_snapshot_with_outcomes` (e2e), `test_cluster_has_two_ready_instances` (e2e), `test_layer_imports_only_stdlib_pydantic_and_itself` (unit).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:169`, `tests/smoke/test_gateway.py:171`, `tests/smoke/test_gateway.py:172`, `tests/smoke/test_gateway.py:173`, `tests/smoke/test_gateway.py:174`, `tests/smoke/test_gateway.py:175`, `tests/smoke/test_gateway.py:177`, `tests/smoke/test_gateway.py:178`, `tests/smoke/test_gateway.py:179`, `tests/smoke/test_gateway.py:382`, `tests/smoke/test_gateway.py:385`, `tests/unit/test_layer_imports.py:42`, `tests/unit/test_layer_imports.py:45`, `tests/unit/test_layer_imports.py:52`.

### ticketscope--e1-s1--AC-2 (P1): Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:95`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The CI matrix declares both architectures; there is no accepted test or current-sha live result proving both builds on an image-changing PR.

**Tests:** none accepted.

### ticketscope--e1-s1--AC-3 (P1): Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:96`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The AST allow-list checks current layer imports. It does not plant an adapter import and assert that lint-imports rejects it.

Test identities and levels: `test_layer_imports_only_stdlib_pydantic_and_itself` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_layer_imports.py:42`, `tests/unit/test_layer_imports.py:45`, `tests/unit/test_layer_imports.py:52`.

### ticketscope--e1-s1--AC-4 (P1): Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:97`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The workflow emits runner-fit metrics, but no accepted static test or matching live result checks those three values.

**Tests:** none accepted.

### ticketscope--e1-s3--AC-1 (P0): Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:91`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Current tests validate schema v2 and identity absence. They do not establish a GitHub-recording ingest or github.com issue URLs: the implementation was superseded by Jira.

Test identities and levels: `test_output_validates_against_schema_v2_and_the_model` (unit), `test_no_identity_appears_in_the_output` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_ingest_jira.py:74`, `tests/unit/test_ingest_jira.py:81`, `tests/unit/test_ingest_jira.py:85`, `tests/unit/test_ingest_jira.py:249`, `tests/unit/test_ingest_jira.py:270`, `tests/unit/test_ingest_jira.py:273`, `tests/unit/test_ingest_jira.py:256`.

### ticketscope--e1-s3--AC-2 (P1): Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:92`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Checksum digest and asset name are checked, load reads the output, and deterministic byte comparisons read the kinds and report output files.

Test identities and levels: `test_checksum_matches_and_load_reads_the_output` (unit), `test_rerun_is_byte_identical` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_ingest_jira.py:95`, `tests/unit/test_ingest_jira.py:99`, `tests/unit/test_ingest_jira.py:100`, `tests/unit/test_ingest_jira.py:102`, `tests/unit/test_ingest_jira.py:111`, `tests/unit/test_ingest_jira.py:116`, `tests/unit/test_ingest_jira.py:118`.

### ticketscope--e1-s3--AC-3 (P1): Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:93`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Notes fields, attribution, version advancement and non-clobber behavior have tests. snapshot.yml was retired; a real two-dispatch publish with unchanged earlier assets is not established.

Test identities and levels: `test_notes_state_subset_counts_pairs_kinds_and_load_time` (unit), `test_notes_carry_the_attribution_line` (unit), `test_version_taken_gives_the_next_n` (unit), `test_n_is_numeric_and_never_reuses_a_gap` (unit), `test_script_never_clobbers_or_deletes` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_ingest_notes.py:31`, `tests/unit/test_ingest_notes.py:33`, `tests/unit/test_ingest_notes.py:34`, `tests/unit/test_ingest_notes.py:35`, `tests/unit/test_ingest_notes.py:36`, `tests/unit/test_ingest_notes.py:37`, `tests/unit/test_ingest_notes.py:38`, `tests/unit/test_ingest_notes.py:39`, `tests/unit/test_ingest_notes.py:40`, `tests/unit/test_ingest_notes.py:43`, `tests/unit/test_ingest_notes.py:44`, `tests/unit/test_ingest_version.py:8`, `tests/unit/test_ingest_version.py:10`, `tests/unit/test_ingest_version.py:18`, `tests/unit/test_ingest_version.py:21`, `tests/unit/test_publish_script.py:111`, `tests/unit/test_publish_script.py:116`, `tests/unit/test_publish_script.py:117`, `tests/unit/test_publish_script.py:118`, `tests/unit/test_publish_script.py:119`.

### ticketscope--e1-s12--AC-1 (P2): The instances and leading projects are compared on the decision rule

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:65`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Research CSVs and findings exist, but none of the discovered static tests verifies every comparison and hygiene count.

**Tests:** none accepted.

### ticketscope--e1-s12--AC-2 (P2): The recommended subset is shown to work

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:67`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The timed measurement and human sample judgments are historical documentation; no source-sha live record is supplied.

**Tests:** none accepted.

### ticketscope--e1-s12--AC-3 (P2): The answer and its consequences are recorded where the waiting tickets read them

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:69`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The epic decision and replanning prose are documents, not a test asserting all required changes.

**Tests:** none accepted.

### ticketscope--e1-s12--AC-4 (P2): The author accepts it

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:78`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Human author acceptance is recorded in prose; absent a criterion-addressed live manifest it is not counted as test coverage.

**Tests:** none accepted.

### ticketscope--e1-s4--AC-1 (P1): Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:80`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Threshold boundaries are tested. The named GitHub outcome branches and tie cases were deliberately removed in story 1.10, so the frozen criterion is only partially established.

Test identities and levels: `test_kind_just_below_threshold_is_short` (unit), `test_kind_at_threshold_is_log_heavy` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_derive.py:56`, `tests/unit/test_derive.py:58`, `tests/unit/test_derive.py:59`, `tests/unit/test_derive.py:63`, `tests/unit/test_derive.py:65`, `tests/unit/test_derive.py:66`.

### ticketscope--e1-s4--AC-2 (P1): Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:81`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Computed kinds are checked against every expected fixture kind.

Test identities and levels: `test_fixture_records_kinds_outside_the_schema_and_they_hold` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_snapshot.py:128`, `tests/unit/test_snapshot.py:131`, `tests/unit/test_snapshot.py:132`, `tests/unit/test_snapshot.py:133`, `tests/unit/test_snapshot.py:134`.

### ticketscope--e1-s14--AC-1 (P1): Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:91`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Synthetic Jira cases cover resolution classes, unknown, answered/non-answered Question cases, and both sides of the block threshold.

Test identities and levels: `test_duplicate_points_at_target` (unit), `test_duplicate_without_link_has_no_ref` (unit), `test_fixed` (unit), `test_not_planned` (unit), `test_stale` (unit), `test_answered_by_resolution` (unit), `test_unresolved_is_unknown` (unit), `test_unmapped_resolution_is_unknown` (unit), `test_resolution_matched_trimmed_and_case_insensitive` (unit), `test_question_answered_by_non_reporter_comment` (unit), `test_question_comment_at_resolution_time_counts` (unit), `test_question_only_reporter_comments_is_fixed` (unit), `test_question_non_reporter_comment_after_resolution_is_fixed` (unit), `test_question_unmapped_resolution_answered` (unit), `test_bug_type_with_non_reporter_comment_stays_fixed` (unit), `test_support_duplicate_stays_duplicate` (unit), `test_support_other_classes_keep_their_class` (unit), `test_kind_just_below_threshold_is_short` (unit), `test_kind_at_threshold_is_log_heavy` (unit), `test_parameterised_toggle_scores_like_plain` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_derive_jira.py:71`, `tests/unit/test_derive_jira.py:73`, `tests/unit/test_derive_jira.py:78`, `tests/unit/test_derive_jira.py:80`, `tests/unit/test_derive_jira.py:83`, `tests/unit/test_derive_jira.py:85`, `tests/unit/test_derive_jira.py:88`, `tests/unit/test_derive_jira.py:90`, `tests/unit/test_derive_jira.py:93`, `tests/unit/test_derive_jira.py:95`, `tests/unit/test_derive_jira.py:98`, `tests/unit/test_derive_jira.py:100`, `tests/unit/test_derive_jira.py:103`, `tests/unit/test_derive_jira.py:104`, `tests/unit/test_derive_jira.py:107`, `tests/unit/test_derive_jira.py:108`, `tests/unit/test_derive_jira.py:111`, `tests/unit/test_derive_jira.py:113`, `tests/unit/test_derive_jira.py:114`, `tests/unit/test_derive_jira.py:120`, `tests/unit/test_derive_jira.py:126`, `tests/unit/test_derive_jira.py:131`, `tests/unit/test_derive_jira.py:137`, `tests/unit/test_derive_jira.py:140`, `tests/unit/test_derive_jira.py:144`, `tests/unit/test_derive_jira.py:147`, `tests/unit/test_derive_jira.py:151`, `tests/unit/test_derive_jira.py:154`, `tests/unit/test_derive_jira.py:158`, `tests/unit/test_derive_jira.py:163`, `tests/unit/test_derive_jira.py:167`, `tests/unit/test_derive_jira.py:170`, `tests/unit/test_derive_jira.py:177`, `tests/unit/test_derive_jira.py:184`, `tests/unit/test_derive_jira.py:191`, `tests/unit/test_derive_jira.py:192`, `tests/unit/test_derive_jira.py:261`, `tests/unit/test_derive_jira.py:262`, `tests/unit/test_derive_jira.py:263`, `tests/unit/test_derive_jira.py:264`, `tests/unit/test_derive_jira.py:267`, `tests/unit/test_derive_jira.py:269`, `tests/unit/test_derive_jira.py:270`, `tests/unit/test_derive_jira.py:278`, `tests/unit/test_derive_jira.py:283`, `tests/unit/test_derive_jira.py:284`, `tests/unit/test_derive_jira.py:285`.

### ticketscope--e1-s14--AC-2 (P1): Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:92`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The GitHub rules were explicitly retired by the sweep; remaining test_derive.py cases test kinds and versions only.

**Tests:** none accepted.

### ticketscope--e1-s14--AC-3 (P1): Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:93`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The version equals kind2-t3.outcome3 and differs from the recorded story-4 version.

Test identities and levels: `test_derivation_version_differs_from_story_4` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_derive_jira.py:246`, `tests/unit/test_derive_jira.py:247`, `tests/unit/test_derive_jira.py:248`.

### ticketscope--e1-s13--AC-1 (P1): Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:95`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The recorded slice output validates against schema v2 and the model; checksum matches the generated compressed asset.

Test identities and levels: `test_output_validates_against_schema_v2_and_the_model` (unit), `test_checksum_matches_and_load_reads_the_output` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_ingest_jira.py:74`, `tests/unit/test_ingest_jira.py:81`, `tests/unit/test_ingest_jira.py:85`, `tests/unit/test_ingest_jira.py:95`, `tests/unit/test_ingest_jira.py:99`, `tests/unit/test_ingest_jira.py:100`, `tests/unit/test_ingest_jira.py:102`.

### ticketscope--e1-s13--AC-2 (P1): Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:96`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Committed schema is compared to the model-generated rendering, and deliberately drifted schema is rejected.

Test identities and levels: `test_committed_schema_matches_the_model` (unit), `test_drift_is_detected` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_snapshot.py:58`, `tests/unit/test_snapshot.py:61`, `tests/unit/test_snapshot.py:64`, `tests/unit/test_snapshot.py:70`.

### ticketscope--e1-s13--AC-3 (P1): Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:97`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

No static test executes time-load.sh against the v2 fixture; its historical manual execution has no live manifest.

**Tests:** none accepted.

### ticketscope--e1-s13--AC-4 (P1): Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:98`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Release note contents and publishing guards are tested; no test completes publishing from a restored dump on clean main and validates the resulting Release.

Test identities and levels: `test_notes_state_subset_counts_pairs_kinds_and_load_time` (unit), `test_notes_carry_the_attribution_line` (unit), `test_refuses_off_main` (unit), `test_refuses_a_dirty_checkout` (unit), `test_refuses_when_head_is_not_origin_main` (unit), `test_clean_main_passes_the_guards` (unit), `test_script_never_clobbers_or_deletes` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_ingest_notes.py:31`, `tests/unit/test_ingest_notes.py:33`, `tests/unit/test_ingest_notes.py:34`, `tests/unit/test_ingest_notes.py:35`, `tests/unit/test_ingest_notes.py:36`, `tests/unit/test_ingest_notes.py:37`, `tests/unit/test_ingest_notes.py:38`, `tests/unit/test_ingest_notes.py:39`, `tests/unit/test_ingest_notes.py:40`, `tests/unit/test_ingest_notes.py:43`, `tests/unit/test_ingest_notes.py:44`, `tests/unit/test_publish_script.py:73`, `tests/unit/test_publish_script.py:77`, `tests/unit/test_publish_script.py:78`, `tests/unit/test_publish_script.py:79`, `tests/unit/test_publish_script.py:82`, `tests/unit/test_publish_script.py:86`, `tests/unit/test_publish_script.py:87`, `tests/unit/test_publish_script.py:88`, `tests/unit/test_publish_script.py:91`, `tests/unit/test_publish_script.py:95`, `tests/unit/test_publish_script.py:96`, `tests/unit/test_publish_script.py:97`, `tests/unit/test_publish_script.py:100`, `tests/unit/test_publish_script.py:104`, `tests/unit/test_publish_script.py:105`, `tests/unit/test_publish_script.py:106`, `tests/unit/test_publish_script.py:107`, `tests/unit/test_publish_script.py:108`, `tests/unit/test_publish_script.py:111`, `tests/unit/test_publish_script.py:116`, `tests/unit/test_publish_script.py:117`, `tests/unit/test_publish_script.py:118`, `tests/unit/test_publish_script.py:119`.

### ticketscope--e1-s5--AC-1 (P1): Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)–(6) pass on snapshot 2026.11.1.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:96`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The six checks have E2E assertions over the pinned version, stored kinds/outcomes, report shares/budget, no-op, derivation reload and two ready instances. This classifies static test coverage, not fresh CI execution.

Test identities and levels: `test_search_serves_the_pinned_snapshot_with_outcomes` (e2e), `test_every_issue_is_loaded_with_a_kind_and_an_outcome` (e2e), `test_load_log_has_the_report` (e2e), `test_upgrade_with_the_same_pin_is_a_no_op` (e2e), `test_stale_preprocessing_version_reloads` (e2e), `test_cluster_has_two_ready_instances` (e2e).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:169`, `tests/smoke/test_gateway.py:171`, `tests/smoke/test_gateway.py:172`, `tests/smoke/test_gateway.py:173`, `tests/smoke/test_gateway.py:174`, `tests/smoke/test_gateway.py:175`, `tests/smoke/test_gateway.py:177`, `tests/smoke/test_gateway.py:178`, `tests/smoke/test_gateway.py:179`, `tests/smoke/test_gateway.py:324`, `tests/smoke/test_gateway.py:325`, `tests/smoke/test_gateway.py:330`, `tests/smoke/test_gateway.py:331`, `tests/smoke/test_gateway.py:332`, `tests/smoke/test_gateway.py:338`, `tests/smoke/test_gateway.py:347`, `tests/smoke/test_gateway.py:349`, `tests/smoke/test_gateway.py:351`, `tests/smoke/test_gateway.py:353`, `tests/smoke/test_gateway.py:354`, `tests/smoke/test_gateway.py:355`, `tests/smoke/test_gateway.py:343`, `tests/smoke/test_gateway.py:345`, `tests/smoke/test_gateway.py:361`, `tests/smoke/test_gateway.py:364`, `tests/smoke/test_gateway.py:365`, `tests/smoke/test_gateway.py:366`, `tests/smoke/test_gateway.py:372`, `tests/smoke/test_gateway.py:374`, `tests/smoke/test_gateway.py:375`, `tests/smoke/test_gateway.py:376`, `tests/smoke/test_gateway.py:382`, `tests/smoke/test_gateway.py:385`.

### ticketscope--e1-s5--AC-2 (P0): Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:97`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Wrong local/downloaded checksums fail with rows and corpus_meta unchanged; the adapter rollback test covers transaction failure.

Test identities and levels: `test_wrong_checksum_exits_1_and_keeps_the_corpus` (unit), `test_wrong_checksum_on_download_exits_1_and_keeps_the_corpus` (unit), `test_replace_corpus_rolls_back_when_the_rows_fail_midway` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_load_main.py:212`, `tests/unit/test_load_main.py:219`, `tests/unit/test_load_main.py:220`, `tests/unit/test_load_main.py:221`, `tests/unit/test_load_main.py:222`, `tests/unit/test_load_main.py:225`, `tests/unit/test_load_main.py:234`, `tests/unit/test_load_main.py:235`, `tests/unit/test_load_main.py:236`, `tests/unit/test_load_main.py:237`, `tests/unit/test_load_main.py:238`, `tests/unit/test_postgres_corpus_meta.py:148`, `tests/unit/test_postgres_corpus_meta.py:155`, `tests/unit/test_postgres_corpus_meta.py:156`.

### ticketscope--e1-s5--AC-3 (P1): Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:98`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Each computed fixture kind and the fixture best-match ranking are asserted by load, API and mode tests.

Test identities and levels: `test_computed_fixture_kinds_equal_the_expected_kinds` (unit), `test_best_match` (api), `test_keyword_ranks_by_overlap_then_number` (unit), `test_fixture_target_ranks_first` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_load_main.py:124`, `tests/unit/test_load_main.py:125`, `tests/unit/test_load_main.py:126`, `tests/unit/test_app.py:22`, `tests/unit/test_app.py:26`, `tests/unit/test_app.py:27`, `tests/unit/test_app.py:28`, `tests/unit/test_app.py:29`, `tests/unit/test_app.py:30`, `tests/unit/test_app.py:32`, `tests/unit/test_app.py:36`, `tests/unit/test_app.py:38`, `tests/unit/test_app.py:39`, `tests/unit/test_app.py:40`, `tests/unit/test_app.py:34`, `tests/unit/test_modes.py:24`, `tests/unit/test_modes.py:34`, `tests/unit/test_modes.py:35`, `tests/unit/test_modes.py:44`, `tests/unit/test_modes.py:46`, `tests/unit/test_modes.py:47`, `tests/unit/test_modes.py:48`.

### ticketscope--e1-s5--AC-4 (P1): Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:99`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Golden version matches the pin, both issue identities exist in the pinned asset, and expected issues differ from sources.

Test identities and levels: `test_file_is_pinned_to_the_chart_snapshot` (unit), `test_expected_issue_differs_from_its_source` (unit), `test_source_and_expected_issues_exist_in_the_pinned_asset` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_golden_queries.py:56`, `tests/unit/test_golden_queries.py:58`, `tests/unit/test_golden_queries.py:59`, `tests/unit/test_golden_queries.py:60`, `tests/unit/test_golden_queries.py:76`, `tests/unit/test_golden_queries.py:79`, `tests/unit/test_golden_queries.py:80`, `tests/unit/test_golden_queries.py:87`, `tests/unit/test_golden_queries.py:93`.

### ticketscope--e1-s5--AC-5 (P1): Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:100`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The exact time-load.sh asset-only invocation and elapsed-time budget lack a rerunnable test or live manifest.

**Tests:** none accepted.

### ticketscope--e1-s6--AC-1 (P1): Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:96`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Kind smoke declares successful issue detail, 404, 422 problem responses and operator/log-heavy search. Tests have not been rerun for this trace.

Test identities and levels: `test_issue_detail_matches_the_search_hit` (e2e), `test_unknown_issue_is_a_404_problem` (e2e), `test_invalid_search_is_a_422_problem` (e2e), `test_operator_characters_rank` (e2e), `test_a_pasted_stack_trace_of_4kb_ranks` (e2e).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:191`, `tests/smoke/test_gateway.py:196`, `tests/smoke/test_gateway.py:197`, `tests/smoke/test_gateway.py:198`, `tests/smoke/test_gateway.py:201`, `tests/smoke/test_gateway.py:203`, `tests/smoke/test_gateway.py:215`, `tests/smoke/test_gateway.py:217`, `tests/smoke/test_gateway.py:75`, `tests/smoke/test_gateway.py:76`, `tests/smoke/test_gateway.py:78`, `tests/smoke/test_gateway.py:220`, `tests/smoke/test_gateway.py:222`, `tests/smoke/test_gateway.py:225`, `tests/smoke/test_gateway.py:234`, `tests/smoke/test_gateway.py:236`.

### ticketscope--e1-s6--AC-2 (P1): Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:97`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Current imports are inspected; no planted forbidden import drives lint-imports and asserts failure.

Test identities and levels: `test_layer_imports_only_stdlib_pydantic_and_itself` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_layer_imports.py:42`, `tests/unit/test_layer_imports.py:45`, `tests/unit/test_layer_imports.py:52`.

### ticketscope--e1-s6--AC-3 (P1): Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:98`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

API shape tests do not compare a saved response from before the change with the response after it.

**Tests:** none accepted.

### ticketscope--e1-s7--AC-1 (P1): Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:80`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Both golden entries drive the Gateway page. Rows assert rank, title, HTTPS link, kind and outcome.

Test identities and levels: `test_page_renders_each_golden_query` (e2e).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:303`, `tests/smoke/test_gateway.py:305`, `tests/smoke/test_gateway.py:306`, `tests/smoke/test_gateway.py:308`, `tests/smoke/test_gateway.py:309`, `tests/smoke/test_gateway.py:310`, `tests/smoke/test_gateway.py:311`, `tests/smoke/test_gateway.py:312`.

### ticketscope--e1-s7--AC-2 (P1): Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:81`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The smoke suite contains the Gateway page check alongside the other smoke behaviors. Static coverage only; no new cluster run.

Test identities and levels: `test_search_serves_the_pinned_snapshot_with_outcomes` (e2e), `test_no_match_is_empty_through_the_gateway` (e2e), `test_issue_detail_matches_the_search_hit` (e2e), `test_unknown_issue_is_a_404_problem` (e2e), `test_invalid_search_is_a_422_problem` (e2e), `test_operator_characters_rank` (e2e), `test_a_pasted_stack_trace_of_4kb_ranks` (e2e), `test_page_serves_the_form` (e2e), `test_page_renders_each_golden_query` (e2e), `test_page_escapes_a_script_query` (e2e), `test_every_issue_is_loaded_with_a_kind_and_an_outcome` (e2e), `test_load_log_has_the_report` (e2e), `test_upgrade_with_the_same_pin_is_a_no_op` (e2e), `test_stale_preprocessing_version_reloads` (e2e), `test_cluster_has_two_ready_instances` (e2e).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:169`, `tests/smoke/test_gateway.py:171`, `tests/smoke/test_gateway.py:172`, `tests/smoke/test_gateway.py:173`, `tests/smoke/test_gateway.py:174`, `tests/smoke/test_gateway.py:175`, `tests/smoke/test_gateway.py:177`, `tests/smoke/test_gateway.py:178`, `tests/smoke/test_gateway.py:179`, `tests/smoke/test_gateway.py:182`, `tests/smoke/test_gateway.py:184`, `tests/smoke/test_gateway.py:185`, `tests/smoke/test_gateway.py:191`, `tests/smoke/test_gateway.py:196`, `tests/smoke/test_gateway.py:197`, `tests/smoke/test_gateway.py:198`, `tests/smoke/test_gateway.py:201`, `tests/smoke/test_gateway.py:203`, `tests/smoke/test_gateway.py:215`, `tests/smoke/test_gateway.py:217`, `tests/smoke/test_gateway.py:75`, `tests/smoke/test_gateway.py:76`, `tests/smoke/test_gateway.py:78`, `tests/smoke/test_gateway.py:220`, `tests/smoke/test_gateway.py:222`, `tests/smoke/test_gateway.py:225`, `tests/smoke/test_gateway.py:234`, `tests/smoke/test_gateway.py:236`, `tests/smoke/test_gateway.py:291`, `tests/smoke/test_gateway.py:295`, `tests/smoke/test_gateway.py:298`, `tests/smoke/test_gateway.py:299`, `tests/smoke/test_gateway.py:303`, `tests/smoke/test_gateway.py:305`, `tests/smoke/test_gateway.py:306`, `tests/smoke/test_gateway.py:308`, `tests/smoke/test_gateway.py:309`, `tests/smoke/test_gateway.py:310`, `tests/smoke/test_gateway.py:311`, `tests/smoke/test_gateway.py:312`, `tests/smoke/test_gateway.py:315`, `tests/smoke/test_gateway.py:317`, `tests/smoke/test_gateway.py:318`, `tests/smoke/test_gateway.py:324`, `tests/smoke/test_gateway.py:325`, `tests/smoke/test_gateway.py:330`, `tests/smoke/test_gateway.py:331`, `tests/smoke/test_gateway.py:332`, `tests/smoke/test_gateway.py:338`, `tests/smoke/test_gateway.py:347`, `tests/smoke/test_gateway.py:349`, `tests/smoke/test_gateway.py:351`, `tests/smoke/test_gateway.py:353`, `tests/smoke/test_gateway.py:354`, `tests/smoke/test_gateway.py:355`, `tests/smoke/test_gateway.py:343`, `tests/smoke/test_gateway.py:345`, `tests/smoke/test_gateway.py:361`, `tests/smoke/test_gateway.py:364`, `tests/smoke/test_gateway.py:365`, `tests/smoke/test_gateway.py:366`, `tests/smoke/test_gateway.py:372`, `tests/smoke/test_gateway.py:374`, `tests/smoke/test_gateway.py:375`, `tests/smoke/test_gateway.py:376`, `tests/smoke/test_gateway.py:382`, `tests/smoke/test_gateway.py:385`.

### ticketscope--e1-s7--AC-3 (P1): Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:82`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

No accepted test compares an actual before/after saved /v1 response.

**Tests:** none accepted.

### ticketscope--e1-s8--AC-1 (P1): Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:92`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Backup completion has E2E checks and CI wiring is tested, but these do not prove checks/charts and all smoke checks passed on a current PR.

Test identities and levels: `test_on_demand_backup_completes_to_seaweedfs` (e2e), `test_ci_runs_integrated_then_smoke_in_one_kind_job` (unit).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:512`, `tests/smoke/test_gateway.py:493`, `tests/smoke/test_gateway.py:494`, `tests/smoke/test_gateway.py:498`, `tests/smoke/test_gateway.py:502`, `tests/smoke/test_gateway.py:503`, `tests/unit/test_integrated_check_expanded.py:65`, `tests/unit/test_integrated_check_expanded.py:67`, `tests/unit/test_integrated_check_expanded.py:68`, `tests/unit/test_integrated_check_expanded.py:69`, `tests/unit/test_integrated_check_expanded.py:70`.

### ticketscope--e1-s8--AC-2 (P1): Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:93`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The backup helper waits for completed and checks backup.info plus data.tar in SeaweedFS.

Test identities and levels: `test_on_demand_backup_completes_to_seaweedfs` (e2e).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:512`, `tests/smoke/test_gateway.py:493`, `tests/smoke/test_gateway.py:494`, `tests/smoke/test_gateway.py:498`, `tests/smoke/test_gateway.py:502`, `tests/smoke/test_gateway.py:503`.

### ticketscope--e1-s8--AC-3 (P1): Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:94`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Platform and app upgrades compare TLS and credential Secret data before and after.

Test identities and levels: `test_upgrades_keep_the_backup_tls_and_credentials` (e2e).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:409`, `tests/smoke/test_gateway.py:411`, `tests/smoke/test_gateway.py:430`.

### ticketscope--e1-s9--AC-1 (P1): Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:96`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Tempo and the Grafana datasource return the AD-10 trace tree on kind.

Test identities and levels: `test_one_search_yields_one_trace_in_tempo` (e2e), `test_the_trace_is_served_by_grafanas_tempo_datasource` (e2e).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:660`, `tests/smoke/test_gateway.py:566`, `tests/smoke/test_gateway.py:569`, `tests/smoke/test_gateway.py:570`, `tests/smoke/test_gateway.py:571`, `tests/smoke/test_gateway.py:573`, `tests/smoke/test_gateway.py:574`, `tests/smoke/test_gateway.py:575`, `tests/smoke/test_gateway.py:576`, `tests/smoke/test_gateway.py:577`, `tests/smoke/test_gateway.py:578`, `tests/smoke/test_gateway.py:582`, `tests/smoke/test_gateway.py:590`, `tests/smoke/test_gateway.py:711`.

### ticketscope--e1-s9--AC-2 (P1): Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:97`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Telemetry assertions establish instrumentation and CI wiring; they do not prove that the full lint/types/imports/pytest command chain passes.

Test identities and levels: `test_search_is_a_server_span_over_a_retrieval_span` (unit), `test_ci_runs_integrated_then_smoke_in_one_kind_job` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_telemetry.py:86`, `tests/unit/test_telemetry.py:96`, `tests/unit/test_telemetry.py:98`, `tests/unit/test_telemetry.py:99`, `tests/unit/test_telemetry.py:100`, `tests/unit/test_telemetry.py:101`, `tests/unit/test_telemetry.py:103`, `tests/unit/test_telemetry.py:104`, `tests/unit/test_telemetry.py:105`, `tests/unit/test_telemetry.py:106`, `tests/unit/test_telemetry.py:107`, `tests/unit/test_telemetry.py:108`, `tests/unit/test_telemetry.py:109`, `tests/unit/test_telemetry.py:110`, `tests/unit/test_telemetry.py:111`, `tests/unit/test_telemetry.py:113`, `tests/unit/test_integrated_check_expanded.py:65`, `tests/unit/test_integrated_check_expanded.py:67`, `tests/unit/test_integrated_check_expanded.py:68`, `tests/unit/test_integrated_check_expanded.py:69`, `tests/unit/test_integrated_check_expanded.py:70`.

### ticketscope--e1-s9--AC-3 (P1): Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.

- **Coverage:** UNIT-ONLY
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:98`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Formatter and in-process request logs carry trace context. No mapped test reads every actual api pod log line after a kind search.

Test identities and levels: `test_log_line_inside_a_span_carries_its_ids` (unit), `test_a_log_line_during_a_request_carries_the_request_trace` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_telemetry.py:240`, `tests/unit/test_telemetry.py:245`, `tests/unit/test_telemetry.py:246`, `tests/unit/test_telemetry.py:247`, `tests/unit/test_telemetry.py:248`, `tests/unit/test_telemetry.py:249`, `tests/unit/test_telemetry.py:250`, `tests/unit/test_telemetry.py:251`, `tests/unit/test_telemetry.py:252`, `tests/unit/test_telemetry_expanded.py:319`, `tests/unit/test_telemetry_expanded.py:323`, `tests/unit/test_telemetry_expanded.py:326`, `tests/unit/test_telemetry_expanded.py:327`, `tests/unit/test_telemetry_expanded.py:328`, `tests/unit/test_telemetry_expanded.py:329`, `tests/unit/test_telemetry_expanded.py:330`, `tests/unit/test_telemetry_expanded.py:331`, `tests/unit/test_telemetry_expanded.py:333`.

### ticketscope--e1-s9--AC-4 (P3): Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:99`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The port-forwarded Grafana datasource serves the tree. No static test drives Explore or checks the human visual tree; operator confirmation is supporting prose only.

Test identities and levels: `test_the_trace_is_served_by_grafanas_tempo_datasource` (e2e).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:711`, `tests/smoke/test_gateway.py:566`, `tests/smoke/test_gateway.py:569`, `tests/smoke/test_gateway.py:570`, `tests/smoke/test_gateway.py:571`, `tests/smoke/test_gateway.py:573`, `tests/smoke/test_gateway.py:574`, `tests/smoke/test_gateway.py:575`, `tests/smoke/test_gateway.py:576`, `tests/smoke/test_gateway.py:577`, `tests/smoke/test_gateway.py:578`, `tests/smoke/test_gateway.py:582`, `tests/smoke/test_gateway.py:590`.

### ticketscope--e1-s10--AC-1 (P2): Given the change, when `grep -rnE "SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS" src tests` runs, then it finds nothing.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:69`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The test scans source and tests for the plan’s retired-symbol pattern.

Test identities and levels: `test_no_source_or_test_names_a_retired_v1_symbol` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_refactor_sweep_expanded.py:41`, `tests/unit/test_refactor_sweep_expanded.py:51`.

### ticketscope--e1-s10--AC-2 (P1): Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:70`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Preprocessing and derivation version invariants are asserted; successful execution of every tool in the complete command chain is not a static assertion.

Test identities and levels: `test_preprocessing_version_is_unchanged_by_the_sweep` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_refactor_sweep_expanded.py:89`, `tests/unit/test_refactor_sweep_expanded.py:91`, `tests/unit/test_refactor_sweep_expanded.py:92`.

### ticketscope--e1-s10--AC-3 (P1): Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.

- **Coverage:** NONE
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:71`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

A before/after golden-response comparison was recorded in the plan, but no static test or matching live manifest records that run.

**Tests:** none accepted.

### ticketscope--e1-s10--AC-4 (P1): Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:72`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The report test handles a no-op by forcing a reload and asserts the report. It does not itself establish the first invocation of the entire suite after kind-up.sh.

Test identities and levels: `test_load_log_has_the_report` (e2e).

Evidence declarations and outcome assertions: `tests/smoke/test_gateway.py:338`, `tests/smoke/test_gateway.py:347`, `tests/smoke/test_gateway.py:349`, `tests/smoke/test_gateway.py:351`, `tests/smoke/test_gateway.py:353`, `tests/smoke/test_gateway.py:354`, `tests/smoke/test_gateway.py:355`, `tests/smoke/test_gateway.py:343`, `tests/smoke/test_gateway.py:345`.

### ticketscope--e1-s11--AC-1 (P1): Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.

- **Coverage:** FULL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:70`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Exactly five E2E checks, with golden verdict/rank output, plus static shape/report guards.

Test identities and levels: `test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2` (e2e), `test_every_loaded_issue_has_a_valid_kind_and_outcome` (e2e), `test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page` (e2e), `test_one_search_reaches_tempo_as_the_ad10_tree` (e2e), `test_an_on_demand_backup_completes_to_seaweedfs` (e2e), `test_module_has_exactly_five_checks_in_order` (unit), `test_report_appends_table_to_github_step_summary` (unit), `test_summary_table_reports_rank_or_absent` (unit).

Evidence declarations and outcome assertions: `tests/integrated/test_done_when.py:76`, `tests/integrated/test_done_when.py:103`, `tests/integrated/test_done_when.py:105`, `tests/integrated/test_done_when.py:111`, `tests/integrated/test_done_when.py:98`, `tests/integrated/test_done_when.py:119`, `tests/integrated/test_done_when.py:127`, `tests/integrated/test_done_when.py:129`, `tests/integrated/test_done_when.py:130`, `tests/integrated/test_done_when.py:146`, `tests/integrated/test_done_when.py:150`, `tests/integrated/test_done_when.py:201`, `tests/integrated/test_done_when.py:169`, `tests/integrated/test_done_when.py:171`, `tests/integrated/test_done_when.py:172`, `tests/integrated/test_done_when.py:187`, `tests/integrated/test_done_when.py:189`, `tests/smoke/test_gateway.py:566`, `tests/smoke/test_gateway.py:569`, `tests/smoke/test_gateway.py:570`, `tests/smoke/test_gateway.py:571`, `tests/smoke/test_gateway.py:590`, `tests/integrated/test_done_when.py:207`, `tests/smoke/test_gateway.py:493`, `tests/smoke/test_gateway.py:494`, `tests/smoke/test_gateway.py:498`, `tests/smoke/test_gateway.py:502`, `tests/smoke/test_gateway.py:503`, `tests/integrated/test_done_when.py:215`, `tests/unit/test_integrated_check_expanded.py:42`, `tests/unit/test_integrated_check_expanded.py:47`, `tests/unit/test_integrated_check_expanded.py:55`, `tests/unit/test_integrated_check_expanded.py:74`, `tests/unit/test_integrated_check_expanded.py:83`, `tests/unit/test_integrated_check_expanded.py:84`, `tests/unit/test_integrated_golden.py:63`, `tests/unit/test_integrated_golden.py:71`, `tests/unit/test_integrated_golden.py:72`, `tests/unit/test_integrated_golden.py:73`, `tests/unit/test_integrated_golden.py:74`, `tests/unit/test_integrated_golden.py:75`, `tests/unit/test_integrated_golden.py:76`.

### ticketscope--e1-s11--AC-2 (P2): Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:71`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

Faults in schema and golden-result/page helpers are rejected. No static test breaks and restores all five deployed checks one at a time.

Test identities and levels: `test_drift_is_detected` (unit), `test_twin_absent_on_a_gated_entry_fails` (unit), `test_twin_absent_from_an_empty_result_fails` (unit), `test_page_lacking_the_twin_has_no_rank` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_snapshot.py:64`, `tests/unit/test_snapshot.py:70`, `tests/unit/test_integrated_golden.py:20`, `tests/unit/test_integrated_golden.py:21`, `tests/unit/test_integrated_golden.py:24`, `tests/unit/test_integrated_golden.py:25`, `tests/unit/test_integrated_golden.py:58`, `tests/unit/test_integrated_golden.py:59`, `tests/unit/test_integrated_golden.py:60`.

### ticketscope--e1-s11--AC-3 (P1): Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.

- **Coverage:** PARTIAL
- **Priority basis:** inferred
- **Source:** `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:72`
- **Exception:** unlinked
- **Declared links:** none; **Invalid links:** none

The integrated module is marked kind and default pytest excludes that marker. No accepted test launches pytest without a cluster and asserts both deselection and new unit-suite success.

Test identities and levels: `test_module_is_marked_kind` (unit).

Evidence declarations and outcome assertions: `tests/unit/test_integrated_check_expanded.py:58`, `tests/unit/test_integrated_check_expanded.py:61`.

## Invalid and Unlinked Criteria

All 45 exception rows in the gate table are unlinked: each declares no R IDs and has no invalid IDs. Their individual links are listed in the details above. Ticket-level covers are preserved as context and not silently inherited by numbered or plan criteria. The remaining verify-only criterion, ticketscope--e1-s2--verify, carries R1 and is included as its contributor.

## Gaps & Recommendations

Execution: sequential; no orchestration capability helpers are bound, so the workflow’s auto-mode helper checks fall back to sequential.

| Priority | Total | FULL | Coverage |
| --- | ---: | ---: | ---: |
| P0 | 3 | 1 | 33% |
| P1 | 41 | 16 | 39% |
| P2 | 7 | 1 | 14% |
| P3 | 1 | 0 | 0% |
| Overall | 52 | 18 | 35% |

FULL-only coverage uses all seven requirement rows and 45 exception rows. Criterion-only evidence: 18/46 FULL. Mapped inventory: 87 unique test declarations in 20 files; 510 declarations were discovered in all 37 test files. Parameter expansions are not counted as separate declarations.

Critical: `ticketscope--e1-s1--AC-1`, `ticketscope--e1-s3--AC-1`.

High: `ticketscope--e1--R2`, `ticketscope--e1--R3`, `ticketscope--e1--R4`, `ticketscope--e1--R5`, `ticketscope--e1--R6`, `ticketscope--e1--R7`, `ticketscope--e1-s1--AC-2`, `ticketscope--e1-s1--AC-4`, `ticketscope--e1-s14--AC-2`, `ticketscope--e1-s13--AC-3`, `ticketscope--e1-s5--AC-5`, `ticketscope--e1-s6--AC-3`, `ticketscope--e1-s7--AC-3`, `ticketscope--e1-s10--AC-3`.

Medium: `ticketscope--e1--R1`, `ticketscope--e1-s12--AC-1`, `ticketscope--e1-s12--AC-2`, `ticketscope--e1-s12--AC-3`, `ticketscope--e1-s12--AC-4`.

Low: none.

Partial coverage and unit-only rows are listed in the mapping and reduce FULL percentages; they are not assigned P1–P3 risk buckets. All tests in accepted mappings have active status. No live results exist.

The last three CI runs were read using `gh run list`: latest successful CI run 42385558996 targets cdffdfe175e4027a2517e8c3cf33bba95ae2a1c7, not the current 53358199a43fee326e8834d0d7c881a2a566b54a. The trace does not claim the current integrated suite passed on GitHub. Historical local results and operator confirmation are supporting evidence only without a matching live manifest.

## Test Quality and Limits

The Gateway module has 726 lines (under 1000), but its backup helper allows 600 seconds and delegates assertions into helpers. Polling sleeps are conditioned on actual state and bounded deadlines, not blind fixed delays. This conflicts with a strict 90-second per-test preference and direct-assertion preference; retain as an infrastructure warning. The trace checks code-level assertion alignment; it does not rerun the cluster, publish snapshots, alter tickets, or repair product/test code. The default suite’s previously documented strict xfail for a page 405 header is supporting test-review context; it is not mapped as accepted coverage here. No duplicated counts across criteria: shared tests are deduplicated by declaration anchor. Smoke/integrated overlap is intentional defense in depth with a runtime cost.

## Recommendations

- **URGENT** Add explicit epic requirement links to the selected numbered/plan criteria, preserving their meaning; reconcile legacy GitHub and fixture-only criteria with the approved Jira migration, then rerun trace. Do not infer these links or retire criteria inside this run.
- **HIGH** Run the current revision through PR CI, including integrated-check; record the five deployed fault-injection outcomes and manual checks with a producer outside trace in live-verification-results.json using qualified criterion IDs and the verified source SHA. Missing live results are not manufactured by trace.
- **HIGH** Add a kind check that an attempted write as ticketscope_ro is rejected; this is the NFR privilege-boundary gap.
- **LOW** Use the existing test-quality review as supporting context; repeat /bmad-tea-test-review after changes to the test suite.
- **MEDIUM** Suggested E1-TRACE-001 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues. First repair explicit criterion links; use existing tests where they already prove the behavior.
- **HIGH** Suggested E1-TRACE-002 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome. First repair explicit criterion links; use existing tests where they already prove the behavior.
- **HIGH** Suggested E1-TRACE-003 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes. First repair explicit criterion links; use existing tests where they already prove the behavior.
- **HIGH** Suggested E1-TRACE-004 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries. First repair explicit criterion links; use existing tests where they already prove the behavior.
- **HIGH** Suggested E1-TRACE-005 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes. First repair explicit criterion links; use existing tests where they already prove the behavior.
- **HIGH** Suggested E1-TRACE-006 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace. First repair explicit criterion links; use existing tests where they already prove the behavior.
- **HIGH** Suggested E1-TRACE-007 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR. First repair explicit criterion links; use existing tests where they already prove the behavior.
- **URGENT** Suggested E1-TRACE-008 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-009 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-010 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-011 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **URGENT** Suggested E1-TRACE-012 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-013 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **MEDIUM** Suggested E1-TRACE-014 (unit): Given the stated preconditions, when the required action runs, assert every stated result: The instances and leading projects are compared on the decision rule Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **MEDIUM** Suggested E1-TRACE-015 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: The recommended subset is shown to work Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **MEDIUM** Suggested E1-TRACE-016 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: The answer and its consequences are recorded where the waiting tickets read them Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **MEDIUM** Suggested E1-TRACE-017 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: The author accepts it Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-018 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-019 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-020 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-021 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-022 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-023 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged). Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-024 (api): Given the stated preconditions, when the required action runs, assert every stated result: Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-025 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-026 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7). Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-027 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-028 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **MEDIUM** Suggested E1-TRACE-029 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual). Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-030 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-031 (api): Given the stated preconditions, when the required action runs, assert every stated result: Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-032 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **MEDIUM** Suggested E1-TRACE-033 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.
- **HIGH** Suggested E1-TRACE-034 (e2e): Given the stated preconditions, when the required action runs, assert every stated result: Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass. Use /bmad-tea-automate expand for implemented behavior, or red mode if behavior is missing; obsolete behavior needs a requirements decision before new tests.


## Supporting Evidence

- NFR: `_bmad-output/test-artifacts/nfr/nfr-assessment-epic-1.md` reports CONCERNS: no write-refusal test for ticketscope_ro and no search-latency threshold (owned by epic 2). These are supporting findings, not overrides of this coverage gate.
- Test design: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md`; parts still describe retired GitHub ingest. Update them alongside criterion links.
- Latest successful [GitHub CI run](https://github.com/Dillon-Based/ticketscope/actions/runs/42385558996) targets cdffdfe175e4027a2517e8c3cf33bba95ae2a1c7; current-source PR execution is not established.
- No code coverage or burn-in report was supplied. NFR and test-review reports document earlier runs; they are not automatically treated as current live criterion coverage.
- No waiver register was found. No waiver was applied.

## Next Actions

1. Link selected criteria explicitly to epic R1–R7 and reconcile superseded GitHub acceptance text.
2. Close current CI and manual-run evidence gaps, preserving source SHA and qualified criterion identities.
3. Add the database write-denial check and the missing negative import-linter check, then rerun trace.

### Requirement Aggregation

```json
{
  "criterionMatrix": [
    {
      "id": "ticketscope--e1-s1--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s1",
      "name": "Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.",
      "text": "Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:94",
      "priority": "P0",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:169",
          "title": "test_search_serves_the_pinned_snapshot_with_outcomes",
          "file": "tests/smoke/test_gateway.py",
          "line": 169,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:382",
          "title": "test_cluster_has_two_ready_instances",
          "file": "tests/smoke/test_gateway.py",
          "line": 382,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_layer_imports.py:42",
          "title": "test_layer_imports_only_stdlib_pydantic_and_itself",
          "file": "tests/unit/test_layer_imports.py",
          "line": 42,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:169",
        "tests/smoke/test_gateway.py:171",
        "tests/smoke/test_gateway.py:172",
        "tests/smoke/test_gateway.py:173",
        "tests/smoke/test_gateway.py:174",
        "tests/smoke/test_gateway.py:175",
        "tests/smoke/test_gateway.py:177",
        "tests/smoke/test_gateway.py:178",
        "tests/smoke/test_gateway.py:179",
        "tests/smoke/test_gateway.py:382",
        "tests/smoke/test_gateway.py:385",
        "tests/unit/test_layer_imports.py:42",
        "tests/unit/test_layer_imports.py:45",
        "tests/unit/test_layer_imports.py:52"
      ],
      "justification": "The Gateway and two-instance assertions cover bring-up outcomes. Workflow wiring runs checks, but no static assertion proves all CI tools and both releases pass on a PR at this source revision.",
      "gaps": [
        "The Gateway and two-instance assertions cover bring-up outcomes. Workflow wiring runs checks, but no static assertion proves all CI tools and both releases pass on a PR at this source revision."
      ]
    },
    {
      "id": "ticketscope--e1-s1--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s1",
      "name": "Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.",
      "text": "Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:95",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The CI matrix declares both architectures; there is no accepted test or current-sha live result proving both builds on an image-changing PR.",
      "gaps": [
        "The CI matrix declares both architectures; there is no accepted test or current-sha live result proving both builds on an image-changing PR."
      ]
    },
    {
      "id": "ticketscope--e1-s1--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s1",
      "name": "Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.",
      "text": "Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_layer_imports.py:42",
          "title": "test_layer_imports_only_stdlib_pydantic_and_itself",
          "file": "tests/unit/test_layer_imports.py",
          "line": 42,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_layer_imports.py:42",
        "tests/unit/test_layer_imports.py:45",
        "tests/unit/test_layer_imports.py:52"
      ],
      "justification": "The AST allow-list checks current layer imports. It does not plant an adapter import and assert that lint-imports rejects it.",
      "gaps": [
        "The AST allow-list checks current layer imports. It does not plant an adapter import and assert that lint-imports rejects it."
      ]
    },
    {
      "id": "ticketscope--e1-s1--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s1",
      "name": "Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.",
      "text": "Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:97",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The workflow emits runner-fit metrics, but no accepted static test or matching live result checks those three values.",
      "gaps": [
        "The workflow emits runner-fit metrics, but no accepted static test or matching live result checks those three values."
      ]
    },
    {
      "id": "ticketscope--e1-s2--verify",
      "localId": "verify",
      "story": "ticketscope--e1-s2",
      "name": "The epic's Notes hold a dated Decision line that says yes, yes with named conditions, or no, and story 3's entry reflects any conditions.",
      "text": "The epic's Notes hold a dated Decision line that says yes, yes with named conditions, or no, and story 3's entry reflects any conditions.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml:27",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [
        "R1"
      ],
      "validLinks": [
        "R1"
      ],
      "invalidLinks": [],
      "exception": "none",
      "requirement": "The epic's Notes hold a dated Decision line that says yes, yes with named conditions, or no, and story 3's entry reflects any conditions.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "Dated decision exists in epic Notes, but no automated document assertion or matching live manifest establishes this research acceptance criterion.",
      "gaps": [
        "Dated decision exists in epic Notes, but no automated document assertion or matching live manifest establishes this research acceptance criterion."
      ]
    },
    {
      "id": "ticketscope--e1-s3--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s3",
      "name": "Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.",
      "text": "Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:91",
      "priority": "P0",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_jira.py:74",
          "title": "test_output_validates_against_schema_v2_and_the_model",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 74,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_jira.py:249",
          "title": "test_no_identity_appears_in_the_output",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 249,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_jira.py:74",
        "tests/unit/test_ingest_jira.py:81",
        "tests/unit/test_ingest_jira.py:85",
        "tests/unit/test_ingest_jira.py:249",
        "tests/unit/test_ingest_jira.py:270",
        "tests/unit/test_ingest_jira.py:273",
        "tests/unit/test_ingest_jira.py:256"
      ],
      "justification": "Current tests validate schema v2 and identity absence. They do not establish a GitHub-recording ingest or github.com issue URLs: the implementation was superseded by Jira.",
      "gaps": [
        "Current tests validate schema v2 and identity absence. They do not establish a GitHub-recording ingest or github.com issue URLs: the implementation was superseded by Jira."
      ]
    },
    {
      "id": "ticketscope--e1-s3--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s3",
      "name": "Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.",
      "text": "Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:92",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_jira.py:95",
          "title": "test_checksum_matches_and_load_reads_the_output",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 95,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_jira.py:111",
          "title": "test_rerun_is_byte_identical",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 111,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_jira.py:95",
        "tests/unit/test_ingest_jira.py:99",
        "tests/unit/test_ingest_jira.py:100",
        "tests/unit/test_ingest_jira.py:102",
        "tests/unit/test_ingest_jira.py:111",
        "tests/unit/test_ingest_jira.py:116",
        "tests/unit/test_ingest_jira.py:118"
      ],
      "justification": "Checksum digest and asset name are checked, load reads the output, and deterministic byte comparisons read the kinds and report output files.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s3--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s3",
      "name": "Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds \u2264 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.",
      "text": "Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds \u2264 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:93",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds \u2264 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_notes.py:31",
          "title": "test_notes_state_subset_counts_pairs_kinds_and_load_time",
          "file": "tests/unit/test_ingest_notes.py",
          "line": 31,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_notes.py:43",
          "title": "test_notes_carry_the_attribution_line",
          "file": "tests/unit/test_ingest_notes.py",
          "line": 43,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_version.py:8",
          "title": "test_version_taken_gives_the_next_n",
          "file": "tests/unit/test_ingest_version.py",
          "line": 8,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_version.py:18",
          "title": "test_n_is_numeric_and_never_reuses_a_gap",
          "file": "tests/unit/test_ingest_version.py",
          "line": 18,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:111",
          "title": "test_script_never_clobbers_or_deletes",
          "file": "tests/unit/test_publish_script.py",
          "line": 111,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_notes.py:31",
        "tests/unit/test_ingest_notes.py:33",
        "tests/unit/test_ingest_notes.py:34",
        "tests/unit/test_ingest_notes.py:35",
        "tests/unit/test_ingest_notes.py:36",
        "tests/unit/test_ingest_notes.py:37",
        "tests/unit/test_ingest_notes.py:38",
        "tests/unit/test_ingest_notes.py:39",
        "tests/unit/test_ingest_notes.py:40",
        "tests/unit/test_ingest_notes.py:43",
        "tests/unit/test_ingest_notes.py:44",
        "tests/unit/test_ingest_version.py:8",
        "tests/unit/test_ingest_version.py:10",
        "tests/unit/test_ingest_version.py:18",
        "tests/unit/test_ingest_version.py:21",
        "tests/unit/test_publish_script.py:111",
        "tests/unit/test_publish_script.py:116",
        "tests/unit/test_publish_script.py:117",
        "tests/unit/test_publish_script.py:118",
        "tests/unit/test_publish_script.py:119"
      ],
      "justification": "Notes fields, attribution, version advancement and non-clobber behavior have tests. snapshot.yml was retired; a real two-dispatch publish with unchanged earlier assets is not established.",
      "gaps": [
        "Notes fields, attribution, version advancement and non-clobber behavior have tests. snapshot.yml was retired; a real two-dispatch publish with unchanged earlier assets is not established."
      ]
    },
    {
      "id": "ticketscope--e1-s12--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s12",
      "name": "The instances and leading projects are compared on the decision rule",
      "text": "**The instances and leading projects are compared on the decision rule** Verify: a findings note beside this ticket holds a table per instance and per leading project. Each table gives the issue count, in-subset duplicate pairs by kind, the outcome shares under the proposed mapping, the issue-type mix, and the text-hygiene counts. The CSVs it was built from sit with it.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:65",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "The instances and leading projects are compared on the decision rule",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "Research CSVs and findings exist, but none of the discovered static tests verifies every comparison and hygiene count.",
      "gaps": [
        "Research CSVs and findings exist, but none of the discovered static tests verifies every comparison and hygiene count."
      ]
    },
    {
      "id": "ticketscope--e1-s12--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s12",
      "name": "The recommended subset is shown to work",
      "text": "**The recommended subset is shown to work** Verify: the findings note names the subset and its expected duplicate-pair count by kind. It shows the subset's measured load time through story 3's timed-load script within 600 s, and 20 sampled issues per leading candidate with the author's judgement of each.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:67",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "The recommended subset is shown to work",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The timed measurement and human sample judgments are historical documentation; no source-sha live record is supplied.",
      "gaps": [
        "The timed measurement and human sample judgments are historical documentation; no source-sha live record is supplied."
      ]
    },
    {
      "id": "ticketscope--e1-s12--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s12",
      "name": "The answer and its consequences are recorded where the waiting tickets read them",
      "text": "**The answer and its consequences are recorded where the waiting tickets read them** Verify: the epic's Notes holds a dated Decision line: switch, stay, or switch with named conditions. On switch, the line names:  - the subset; - the `resolution`-to-outcome mapping and the \"answered\" rule; - the kind rule extended to Jira `{code}` and `{noformat}` blocks, since a kind-rule change needs a reload and a baseline update (epic Constraints, Kind rule); - the attribution line.  It also amends the epic's Corpus scope (the 20,000 cap and the source) and Corpus terms for the new source, and says the data lane and epic-eval-gate are to be replanned.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:69",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "The answer and its consequences are recorded where the waiting tickets read them",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The epic decision and replanning prose are documents, not a test asserting all required changes.",
      "gaps": [
        "The epic decision and replanning prose are documents, not a test asserting all required changes."
      ]
    },
    {
      "id": "ticketscope--e1-s12--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s12",
      "name": "The author accepts it",
      "text": "**The author accepts it** Verify: the Decision line is attributed to the author (user) and dated.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:78",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "The author accepts it",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "Human author acceptance is recorded in prose; absent a criterion-addressed live manifest it is not counted as test coverage.",
      "gaps": [
        "Human author acceptance is recorded in prose; absent a criterion-addressed live manifest it is not counted as test coverage."
      ]
    },
    {
      "id": "ticketscope--e1-s4--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s4",
      "name": "Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.",
      "text": "Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:80",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_derive.py:56",
          "title": "test_kind_just_below_threshold_is_short",
          "file": "tests/unit/test_derive.py",
          "line": 56,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive.py:63",
          "title": "test_kind_at_threshold_is_log_heavy",
          "file": "tests/unit/test_derive.py",
          "line": 63,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_derive.py:56",
        "tests/unit/test_derive.py:58",
        "tests/unit/test_derive.py:59",
        "tests/unit/test_derive.py:63",
        "tests/unit/test_derive.py:65",
        "tests/unit/test_derive.py:66"
      ],
      "justification": "Threshold boundaries are tested. The named GitHub outcome branches and tie cases were deliberately removed in story 1.10, so the frozen criterion is only partially established.",
      "gaps": [
        "Threshold boundaries are tested. The named GitHub outcome branches and tie cases were deliberately removed in story 1.10, so the frozen criterion is only partially established."
      ]
    },
    {
      "id": "ticketscope--e1-s4--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s4",
      "name": "Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).",
      "text": "Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:81",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_snapshot.py:128",
          "title": "test_fixture_records_kinds_outside_the_schema_and_they_hold",
          "file": "tests/unit/test_snapshot.py",
          "line": 128,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_snapshot.py:128",
        "tests/unit/test_snapshot.py:131",
        "tests/unit/test_snapshot.py:132",
        "tests/unit/test_snapshot.py:133",
        "tests/unit/test_snapshot.py:134"
      ],
      "justification": "Computed kinds are checked against every expected fixture kind.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s14--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s14",
      "name": "Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.",
      "text": "Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:91",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_derive_jira.py:71",
          "title": "test_duplicate_points_at_target",
          "file": "tests/unit/test_derive_jira.py",
          "line": 71,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:78",
          "title": "test_duplicate_without_link_has_no_ref",
          "file": "tests/unit/test_derive_jira.py",
          "line": 78,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:83",
          "title": "test_fixed",
          "file": "tests/unit/test_derive_jira.py",
          "line": 83,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:88",
          "title": "test_not_planned",
          "file": "tests/unit/test_derive_jira.py",
          "line": 88,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:93",
          "title": "test_stale",
          "file": "tests/unit/test_derive_jira.py",
          "line": 93,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:98",
          "title": "test_answered_by_resolution",
          "file": "tests/unit/test_derive_jira.py",
          "line": 98,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:103",
          "title": "test_unresolved_is_unknown",
          "file": "tests/unit/test_derive_jira.py",
          "line": 103,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:107",
          "title": "test_unmapped_resolution_is_unknown",
          "file": "tests/unit/test_derive_jira.py",
          "line": 107,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:111",
          "title": "test_resolution_matched_trimmed_and_case_insensitive",
          "file": "tests/unit/test_derive_jira.py",
          "line": 111,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:120",
          "title": "test_question_answered_by_non_reporter_comment",
          "file": "tests/unit/test_derive_jira.py",
          "line": 120,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:131",
          "title": "test_question_comment_at_resolution_time_counts",
          "file": "tests/unit/test_derive_jira.py",
          "line": 131,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:140",
          "title": "test_question_only_reporter_comments_is_fixed",
          "file": "tests/unit/test_derive_jira.py",
          "line": 140,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:147",
          "title": "test_question_non_reporter_comment_after_resolution_is_fixed",
          "file": "tests/unit/test_derive_jira.py",
          "line": 147,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:154",
          "title": "test_question_unmapped_resolution_answered",
          "file": "tests/unit/test_derive_jira.py",
          "line": 154,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:163",
          "title": "test_bug_type_with_non_reporter_comment_stays_fixed",
          "file": "tests/unit/test_derive_jira.py",
          "line": 163,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:170",
          "title": "test_support_duplicate_stays_duplicate",
          "file": "tests/unit/test_derive_jira.py",
          "line": 170,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:184",
          "title": "test_support_other_classes_keep_their_class",
          "file": "tests/unit/test_derive_jira.py",
          "line": 184,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:261",
          "title": "test_kind_just_below_threshold_is_short",
          "file": "tests/unit/test_derive_jira.py",
          "line": 261,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:267",
          "title": "test_kind_at_threshold_is_log_heavy",
          "file": "tests/unit/test_derive_jira.py",
          "line": 267,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:278",
          "title": "test_parameterised_toggle_scores_like_plain",
          "file": "tests/unit/test_derive_jira.py",
          "line": 278,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_derive_jira.py:71",
        "tests/unit/test_derive_jira.py:73",
        "tests/unit/test_derive_jira.py:78",
        "tests/unit/test_derive_jira.py:80",
        "tests/unit/test_derive_jira.py:83",
        "tests/unit/test_derive_jira.py:85",
        "tests/unit/test_derive_jira.py:88",
        "tests/unit/test_derive_jira.py:90",
        "tests/unit/test_derive_jira.py:93",
        "tests/unit/test_derive_jira.py:95",
        "tests/unit/test_derive_jira.py:98",
        "tests/unit/test_derive_jira.py:100",
        "tests/unit/test_derive_jira.py:103",
        "tests/unit/test_derive_jira.py:104",
        "tests/unit/test_derive_jira.py:107",
        "tests/unit/test_derive_jira.py:108",
        "tests/unit/test_derive_jira.py:111",
        "tests/unit/test_derive_jira.py:113",
        "tests/unit/test_derive_jira.py:114",
        "tests/unit/test_derive_jira.py:120",
        "tests/unit/test_derive_jira.py:126",
        "tests/unit/test_derive_jira.py:131",
        "tests/unit/test_derive_jira.py:137",
        "tests/unit/test_derive_jira.py:140",
        "tests/unit/test_derive_jira.py:144",
        "tests/unit/test_derive_jira.py:147",
        "tests/unit/test_derive_jira.py:151",
        "tests/unit/test_derive_jira.py:154",
        "tests/unit/test_derive_jira.py:158",
        "tests/unit/test_derive_jira.py:163",
        "tests/unit/test_derive_jira.py:167",
        "tests/unit/test_derive_jira.py:170",
        "tests/unit/test_derive_jira.py:177",
        "tests/unit/test_derive_jira.py:184",
        "tests/unit/test_derive_jira.py:191",
        "tests/unit/test_derive_jira.py:192",
        "tests/unit/test_derive_jira.py:261",
        "tests/unit/test_derive_jira.py:262",
        "tests/unit/test_derive_jira.py:263",
        "tests/unit/test_derive_jira.py:264",
        "tests/unit/test_derive_jira.py:267",
        "tests/unit/test_derive_jira.py:269",
        "tests/unit/test_derive_jira.py:270",
        "tests/unit/test_derive_jira.py:278",
        "tests/unit/test_derive_jira.py:283",
        "tests/unit/test_derive_jira.py:284",
        "tests/unit/test_derive_jira.py:285"
      ],
      "justification": "Synthetic Jira cases cover resolution classes, unknown, answered/non-answered Question cases, and both sides of the block threshold.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s14--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s14",
      "name": "Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.",
      "text": "Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:92",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The GitHub rules were explicitly retired by the sweep; remaining test_derive.py cases test kinds and versions only.",
      "gaps": [
        "The GitHub rules were explicitly retired by the sweep; remaining test_derive.py cases test kinds and versions only."
      ]
    },
    {
      "id": "ticketscope--e1-s14--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s14",
      "name": "Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.",
      "text": "Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:93",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_derive_jira.py:246",
          "title": "test_derivation_version_differs_from_story_4",
          "file": "tests/unit/test_derive_jira.py",
          "line": 246,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_derive_jira.py:246",
        "tests/unit/test_derive_jira.py:247",
        "tests/unit/test_derive_jira.py:248"
      ],
      "justification": "The version equals kind2-t3.outcome3 and differs from the recorded story-4 version.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s13--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s13",
      "name": "Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.",
      "text": "Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:95",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_jira.py:74",
          "title": "test_output_validates_against_schema_v2_and_the_model",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 74,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_jira.py:95",
          "title": "test_checksum_matches_and_load_reads_the_output",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 95,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_jira.py:74",
        "tests/unit/test_ingest_jira.py:81",
        "tests/unit/test_ingest_jira.py:85",
        "tests/unit/test_ingest_jira.py:95",
        "tests/unit/test_ingest_jira.py:99",
        "tests/unit/test_ingest_jira.py:100",
        "tests/unit/test_ingest_jira.py:102"
      ],
      "justification": "The recorded slice output validates against schema v2 and the model; checksum matches the generated compressed asset.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s13--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s13",
      "name": "Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.",
      "text": "Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_snapshot.py:58",
          "title": "test_committed_schema_matches_the_model",
          "file": "tests/unit/test_snapshot.py",
          "line": 58,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_snapshot.py:64",
          "title": "test_drift_is_detected",
          "file": "tests/unit/test_snapshot.py",
          "line": 64,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_snapshot.py:58",
        "tests/unit/test_snapshot.py:61",
        "tests/unit/test_snapshot.py:64",
        "tests/unit/test_snapshot.py:70"
      ],
      "justification": "Committed schema is compared to the model-generated rendering, and deliberately drifted schema is rejected.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s13--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s13",
      "name": "Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.",
      "text": "Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:97",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "No static test executes time-load.sh against the v2 fixture; its historical manual execution has no live manifest.",
      "gaps": [
        "No static test executes time-load.sh against the v2 fixture; its historical manual execution has no live manifest."
      ]
    },
    {
      "id": "ticketscope--e1-s13--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s13",
      "name": "Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds \u2264 600 and the attribution line.",
      "text": "Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds \u2264 600 and the attribution line.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:98",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds \u2264 600 and the attribution line.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_notes.py:31",
          "title": "test_notes_state_subset_counts_pairs_kinds_and_load_time",
          "file": "tests/unit/test_ingest_notes.py",
          "line": 31,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_notes.py:43",
          "title": "test_notes_carry_the_attribution_line",
          "file": "tests/unit/test_ingest_notes.py",
          "line": 43,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:73",
          "title": "test_refuses_off_main",
          "file": "tests/unit/test_publish_script.py",
          "line": 73,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:82",
          "title": "test_refuses_a_dirty_checkout",
          "file": "tests/unit/test_publish_script.py",
          "line": 82,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:91",
          "title": "test_refuses_when_head_is_not_origin_main",
          "file": "tests/unit/test_publish_script.py",
          "line": 91,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:100",
          "title": "test_clean_main_passes_the_guards",
          "file": "tests/unit/test_publish_script.py",
          "line": 100,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:111",
          "title": "test_script_never_clobbers_or_deletes",
          "file": "tests/unit/test_publish_script.py",
          "line": 111,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_notes.py:31",
        "tests/unit/test_ingest_notes.py:33",
        "tests/unit/test_ingest_notes.py:34",
        "tests/unit/test_ingest_notes.py:35",
        "tests/unit/test_ingest_notes.py:36",
        "tests/unit/test_ingest_notes.py:37",
        "tests/unit/test_ingest_notes.py:38",
        "tests/unit/test_ingest_notes.py:39",
        "tests/unit/test_ingest_notes.py:40",
        "tests/unit/test_ingest_notes.py:43",
        "tests/unit/test_ingest_notes.py:44",
        "tests/unit/test_publish_script.py:73",
        "tests/unit/test_publish_script.py:77",
        "tests/unit/test_publish_script.py:78",
        "tests/unit/test_publish_script.py:79",
        "tests/unit/test_publish_script.py:82",
        "tests/unit/test_publish_script.py:86",
        "tests/unit/test_publish_script.py:87",
        "tests/unit/test_publish_script.py:88",
        "tests/unit/test_publish_script.py:91",
        "tests/unit/test_publish_script.py:95",
        "tests/unit/test_publish_script.py:96",
        "tests/unit/test_publish_script.py:97",
        "tests/unit/test_publish_script.py:100",
        "tests/unit/test_publish_script.py:104",
        "tests/unit/test_publish_script.py:105",
        "tests/unit/test_publish_script.py:106",
        "tests/unit/test_publish_script.py:107",
        "tests/unit/test_publish_script.py:108",
        "tests/unit/test_publish_script.py:111",
        "tests/unit/test_publish_script.py:116",
        "tests/unit/test_publish_script.py:117",
        "tests/unit/test_publish_script.py:118",
        "tests/unit/test_publish_script.py:119"
      ],
      "justification": "Release note contents and publishing guards are tested; no test completes publishing from a restored dump on clean main and validates the resulting Release.",
      "gaps": [
        "Release note contents and publishing guards are tested; no test completes publishing from a restored dump on clean main and validates the resulting Release."
      ]
    },
    {
      "id": "ticketscope--e1-s5--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s5",
      "name": "Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)\u2013(6) pass on snapshot 2026.11.1.",
      "text": "Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)\u2013(6) pass on snapshot 2026.11.1.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)\u2013(6) pass on snapshot 2026.11.1.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:169",
          "title": "test_search_serves_the_pinned_snapshot_with_outcomes",
          "file": "tests/smoke/test_gateway.py",
          "line": 169,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:324",
          "title": "test_every_issue_is_loaded_with_a_kind_and_an_outcome",
          "file": "tests/smoke/test_gateway.py",
          "line": 324,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:338",
          "title": "test_load_log_has_the_report",
          "file": "tests/smoke/test_gateway.py",
          "line": 338,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:361",
          "title": "test_upgrade_with_the_same_pin_is_a_no_op",
          "file": "tests/smoke/test_gateway.py",
          "line": 361,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:372",
          "title": "test_stale_preprocessing_version_reloads",
          "file": "tests/smoke/test_gateway.py",
          "line": 372,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:382",
          "title": "test_cluster_has_two_ready_instances",
          "file": "tests/smoke/test_gateway.py",
          "line": 382,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:169",
        "tests/smoke/test_gateway.py:171",
        "tests/smoke/test_gateway.py:172",
        "tests/smoke/test_gateway.py:173",
        "tests/smoke/test_gateway.py:174",
        "tests/smoke/test_gateway.py:175",
        "tests/smoke/test_gateway.py:177",
        "tests/smoke/test_gateway.py:178",
        "tests/smoke/test_gateway.py:179",
        "tests/smoke/test_gateway.py:324",
        "tests/smoke/test_gateway.py:325",
        "tests/smoke/test_gateway.py:330",
        "tests/smoke/test_gateway.py:331",
        "tests/smoke/test_gateway.py:332",
        "tests/smoke/test_gateway.py:338",
        "tests/smoke/test_gateway.py:347",
        "tests/smoke/test_gateway.py:349",
        "tests/smoke/test_gateway.py:351",
        "tests/smoke/test_gateway.py:353",
        "tests/smoke/test_gateway.py:354",
        "tests/smoke/test_gateway.py:355",
        "tests/smoke/test_gateway.py:343",
        "tests/smoke/test_gateway.py:345",
        "tests/smoke/test_gateway.py:361",
        "tests/smoke/test_gateway.py:364",
        "tests/smoke/test_gateway.py:365",
        "tests/smoke/test_gateway.py:366",
        "tests/smoke/test_gateway.py:372",
        "tests/smoke/test_gateway.py:374",
        "tests/smoke/test_gateway.py:375",
        "tests/smoke/test_gateway.py:376",
        "tests/smoke/test_gateway.py:382",
        "tests/smoke/test_gateway.py:385"
      ],
      "justification": "The six checks have E2E assertions over the pinned version, stored kinds/outcomes, report shares/budget, no-op, derivation reload and two ready instances. This classifies static test coverage, not fresh CI execution.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s5--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s5",
      "name": "Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).",
      "text": "Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:97",
      "priority": "P0",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_load_main.py:212",
          "title": "test_wrong_checksum_exits_1_and_keeps_the_corpus",
          "file": "tests/unit/test_load_main.py",
          "line": 212,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_load_main.py:225",
          "title": "test_wrong_checksum_on_download_exits_1_and_keeps_the_corpus",
          "file": "tests/unit/test_load_main.py",
          "line": 225,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_postgres_corpus_meta.py:148",
          "title": "test_replace_corpus_rolls_back_when_the_rows_fail_midway",
          "file": "tests/unit/test_postgres_corpus_meta.py",
          "line": 148,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_load_main.py:212",
        "tests/unit/test_load_main.py:219",
        "tests/unit/test_load_main.py:220",
        "tests/unit/test_load_main.py:221",
        "tests/unit/test_load_main.py:222",
        "tests/unit/test_load_main.py:225",
        "tests/unit/test_load_main.py:234",
        "tests/unit/test_load_main.py:235",
        "tests/unit/test_load_main.py:236",
        "tests/unit/test_load_main.py:237",
        "tests/unit/test_load_main.py:238",
        "tests/unit/test_postgres_corpus_meta.py:148",
        "tests/unit/test_postgres_corpus_meta.py:155",
        "tests/unit/test_postgres_corpus_meta.py:156"
      ],
      "justification": "Wrong local/downloaded checksums fail with rows and corpus_meta unchanged; the adapter rollback test covers transaction failure.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s5--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s5",
      "name": "Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.",
      "text": "Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:98",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_load_main.py:124",
          "title": "test_computed_fixture_kinds_equal_the_expected_kinds",
          "file": "tests/unit/test_load_main.py",
          "line": 124,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_app.py:22",
          "title": "test_best_match",
          "file": "tests/unit/test_app.py",
          "line": 22,
          "level": "api",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_modes.py:24",
          "title": "test_keyword_ranks_by_overlap_then_number",
          "file": "tests/unit/test_modes.py",
          "line": 24,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_modes.py:44",
          "title": "test_fixture_target_ranks_first",
          "file": "tests/unit/test_modes.py",
          "line": 44,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_load_main.py:124",
        "tests/unit/test_load_main.py:125",
        "tests/unit/test_load_main.py:126",
        "tests/unit/test_app.py:22",
        "tests/unit/test_app.py:26",
        "tests/unit/test_app.py:27",
        "tests/unit/test_app.py:28",
        "tests/unit/test_app.py:29",
        "tests/unit/test_app.py:30",
        "tests/unit/test_app.py:32",
        "tests/unit/test_app.py:36",
        "tests/unit/test_app.py:38",
        "tests/unit/test_app.py:39",
        "tests/unit/test_app.py:40",
        "tests/unit/test_app.py:34",
        "tests/unit/test_modes.py:24",
        "tests/unit/test_modes.py:34",
        "tests/unit/test_modes.py:35",
        "tests/unit/test_modes.py:44",
        "tests/unit/test_modes.py:46",
        "tests/unit/test_modes.py:47",
        "tests/unit/test_modes.py:48"
      ],
      "justification": "Each computed fixture kind and the fixture best-match ranking are asserted by load, API and mode tests.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s5--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s5",
      "name": "Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.",
      "text": "Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:99",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_golden_queries.py:56",
          "title": "test_file_is_pinned_to_the_chart_snapshot",
          "file": "tests/unit/test_golden_queries.py",
          "line": 56,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_golden_queries.py:76",
          "title": "test_expected_issue_differs_from_its_source",
          "file": "tests/unit/test_golden_queries.py",
          "line": 76,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_golden_queries.py:87",
          "title": "test_source_and_expected_issues_exist_in_the_pinned_asset",
          "file": "tests/unit/test_golden_queries.py",
          "line": 87,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_golden_queries.py:56",
        "tests/unit/test_golden_queries.py:58",
        "tests/unit/test_golden_queries.py:59",
        "tests/unit/test_golden_queries.py:60",
        "tests/unit/test_golden_queries.py:76",
        "tests/unit/test_golden_queries.py:79",
        "tests/unit/test_golden_queries.py:80",
        "tests/unit/test_golden_queries.py:87",
        "tests/unit/test_golden_queries.py:93"
      ],
      "justification": "Golden version matches the pin, both issue identities exist in the pinned asset, and expected issues differ from sources.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s5--AC-5",
      "localId": "AC-5",
      "story": "ticketscope--e1-s5",
      "name": "Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.",
      "text": "Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:100",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The exact time-load.sh asset-only invocation and elapsed-time budget lack a rerunnable test or live manifest.",
      "gaps": [
        "The exact time-load.sh asset-only invocation and elapsed-time budget lack a rerunnable test or live manifest."
      ]
    },
    {
      "id": "ticketscope--e1-s6--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s6",
      "name": "Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.",
      "text": "Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:191",
          "title": "test_issue_detail_matches_the_search_hit",
          "file": "tests/smoke/test_gateway.py",
          "line": 191,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:201",
          "title": "test_unknown_issue_is_a_404_problem",
          "file": "tests/smoke/test_gateway.py",
          "line": 201,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:215",
          "title": "test_invalid_search_is_a_422_problem",
          "file": "tests/smoke/test_gateway.py",
          "line": 215,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:220",
          "title": "test_operator_characters_rank",
          "file": "tests/smoke/test_gateway.py",
          "line": 220,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:225",
          "title": "test_a_pasted_stack_trace_of_4kb_ranks",
          "file": "tests/smoke/test_gateway.py",
          "line": 225,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:191",
        "tests/smoke/test_gateway.py:196",
        "tests/smoke/test_gateway.py:197",
        "tests/smoke/test_gateway.py:198",
        "tests/smoke/test_gateway.py:201",
        "tests/smoke/test_gateway.py:203",
        "tests/smoke/test_gateway.py:215",
        "tests/smoke/test_gateway.py:217",
        "tests/smoke/test_gateway.py:75",
        "tests/smoke/test_gateway.py:76",
        "tests/smoke/test_gateway.py:78",
        "tests/smoke/test_gateway.py:220",
        "tests/smoke/test_gateway.py:222",
        "tests/smoke/test_gateway.py:225",
        "tests/smoke/test_gateway.py:234",
        "tests/smoke/test_gateway.py:236"
      ],
      "justification": "Kind smoke declares successful issue detail, 404, 422 problem responses and operator/log-heavy search. Tests have not been rerun for this trace.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s6--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s6",
      "name": "Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).",
      "text": "Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:97",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_layer_imports.py:42",
          "title": "test_layer_imports_only_stdlib_pydantic_and_itself",
          "file": "tests/unit/test_layer_imports.py",
          "line": 42,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_layer_imports.py:42",
        "tests/unit/test_layer_imports.py:45",
        "tests/unit/test_layer_imports.py:52"
      ],
      "justification": "Current imports are inspected; no planted forbidden import drives lint-imports and asserts failure.",
      "gaps": [
        "Current imports are inspected; no planted forbidden import drives lint-imports and asserts failure."
      ]
    },
    {
      "id": "ticketscope--e1-s6--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s6",
      "name": "Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.",
      "text": "Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:98",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "API shape tests do not compare a saved response from before the change with the response after it.",
      "gaps": [
        "API shape tests do not compare a saved response from before the change with the response after it."
      ]
    },
    {
      "id": "ticketscope--e1-s7--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s7",
      "name": "Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.",
      "text": "Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:80",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:303",
          "title": "test_page_renders_each_golden_query",
          "file": "tests/smoke/test_gateway.py",
          "line": 303,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:303",
        "tests/smoke/test_gateway.py:305",
        "tests/smoke/test_gateway.py:306",
        "tests/smoke/test_gateway.py:308",
        "tests/smoke/test_gateway.py:309",
        "tests/smoke/test_gateway.py:310",
        "tests/smoke/test_gateway.py:311",
        "tests/smoke/test_gateway.py:312"
      ],
      "justification": "Both golden entries drive the Gateway page. Rows assert rank, title, HTTPS link, kind and outcome.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s7--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s7",
      "name": "Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).",
      "text": "Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:81",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:169",
          "title": "test_search_serves_the_pinned_snapshot_with_outcomes",
          "file": "tests/smoke/test_gateway.py",
          "line": 169,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:182",
          "title": "test_no_match_is_empty_through_the_gateway",
          "file": "tests/smoke/test_gateway.py",
          "line": 182,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:191",
          "title": "test_issue_detail_matches_the_search_hit",
          "file": "tests/smoke/test_gateway.py",
          "line": 191,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:201",
          "title": "test_unknown_issue_is_a_404_problem",
          "file": "tests/smoke/test_gateway.py",
          "line": 201,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:215",
          "title": "test_invalid_search_is_a_422_problem",
          "file": "tests/smoke/test_gateway.py",
          "line": 215,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:220",
          "title": "test_operator_characters_rank",
          "file": "tests/smoke/test_gateway.py",
          "line": 220,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:225",
          "title": "test_a_pasted_stack_trace_of_4kb_ranks",
          "file": "tests/smoke/test_gateway.py",
          "line": 225,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:291",
          "title": "test_page_serves_the_form",
          "file": "tests/smoke/test_gateway.py",
          "line": 291,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:303",
          "title": "test_page_renders_each_golden_query",
          "file": "tests/smoke/test_gateway.py",
          "line": 303,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:315",
          "title": "test_page_escapes_a_script_query",
          "file": "tests/smoke/test_gateway.py",
          "line": 315,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:324",
          "title": "test_every_issue_is_loaded_with_a_kind_and_an_outcome",
          "file": "tests/smoke/test_gateway.py",
          "line": 324,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:338",
          "title": "test_load_log_has_the_report",
          "file": "tests/smoke/test_gateway.py",
          "line": 338,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:361",
          "title": "test_upgrade_with_the_same_pin_is_a_no_op",
          "file": "tests/smoke/test_gateway.py",
          "line": 361,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:372",
          "title": "test_stale_preprocessing_version_reloads",
          "file": "tests/smoke/test_gateway.py",
          "line": 372,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:382",
          "title": "test_cluster_has_two_ready_instances",
          "file": "tests/smoke/test_gateway.py",
          "line": 382,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:169",
        "tests/smoke/test_gateway.py:171",
        "tests/smoke/test_gateway.py:172",
        "tests/smoke/test_gateway.py:173",
        "tests/smoke/test_gateway.py:174",
        "tests/smoke/test_gateway.py:175",
        "tests/smoke/test_gateway.py:177",
        "tests/smoke/test_gateway.py:178",
        "tests/smoke/test_gateway.py:179",
        "tests/smoke/test_gateway.py:182",
        "tests/smoke/test_gateway.py:184",
        "tests/smoke/test_gateway.py:185",
        "tests/smoke/test_gateway.py:191",
        "tests/smoke/test_gateway.py:196",
        "tests/smoke/test_gateway.py:197",
        "tests/smoke/test_gateway.py:198",
        "tests/smoke/test_gateway.py:201",
        "tests/smoke/test_gateway.py:203",
        "tests/smoke/test_gateway.py:215",
        "tests/smoke/test_gateway.py:217",
        "tests/smoke/test_gateway.py:75",
        "tests/smoke/test_gateway.py:76",
        "tests/smoke/test_gateway.py:78",
        "tests/smoke/test_gateway.py:220",
        "tests/smoke/test_gateway.py:222",
        "tests/smoke/test_gateway.py:225",
        "tests/smoke/test_gateway.py:234",
        "tests/smoke/test_gateway.py:236",
        "tests/smoke/test_gateway.py:291",
        "tests/smoke/test_gateway.py:295",
        "tests/smoke/test_gateway.py:298",
        "tests/smoke/test_gateway.py:299",
        "tests/smoke/test_gateway.py:303",
        "tests/smoke/test_gateway.py:305",
        "tests/smoke/test_gateway.py:306",
        "tests/smoke/test_gateway.py:308",
        "tests/smoke/test_gateway.py:309",
        "tests/smoke/test_gateway.py:310",
        "tests/smoke/test_gateway.py:311",
        "tests/smoke/test_gateway.py:312",
        "tests/smoke/test_gateway.py:315",
        "tests/smoke/test_gateway.py:317",
        "tests/smoke/test_gateway.py:318",
        "tests/smoke/test_gateway.py:324",
        "tests/smoke/test_gateway.py:325",
        "tests/smoke/test_gateway.py:330",
        "tests/smoke/test_gateway.py:331",
        "tests/smoke/test_gateway.py:332",
        "tests/smoke/test_gateway.py:338",
        "tests/smoke/test_gateway.py:347",
        "tests/smoke/test_gateway.py:349",
        "tests/smoke/test_gateway.py:351",
        "tests/smoke/test_gateway.py:353",
        "tests/smoke/test_gateway.py:354",
        "tests/smoke/test_gateway.py:355",
        "tests/smoke/test_gateway.py:343",
        "tests/smoke/test_gateway.py:345",
        "tests/smoke/test_gateway.py:361",
        "tests/smoke/test_gateway.py:364",
        "tests/smoke/test_gateway.py:365",
        "tests/smoke/test_gateway.py:366",
        "tests/smoke/test_gateway.py:372",
        "tests/smoke/test_gateway.py:374",
        "tests/smoke/test_gateway.py:375",
        "tests/smoke/test_gateway.py:376",
        "tests/smoke/test_gateway.py:382",
        "tests/smoke/test_gateway.py:385"
      ],
      "justification": "The smoke suite contains the Gateway page check alongside the other smoke behaviors. Static coverage only; no new cluster run.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s7--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s7",
      "name": "Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.",
      "text": "Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:82",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "No accepted test compares an actual before/after saved /v1 response.",
      "gaps": [
        "No accepted test compares an actual before/after saved /v1 response."
      ]
    },
    {
      "id": "ticketscope--e1-s8--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s8",
      "name": "Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).",
      "text": "Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:92",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:512",
          "title": "test_on_demand_backup_completes_to_seaweedfs",
          "file": "tests/smoke/test_gateway.py",
          "line": 512,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_check_expanded.py:65",
          "title": "test_ci_runs_integrated_then_smoke_in_one_kind_job",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 65,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:512",
        "tests/smoke/test_gateway.py:493",
        "tests/smoke/test_gateway.py:494",
        "tests/smoke/test_gateway.py:498",
        "tests/smoke/test_gateway.py:502",
        "tests/smoke/test_gateway.py:503",
        "tests/unit/test_integrated_check_expanded.py:65",
        "tests/unit/test_integrated_check_expanded.py:67",
        "tests/unit/test_integrated_check_expanded.py:68",
        "tests/unit/test_integrated_check_expanded.py:69",
        "tests/unit/test_integrated_check_expanded.py:70"
      ],
      "justification": "Backup completion has E2E checks and CI wiring is tested, but these do not prove checks/charts and all smoke checks passed on a current PR.",
      "gaps": [
        "Backup completion has E2E checks and CI wiring is tested, but these do not prove checks/charts and all smoke checks passed on a current PR."
      ]
    },
    {
      "id": "ticketscope--e1-s8--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s8",
      "name": "Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.",
      "text": "Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:93",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:512",
          "title": "test_on_demand_backup_completes_to_seaweedfs",
          "file": "tests/smoke/test_gateway.py",
          "line": 512,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:512",
        "tests/smoke/test_gateway.py:493",
        "tests/smoke/test_gateway.py:494",
        "tests/smoke/test_gateway.py:498",
        "tests/smoke/test_gateway.py:502",
        "tests/smoke/test_gateway.py:503"
      ],
      "justification": "The backup helper waits for completed and checks backup.info plus data.tar in SeaweedFS.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s8--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s8",
      "name": "Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.",
      "text": "Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:94",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:409",
          "title": "test_upgrades_keep_the_backup_tls_and_credentials",
          "file": "tests/smoke/test_gateway.py",
          "line": 409,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:409",
        "tests/smoke/test_gateway.py:411",
        "tests/smoke/test_gateway.py:430"
      ],
      "justification": "Platform and app upgrades compare TLS and credential Secret data before and after.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s9--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s9",
      "name": "Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).",
      "text": "Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:660",
          "title": "test_one_search_yields_one_trace_in_tempo",
          "file": "tests/smoke/test_gateway.py",
          "line": 660,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:711",
          "title": "test_the_trace_is_served_by_grafanas_tempo_datasource",
          "file": "tests/smoke/test_gateway.py",
          "line": 711,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:660",
        "tests/smoke/test_gateway.py:566",
        "tests/smoke/test_gateway.py:569",
        "tests/smoke/test_gateway.py:570",
        "tests/smoke/test_gateway.py:571",
        "tests/smoke/test_gateway.py:573",
        "tests/smoke/test_gateway.py:574",
        "tests/smoke/test_gateway.py:575",
        "tests/smoke/test_gateway.py:576",
        "tests/smoke/test_gateway.py:577",
        "tests/smoke/test_gateway.py:578",
        "tests/smoke/test_gateway.py:582",
        "tests/smoke/test_gateway.py:590",
        "tests/smoke/test_gateway.py:711"
      ],
      "justification": "Tempo and the Grafana datasource return the AD-10 trace tree on kind.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s9--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s9",
      "name": "Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.",
      "text": "Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:97",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_telemetry.py:86",
          "title": "test_search_is_a_server_span_over_a_retrieval_span",
          "file": "tests/unit/test_telemetry.py",
          "line": 86,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_check_expanded.py:65",
          "title": "test_ci_runs_integrated_then_smoke_in_one_kind_job",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 65,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_telemetry.py:86",
        "tests/unit/test_telemetry.py:96",
        "tests/unit/test_telemetry.py:98",
        "tests/unit/test_telemetry.py:99",
        "tests/unit/test_telemetry.py:100",
        "tests/unit/test_telemetry.py:101",
        "tests/unit/test_telemetry.py:103",
        "tests/unit/test_telemetry.py:104",
        "tests/unit/test_telemetry.py:105",
        "tests/unit/test_telemetry.py:106",
        "tests/unit/test_telemetry.py:107",
        "tests/unit/test_telemetry.py:108",
        "tests/unit/test_telemetry.py:109",
        "tests/unit/test_telemetry.py:110",
        "tests/unit/test_telemetry.py:111",
        "tests/unit/test_telemetry.py:113",
        "tests/unit/test_integrated_check_expanded.py:65",
        "tests/unit/test_integrated_check_expanded.py:67",
        "tests/unit/test_integrated_check_expanded.py:68",
        "tests/unit/test_integrated_check_expanded.py:69",
        "tests/unit/test_integrated_check_expanded.py:70"
      ],
      "justification": "Telemetry assertions establish instrumentation and CI wiring; they do not prove that the full lint/types/imports/pytest command chain passes.",
      "gaps": [
        "Telemetry assertions establish instrumentation and CI wiring; they do not prove that the full lint/types/imports/pytest command chain passes."
      ]
    },
    {
      "id": "ticketscope--e1-s9--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s9",
      "name": "Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.",
      "text": "Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:98",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.",
      "coverage": "UNIT-ONLY",
      "tests": [
        {
          "id": "tests/unit/test_telemetry.py:240",
          "title": "test_log_line_inside_a_span_carries_its_ids",
          "file": "tests/unit/test_telemetry.py",
          "line": 240,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_telemetry_expanded.py:319",
          "title": "test_a_log_line_during_a_request_carries_the_request_trace",
          "file": "tests/unit/test_telemetry_expanded.py",
          "line": 319,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_telemetry.py:240",
        "tests/unit/test_telemetry.py:245",
        "tests/unit/test_telemetry.py:246",
        "tests/unit/test_telemetry.py:247",
        "tests/unit/test_telemetry.py:248",
        "tests/unit/test_telemetry.py:249",
        "tests/unit/test_telemetry.py:250",
        "tests/unit/test_telemetry.py:251",
        "tests/unit/test_telemetry.py:252",
        "tests/unit/test_telemetry_expanded.py:319",
        "tests/unit/test_telemetry_expanded.py:323",
        "tests/unit/test_telemetry_expanded.py:326",
        "tests/unit/test_telemetry_expanded.py:327",
        "tests/unit/test_telemetry_expanded.py:328",
        "tests/unit/test_telemetry_expanded.py:329",
        "tests/unit/test_telemetry_expanded.py:330",
        "tests/unit/test_telemetry_expanded.py:331",
        "tests/unit/test_telemetry_expanded.py:333"
      ],
      "justification": "Formatter and in-process request logs carry trace context. No mapped test reads every actual api pod log line after a kind search.",
      "gaps": [
        "Formatter and in-process request logs carry trace context. No mapped test reads every actual api pod log line after a kind search."
      ]
    },
    {
      "id": "ticketscope--e1-s9--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s9",
      "name": "Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).",
      "text": "Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:99",
      "priority": "P3",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:711",
          "title": "test_the_trace_is_served_by_grafanas_tempo_datasource",
          "file": "tests/smoke/test_gateway.py",
          "line": 711,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:711",
        "tests/smoke/test_gateway.py:566",
        "tests/smoke/test_gateway.py:569",
        "tests/smoke/test_gateway.py:570",
        "tests/smoke/test_gateway.py:571",
        "tests/smoke/test_gateway.py:573",
        "tests/smoke/test_gateway.py:574",
        "tests/smoke/test_gateway.py:575",
        "tests/smoke/test_gateway.py:576",
        "tests/smoke/test_gateway.py:577",
        "tests/smoke/test_gateway.py:578",
        "tests/smoke/test_gateway.py:582",
        "tests/smoke/test_gateway.py:590"
      ],
      "justification": "The port-forwarded Grafana datasource serves the tree. No static test drives Explore or checks the human visual tree; operator confirmation is supporting prose only.",
      "gaps": [
        "The port-forwarded Grafana datasource serves the tree. No static test drives Explore or checks the human visual tree; operator confirmation is supporting prose only."
      ]
    },
    {
      "id": "ticketscope--e1-s10--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s10",
      "name": "Given the change, when `grep -rnE \"SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS\" src tests` runs, then it finds nothing.",
      "text": "Given the change, when `grep -rnE \"SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS\" src tests` runs, then it finds nothing.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:69",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the change, when `grep -rnE \"SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS\" src tests` runs, then it finds nothing.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_refactor_sweep_expanded.py:41",
          "title": "test_no_source_or_test_names_a_retired_v1_symbol",
          "file": "tests/unit/test_refactor_sweep_expanded.py",
          "line": 41,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_refactor_sweep_expanded.py:41",
        "tests/unit/test_refactor_sweep_expanded.py:51"
      ],
      "justification": "The test scans source and tests for the plan\u2019s retired-symbol pattern.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s10--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s10",
      "name": "Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.",
      "text": "Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:70",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_refactor_sweep_expanded.py:89",
          "title": "test_preprocessing_version_is_unchanged_by_the_sweep",
          "file": "tests/unit/test_refactor_sweep_expanded.py",
          "line": 89,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_refactor_sweep_expanded.py:89",
        "tests/unit/test_refactor_sweep_expanded.py:91",
        "tests/unit/test_refactor_sweep_expanded.py:92"
      ],
      "justification": "Preprocessing and derivation version invariants are asserted; successful execution of every tool in the complete command chain is not a static assertion.",
      "gaps": [
        "Preprocessing and derivation version invariants are asserted; successful execution of every tool in the complete command chain is not a static assertion."
      ]
    },
    {
      "id": "ticketscope--e1-s10--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s10",
      "name": "Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.",
      "text": "Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:71",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "A before/after golden-response comparison was recorded in the plan, but no static test or matching live manifest records that run.",
      "gaps": [
        "A before/after golden-response comparison was recorded in the plan, but no static test or matching live manifest records that run."
      ]
    },
    {
      "id": "ticketscope--e1-s10--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s10",
      "name": "Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.",
      "text": "Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:72",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:338",
          "title": "test_load_log_has_the_report",
          "file": "tests/smoke/test_gateway.py",
          "line": 338,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:338",
        "tests/smoke/test_gateway.py:347",
        "tests/smoke/test_gateway.py:349",
        "tests/smoke/test_gateway.py:351",
        "tests/smoke/test_gateway.py:353",
        "tests/smoke/test_gateway.py:354",
        "tests/smoke/test_gateway.py:355",
        "tests/smoke/test_gateway.py:343",
        "tests/smoke/test_gateway.py:345"
      ],
      "justification": "The report test handles a no-op by forcing a reload and asserts the report. It does not itself establish the first invocation of the entire suite after kind-up.sh.",
      "gaps": [
        "The report test handles a no-op by forcing a reload and asserts the report. It does not itself establish the first invocation of the entire suite after kind-up.sh."
      ]
    },
    {
      "id": "ticketscope--e1-s11--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s11",
      "name": "Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.",
      "text": "Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:70",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/integrated/test_done_when.py:76",
          "title": "test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2",
          "file": "tests/integrated/test_done_when.py",
          "line": 76,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/integrated/test_done_when.py:119",
          "title": "test_every_loaded_issue_has_a_valid_kind_and_outcome",
          "file": "tests/integrated/test_done_when.py",
          "line": 119,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/integrated/test_done_when.py:146",
          "title": "test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page",
          "file": "tests/integrated/test_done_when.py",
          "line": 146,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/integrated/test_done_when.py:207",
          "title": "test_one_search_reaches_tempo_as_the_ad10_tree",
          "file": "tests/integrated/test_done_when.py",
          "line": 207,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/integrated/test_done_when.py:215",
          "title": "test_an_on_demand_backup_completes_to_seaweedfs",
          "file": "tests/integrated/test_done_when.py",
          "line": 215,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_check_expanded.py:42",
          "title": "test_module_has_exactly_five_checks_in_order",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 42,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_check_expanded.py:74",
          "title": "test_report_appends_table_to_github_step_summary",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 74,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_golden.py:63",
          "title": "test_summary_table_reports_rank_or_absent",
          "file": "tests/unit/test_integrated_golden.py",
          "line": 63,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/integrated/test_done_when.py:76",
        "tests/integrated/test_done_when.py:103",
        "tests/integrated/test_done_when.py:105",
        "tests/integrated/test_done_when.py:111",
        "tests/integrated/test_done_when.py:98",
        "tests/integrated/test_done_when.py:119",
        "tests/integrated/test_done_when.py:127",
        "tests/integrated/test_done_when.py:129",
        "tests/integrated/test_done_when.py:130",
        "tests/integrated/test_done_when.py:146",
        "tests/integrated/test_done_when.py:150",
        "tests/integrated/test_done_when.py:201",
        "tests/integrated/test_done_when.py:169",
        "tests/integrated/test_done_when.py:171",
        "tests/integrated/test_done_when.py:172",
        "tests/integrated/test_done_when.py:187",
        "tests/integrated/test_done_when.py:189",
        "tests/smoke/test_gateway.py:566",
        "tests/smoke/test_gateway.py:569",
        "tests/smoke/test_gateway.py:570",
        "tests/smoke/test_gateway.py:571",
        "tests/smoke/test_gateway.py:590",
        "tests/integrated/test_done_when.py:207",
        "tests/smoke/test_gateway.py:493",
        "tests/smoke/test_gateway.py:494",
        "tests/smoke/test_gateway.py:498",
        "tests/smoke/test_gateway.py:502",
        "tests/smoke/test_gateway.py:503",
        "tests/integrated/test_done_when.py:215",
        "tests/unit/test_integrated_check_expanded.py:42",
        "tests/unit/test_integrated_check_expanded.py:47",
        "tests/unit/test_integrated_check_expanded.py:55",
        "tests/unit/test_integrated_check_expanded.py:74",
        "tests/unit/test_integrated_check_expanded.py:83",
        "tests/unit/test_integrated_check_expanded.py:84",
        "tests/unit/test_integrated_golden.py:63",
        "tests/unit/test_integrated_golden.py:71",
        "tests/unit/test_integrated_golden.py:72",
        "tests/unit/test_integrated_golden.py:73",
        "tests/unit/test_integrated_golden.py:74",
        "tests/unit/test_integrated_golden.py:75",
        "tests/unit/test_integrated_golden.py:76"
      ],
      "justification": "Exactly five E2E checks, with golden verdict/rank output, plus static shape/report guards.",
      "gaps": []
    },
    {
      "id": "ticketscope--e1-s11--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s11",
      "name": "Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.",
      "text": "Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:71",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_snapshot.py:64",
          "title": "test_drift_is_detected",
          "file": "tests/unit/test_snapshot.py",
          "line": 64,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_golden.py:20",
          "title": "test_twin_absent_on_a_gated_entry_fails",
          "file": "tests/unit/test_integrated_golden.py",
          "line": 20,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_golden.py:24",
          "title": "test_twin_absent_from_an_empty_result_fails",
          "file": "tests/unit/test_integrated_golden.py",
          "line": 24,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_golden.py:58",
          "title": "test_page_lacking_the_twin_has_no_rank",
          "file": "tests/unit/test_integrated_golden.py",
          "line": 58,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_snapshot.py:64",
        "tests/unit/test_snapshot.py:70",
        "tests/unit/test_integrated_golden.py:20",
        "tests/unit/test_integrated_golden.py:21",
        "tests/unit/test_integrated_golden.py:24",
        "tests/unit/test_integrated_golden.py:25",
        "tests/unit/test_integrated_golden.py:58",
        "tests/unit/test_integrated_golden.py:59",
        "tests/unit/test_integrated_golden.py:60"
      ],
      "justification": "Faults in schema and golden-result/page helpers are rejected. No static test breaks and restores all five deployed checks one at a time.",
      "gaps": [
        "Faults in schema and golden-result/page helpers are rejected. No static test breaks and restores all five deployed checks one at a time."
      ]
    },
    {
      "id": "ticketscope--e1-s11--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s11",
      "name": "Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.",
      "text": "Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:72",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_integrated_check_expanded.py:58",
          "title": "test_module_is_marked_kind",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 58,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_integrated_check_expanded.py:58",
        "tests/unit/test_integrated_check_expanded.py:61"
      ],
      "justification": "The integrated module is marked kind and default pytest excludes that marker. No accepted test launches pytest without a cluster and asserts both deselection and new unit-suite success.",
      "gaps": [
        "The integrated module is marked kind and default pytest excludes that marker. No accepted test launches pytest without a cluster and asserts both deselection and new unit-suite success."
      ]
    }
  ],
  "traceabilityMatrix": [
    {
      "id": "ticketscope--e1--R1",
      "kind": "requirement",
      "requirement": "An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues.",
      "parent": "parent R1",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:33",
      "priority": "P2",
      "priorityBasis": "contributors",
      "contributors": [
        {
          "id": "ticketscope--e1-s2--verify",
          "story": "ticketscope--e1-s2",
          "coverage": "NONE",
          "tests": []
        }
      ],
      "coverage": "NONE",
      "missingBehaviors": [
        "An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope).",
        "The snapshot carries every field the spine's snapshot contract names.",
        "a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues."
      ],
      "tests": [],
      "gaps": [
        "An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope).",
        "The snapshot carries every field the spine's snapshot contract names.",
        "a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues."
      ]
    },
    {
      "id": "ticketscope--e1--R2",
      "kind": "requirement",
      "requirement": "A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome.",
      "parent": "parent R1",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:34",
      "priority": "P1",
      "priorityBasis": "inferred",
      "contributors": [],
      "coverage": "NONE",
      "missingBehaviors": [
        "A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome."
      ],
      "tests": [],
      "gaps": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R3",
      "kind": "requirement",
      "requirement": "Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes.",
      "parent": "parent R2",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:35",
      "priority": "P1",
      "priorityBasis": "inferred",
      "contributors": [],
      "coverage": "NONE",
      "missingBehaviors": [
        "Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes."
      ],
      "tests": [],
      "gaps": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R4",
      "kind": "requirement",
      "requirement": "One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries.",
      "parent": "parent R5",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:36",
      "priority": "P1",
      "priorityBasis": "inferred",
      "contributors": [],
      "coverage": "NONE",
      "missingBehaviors": [
        "One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries."
      ],
      "tests": [],
      "gaps": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R5",
      "kind": "requirement",
      "requirement": "CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes.",
      "parent": "parent R3",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:37",
      "priority": "P1",
      "priorityBasis": "inferred",
      "contributors": [],
      "coverage": "NONE",
      "missingBehaviors": [
        "CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes."
      ],
      "tests": [],
      "gaps": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R6",
      "kind": "requirement",
      "requirement": "One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace.",
      "parent": "parent R8",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:38",
      "priority": "P1",
      "priorityBasis": "inferred",
      "contributors": [],
      "coverage": "NONE",
      "missingBehaviors": [
        "One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace."
      ],
      "tests": [],
      "gaps": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1--R7",
      "kind": "requirement",
      "requirement": "Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR.",
      "parent": "parent R11",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md:39",
      "priority": "P1",
      "priorityBasis": "inferred",
      "contributors": [],
      "coverage": "NONE",
      "missingBehaviors": [
        "Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR."
      ],
      "tests": [],
      "gaps": [
        "no story covers it"
      ]
    },
    {
      "id": "ticketscope--e1-s1--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s1",
      "name": "Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.",
      "text": "Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:94",
      "priority": "P0",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:169",
          "title": "test_search_serves_the_pinned_snapshot_with_outcomes",
          "file": "tests/smoke/test_gateway.py",
          "line": 169,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:382",
          "title": "test_cluster_has_two_ready_instances",
          "file": "tests/smoke/test_gateway.py",
          "line": 382,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_layer_imports.py:42",
          "title": "test_layer_imports_only_stdlib_pydantic_and_itself",
          "file": "tests/unit/test_layer_imports.py",
          "line": 42,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:169",
        "tests/smoke/test_gateway.py:171",
        "tests/smoke/test_gateway.py:172",
        "tests/smoke/test_gateway.py:173",
        "tests/smoke/test_gateway.py:174",
        "tests/smoke/test_gateway.py:175",
        "tests/smoke/test_gateway.py:177",
        "tests/smoke/test_gateway.py:178",
        "tests/smoke/test_gateway.py:179",
        "tests/smoke/test_gateway.py:382",
        "tests/smoke/test_gateway.py:385",
        "tests/unit/test_layer_imports.py:42",
        "tests/unit/test_layer_imports.py:45",
        "tests/unit/test_layer_imports.py:52"
      ],
      "justification": "The Gateway and two-instance assertions cover bring-up outcomes. Workflow wiring runs checks, but no static assertion proves all CI tools and both releases pass on a PR at this source revision.",
      "gaps": [
        "The Gateway and two-instance assertions cover bring-up outcomes. Workflow wiring runs checks, but no static assertion proves all CI tools and both releases pass on a PR at this source revision."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s1--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s1",
      "name": "Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.",
      "text": "Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:95",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The CI matrix declares both architectures; there is no accepted test or current-sha live result proving both builds on an image-changing PR.",
      "gaps": [
        "The CI matrix declares both architectures; there is no accepted test or current-sha live result proving both builds on an image-changing PR."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s1--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s1",
      "name": "Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.",
      "text": "Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_layer_imports.py:42",
          "title": "test_layer_imports_only_stdlib_pydantic_and_itself",
          "file": "tests/unit/test_layer_imports.py",
          "line": 42,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_layer_imports.py:42",
        "tests/unit/test_layer_imports.py:45",
        "tests/unit/test_layer_imports.py:52"
      ],
      "justification": "The AST allow-list checks current layer imports. It does not plant an adapter import and assert that lint-imports rejects it.",
      "gaps": [
        "The AST allow-list checks current layer imports. It does not plant an adapter import and assert that lint-imports rejects it."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s1--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s1",
      "name": "Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.",
      "text": "Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md:97",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The workflow emits runner-fit metrics, but no accepted static test or matching live result checks those three values.",
      "gaps": [
        "The workflow emits runner-fit metrics, but no accepted static test or matching live result checks those three values."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s3--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s3",
      "name": "Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.",
      "text": "Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:91",
      "priority": "P0",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_jira.py:74",
          "title": "test_output_validates_against_schema_v2_and_the_model",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 74,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_jira.py:249",
          "title": "test_no_identity_appears_in_the_output",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 249,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_jira.py:74",
        "tests/unit/test_ingest_jira.py:81",
        "tests/unit/test_ingest_jira.py:85",
        "tests/unit/test_ingest_jira.py:249",
        "tests/unit/test_ingest_jira.py:270",
        "tests/unit/test_ingest_jira.py:273",
        "tests/unit/test_ingest_jira.py:256"
      ],
      "justification": "Current tests validate schema v2 and identity absence. They do not establish a GitHub-recording ingest or github.com issue URLs: the implementation was superseded by Jira.",
      "gaps": [
        "Current tests validate schema v2 and identity absence. They do not establish a GitHub-recording ingest or github.com issue URLs: the implementation was superseded by Jira."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s3--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s3",
      "name": "Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.",
      "text": "Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:92",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_jira.py:95",
          "title": "test_checksum_matches_and_load_reads_the_output",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 95,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_jira.py:111",
          "title": "test_rerun_is_byte_identical",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 111,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_jira.py:95",
        "tests/unit/test_ingest_jira.py:99",
        "tests/unit/test_ingest_jira.py:100",
        "tests/unit/test_ingest_jira.py:102",
        "tests/unit/test_ingest_jira.py:111",
        "tests/unit/test_ingest_jira.py:116",
        "tests/unit/test_ingest_jira.py:118"
      ],
      "justification": "Checksum digest and asset name are checked, load reads the output, and deterministic byte comparisons read the kinds and report output files.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s3--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s3",
      "name": "Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds \u2264 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.",
      "text": "Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds \u2264 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot-plan.md:93",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds \u2264 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_notes.py:31",
          "title": "test_notes_state_subset_counts_pairs_kinds_and_load_time",
          "file": "tests/unit/test_ingest_notes.py",
          "line": 31,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_notes.py:43",
          "title": "test_notes_carry_the_attribution_line",
          "file": "tests/unit/test_ingest_notes.py",
          "line": 43,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_version.py:8",
          "title": "test_version_taken_gives_the_next_n",
          "file": "tests/unit/test_ingest_version.py",
          "line": 8,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_version.py:18",
          "title": "test_n_is_numeric_and_never_reuses_a_gap",
          "file": "tests/unit/test_ingest_version.py",
          "line": 18,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:111",
          "title": "test_script_never_clobbers_or_deletes",
          "file": "tests/unit/test_publish_script.py",
          "line": 111,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_notes.py:31",
        "tests/unit/test_ingest_notes.py:33",
        "tests/unit/test_ingest_notes.py:34",
        "tests/unit/test_ingest_notes.py:35",
        "tests/unit/test_ingest_notes.py:36",
        "tests/unit/test_ingest_notes.py:37",
        "tests/unit/test_ingest_notes.py:38",
        "tests/unit/test_ingest_notes.py:39",
        "tests/unit/test_ingest_notes.py:40",
        "tests/unit/test_ingest_notes.py:43",
        "tests/unit/test_ingest_notes.py:44",
        "tests/unit/test_ingest_version.py:8",
        "tests/unit/test_ingest_version.py:10",
        "tests/unit/test_ingest_version.py:18",
        "tests/unit/test_ingest_version.py:21",
        "tests/unit/test_publish_script.py:111",
        "tests/unit/test_publish_script.py:116",
        "tests/unit/test_publish_script.py:117",
        "tests/unit/test_publish_script.py:118",
        "tests/unit/test_publish_script.py:119"
      ],
      "justification": "Notes fields, attribution, version advancement and non-clobber behavior have tests. snapshot.yml was retired; a real two-dispatch publish with unchanged earlier assets is not established.",
      "gaps": [
        "Notes fields, attribution, version advancement and non-clobber behavior have tests. snapshot.yml was retired; a real two-dispatch publish with unchanged earlier assets is not established."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s12--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s12",
      "name": "The instances and leading projects are compared on the decision rule",
      "text": "**The instances and leading projects are compared on the decision rule** Verify: a findings note beside this ticket holds a table per instance and per leading project. Each table gives the issue count, in-subset duplicate pairs by kind, the outcome shares under the proposed mapping, the issue-type mix, and the text-hygiene counts. The CSVs it was built from sit with it.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:65",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "The instances and leading projects are compared on the decision rule",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "Research CSVs and findings exist, but none of the discovered static tests verifies every comparison and hygiene count.",
      "gaps": [
        "Research CSVs and findings exist, but none of the discovered static tests verifies every comparison and hygiene count."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s12--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s12",
      "name": "The recommended subset is shown to work",
      "text": "**The recommended subset is shown to work** Verify: the findings note names the subset and its expected duplicate-pair count by kind. It shows the subset's measured load time through story 3's timed-load script within 600 s, and 20 sampled issues per leading candidate with the author's judgement of each.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:67",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "The recommended subset is shown to work",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The timed measurement and human sample judgments are historical documentation; no source-sha live record is supplied.",
      "gaps": [
        "The timed measurement and human sample judgments are historical documentation; no source-sha live record is supplied."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s12--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s12",
      "name": "The answer and its consequences are recorded where the waiting tickets read them",
      "text": "**The answer and its consequences are recorded where the waiting tickets read them** Verify: the epic's Notes holds a dated Decision line: switch, stay, or switch with named conditions. On switch, the line names:  - the subset; - the `resolution`-to-outcome mapping and the \"answered\" rule; - the kind rule extended to Jira `{code}` and `{noformat}` blocks, since a kind-rule change needs a reload and a baseline update (epic Constraints, Kind rule); - the attribution line.  It also amends the epic's Corpus scope (the 20,000 cap and the source) and Corpus terms for the new source, and says the data lane and epic-eval-gate are to be replanned.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:69",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "The answer and its consequences are recorded where the waiting tickets read them",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The epic decision and replanning prose are documents, not a test asserting all required changes.",
      "gaps": [
        "The epic decision and replanning prose are documents, not a test asserting all required changes."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s12--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s12",
      "name": "The author accepts it",
      "text": "**The author accepts it** Verify: the Decision line is attributed to the author (user) and dated.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus.md:78",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "The author accepts it",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "Human author acceptance is recorded in prose; absent a criterion-addressed live manifest it is not counted as test coverage.",
      "gaps": [
        "Human author acceptance is recorded in prose; absent a criterion-addressed live manifest it is not counted as test coverage."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s4--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s4",
      "name": "Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.",
      "text": "Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:80",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the unit suite, when `uv run pytest tests/unit/test_derive.py -v` runs, then one named case passes for each outcome branch (duplicate, fixed, not_planned, stale, answered, unknown), the duplicate-also-fixed tie, the CONTRIBUTOR-only support issue, the unmerged cross-referenced PR, and kind cases at `threshold-1` and `threshold`.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_derive.py:56",
          "title": "test_kind_just_below_threshold_is_short",
          "file": "tests/unit/test_derive.py",
          "line": 56,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive.py:63",
          "title": "test_kind_at_threshold_is_log_heavy",
          "file": "tests/unit/test_derive.py",
          "line": 63,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_derive.py:56",
        "tests/unit/test_derive.py:58",
        "tests/unit/test_derive.py:59",
        "tests/unit/test_derive.py:63",
        "tests/unit/test_derive.py:65",
        "tests/unit/test_derive.py:66"
      ],
      "justification": "Threshold boundaries are tested. The named GitHub outcome branches and tie cases were deliberately removed in story 1.10, so the frozen criterion is only partially established.",
      "gaps": [
        "Threshold boundaries are tested. The named GitHub outcome branches and tie cases were deliberately removed in story 1.10, so the frozen criterion is only partially established."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s4--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s4",
      "name": "Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).",
      "text": "Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-kind-and-outcome-in-core-plan.md:81",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the default threshold, when `derive_kind` runs over each issue in `snapshot/fixture.jsonl`, then it returns the kind in `snapshot/fixture-kinds.json` (checked by hand in Implementation Notes; story 5 owns the committed test).",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_snapshot.py:128",
          "title": "test_fixture_records_kinds_outside_the_schema_and_they_hold",
          "file": "tests/unit/test_snapshot.py",
          "line": 128,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_snapshot.py:128",
        "tests/unit/test_snapshot.py:131",
        "tests/unit/test_snapshot.py:132",
        "tests/unit/test_snapshot.py:133",
        "tests/unit/test_snapshot.py:134"
      ],
      "justification": "Computed kinds are checked against every expected fixture kind.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s14--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s14",
      "name": "Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.",
      "text": "Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:91",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the unit suite, when `uv run pytest tests/unit/test_derive_jira.py -v` runs, then one passing case exists per outcome class from a Jira resolution, an unmapped resolution reading unknown, an answered and a not-answered Question case, and kind cases with `{code}` and `{noformat}` blocks on either side of the threshold.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_derive_jira.py:71",
          "title": "test_duplicate_points_at_target",
          "file": "tests/unit/test_derive_jira.py",
          "line": 71,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:78",
          "title": "test_duplicate_without_link_has_no_ref",
          "file": "tests/unit/test_derive_jira.py",
          "line": 78,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:83",
          "title": "test_fixed",
          "file": "tests/unit/test_derive_jira.py",
          "line": 83,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:88",
          "title": "test_not_planned",
          "file": "tests/unit/test_derive_jira.py",
          "line": 88,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:93",
          "title": "test_stale",
          "file": "tests/unit/test_derive_jira.py",
          "line": 93,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:98",
          "title": "test_answered_by_resolution",
          "file": "tests/unit/test_derive_jira.py",
          "line": 98,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:103",
          "title": "test_unresolved_is_unknown",
          "file": "tests/unit/test_derive_jira.py",
          "line": 103,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:107",
          "title": "test_unmapped_resolution_is_unknown",
          "file": "tests/unit/test_derive_jira.py",
          "line": 107,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:111",
          "title": "test_resolution_matched_trimmed_and_case_insensitive",
          "file": "tests/unit/test_derive_jira.py",
          "line": 111,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:120",
          "title": "test_question_answered_by_non_reporter_comment",
          "file": "tests/unit/test_derive_jira.py",
          "line": 120,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:131",
          "title": "test_question_comment_at_resolution_time_counts",
          "file": "tests/unit/test_derive_jira.py",
          "line": 131,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:140",
          "title": "test_question_only_reporter_comments_is_fixed",
          "file": "tests/unit/test_derive_jira.py",
          "line": 140,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:147",
          "title": "test_question_non_reporter_comment_after_resolution_is_fixed",
          "file": "tests/unit/test_derive_jira.py",
          "line": 147,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:154",
          "title": "test_question_unmapped_resolution_answered",
          "file": "tests/unit/test_derive_jira.py",
          "line": 154,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:163",
          "title": "test_bug_type_with_non_reporter_comment_stays_fixed",
          "file": "tests/unit/test_derive_jira.py",
          "line": 163,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:170",
          "title": "test_support_duplicate_stays_duplicate",
          "file": "tests/unit/test_derive_jira.py",
          "line": 170,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:184",
          "title": "test_support_other_classes_keep_their_class",
          "file": "tests/unit/test_derive_jira.py",
          "line": 184,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:261",
          "title": "test_kind_just_below_threshold_is_short",
          "file": "tests/unit/test_derive_jira.py",
          "line": 261,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:267",
          "title": "test_kind_at_threshold_is_log_heavy",
          "file": "tests/unit/test_derive_jira.py",
          "line": 267,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_derive_jira.py:278",
          "title": "test_parameterised_toggle_scores_like_plain",
          "file": "tests/unit/test_derive_jira.py",
          "line": 278,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_derive_jira.py:71",
        "tests/unit/test_derive_jira.py:73",
        "tests/unit/test_derive_jira.py:78",
        "tests/unit/test_derive_jira.py:80",
        "tests/unit/test_derive_jira.py:83",
        "tests/unit/test_derive_jira.py:85",
        "tests/unit/test_derive_jira.py:88",
        "tests/unit/test_derive_jira.py:90",
        "tests/unit/test_derive_jira.py:93",
        "tests/unit/test_derive_jira.py:95",
        "tests/unit/test_derive_jira.py:98",
        "tests/unit/test_derive_jira.py:100",
        "tests/unit/test_derive_jira.py:103",
        "tests/unit/test_derive_jira.py:104",
        "tests/unit/test_derive_jira.py:107",
        "tests/unit/test_derive_jira.py:108",
        "tests/unit/test_derive_jira.py:111",
        "tests/unit/test_derive_jira.py:113",
        "tests/unit/test_derive_jira.py:114",
        "tests/unit/test_derive_jira.py:120",
        "tests/unit/test_derive_jira.py:126",
        "tests/unit/test_derive_jira.py:131",
        "tests/unit/test_derive_jira.py:137",
        "tests/unit/test_derive_jira.py:140",
        "tests/unit/test_derive_jira.py:144",
        "tests/unit/test_derive_jira.py:147",
        "tests/unit/test_derive_jira.py:151",
        "tests/unit/test_derive_jira.py:154",
        "tests/unit/test_derive_jira.py:158",
        "tests/unit/test_derive_jira.py:163",
        "tests/unit/test_derive_jira.py:167",
        "tests/unit/test_derive_jira.py:170",
        "tests/unit/test_derive_jira.py:177",
        "tests/unit/test_derive_jira.py:184",
        "tests/unit/test_derive_jira.py:191",
        "tests/unit/test_derive_jira.py:192",
        "tests/unit/test_derive_jira.py:261",
        "tests/unit/test_derive_jira.py:262",
        "tests/unit/test_derive_jira.py:263",
        "tests/unit/test_derive_jira.py:264",
        "tests/unit/test_derive_jira.py:267",
        "tests/unit/test_derive_jira.py:269",
        "tests/unit/test_derive_jira.py:270",
        "tests/unit/test_derive_jira.py:278",
        "tests/unit/test_derive_jira.py:283",
        "tests/unit/test_derive_jira.py:284",
        "tests/unit/test_derive_jira.py:285"
      ],
      "justification": "Synthetic Jira cases cover resolution classes, unknown, answered/non-answered Question cases, and both sides of the block threshold.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s14--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s14",
      "name": "Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.",
      "text": "Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:92",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given story 4's suite, when `uv run pytest tests/unit/test_derive.py` runs, then every GitHub-rule case still passes.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The GitHub rules were explicitly retired by the sweep; remaining test_derive.py cases test kinds and versions only.",
      "gaps": [
        "The GitHub rules were explicitly retired by the sweep; remaining test_derive.py cases test kinds and versions only."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s14--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s14",
      "name": "Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.",
      "text": "Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md:93",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the defaults, when `derivation_version()` is called, then it returns `kind2-t3.outcome3`, not story 4's `kind1-t3.outcome2`.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_derive_jira.py:246",
          "title": "test_derivation_version_differs_from_story_4",
          "file": "tests/unit/test_derive_jira.py",
          "line": 246,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_derive_jira.py:246",
        "tests/unit/test_derive_jira.py:247",
        "tests/unit/test_derive_jira.py:248"
      ],
      "justification": "The version equals kind2-t3.outcome3 and differs from the recorded story-4 version.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s13--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s13",
      "name": "Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.",
      "text": "Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:95",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_jira.py:74",
          "title": "test_output_validates_against_schema_v2_and_the_model",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 74,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_jira.py:95",
          "title": "test_checksum_matches_and_load_reads_the_output",
          "file": "tests/unit/test_ingest_jira.py",
          "line": 95,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_jira.py:74",
        "tests/unit/test_ingest_jira.py:81",
        "tests/unit/test_ingest_jira.py:85",
        "tests/unit/test_ingest_jira.py:95",
        "tests/unit/test_ingest_jira.py:99",
        "tests/unit/test_ingest_jira.py:100",
        "tests/unit/test_ingest_jira.py:102"
      ],
      "justification": "The recorded slice output validates against schema v2 and the model; checksum matches the generated compressed asset.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s13--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s13",
      "name": "Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.",
      "text": "Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_snapshot.py:58",
          "title": "test_committed_schema_matches_the_model",
          "file": "tests/unit/test_snapshot.py",
          "line": 58,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_snapshot.py:64",
          "title": "test_drift_is_detected",
          "file": "tests/unit/test_snapshot.py",
          "line": 64,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_snapshot.py:58",
        "tests/unit/test_snapshot.py:61",
        "tests/unit/test_snapshot.py:64",
        "tests/unit/test_snapshot.py:70"
      ],
      "justification": "Committed schema is compared to the model-generated rendering, and deliberately drifted schema is rejected.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s13--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s13",
      "name": "Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.",
      "text": "Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:97",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "No static test executes time-load.sh against the v2 fixture; its historical manual execution has no live manifest.",
      "gaps": [
        "No static test executes time-load.sh against the v2 fixture; its historical manual execution has no live manifest."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s13--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s13",
      "name": "Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds \u2264 600 and the attribution line.",
      "text": "Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds \u2264 600 and the attribution line.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md:98",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds \u2264 600 and the attribution line.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_ingest_notes.py:31",
          "title": "test_notes_state_subset_counts_pairs_kinds_and_load_time",
          "file": "tests/unit/test_ingest_notes.py",
          "line": 31,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_ingest_notes.py:43",
          "title": "test_notes_carry_the_attribution_line",
          "file": "tests/unit/test_ingest_notes.py",
          "line": 43,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:73",
          "title": "test_refuses_off_main",
          "file": "tests/unit/test_publish_script.py",
          "line": 73,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:82",
          "title": "test_refuses_a_dirty_checkout",
          "file": "tests/unit/test_publish_script.py",
          "line": 82,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:91",
          "title": "test_refuses_when_head_is_not_origin_main",
          "file": "tests/unit/test_publish_script.py",
          "line": 91,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:100",
          "title": "test_clean_main_passes_the_guards",
          "file": "tests/unit/test_publish_script.py",
          "line": 100,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_publish_script.py:111",
          "title": "test_script_never_clobbers_or_deletes",
          "file": "tests/unit/test_publish_script.py",
          "line": 111,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_ingest_notes.py:31",
        "tests/unit/test_ingest_notes.py:33",
        "tests/unit/test_ingest_notes.py:34",
        "tests/unit/test_ingest_notes.py:35",
        "tests/unit/test_ingest_notes.py:36",
        "tests/unit/test_ingest_notes.py:37",
        "tests/unit/test_ingest_notes.py:38",
        "tests/unit/test_ingest_notes.py:39",
        "tests/unit/test_ingest_notes.py:40",
        "tests/unit/test_ingest_notes.py:43",
        "tests/unit/test_ingest_notes.py:44",
        "tests/unit/test_publish_script.py:73",
        "tests/unit/test_publish_script.py:77",
        "tests/unit/test_publish_script.py:78",
        "tests/unit/test_publish_script.py:79",
        "tests/unit/test_publish_script.py:82",
        "tests/unit/test_publish_script.py:86",
        "tests/unit/test_publish_script.py:87",
        "tests/unit/test_publish_script.py:88",
        "tests/unit/test_publish_script.py:91",
        "tests/unit/test_publish_script.py:95",
        "tests/unit/test_publish_script.py:96",
        "tests/unit/test_publish_script.py:97",
        "tests/unit/test_publish_script.py:100",
        "tests/unit/test_publish_script.py:104",
        "tests/unit/test_publish_script.py:105",
        "tests/unit/test_publish_script.py:106",
        "tests/unit/test_publish_script.py:107",
        "tests/unit/test_publish_script.py:108",
        "tests/unit/test_publish_script.py:111",
        "tests/unit/test_publish_script.py:116",
        "tests/unit/test_publish_script.py:117",
        "tests/unit/test_publish_script.py:118",
        "tests/unit/test_publish_script.py:119"
      ],
      "justification": "Release note contents and publishing guards are tested; no test completes publishing from a restored dump on clean main and validates the resulting Release.",
      "gaps": [
        "Release note contents and publishing guards are tested; no test completes publishing from a restored dump on clean main and validates the resulting Release."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s5--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s5",
      "name": "Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)\u2013(6) pass on snapshot 2026.11.1.",
      "text": "Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)\u2013(6) pass on snapshot 2026.11.1.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)\u2013(6) pass on snapshot 2026.11.1.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:169",
          "title": "test_search_serves_the_pinned_snapshot_with_outcomes",
          "file": "tests/smoke/test_gateway.py",
          "line": 169,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:324",
          "title": "test_every_issue_is_loaded_with_a_kind_and_an_outcome",
          "file": "tests/smoke/test_gateway.py",
          "line": 324,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:338",
          "title": "test_load_log_has_the_report",
          "file": "tests/smoke/test_gateway.py",
          "line": 338,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:361",
          "title": "test_upgrade_with_the_same_pin_is_a_no_op",
          "file": "tests/smoke/test_gateway.py",
          "line": 361,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:372",
          "title": "test_stale_preprocessing_version_reloads",
          "file": "tests/smoke/test_gateway.py",
          "line": 372,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:382",
          "title": "test_cluster_has_two_ready_instances",
          "file": "tests/smoke/test_gateway.py",
          "line": 382,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:169",
        "tests/smoke/test_gateway.py:171",
        "tests/smoke/test_gateway.py:172",
        "tests/smoke/test_gateway.py:173",
        "tests/smoke/test_gateway.py:174",
        "tests/smoke/test_gateway.py:175",
        "tests/smoke/test_gateway.py:177",
        "tests/smoke/test_gateway.py:178",
        "tests/smoke/test_gateway.py:179",
        "tests/smoke/test_gateway.py:324",
        "tests/smoke/test_gateway.py:325",
        "tests/smoke/test_gateway.py:330",
        "tests/smoke/test_gateway.py:331",
        "tests/smoke/test_gateway.py:332",
        "tests/smoke/test_gateway.py:338",
        "tests/smoke/test_gateway.py:347",
        "tests/smoke/test_gateway.py:349",
        "tests/smoke/test_gateway.py:351",
        "tests/smoke/test_gateway.py:353",
        "tests/smoke/test_gateway.py:354",
        "tests/smoke/test_gateway.py:355",
        "tests/smoke/test_gateway.py:343",
        "tests/smoke/test_gateway.py:345",
        "tests/smoke/test_gateway.py:361",
        "tests/smoke/test_gateway.py:364",
        "tests/smoke/test_gateway.py:365",
        "tests/smoke/test_gateway.py:366",
        "tests/smoke/test_gateway.py:372",
        "tests/smoke/test_gateway.py:374",
        "tests/smoke/test_gateway.py:375",
        "tests/smoke/test_gateway.py:376",
        "tests/smoke/test_gateway.py:382",
        "tests/smoke/test_gateway.py:385"
      ],
      "justification": "The six checks have E2E assertions over the pinned version, stored kinds/outcomes, report shares/budget, no-op, derivation reload and two ready instances. This classifies static test coverage, not fresh CI execution.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s5--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s5",
      "name": "Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).",
      "text": "Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:97",
      "priority": "P0",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_load_main.py:212",
          "title": "test_wrong_checksum_exits_1_and_keeps_the_corpus",
          "file": "tests/unit/test_load_main.py",
          "line": 212,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_load_main.py:225",
          "title": "test_wrong_checksum_on_download_exits_1_and_keeps_the_corpus",
          "file": "tests/unit/test_load_main.py",
          "line": 225,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_postgres_corpus_meta.py:148",
          "title": "test_replace_corpus_rolls_back_when_the_rows_fail_midway",
          "file": "tests/unit/test_postgres_corpus_meta.py",
          "line": 148,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_load_main.py:212",
        "tests/unit/test_load_main.py:219",
        "tests/unit/test_load_main.py:220",
        "tests/unit/test_load_main.py:221",
        "tests/unit/test_load_main.py:222",
        "tests/unit/test_load_main.py:225",
        "tests/unit/test_load_main.py:234",
        "tests/unit/test_load_main.py:235",
        "tests/unit/test_load_main.py:236",
        "tests/unit/test_load_main.py:237",
        "tests/unit/test_load_main.py:238",
        "tests/unit/test_postgres_corpus_meta.py:148",
        "tests/unit/test_postgres_corpus_meta.py:155",
        "tests/unit/test_postgres_corpus_meta.py:156"
      ],
      "justification": "Wrong local/downloaded checksums fail with rows and corpus_meta unchanged; the adapter rollback test covers transaction failure.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s5--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s5",
      "name": "Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.",
      "text": "Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:98",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_load_main.py:124",
          "title": "test_computed_fixture_kinds_equal_the_expected_kinds",
          "file": "tests/unit/test_load_main.py",
          "line": 124,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_app.py:22",
          "title": "test_best_match",
          "file": "tests/unit/test_app.py",
          "line": 22,
          "level": "api",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_modes.py:24",
          "title": "test_keyword_ranks_by_overlap_then_number",
          "file": "tests/unit/test_modes.py",
          "line": 24,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_modes.py:44",
          "title": "test_fixture_target_ranks_first",
          "file": "tests/unit/test_modes.py",
          "line": 44,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_load_main.py:124",
        "tests/unit/test_load_main.py:125",
        "tests/unit/test_load_main.py:126",
        "tests/unit/test_app.py:22",
        "tests/unit/test_app.py:26",
        "tests/unit/test_app.py:27",
        "tests/unit/test_app.py:28",
        "tests/unit/test_app.py:29",
        "tests/unit/test_app.py:30",
        "tests/unit/test_app.py:32",
        "tests/unit/test_app.py:36",
        "tests/unit/test_app.py:38",
        "tests/unit/test_app.py:39",
        "tests/unit/test_app.py:40",
        "tests/unit/test_app.py:34",
        "tests/unit/test_modes.py:24",
        "tests/unit/test_modes.py:34",
        "tests/unit/test_modes.py:35",
        "tests/unit/test_modes.py:44",
        "tests/unit/test_modes.py:46",
        "tests/unit/test_modes.py:47",
        "tests/unit/test_modes.py:48"
      ],
      "justification": "Each computed fixture kind and the fixture best-match ranking are asserted by load, API and mode tests.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s5--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s5",
      "name": "Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.",
      "text": "Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:99",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_golden_queries.py:56",
          "title": "test_file_is_pinned_to_the_chart_snapshot",
          "file": "tests/unit/test_golden_queries.py",
          "line": 56,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_golden_queries.py:76",
          "title": "test_expected_issue_differs_from_its_source",
          "file": "tests/unit/test_golden_queries.py",
          "line": 76,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_golden_queries.py:87",
          "title": "test_source_and_expected_issues_exist_in_the_pinned_asset",
          "file": "tests/unit/test_golden_queries.py",
          "line": 87,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_golden_queries.py:56",
        "tests/unit/test_golden_queries.py:58",
        "tests/unit/test_golden_queries.py:59",
        "tests/unit/test_golden_queries.py:60",
        "tests/unit/test_golden_queries.py:76",
        "tests/unit/test_golden_queries.py:79",
        "tests/unit/test_golden_queries.py:80",
        "tests/unit/test_golden_queries.py:87",
        "tests/unit/test_golden_queries.py:93"
      ],
      "justification": "Golden version matches the pin, both issue identities exist in the pinned asset, and expected issues differ from sources.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s5--AC-5",
      "localId": "AC-5",
      "story": "ticketscope--e1-s5",
      "name": "Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.",
      "text": "Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-plan.md:100",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "The exact time-load.sh asset-only invocation and elapsed-time budget lack a rerunnable test or live manifest.",
      "gaps": [
        "The exact time-load.sh asset-only invocation and elapsed-time budget lack a rerunnable test or live manifest."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s6--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s6",
      "name": "Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.",
      "text": "Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:191",
          "title": "test_issue_detail_matches_the_search_hit",
          "file": "tests/smoke/test_gateway.py",
          "line": 191,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:201",
          "title": "test_unknown_issue_is_a_404_problem",
          "file": "tests/smoke/test_gateway.py",
          "line": 201,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:215",
          "title": "test_invalid_search_is_a_422_problem",
          "file": "tests/smoke/test_gateway.py",
          "line": 215,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:220",
          "title": "test_operator_characters_rank",
          "file": "tests/smoke/test_gateway.py",
          "line": 220,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:225",
          "title": "test_a_pasted_stack_trace_of_4kb_ranks",
          "file": "tests/smoke/test_gateway.py",
          "line": 225,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:191",
        "tests/smoke/test_gateway.py:196",
        "tests/smoke/test_gateway.py:197",
        "tests/smoke/test_gateway.py:198",
        "tests/smoke/test_gateway.py:201",
        "tests/smoke/test_gateway.py:203",
        "tests/smoke/test_gateway.py:215",
        "tests/smoke/test_gateway.py:217",
        "tests/smoke/test_gateway.py:75",
        "tests/smoke/test_gateway.py:76",
        "tests/smoke/test_gateway.py:78",
        "tests/smoke/test_gateway.py:220",
        "tests/smoke/test_gateway.py:222",
        "tests/smoke/test_gateway.py:225",
        "tests/smoke/test_gateway.py:234",
        "tests/smoke/test_gateway.py:236"
      ],
      "justification": "Kind smoke declares successful issue detail, 404, 422 problem responses and operator/log-heavy search. Tests have not been rerun for this trace.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s6--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s6",
      "name": "Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).",
      "text": "Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:97",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_layer_imports.py:42",
          "title": "test_layer_imports_only_stdlib_pydantic_and_itself",
          "file": "tests/unit/test_layer_imports.py",
          "line": 42,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_layer_imports.py:42",
        "tests/unit/test_layer_imports.py:45",
        "tests/unit/test_layer_imports.py:52"
      ],
      "justification": "Current imports are inspected; no planted forbidden import drives lint-imports and asserts failure.",
      "gaps": [
        "Current imports are inspected; no planted forbidden import drives lint-imports and asserts failure."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s6--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s6",
      "name": "Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.",
      "text": "Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md:98",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "API shape tests do not compare a saved response from before the change with the response after it.",
      "gaps": [
        "API shape tests do not compare a saved response from before the change with the response after it."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s7--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s7",
      "name": "Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.",
      "text": "Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:80",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:303",
          "title": "test_page_renders_each_golden_query",
          "file": "tests/smoke/test_gateway.py",
          "line": 303,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:303",
        "tests/smoke/test_gateway.py:305",
        "tests/smoke/test_gateway.py:306",
        "tests/smoke/test_gateway.py:308",
        "tests/smoke/test_gateway.py:309",
        "tests/smoke/test_gateway.py:310",
        "tests/smoke/test_gateway.py:311",
        "tests/smoke/test_gateway.py:312"
      ],
      "justification": "Both golden entries drive the Gateway page. Rows assert rank, title, HTTPS link, kind and outcome.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s7--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s7",
      "name": "Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).",
      "text": "Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:81",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c).",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:169",
          "title": "test_search_serves_the_pinned_snapshot_with_outcomes",
          "file": "tests/smoke/test_gateway.py",
          "line": 169,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:182",
          "title": "test_no_match_is_empty_through_the_gateway",
          "file": "tests/smoke/test_gateway.py",
          "line": 182,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:191",
          "title": "test_issue_detail_matches_the_search_hit",
          "file": "tests/smoke/test_gateway.py",
          "line": 191,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:201",
          "title": "test_unknown_issue_is_a_404_problem",
          "file": "tests/smoke/test_gateway.py",
          "line": 201,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:215",
          "title": "test_invalid_search_is_a_422_problem",
          "file": "tests/smoke/test_gateway.py",
          "line": 215,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:220",
          "title": "test_operator_characters_rank",
          "file": "tests/smoke/test_gateway.py",
          "line": 220,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:225",
          "title": "test_a_pasted_stack_trace_of_4kb_ranks",
          "file": "tests/smoke/test_gateway.py",
          "line": 225,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:291",
          "title": "test_page_serves_the_form",
          "file": "tests/smoke/test_gateway.py",
          "line": 291,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:303",
          "title": "test_page_renders_each_golden_query",
          "file": "tests/smoke/test_gateway.py",
          "line": 303,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:315",
          "title": "test_page_escapes_a_script_query",
          "file": "tests/smoke/test_gateway.py",
          "line": 315,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:324",
          "title": "test_every_issue_is_loaded_with_a_kind_and_an_outcome",
          "file": "tests/smoke/test_gateway.py",
          "line": 324,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:338",
          "title": "test_load_log_has_the_report",
          "file": "tests/smoke/test_gateway.py",
          "line": 338,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:361",
          "title": "test_upgrade_with_the_same_pin_is_a_no_op",
          "file": "tests/smoke/test_gateway.py",
          "line": 361,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:372",
          "title": "test_stale_preprocessing_version_reloads",
          "file": "tests/smoke/test_gateway.py",
          "line": 372,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:382",
          "title": "test_cluster_has_two_ready_instances",
          "file": "tests/smoke/test_gateway.py",
          "line": 382,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:169",
        "tests/smoke/test_gateway.py:171",
        "tests/smoke/test_gateway.py:172",
        "tests/smoke/test_gateway.py:173",
        "tests/smoke/test_gateway.py:174",
        "tests/smoke/test_gateway.py:175",
        "tests/smoke/test_gateway.py:177",
        "tests/smoke/test_gateway.py:178",
        "tests/smoke/test_gateway.py:179",
        "tests/smoke/test_gateway.py:182",
        "tests/smoke/test_gateway.py:184",
        "tests/smoke/test_gateway.py:185",
        "tests/smoke/test_gateway.py:191",
        "tests/smoke/test_gateway.py:196",
        "tests/smoke/test_gateway.py:197",
        "tests/smoke/test_gateway.py:198",
        "tests/smoke/test_gateway.py:201",
        "tests/smoke/test_gateway.py:203",
        "tests/smoke/test_gateway.py:215",
        "tests/smoke/test_gateway.py:217",
        "tests/smoke/test_gateway.py:75",
        "tests/smoke/test_gateway.py:76",
        "tests/smoke/test_gateway.py:78",
        "tests/smoke/test_gateway.py:220",
        "tests/smoke/test_gateway.py:222",
        "tests/smoke/test_gateway.py:225",
        "tests/smoke/test_gateway.py:234",
        "tests/smoke/test_gateway.py:236",
        "tests/smoke/test_gateway.py:291",
        "tests/smoke/test_gateway.py:295",
        "tests/smoke/test_gateway.py:298",
        "tests/smoke/test_gateway.py:299",
        "tests/smoke/test_gateway.py:303",
        "tests/smoke/test_gateway.py:305",
        "tests/smoke/test_gateway.py:306",
        "tests/smoke/test_gateway.py:308",
        "tests/smoke/test_gateway.py:309",
        "tests/smoke/test_gateway.py:310",
        "tests/smoke/test_gateway.py:311",
        "tests/smoke/test_gateway.py:312",
        "tests/smoke/test_gateway.py:315",
        "tests/smoke/test_gateway.py:317",
        "tests/smoke/test_gateway.py:318",
        "tests/smoke/test_gateway.py:324",
        "tests/smoke/test_gateway.py:325",
        "tests/smoke/test_gateway.py:330",
        "tests/smoke/test_gateway.py:331",
        "tests/smoke/test_gateway.py:332",
        "tests/smoke/test_gateway.py:338",
        "tests/smoke/test_gateway.py:347",
        "tests/smoke/test_gateway.py:349",
        "tests/smoke/test_gateway.py:351",
        "tests/smoke/test_gateway.py:353",
        "tests/smoke/test_gateway.py:354",
        "tests/smoke/test_gateway.py:355",
        "tests/smoke/test_gateway.py:343",
        "tests/smoke/test_gateway.py:345",
        "tests/smoke/test_gateway.py:361",
        "tests/smoke/test_gateway.py:364",
        "tests/smoke/test_gateway.py:365",
        "tests/smoke/test_gateway.py:366",
        "tests/smoke/test_gateway.py:372",
        "tests/smoke/test_gateway.py:374",
        "tests/smoke/test_gateway.py:375",
        "tests/smoke/test_gateway.py:376",
        "tests/smoke/test_gateway.py:382",
        "tests/smoke/test_gateway.py:385"
      ],
      "justification": "The smoke suite contains the Gateway page check alongside the other smoke behaviors. Static coverage only; no new cluster run.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s7--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s7",
      "name": "Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.",
      "text": "Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-search-page-shows-ranked-issues-with-how-each-ended-plan.md:82",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "No accepted test compares an actual before/after saved /v1 response.",
      "gaps": [
        "No accepted test compares an actual before/after saved /v1 response."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s8--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s8",
      "name": "Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).",
      "text": "Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:92",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a PR, when `ci.yml` runs, then the `checks` and `charts` jobs pass, and `_kind-deploy` passes every `kind` smoke test, including test (7).",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:512",
          "title": "test_on_demand_backup_completes_to_seaweedfs",
          "file": "tests/smoke/test_gateway.py",
          "line": 512,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_check_expanded.py:65",
          "title": "test_ci_runs_integrated_then_smoke_in_one_kind_job",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 65,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:512",
        "tests/smoke/test_gateway.py:493",
        "tests/smoke/test_gateway.py:494",
        "tests/smoke/test_gateway.py:498",
        "tests/smoke/test_gateway.py:502",
        "tests/smoke/test_gateway.py:503",
        "tests/unit/test_integrated_check_expanded.py:65",
        "tests/unit/test_integrated_check_expanded.py:67",
        "tests/unit/test_integrated_check_expanded.py:68",
        "tests/unit/test_integrated_check_expanded.py:69",
        "tests/unit/test_integrated_check_expanded.py:70"
      ],
      "justification": "Backup completion has E2E checks and CI wiring is tested, but these do not prove checks/charts and all smoke checks passed on a current PR.",
      "gaps": [
        "Backup completion has E2E checks and CI wiring is tested, but these do not prove checks/charts and all smoke checks passed on a current PR."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s8--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s8",
      "name": "Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.",
      "text": "Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:93",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given `scripts/kind-up.sh` on the local kind cluster, when it finishes and test (7) runs, then the Backup reaches `completed` and its objects are listed in the `ticketscope-backups` bucket.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:512",
          "title": "test_on_demand_backup_completes_to_seaweedfs",
          "file": "tests/smoke/test_gateway.py",
          "line": 512,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:512",
        "tests/smoke/test_gateway.py:493",
        "tests/smoke/test_gateway.py:494",
        "tests/smoke/test_gateway.py:498",
        "tests/smoke/test_gateway.py:502",
        "tests/smoke/test_gateway.py:503"
      ],
      "justification": "The backup helper waits for completed and checks backup.info plus data.tar in SeaweedFS.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s8--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s8",
      "name": "Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.",
      "text": "Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md:94",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a second `scripts/kind-up.sh` run on the same cluster, when it finishes, then the plugin TLS Secrets and `ticketscope-backup-s3` carry the same data as before the run.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:409",
          "title": "test_upgrades_keep_the_backup_tls_and_credentials",
          "file": "tests/smoke/test_gateway.py",
          "line": 409,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:409",
        "tests/smoke/test_gateway.py:411",
        "tests/smoke/test_gateway.py:430"
      ],
      "justification": "Platform and app upgrades compare TLS and credential Secret data before and after.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s9--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s9",
      "name": "Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).",
      "text": "Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:96",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:660",
          "title": "test_one_search_yields_one_trace_in_tempo",
          "file": "tests/smoke/test_gateway.py",
          "line": 660,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/smoke/test_gateway.py:711",
          "title": "test_the_trace_is_served_by_grafanas_tempo_datasource",
          "file": "tests/smoke/test_gateway.py",
          "line": 711,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:660",
        "tests/smoke/test_gateway.py:566",
        "tests/smoke/test_gateway.py:569",
        "tests/smoke/test_gateway.py:570",
        "tests/smoke/test_gateway.py:571",
        "tests/smoke/test_gateway.py:573",
        "tests/smoke/test_gateway.py:574",
        "tests/smoke/test_gateway.py:575",
        "tests/smoke/test_gateway.py:576",
        "tests/smoke/test_gateway.py:577",
        "tests/smoke/test_gateway.py:578",
        "tests/smoke/test_gateway.py:582",
        "tests/smoke/test_gateway.py:590",
        "tests/smoke/test_gateway.py:711"
      ],
      "justification": "Tempo and the Grafana datasource return the AD-10 trace tree on kind.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s9--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s9",
      "name": "Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.",
      "text": "Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:97",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_telemetry.py:86",
          "title": "test_search_is_a_server_span_over_a_retrieval_span",
          "file": "tests/unit/test_telemetry.py",
          "line": 86,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_check_expanded.py:65",
          "title": "test_ci_runs_integrated_then_smoke_in_one_kind_job",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 65,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_telemetry.py:86",
        "tests/unit/test_telemetry.py:96",
        "tests/unit/test_telemetry.py:98",
        "tests/unit/test_telemetry.py:99",
        "tests/unit/test_telemetry.py:100",
        "tests/unit/test_telemetry.py:101",
        "tests/unit/test_telemetry.py:103",
        "tests/unit/test_telemetry.py:104",
        "tests/unit/test_telemetry.py:105",
        "tests/unit/test_telemetry.py:106",
        "tests/unit/test_telemetry.py:107",
        "tests/unit/test_telemetry.py:108",
        "tests/unit/test_telemetry.py:109",
        "tests/unit/test_telemetry.py:110",
        "tests/unit/test_telemetry.py:111",
        "tests/unit/test_telemetry.py:113",
        "tests/unit/test_integrated_check_expanded.py:65",
        "tests/unit/test_integrated_check_expanded.py:67",
        "tests/unit/test_integrated_check_expanded.py:68",
        "tests/unit/test_integrated_check_expanded.py:69",
        "tests/unit/test_integrated_check_expanded.py:70"
      ],
      "justification": "Telemetry assertions establish instrumentation and CI wiring; they do not prove that the full lint/types/imports/pytest command chain passes.",
      "gaps": [
        "Telemetry assertions establish instrumentation and CI wiring; they do not prove that the full lint/types/imports/pytest command chain passes."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s9--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s9",
      "name": "Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.",
      "text": "Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:98",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.",
      "coverage": "UNIT-ONLY",
      "tests": [
        {
          "id": "tests/unit/test_telemetry.py:240",
          "title": "test_log_line_inside_a_span_carries_its_ids",
          "file": "tests/unit/test_telemetry.py",
          "line": 240,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_telemetry_expanded.py:319",
          "title": "test_a_log_line_during_a_request_carries_the_request_trace",
          "file": "tests/unit/test_telemetry_expanded.py",
          "line": 319,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_telemetry.py:240",
        "tests/unit/test_telemetry.py:245",
        "tests/unit/test_telemetry.py:246",
        "tests/unit/test_telemetry.py:247",
        "tests/unit/test_telemetry.py:248",
        "tests/unit/test_telemetry.py:249",
        "tests/unit/test_telemetry.py:250",
        "tests/unit/test_telemetry.py:251",
        "tests/unit/test_telemetry.py:252",
        "tests/unit/test_telemetry_expanded.py:319",
        "tests/unit/test_telemetry_expanded.py:323",
        "tests/unit/test_telemetry_expanded.py:326",
        "tests/unit/test_telemetry_expanded.py:327",
        "tests/unit/test_telemetry_expanded.py:328",
        "tests/unit/test_telemetry_expanded.py:329",
        "tests/unit/test_telemetry_expanded.py:330",
        "tests/unit/test_telemetry_expanded.py:331",
        "tests/unit/test_telemetry_expanded.py:333"
      ],
      "justification": "Formatter and in-process request logs carry trace context. No mapped test reads every actual api pod log line after a kind search.",
      "gaps": [
        "Formatter and in-process request logs carry trace context. No mapped test reads every actual api pod log line after a kind search."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s9--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s9",
      "name": "Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).",
      "text": "Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md:99",
      "priority": "P3",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:711",
          "title": "test_the_trace_is_served_by_grafanas_tempo_datasource",
          "file": "tests/smoke/test_gateway.py",
          "line": 711,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:711",
        "tests/smoke/test_gateway.py:566",
        "tests/smoke/test_gateway.py:569",
        "tests/smoke/test_gateway.py:570",
        "tests/smoke/test_gateway.py:571",
        "tests/smoke/test_gateway.py:573",
        "tests/smoke/test_gateway.py:574",
        "tests/smoke/test_gateway.py:575",
        "tests/smoke/test_gateway.py:576",
        "tests/smoke/test_gateway.py:577",
        "tests/smoke/test_gateway.py:578",
        "tests/smoke/test_gateway.py:582",
        "tests/smoke/test_gateway.py:590"
      ],
      "justification": "The port-forwarded Grafana datasource serves the tree. No static test drives Explore or checks the human visual tree; operator confirmation is supporting prose only.",
      "gaps": [
        "The port-forwarded Grafana datasource serves the tree. No static test drives Explore or checks the human visual tree; operator confirmation is supporting prose only."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s10--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s10",
      "name": "Given the change, when `grep -rnE \"SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS\" src tests` runs, then it finds nothing.",
      "text": "Given the change, when `grep -rnE \"SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS\" src tests` runs, then it finds nothing.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:69",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the change, when `grep -rnE \"SnapshotIssue([^V]|$)|TimelineEvent|_github_outcome|MAINTAINER_ASSOCIATIONS\" src tests` runs, then it finds nothing.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/unit/test_refactor_sweep_expanded.py:41",
          "title": "test_no_source_or_test_names_a_retired_v1_symbol",
          "file": "tests/unit/test_refactor_sweep_expanded.py",
          "line": 41,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_refactor_sweep_expanded.py:41",
        "tests/unit/test_refactor_sweep_expanded.py:51"
      ],
      "justification": "The test scans source and tests for the plan\u2019s retired-symbol pattern.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s10--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s10",
      "name": "Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.",
      "text": "Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:70",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the change, when ruff, pyright, lint-imports and pytest run, then all pass, and `preprocessing_version()` still returns `pre1.kind2-t3.outcome3`.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_refactor_sweep_expanded.py:89",
          "title": "test_preprocessing_version_is_unchanged_by_the_sweep",
          "file": "tests/unit/test_refactor_sweep_expanded.py",
          "line": 89,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_refactor_sweep_expanded.py:89",
        "tests/unit/test_refactor_sweep_expanded.py:91",
        "tests/unit/test_refactor_sweep_expanded.py:92"
      ],
      "justification": "Preprocessing and derivation version invariants are asserted; successful execution of every tool in the complete command chain is not a static assertion.",
      "gaps": [
        "Preprocessing and derivation version invariants are asserted; successful execution of every tool in the complete command chain is not a static assertion."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s10--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s10",
      "name": "Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.",
      "text": "Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:71",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a kind cluster that ran the baseline and then `kind-up.sh` on the sweep commit, when the golden queries are posted before and after, then the two sets of responses are identical.",
      "coverage": "NONE",
      "tests": [],
      "evidence": [],
      "justification": "A before/after golden-response comparison was recorded in the plan, but no static test or matching live manifest records that run.",
      "gaps": [
        "A before/after golden-response comparison was recorded in the plan, but no static test or matching live manifest records that run."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s10--AC-4",
      "localId": "AC-4",
      "story": "ticketscope--e1-s10",
      "name": "Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.",
      "text": "Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-refactor-sweep-plan.md:72",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given a cluster that was just upgraded in place, when `uv run pytest -m kind tests/smoke` runs once, then (3) passes on the first run.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/smoke/test_gateway.py:338",
          "title": "test_load_log_has_the_report",
          "file": "tests/smoke/test_gateway.py",
          "line": 338,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/smoke/test_gateway.py:338",
        "tests/smoke/test_gateway.py:347",
        "tests/smoke/test_gateway.py:349",
        "tests/smoke/test_gateway.py:351",
        "tests/smoke/test_gateway.py:353",
        "tests/smoke/test_gateway.py:354",
        "tests/smoke/test_gateway.py:355",
        "tests/smoke/test_gateway.py:343",
        "tests/smoke/test_gateway.py:345"
      ],
      "justification": "The report test handles a no-op by forcing a reload and asserts the report. It does not itself establish the first invocation of the entire suite after kind-up.sh.",
      "gaps": [
        "The report test handles a no-op by forcing a reload and asserts the report. It does not itself establish the first invocation of the entire suite after kind-up.sh."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s11--AC-1",
      "localId": "AC-1",
      "story": "ticketscope--e1-s11",
      "name": "Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.",
      "text": "Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:70",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the local kind cluster on the pinned snapshot, when `uv run pytest -m kind tests/integrated -v` runs, then exactly five tests run and pass, and the output reports each golden entry's verdict and rank.",
      "coverage": "FULL",
      "tests": [
        {
          "id": "tests/integrated/test_done_when.py:76",
          "title": "test_loaded_corpus_is_the_pinned_asset_valid_against_schema_v2",
          "file": "tests/integrated/test_done_when.py",
          "line": 76,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/integrated/test_done_when.py:119",
          "title": "test_every_loaded_issue_has_a_valid_kind_and_outcome",
          "file": "tests/integrated/test_done_when.py",
          "line": 119,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/integrated/test_done_when.py:146",
          "title": "test_golden_queries_return_their_twins_with_outcomes_via_v1_and_page",
          "file": "tests/integrated/test_done_when.py",
          "line": 146,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/integrated/test_done_when.py:207",
          "title": "test_one_search_reaches_tempo_as_the_ad10_tree",
          "file": "tests/integrated/test_done_when.py",
          "line": 207,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/integrated/test_done_when.py:215",
          "title": "test_an_on_demand_backup_completes_to_seaweedfs",
          "file": "tests/integrated/test_done_when.py",
          "line": 215,
          "level": "e2e",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_check_expanded.py:42",
          "title": "test_module_has_exactly_five_checks_in_order",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 42,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_check_expanded.py:74",
          "title": "test_report_appends_table_to_github_step_summary",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 74,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_golden.py:63",
          "title": "test_summary_table_reports_rank_or_absent",
          "file": "tests/unit/test_integrated_golden.py",
          "line": 63,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/integrated/test_done_when.py:76",
        "tests/integrated/test_done_when.py:103",
        "tests/integrated/test_done_when.py:105",
        "tests/integrated/test_done_when.py:111",
        "tests/integrated/test_done_when.py:98",
        "tests/integrated/test_done_when.py:119",
        "tests/integrated/test_done_when.py:127",
        "tests/integrated/test_done_when.py:129",
        "tests/integrated/test_done_when.py:130",
        "tests/integrated/test_done_when.py:146",
        "tests/integrated/test_done_when.py:150",
        "tests/integrated/test_done_when.py:201",
        "tests/integrated/test_done_when.py:169",
        "tests/integrated/test_done_when.py:171",
        "tests/integrated/test_done_when.py:172",
        "tests/integrated/test_done_when.py:187",
        "tests/integrated/test_done_when.py:189",
        "tests/smoke/test_gateway.py:566",
        "tests/smoke/test_gateway.py:569",
        "tests/smoke/test_gateway.py:570",
        "tests/smoke/test_gateway.py:571",
        "tests/smoke/test_gateway.py:590",
        "tests/integrated/test_done_when.py:207",
        "tests/smoke/test_gateway.py:493",
        "tests/smoke/test_gateway.py:494",
        "tests/smoke/test_gateway.py:498",
        "tests/smoke/test_gateway.py:502",
        "tests/smoke/test_gateway.py:503",
        "tests/integrated/test_done_when.py:215",
        "tests/unit/test_integrated_check_expanded.py:42",
        "tests/unit/test_integrated_check_expanded.py:47",
        "tests/unit/test_integrated_check_expanded.py:55",
        "tests/unit/test_integrated_check_expanded.py:74",
        "tests/unit/test_integrated_check_expanded.py:83",
        "tests/unit/test_integrated_check_expanded.py:84",
        "tests/unit/test_integrated_golden.py:63",
        "tests/unit/test_integrated_golden.py:71",
        "tests/unit/test_integrated_golden.py:72",
        "tests/unit/test_integrated_golden.py:73",
        "tests/unit/test_integrated_golden.py:74",
        "tests/unit/test_integrated_golden.py:75",
        "tests/unit/test_integrated_golden.py:76"
      ],
      "justification": "Exactly five E2E checks, with golden verdict/rank output, plus static shape/report guards.",
      "gaps": [],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s11--AC-2",
      "localId": "AC-2",
      "story": "ticketscope--e1-s11",
      "name": "Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.",
      "text": "Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:71",
      "priority": "P2",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given each of the five checks broken on purpose by hand, one at a time (e.g. a stricter schema copy, a NULLed kind via SQL, a golden expected number swapped in a scratch copy, Tempo scaled to 0, the backup ObjectStore pointed at a missing bucket), when the suite runs, then that check fails; the break is then reverted and the suite passes again.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_snapshot.py:64",
          "title": "test_drift_is_detected",
          "file": "tests/unit/test_snapshot.py",
          "line": 64,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_golden.py:20",
          "title": "test_twin_absent_on_a_gated_entry_fails",
          "file": "tests/unit/test_integrated_golden.py",
          "line": 20,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_golden.py:24",
          "title": "test_twin_absent_from_an_empty_result_fails",
          "file": "tests/unit/test_integrated_golden.py",
          "line": 24,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        },
        {
          "id": "tests/unit/test_integrated_golden.py:58",
          "title": "test_page_lacking_the_twin_has_no_rank",
          "file": "tests/unit/test_integrated_golden.py",
          "line": 58,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_snapshot.py:64",
        "tests/unit/test_snapshot.py:70",
        "tests/unit/test_integrated_golden.py:20",
        "tests/unit/test_integrated_golden.py:21",
        "tests/unit/test_integrated_golden.py:24",
        "tests/unit/test_integrated_golden.py:25",
        "tests/unit/test_integrated_golden.py:58",
        "tests/unit/test_integrated_golden.py:59",
        "tests/unit/test_integrated_golden.py:60"
      ],
      "justification": "Faults in schema and golden-result/page helpers are rejected. No static test breaks and restores all five deployed checks one at a time.",
      "gaps": [
        "Faults in schema and golden-result/page helpers are rejected. No static test breaks and restores all five deployed checks one at a time."
      ],
      "kind": "exception"
    },
    {
      "id": "ticketscope--e1-s11--AC-3",
      "localId": "AC-3",
      "story": "ticketscope--e1-s11",
      "name": "Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.",
      "text": "Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.",
      "source": "_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-integrated-check-on-kind-plan.md:72",
      "priority": "P1",
      "priorityBasis": "inferred",
      "declaredLinks": [],
      "validLinks": [],
      "invalidLinks": [],
      "exception": "unlinked",
      "requirement": "Given the change, when `uv run pytest` runs without a cluster, then the integrated module is deselected and the new unit tests pass.",
      "coverage": "PARTIAL",
      "tests": [
        {
          "id": "tests/unit/test_integrated_check_expanded.py:58",
          "title": "test_module_is_marked_kind",
          "file": "tests/unit/test_integrated_check_expanded.py",
          "line": 58,
          "level": "unit",
          "status": "active",
          "skipped": false,
          "pending": false,
          "fixme": false,
          "priority": null
        }
      ],
      "evidence": [
        "tests/unit/test_integrated_check_expanded.py:58",
        "tests/unit/test_integrated_check_expanded.py:61"
      ],
      "justification": "The integrated module is marked kind and default pytest excludes that marker. No accepted test launches pytest without a cluster and asserts both deselection and new unit-suite success.",
      "gaps": [
        "The integrated module is marked kind and default pytest excludes that marker. No accepted test launches pytest without a cluster and asserts both deselection and new unit-suite success."
      ],
      "kind": "exception"
    }
  ]
}
```

## Gate Summary

**FAIL — release gate blocked.** P0 33%, P1 39%, overall 35%; all required thresholds are unmet. The workflow completed successfully and produced its matrix, summary and gate JSON.
