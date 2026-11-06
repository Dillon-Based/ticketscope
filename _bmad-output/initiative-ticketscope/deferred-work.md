# Deferred work

- source_plan: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind-plan.md`
  summary: Generate and commit `deploy/charts/platform/Chart.lock` with `helm dependency update deploy/charts/platform`, so kind-up.sh and CI use `helm dependency build`.
  evidence: The story 1.1 build had no helm binary. Both dependencies (gateway-helm v1.9.3, cloudnative-pg 0.29.1) are pinned exactly, so only helm's digest check is missing; ci.yml's `charts` job emits a warning until the lock exists.
