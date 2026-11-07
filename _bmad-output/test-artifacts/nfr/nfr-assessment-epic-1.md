---
runScope: 'epic'
runKey: 'epic-1'
workflowStatus: 'completed'
stepsCompleted: ['step-01-load-context', 'step-02-define-thresholds', 'step-03-gather-evidence', 'step-04-evaluate-and-score', 'step-04e-aggregate-nfr', 'step-05-generate-report']
lastStep: 'step-05-generate-report'
lastSaved: '2026-11-07'
workflowType: 'testarch-nfr-assess'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml
  - knowledge/adr-quality-readiness-checklist.md
  - knowledge/ci-burn-in.md
  - knowledge/test-quality.md
  - knowledge/playwright-config.md
  - knowledge/error-handling.md
  - knowledge/playwright-cli.md
---

# NFR Evidence Audit - epic-search-baseline (epic 1): Keyword search over Mojang issues, deployed on kind

**Date:** 2026-11-07
**Story:** n/a (epic scope, run key `epic-1`)
**Overall Status:** CONCERNS ⚠️

---

Note: This audit summarizes existing implementation evidence; it does not run tests or CI workflows. NFR thresholds come from the epic's test design (`test-design-epic-1.md`, section NFR Planning), the primary source per step 2. Two exceptions, both re-run locally on 2026-11-07 as a freshness check: `uv run lint-imports` (7 contracts kept, 0 broken) and `uv run pytest` (712 passed, 27 deselected kind tests, 1 xfailed).

**Execution mode:** sequential (the four domains were evaluated in this session, with no subagents).

## Executive Summary

**Assessment:** 5 PASS, 2 CONCERNS, 0 FAIL (plus 2 N/A)

**Blockers:** 0

**High Priority Issues:** 0

**Recommendation:** CONCERNS. Nothing blocks release, but two declared criteria lack evidence. The planned test that a write through `ticketscope_ro` is refused does not exist. Search latency on kind has no declared threshold (UNKNOWN by design: epic 2 reports p95 and does not gate it).

**Scope note:** the kind-side evidence below comes from CI run 42385558996 on PR #19 (stories 1.5 to 1.9), the last run of `_kind-deploy`. Stories 1.10 (refactor sweep) and 1.11 (integrated check) are local commits on `main`, three commits ahead of `origin/main`, and have not run in CI. No declared NFR criterion depends on them, so that gap sits with `trace` (R7, Done when), not here.

---

## Security Assessment

Domain status: **CONCERNS**

### Ingest reads with a read-only token stored as a repo secret

- **Status:** N/A
- **Threshold:** Ingest issues only `GET` with a read-only token held as a repo secret (story 3)
- **Threshold Source:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Actual:** No GitHub API caller remains. Since spike 12 and story 13, ingest reads a restored Public Jira Dataset dump from a local MongoDB on the person's machine. It uses no token and no CI secret, and `snapshot.yml` no longer exists.
- **Evidence:** src/ticketscope/jobs/ingest/main.py
- **Supports:** ingest reads a restored Jira dump from a local MongoDB; no GitHub API call or token remains
- **Findings:** Superseded by the epic's Decision (2026-11-06) that story 13's ingest is person-run. The test design's NFR row predates the switch and should be updated.

### api connects as ticketscope_ro

- **Status:** CONCERNS ⚠️
- **Threshold:** `api` connects as `ticketscope_ro` (AD-7); planned validation: a write through `ticketscope_ro` is refused
- **Threshold Source:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Actual:** Implemented: migration 0001 grants `ticketscope_ro` only `USAGE` and default `SELECT`; the chart creates the role; settings default the api role to it, and a unit test pins that conninfo. No test attempts a write through the role.
- **Evidence:** deploy/charts/ticketscope/templates/database.yaml
- **Supports:** the chart creates the ticketscope_ro role with a generated password kept across upgrades
- **Evidence:** migrations/0001_init.sql
- **Supports:** ticketscope_ro is granted schema USAGE and default SELECT only
- **Evidence:** tests/unit/test_settings.py
- **Supports:** the api conninfo uses user ticketscope_ro
- **Findings:** The privilege boundary is configured but never exercised. The planned check, a write through `ticketscope_ro` that must be refused, is missing from the smoke and integrated suites.
- **Recommendation:** Add a kind smoke test that runs `INSERT INTO issue ...` as `ticketscope_ro` and asserts `permission denied`.

### Query text on spans only when a value opts in

- **Status:** PASS ✅
- **Threshold:** Query text absent from spans unless a value opts in (AD-10)
- **Threshold Source:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Actual:** By default no span carries query text. Opting in records it on the API's retrieval span only, and the chart sets the opt-in on `api` alone.
- **Evidence:** tests/unit/test_chart_telemetry_expanded.py
- **Supports:** the query-text opt-in renders on the api workload only
- **Evidence:** tests/unit/test_telemetry.py
- **Supports:** no span carries query text by default, and it is recorded when opted in
- **Findings:** Met and tested at unit and chart level.

---

## Performance Assessment

Domain status: **CONCERNS**

### Snapshot load within 10 minutes

- **Status:** PASS ✅
- **Threshold:** A load of the snapshot finishes within 10 minutes (600 s) on the runner (initiative R10)
- **Threshold Source:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Actual:** 2.6 s timed load of `snapshot-2026.11.1` (32,153 issues) before publish. On kind, the load job's report carries `within_budget=true`, which the smoke suite asserts; it passed in CI run 42385558996.
- **Evidence:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-the-jira-snapshot-schema-v2-plan.md
- **Supports:** the person-run publish of snapshot-2026.11.1 recorded a 2.6 s timed load
- **Evidence:** src/ticketscope/jobs/load/main.py
- **Supports:** the load report logs load_seconds against budget_seconds=600 with within_budget
- **Evidence:** tests/smoke/test_gateway.py
- **Supports:** the kind smoke suite asserts the load report carries within_budget=true
- **Findings:** About 230 times under budget.

### Search latency on kind

- **Status:** CONCERNS ⚠️
- **Threshold:** UNKNOWN (p95 is reported, never gated, by epic 2, AD-12)
- **Threshold Source:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Actual:** Not measured in this epic.
- **Findings:** CONCERNS by the undefined-threshold rule. This is expected for this epic: epic-eval-gate owns the p95 report.

---

## Reliability Assessment

Domain status: **PASS**

### Two Postgres instances with persistent volumes and a completed backup to SeaweedFS

- **Status:** PASS ✅
- **Threshold:** CNPG runs two instances with persistent volumes, and an on-demand backup to SeaweedFS completes (R5, story 8)
- **Threshold Source:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Actual:** `database.instances: 2`. On kind (CI run 42385558996, PR #19), the smoke suite saw two ready instances and an on-demand Backup reach `completed` with objects in the bucket; all 22 smoke tests passed.
- **Evidence:** deploy/charts/ticketscope/values.yaml
- **Supports:** the Cluster is configured with two instances
- **Evidence:** tests/smoke/test_gateway.py
- **Supports:** the kind smoke suite checks two ready instances and an on-demand backup completing to SeaweedFS
- **Findings:** Met.

### Ingest resumes after a rate limit or job timeout

- **Status:** N/A
- **Threshold:** Ingest resumes after a rate limit or job timeout (story 3)
- **Threshold Source:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Actual:** No rate-limited API remains: ingest reads a local dump in one pass (story 13).
- **Evidence:** src/ticketscope/jobs/ingest/main.py
- **Supports:** ingest reads a restored Jira dump from a local MongoDB; no GitHub API call or token remains
- **Findings:** Superseded by the corpus switch, like the token criterion above.

---

## Maintainability Assessment

Domain status: **PASS**

### import-linter enforces the AD-1 layer rules

- **Status:** PASS ✅
- **Threshold:** import-linter enforces AD-1 in CI; a deliberate core-imports-adapter change fails
- **Threshold Source:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Actual:** `ci.yml` runs `uv run lint-imports` on every PR, and an AST allow-list test closes the gap for third-party imports the deny-list contracts do not name. A local run on 2026-11-07 kept 7 of 7 contracts. The planted core-imports-adapter failure was story 1's verify step; no committed test re-proves it.
- **Evidence:** .github/workflows/ci.yml
- **Supports:** the checks job runs uv run lint-imports on every PR
- **Evidence:** tests/unit/test_layer_imports.py
- **Supports:** core imports only stdlib and pydantic, and contract only pydantic, checked by AST
- **Findings:** Met. Advisory: a committed negative test (a temporary module importing an adapter from core, then `lint-imports` asserting a broken contract) would keep the planted-violation proof from regressing silently.

### Spans follow the AD-10 tree and attributes

- **Status:** PASS ✅
- **Threshold:** Spans follow the AD-10 tree and attributes; Tempo returns the tree
- **Threshold Source:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Actual:** In-memory exporter tests assert the SERVER, retrieval and db span tree and attributes. On kind, Tempo and Grafana served the trace in CI run 42385558996.
- **Evidence:** tests/smoke/test_gateway.py
- **Supports:** one search yields one trace in Tempo with the AD-10 tree, also served through Grafana
- **Evidence:** tests/unit/test_telemetry.py
- **Supports:** the in-memory exporter shows the SERVER, retrieval and db spans in the AD-10 tree
- **Findings:** Met.

---

## Evidence Gaps

2 evidence gaps identified - action required:

- **security-api-connects-as-ticketscope-ro:** api connects as ticketscope_ro: planned write-refusal test has no supplied implementation evidence
- **performance-search-latency-on-kind:** Search latency on kind: declared threshold is UNKNOWN

---

## Recorded-Only NFR Criteria

These criteria were preserved without automated assessment.

| ID | Category | Label | Declared threshold | Threshold source | Assessment mode |
| --- | --- | --- | --- | --- | --- |
| deployability-kind-deploy-ci-duration | Deployability | CI duration budget for `_kind-deploy` | UNKNOWN | _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md | RECORDED ONLY |
| deployability-runner-fit | Deployability | GitHub-hosted runner fits kind with both releases (peak memory, free disk, kind-up-to-Ready time in the job summary) | Recorded as evidence, not a threshold | _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md | RECORDED ONLY |

---

## Recommended Actions

### Short-term (Next Milestone) - MEDIUM Priority

1. **Add a write-refusal check for `ticketscope_ro`** - MEDIUM - small - epic-search-baseline follow-up
   - A kind smoke test runs an `INSERT` as `ticketscope_ro` and asserts `permission denied`.

2. **Refresh the test design's NFR rows for the Jira corpus** - LOW - small - test design owner
   - Retire the token and rate-limit-resume rows (GitHub ingest is gone) and add the corpus-terms checks (masking, no identities, takedown), which now carry the security weight.

### Long-term (Backlog) - LOW Priority

1. **Search latency p95** - LOW - epic-eval-gate
   - Report p95 on kind as AD-12 plans; it becomes a threshold only if a later epic sets one.

---

## Gate YAML Snippet

```yaml
nfr_assessment:
  date: '2026-11-07'
  story_id: 'n/a (epic-1)'
  feature_name: 'epic-search-baseline: Keyword search over Mojang issues, deployed on kind'
  audited_domains:
    security: 'CONCERNS'
    performance: 'CONCERNS'
    reliability: 'PASS'
    maintainability: 'PASS'
  overall_status: 'CONCERNS'
  critical_issues: 0
  high_priority_issues: 0
  medium_priority_issues: 1
  concerns: 2
  blockers: false
  quick_wins: 1
  evidence_gaps: 2
  recommendations:
    - 'Add a kind smoke test that a write through ticketscope_ro is refused'
    - 'Update the test design NFR rows for the Jira corpus (retire token and rate-limit rows)'
    - 'Report search p95 on kind in epic-eval-gate'
```

---

## Related Artifacts

- **Epic:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md
- **Test Design:** _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
- **Evidence Sources:**
  - CI Results: GitHub Actions run 42385558996 (PR #19; checks, charts and `_kind-deploy`, all success; 22 kind smoke tests passed)
  - Release: `snapshot-2026.11.1` notes (32,153 issues, 2.6 s timed load, budget 600 s)
  - Test quality: _bmad-output/test-artifacts/test-review/test-review-epic-1.md

---

## Sign-Off

**NFR Evidence Audit:**

- Overall Status: CONCERNS ⚠️
- Critical Issues: 0
- High Priority Issues: 0
- Concerns: 2
- Evidence Gaps: 2

**Gate Status:** CONCERNS ⚠️

**Generated:** 2026-11-07
**Workflow:** testarch-nfr v5.0
