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
