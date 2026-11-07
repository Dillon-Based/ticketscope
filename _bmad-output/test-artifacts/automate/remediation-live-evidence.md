# Local remediation execution evidence

Date: 2026-11-07. Uncommitted worktree; source digests are in `remediation-source-digests.json`. This is local evidence, not a verified-commit trace live-results manifest.

- `TAG=tea-remediation-20261107 scripts/kind-up.sh`: exit 0; app image id `22859ddfcb4de6284656d17a9fbafd58227b5873a0f57e7f3f91b3f4f0ab188c`; API Ready in 74 s; cluster Ready in 94 s. Both images built, platform and ticketscope upgraded.
- `POSTGRES_IMAGE=ticketscope-postgres:18-tea-remediation-20261107 scripts/time-load.sh .pytest_cache/d/ticketscope-snapshot 2026.11.1`: exit 0; verified checksum; migrate applied 0001_init; 32,153 issues loaded. Internal report `load_seconds=6.7 budget_seconds=600 within_budget=true`; shell wall duration **7.2 s**. Temporary container cleaned by script EXIT trap. This checks the pinned real snapshot; the separate v2 fixture timed-load criterion was not executed.
- Initial kind run: 12 passed, 16 failed in 93.69 s. All failures were gateway `Connection refused` after deployment's background port-forward exited. Backup, SQL integrity, API-role privilege rejection, ready-instance, trace and Grafana checks passed. Full failures preserved in `remediation-kind-initial.xml`.
- Environment correction: a persistent `kubectl -n platform port-forward service/envoy-platform-ticketscope-96135874 18080:80` was kept running through the rerun. No test assertions or timeouts changed to address these failures.

Final result files: `remediation-unit.xml` and `remediation-kind.xml`.

Final cluster rerun: **28 passed in 201.33 s**, including all five integrated checks before smoke. Golden twins passed at ranks 5 and 9. Final local suite: **725 passed, 28 deselected in 14.18 s**. Ruff, formatting, Pyright and all seven import contracts pass. These observations apply to the uncommitted worktree/digest manifest, not a published CI revision.
