# Deferred work

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md`
  summary: Generate and commit `deploy/charts/platform/Chart.lock` with `helm dependency update deploy/charts/platform`, so kind-up.sh and CI use `helm dependency build`.
  evidence: The story 1.1 build had no helm binary. Both dependencies (gateway-helm v1.9.3, cloudnative-pg 0.29.1) are pinned exactly, so only helm's digest check is missing; ci.yml's `charts` job emits a warning until the lock exists.

### DW-1: duplicate_target does not check link_type, so a non-Duplicate link in duplicate_links could become the duplicate target and /v1 ref.
origin: spec-deferred 98c5dbcafc93
location: src/ticketscope/core/derive.py duplicate_target
source_spec: `tickets/epic-search-baseline/tickets/story-derive-jira-outcome-and-kind-in-core-plan.md`
severity: medium
reason: Unverified (maybe-false). AD-26 names "any Duplicate-mapped link"; the spike filters by jira_issue_linktype_mapping.json. Harmless if story 13's ingest writes only Duplicate-mapped links into duplicate_links; settle in story 13 by filtering at ingest or by having core check link_type. (declared severity: medium (unverified))
status: open

### DW-2: The kind smoke test (3) test_load_log_has_the_report fails when the suite runs right after an in-place kind-up.sh upgrade of an already-loaded cluster.
origin: spec-deferred 041265e3f274
location: tests/smoke/test_gateway.py (section 3); scripts/kind-up.sh
source_spec: `tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md`
severity: low
reason: The same-pin load is a no-op, so the newest Succeeded load pod logs no "load report:" line; only (5)'s forced reload restores it, so a rerun passes. Reproduced twice in this build, after each in-place upgrade. It predates this change: test (3) and the no-op load come from story 1.5. Also, kind-up.sh reuses the HEAD-SHA tag, so an in-place re-run with uncommitted code does not roll the api pod; `kubectl rollout restart` was needed.
status: open
