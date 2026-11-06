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
