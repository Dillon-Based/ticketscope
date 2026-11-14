# Deferred work

### DW-1: duplicate_target does not check link_type, so a non-Duplicate link in duplicate_links could become the duplicate target and /v1 ref.
origin: spec-deferred 98c5dbcafc93
location: src/ticketscope/core/derive.py duplicate_target
source_spec: `tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md`
severity: medium
reason: Unverified (maybe-false). AD-26 names "any Duplicate-mapped link"; the spike filters by jira_issue_linktype_mapping.json. Harmless if story 13's ingest writes only Duplicate-mapped links into duplicate_links; settle in story 13 by filtering at ingest or by having core check link_type. (declared severity: medium (unverified))
status: done 2026-11-07
resolution: settled by story 1.13 (aac2796): ingest keeps only Duplicate-mapped links (src/ticketscope/jobs/ingest/jira.py is_duplicate_linktype), so duplicate_links never holds another link type

### DW-2: The kind smoke test (3) test_load_log_has_the_report fails when the suite runs right after an in-place kind-up.sh upgrade of an already-loaded cluster.
origin: spec-deferred 041265e3f274
location: tests/smoke/test_gateway.py (section 3); scripts/kind-up.sh
source_spec: `tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md`
severity: low
reason: The same-pin load is a no-op, so the newest Succeeded load pod logs no "load report:" line; only (5)'s forced reload restores it, so a rerun passes. Reproduced twice in this build, after each in-place upgrade. It predates this change: test (3) and the no-op load come from story 1.5. Also, kind-up.sh reuses the HEAD-SHA tag, so an in-place re-run with uncommitted code does not roll the api pod; `kubectl rollout restart` was needed.
status: done 2026-11-07
resolution: resolved by story 10 (refactor sweep): smoke (3) forces a reload when the newest load was a no-op, and kind-up.sh restarts api after rebuilding the app image under an existing release

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/tickets/story-a-regressing-pr-cannot-merge-plan.md`
  summary: Eval gate diffs against the event's `pull_request.base.sha`, which can be stale on a rerun.
  evidence: If main advanced and a baseline update landed, a rerun's `git diff <base.sha> HEAD` includes it, so `baseline_changed` is true for a PR that did not touch the baseline. Diff against the merge commit's first parent instead.

### DW-3: Embedder reference vectors (test-design oracle) are not committed; they need the model run outside this code path.
origin: spec-deferred 14119ac8a05e
location: n/a
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: No red-mode session ran; the cosine fixture was committed, reference vectors were not producible in-code.
status: open
carried_to: epic-eks-environment (5), raised at its refinement together with DW-6 and the R-004 embedding parity row (retro A6); carried at epic 3's closure (user, 2026-11-11)

### DW-4: Kind run (EMBEDDINGS_COMPUTE=1 and flag-off kind-up), Tempo trace check, OOM and api memory measurement on kind were not run.
origin: spec-deferred 166db8a1336b
location: n/a
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: Verified instead with a local Docker run of migrate, load, api and a --network none embed; ci.yml and eval.yml have not run on a PR.
status: done 2026-11-11
resolution: resolved by story 3.6's measurement (deploy/charts/ticketscope/values.yaml api resources, with the measured memory, CPU and embedding time) and story 3.8's integrated check on kind (tests/integrated/test_dense_kind.py); ci run 42910706544 integrated-check / deploy success (retro A8)

### DW-5: tests/postgres (the only tests of the dense SQL, vector literal and embedding transaction) skip in CI because nothing sets TICKETSCOPE_TEST_PG_IMAGE.
origin: spec-deferred 7e859249ed86
location: tests/postgres/conftest.py
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: grep of .github, scripts and pyproject finds no setter; a regression in _DENSE_SQL would stay green.
status: done 2026-11-11
resolution: resolved by PR #55 (74c1225, retro A3): ci.yml's containers job sets TICKETSCOPE_TEST_PG_IMAGE (.github/workflows/ci.yml:145) with TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1, so a missing image fails instead of skipping; ci run 42915486385 containers success

### DW-6: Model download has no revision pin or file checksum (test-design C-7), and fastembed resolves a quantized Qdrant export.
origin: spec-deferred 016b9d8214a7
location: images/app.Dockerfile
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: images/app.Dockerfile downloads BAAI/bge-small-en-v1.5 unpinned; a changed upstream file would change retrieval under the same model_id.
status: open
carried_to: epic-eks-environment (5), the first epic to build the app image for a non-kind environment; overlaps the NFR CONCERNS on cross-machine ranking reproducibility (R-004, retro A6); carried at epic 3's closure (user, 2026-11-11)

### DW-7: Corpus identity and retrieval use separate connections, so a concurrent reload can label results with the previously read corpus version.
origin: spec-deferred a5abd69c08c2
location: src/ticketscope/http/app.py:224; src/ticketscope/adapters/postgres.py
source_spec: `tickets/epic-hybrid-retrieval/tickets/story-tracer-dense-search-answers-through-v1-on-kind-plan.md`
severity: medium
reason: The API reads corpus_version before mode availability and retrieval, each using a separate Postgres connection. Baseline keyword requests already have the same race. A concurrent old/new snapshot reload can therefore interleave with a response; request-snapshot consistency needs its own design.
status: open
carried_to: epic-eks-environment (5), where corpus reloads first run under live traffic; carried at epic 3's closure (user, 2026-11-11)

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/story-claude-desktop-answers-from-ticketscope-through-a-tunnel-plan.md`
  summary: The api HTTPRoute pins hostnames only when `hostname` is set, so with an empty `hostname` the tunnel host would also reach `/v1` and `/`.
  evidence: deploy/charts/ticketscope/templates/api.yaml:99 renders `hostnames` inside `with .Values.hostname`; kind and every real environment set it, so it needs a misconfigured release, but a chart guard (fail when mcp.tunnelHostname is set and hostname is empty) would close it.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-tracer-setup-the-aws-account-and-bootstrap-layer-exist-plan.md`
  summary: The deploy role can still attach any managed policy to the `ticketscope-env-*` roles it creates, so CI can escalate through a new role.
  evidence: infra/bootstrap/policies/deploy-permissions.json.tftpl allows iam:AttachRolePolicy and iam:PutRolePolicy on `ticketscope-env-*` with no permissions boundary or iam:PolicyARN condition; story 5.2 shows which policies env needs, then a boundary closes it.

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-tracer-setup-the-aws-account-and-bootstrap-layer-exist-plan.md`
  summary: The read-only agent role may read `bootstrap/` state objects through ReadOnlyAccess (unverified).
  evidence: Would be settled by `aws s3 cp` of the bootstrap state under the read-only profile; state holds no secrets, so a deny on `bootstrap/*` is low value.
