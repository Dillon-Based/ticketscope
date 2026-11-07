---
runScope: 'story'
runKey: 'story-ticketscope--e1-s8'
testMode: 'expand'
testEntry: 'bmad-tea-automate'
storyId: '1.8'
storyKey: 'ticketscope--e1-s8'
ticketRef: '1.8 @ _bmad-output/initiative-ticketscope/tickets/epic-search-baseline'
storyFile: ''
workflowStatus: 'completed'
stepsCompleted: ['step-01-preflight-and-context', 'step-02-identify-targets', 'step-03-generate-tests', 'step-03c-aggregate', 'step-04-validate-and-summarize']
lastStep: 'step-04-validate-and-summarize'
lastSaved: '2026-11-07'
test_mode: 'expand'
test_operation: 'create'
auto_validate: true
auto_heal_failures: true
max_healing_iterations: 3
use_mcp_healing: true
healing_rounds_used: 1
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md (entry 8, from tickets.py find; R5)
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-postgres-backs-up-to-seaweedfs-on-kind-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
  - deploy/charts/platform/{Chart.yaml,Chart.lock,values.yaml,values-kind.yaml,templates/barman-cloud-tls.yaml}
  - deploy/charts/ticketscope/{values.yaml,values-kind.yaml,templates/backup.yaml,templates/database.yaml}
  - scripts/kind-up.sh, .github/workflows/{ci.yml,_kind-deploy.yml}
  - tests/unit/test_chart_backup.py, tests/unit/test_chart_pin.py, tests/smoke/test_gateway.py, tests/target.py
  - knowledge: test-levels-framework.md, test-priorities-matrix.md, data-factories.md, selective-testing.md, ci-burn-in.md, test-quality.md, test-healing-patterns.md, selector-resilience.md, timing-debugging.md
---

# Automation Summary: story 1.8 (Postgres backs up to SeaweedFS on kind)

## Preflight

- Mode: **expand**, set explicitly by the request. Operation: Create (autonomous). Context: BMad-Integrated.
- Stack: `backend` (Python, pytest; Helm charts rendered offline through `helm template`). No Playwright or Pact applies.
- Story: `tickets.py find 1.8` resolved it to `epic-search-baseline` entry 8 (not pulled), state `review`. **The ticket status was not changed.**
- Criteria: the ticket has only a `verify` line, so this run used the plan's acceptance criteria, its I/O matrix and its Boundaries. It also used test-design row "Backup to SeaweedFS completes (R5)", which is E2E and already covered by smoke test (7).
- Execution: sequential, with no subagents. The tools were helm 3 and openssl, both present locally, and the platform chart dependencies were built.

## Existing coverage (before this run)

- `tests/unit/test_chart_backup.py` (9 cases) covers these offline renders:
  - platform kind: SeaweedFS all-in-one, the bucket hook, nothing exposed;
  - the plugin Service annotations and that the TLS Secrets exist with no cert-manager;
  - no SeaweedFS without the kind values;
  - the ticketscope ObjectStore and the WAL archiver;
  - with backup disabled, neither renders;
  - render failures for a missing destination and for a live cluster with no platform Secret;
  - the IAM-role path.
- `tests/smoke/test_gateway.py` covers (6b), where upgrades keep the TLS and credential Secrets, and (7), where an on-demand Backup completes and is listed in the bucket. Both are `kind`-marked.

## Coverage plan (gaps targeted)

| Target | Level | Priority | Gap |
|---|---|---|---|
| Plugin mTLS certs | Unit (helm+openssl) | P1 | The cert contents were never checked: CN/SAN per role, self-signed `ca.crt == tls.crt`, a lifetime of about 10 years, the key matching the cert, server and client certs distinct |
| Plugin Deployment | Unit (helm) | P2 | It runs in `platform` and mounts the generated Secret names; disabling the plugin drops its Secrets and Service |
| Cross-chart agreement | Unit (helm) | P1 | The ticketscope kind `endpointURL` names a rendered platform Service, namespace and port; the `destinationPath` bucket is one the bucket hook creates; the `copyFrom` keys exist in `seaweedfs-s3-secret`, which carries `resource-policy: keep` |
| `backup.yaml` guards | Unit (helm) | P2 | No credential source makes the render fail with the documented message |
| Value plumbing | Unit (helm) | P2 | A custom `objectStoreName` reaches both the ObjectStore and the Cluster plugin; retention and compression overrides take effect; the namespace and labels are set |
| Boundary: Cluster unchanged | Unit (helm) | P2 | Turning on backup adds only the `plugins` block to the Cluster; no in-tree `barmanObjectStore`, no ScheduledBackup, no Backup in the chart |
| AD-25 | Unit (static) | P2 | Both `values-kind.yaml` files set only environment-fact keys; default values hold no environment backup facts; no certificate, private key or literal S3 key in charts or values |
| CI/kind wiring | Unit (static) | P2 | Every http chart repository in `Chart.yaml` is `helm repo add`ed before `dependency build` in `kind-up.sh` and `ci.yml`; `Chart.lock` pins exactly the `Chart.yaml` dependencies; Diagnostics print Backups and ObjectStores; the `charts` job runs the render tests after the dependency build |

## Generated files

- `tests/unit/test_chart_backup_expanded.py`: 23 test functions (28 cases with parameters). Platform-render tests skip without helm or built dependencies, the same gate as `test_chart_backup.py`. The cert tests also skip without openssl.

No existing test files and no production files were modified.

## Run and heal

- Command: `uv run pytest tests/unit/test_chart_backup_expanded.py -q`
- Initial run: 28 cases, 24 passed, 4 failed. All four failures were test defects:
  - Two AD-25 key-extraction regexes used `\s*\S`, which crossed newlines into the next key. Changed to `[ \t]*[^\s#]`.
  - The key-material regex had the same newline crossing, which read `name:` as a key value. Fixed the same way.
  - The Cluster-unchanged diff did not remove the comment lines above `plugins:`. The removal pattern now includes them.
- `ruff format` reflowed four lines.
- Final run: **28 passed**, stable across 3 repeated runs.
- Repo gates: `ruff check .`, `ruff format --check .`, `pyright` (0 errors) and `lint-imports` (6 kept) are clean. Full suite `uv run pytest -q`: 624 passed, 1 xfailed (the 1.7 product defect), 20 deselected (`kind`).
- The kind smoke tests were not run: they need the cluster, and this run added no smoke tests.

## Product defects

None found. The two low findings that the story review rejected still stand as known behaviour and were not re-raised:
- an empty-data source Secret gets the "not found" message;
- an empty `copyFrom.namespace` goes unchecked.

## Notes

- The `charts` CI job runs only `tests/unit/test_chart_backup.py`. The new platform-render tests in `test_chart_backup_expanded.py` therefore skip in CI, because `checks` never builds the dependencies. The static and ticketscope-render tests run in `checks`. To run the new platform tests in CI, add this file to the `charts` job's pytest command. That is a workflow change, so it was left to the orchestrator.
