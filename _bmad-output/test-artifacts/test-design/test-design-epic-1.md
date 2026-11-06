---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-06'
runScope: 'epic'
runKey: 'epic-1'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md
  - _bmad-output/initiative-ticketscope/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/initiative-ticketscope.md
  - _bmad-output/initiative-ticketscope/brief-ticketscope/brief-ticketscope.md
  - _bmad-output/initiative-ticketscope/brief-ticketscope/addendum.md
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/nfr-criteria.md
  - knowledge/playwright-cli.md
---

# Test Design: Epic 1 - Keyword search over Kubernetes issues, deployed on kind

**Date:** 2026-11-06
**Author:** Dillon
**Status:** Draft

Epic slug: `epic-search-baseline`. Covers initiative requirements R1, R2, R3, R5, R8 and R11.

---

## Executive Summary

**Scope:** full test design for Epic 1.

This plan was written before the epic's stories and before the architecture run. The repository has no application code and no tests yet. The epic file has `refined: false` and no stories. The stack, the retrieval API contract and the span contract are still to be decided. Every scenario below is planned, and none has run. Where the sources leave a value open, the plan marks it `UNKNOWN`.

**Risk Summary:**

- Total risks identified: 4
- High-priority risks (≥6): 3 (R-001, R-002, R-004)
- Critical categories: TECH (unsettled shared contracts), DATA (how each issue ended), BUS (keyword-only relevance)

**Coverage Summary:**

- P0 scenarios: 3 (~6–12 hours)
- P1 scenarios: 24 (~20–32 hours)
- P2/P3 scenarios: 15 (~7–12 hours)
- **Total effort**: ~33–56 hours (~1–1.5 weeks)

---

## Not in Scope

| Item | Reasoning | Mitigation |
| ---- | --------- | ---------- |
| **Dense and hybrid modes, embedding column** | Owned by epic-hybrid-retrieval (epic Boundaries). | The R-001 contract tests pin the mode parameter, so epic 3 extends it without breaking keyword mode. |
| **Labelled pairs, Recall@k, MRR, p95 latency scoring** | Owned by epic-eval-gate (epic Boundaries). | Epic 1 only checks that labels and closing comments are stored. Retrieval quality is scored by epic 2. |
| **MCP server** | Owned by epic-mcp-server (epic Boundaries). | The R-001 contract tests protect the default-mode contract that epic 4 calls. |
| **EKS, S3 backups, restore and failure drills** | Owned by epic-eks-environment (epic Boundaries). | Epic 1 checks only that CNPG data survives a primary pod deletion on persistent volumes. |
| **Live source API in pull-request CI** | Calling the issues API on every PR adds rate-limit and network flakiness. No source requires it. | PR tests use recorded API responses. A nightly smoke test ingests a small live page. |

---

## Risk Assessment

Risks come from gap statements in the sources. Each gap statement yields one risk. Sources were read in this order: epic file, `tickets.toml`, initiative, brief, addendum. The epic file and `tickets.toml` state no gaps. The brief's Open Questions repeat the initiative's and are merged into them.

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R-001 | TECH | Shared decisions (stack, retrieval API contract, span conventions, chart and CI layout, schema ownership) are not yet settled; the initiative Notes defer them to a bmad-architecture run, and no architecture document exists. Epics 2–7 build on these contracts, so an unpinned or drifting contract breaks downstream epics. | 2 | 3 | 6 | Settle and write down the contracts in the architecture run. Store the response contract as a machine-readable schema. API contract tests read that schema file. | Dillon (architecture run) | Before epic 1 stories are planned |
| R-002 | DATA | "How it ended" is an open question: does the outcome come from the closing comment, the linked PR or the label (initiative Open questions)? R1 is met only when every issue has an outcome recorded. Without a rule, outcomes go missing or are wrong. | 3 | 2 | 6 | Decide a precedence rule and a closed set of outcome values, including explicit values for "closed with no reason" and "still open". Cover each closing path with an integration fixture. | Dillon (architecture run) | Before the ingest story is planned |
| R-004 | BUS | The source ticket tracker's keyword search "fails both kinds of ticket": vague tickets share no words, and log-heavy tickets drown the signal in noise (brief, The Problem). Epic 1 ships keyword mode only. Its Done-when ("return ranked issues") passes on any ranked list, even an irrelevant one. | 3 | 2 | 6 | Build a curated fixture corpus with known twin issues. Assert that the twin appears in the top-k results, not just that some results come back. Record the vague-query result as a keyword baseline for epic 2. | Dillon (retrieval API story) | During the retrieval API story |

Score rationale:

- **R-001:** probability 2, because the architecture run is already scheduled. Impact 3, because four later epics consume the contracts.
- **R-002:** probability 3, because the question is unresolved. Impact 2, because an issue with a missing outcome still appears in results. That degrades the product promise but does not break search.
- **R-004:** probability 3, because the brief states the failure as fact. Impact 2, because epic 3 adds dense and hybrid modes.

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-003 | BUS | Corpus terms are an open question: what do GitHub's terms allow when issue text is stored and served in a public demo index (initiative Open questions)? A late answer forces the stored fields or the corpus to be reworked. | 2 | 2 | 4 | Check the terms before the ingest schema is fixed. Store an allow-listed set of fields, and keep each issue's source URL. Keep a purge-and-reingest path. | Dillon, before the ingest story |

Score rationale: impact is 2, because epic 1 runs on kind only; the public index arrives with epic 5. Re-ingesting with fewer fields fixes the problem.

### Low-Priority Risks (Score 1-2)

No low-priority risks were identified. The sources contain no gap statement that scores 1–2.

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |

### Scope Constraints (verified by regression checks, not scored)

These stated constraints have no evidence of a new exposure. The coverage plan and CI checks verify them:

- The issues API is read only (epic Boundaries). Covered by the P2 read-only integration test.
- Only public material is used. Nothing derived from youscope is carried over: no names, identifier keys, database, logs or `.env` contents (initiative Constraints; addendum, youscope reference). Planned check: a CI denylist scan.
- No server-side LLM generation (initiative Constraints). Planned check: a CI scan that fails if a server-side LLM client dependency is added.
- Outward-facing README text cannot say "vector database" until the claims ledger has a row for it (addendum, Claim discipline). The existing pre-commit check enforces this.

### Risk Category Legend

- **TECH**: Technical/Architecture (flaws, integration, scalability)
- **SEC**: Security (access controls, auth, data exposure)
- **PERF**: Performance (SLA violations, degradation, resource limits)
- **DATA**: Data Integrity (loss, corruption, inconsistency)
- **BUS**: Business Impact (UX harm, logic errors, revenue)
- **OPS**: Operations (deployment, config, monitoring)

---

## NFR Planning

**Purpose:** Capture epic-specific NFR thresholds, planned validation, and evidence expected for later `nfr-assess`. This is not a final evidence audit.

| NFR Category | Requirement / Threshold | Risk Link | Planned Validation | Evidence Needed |
| ------------ | ----------------------- | --------- | ------------------ | --------------- |
| Security | Source access is read only (epic Boundaries). Token handling for ingest: UNKNOWN. | - | Integration test that the ingest client issues only `GET` requests against recorded responses. | CI test report |
| Performance | Search latency on kind: UNKNOWN. CI duration budget for the kind deploy: UNKNOWN. p95 latency is scored by epic 2. | - | Record retrieval span durations as a non-gating baseline. | Span durations from the trace backend, CI job timing |
| Reliability | CNPG Postgres runs with persistent volumes (epic Done-when). Data survives deletion of the primary pod. | - | Nightly E2E: delete the CNPG primary pod, wait for recovery, assert the issue row count is unchanged. | CI job log |
| Maintainability | A search request yields one trace with retrieval and database spans, following the pinned span contract and the GenAI semantic conventions (R8, epic Done-when). | R-001 | API test with an in-memory span exporter. E2E query against the trace backend. | CI test report, trace backend query output |
| Compliance | Storing and serving issue text is allowed by the corpus terms: UNKNOWN until checked. | R-003 | Integration test that stored columns match the allow-list and every row keeps its source URL. | Terms decision record, CI test report |

**Unknown thresholds:** search latency on kind; CI duration budget for the kind deploy; ingest token handling; maximum query length; the rule that classifies a ticket as short or log-heavy; epic 1 corpus size. Each one is a clarification for the architecture run. This plan does not invent values for them.

---

## Entry Criteria

- [ ] Requirements and assumptions agreed by Dillon (sole author)
- [ ] Test environment provisioned and accessible (kind cluster in CI with CNPG and pgvector)
- [ ] Test data available: recorded issues-API responses and a curated fixture corpus with known twin issues
- [ ] Feature deployed to the test environment (Helm chart on kind)
- [ ] Architecture run done: retrieval API contract, span contract, CI layout and chart layout written down (R-001)
- [ ] Outcome precedence rule and outcome value set decided (R-002)
- [ ] Corpus-terms check done and the stored-field allow-list decided (R-003)
- [ ] Epic 1 stories written with acceptance criteria (the epic is currently `refined: false`)

## Exit Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing (or failures triaged)
- [ ] No open high-priority / high-severity bugs
- [ ] Test coverage agreed as sufficient
- [ ] The integrated check passes in CI on kind (epic Done-when)
- [ ] The contract tests for the API and spans read the written contract files, so epics 2–7 inherit them
- [ ] Mitigations for R-001, R-002 and R-004 complete

---

## Test Coverage Plan

P0, P1, P2 and P3 are priorities, not execution timing. The Execution Strategy section decides when each test runs.

### P0 (Critical)

**Criteria**: Critical business, security, data-integrity, or compliance impact with no safe
workaround. Risk score is supporting evidence and is not a required condition.

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| CI deploys the Helm chart to kind with CNPG Postgres, pgvector enabled and persistent volumes, on every PR (R3, R11) | E2E | - | 3 | Dillon | Scenarios: (1) `helm install` on kind succeeds and every pod reaches Ready. (2) The CNPG cluster is healthy, its PVCs are Bound, and the `vector` extension exists in the database. (3) The retrieval API health endpoint and the search page respond inside the cluster. Consequence: if this fails, no other scenario runs and nothing is delivered on the cluster. The initiative assumes the cluster counts as production. Workaround: none in CI. Spans the chart, the operator and the app deployables, so the level is E2E. |

**Total P0**: 3 tests, ~6–12 hours

### P1 (High)

**Criteria**: Core, frequent, or complex behavior with material user reach and a limited workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Retrieval API mode parameter and response contract are pinned (epic Done-when) | API | R-001 | 5 | Dillon | Mechanism: an unpinned contract drifts. Boundary: the retrieval service's HTTP contract, so the level is API. Scenarios: (1) `mode=keyword` is accepted. (2) A request with no mode falls back to the documented default. (3) An unknown mode returns the documented 4xx error body. (4) Every response validates against the written contract schema file. (5) Every result carries its outcome field. Consequence: epics 2, 3, 4 and 7 break. Workaround: amend the contract and re-plan the dependent epics, which is recoverable but costly. |
| Every ingested issue has an outcome recorded (R1) | Integration | R-002 | 6 | Dillon | Mechanism: no outcome rule. Boundary: the ingest job writes to the owned Postgres store, so the level is Integration. Scenarios, one fixture issue per closing path: (1) outcome from a label, (2) from a linked merged PR, (3) from a closing comment, (4) closed with no reason gives the explicit fallback value, (5) a still-open issue gives the explicit open value, (6) a whole-corpus query finds zero rows with a null outcome. Consequence: results lose "how it ended". Workaround: fix the rule and re-run ingest from the source, which is recoverable. |
| A vague query and a log-heavy query to keyword mode return ranked issues (R2) | API | R-004 | 4 | Dillon | Mechanism: keyword ranking returns irrelevant or noise-drowned results. Boundary: the retrieval service's HTTP contract, so the level is API. Scenarios run against the curated fixture corpus: (1) a log-heavy query containing an exact error string ranks its known twin in the top-k. (2) A vague query whose twin shares key terms ranks that twin in the top-k. (3) A log-heavy query of several KB containing full-text-search operator characters (`&`, `\|`, `!`, `:`, `(`) returns 200 with ranked results. (4) The same query run twice gives the same order, and scores do not increase down the list. Consequence: the triage engineer sees irrelevant matches. Workaround: none in epic 1. Epic 3 adds dense and hybrid modes. |
| The ingest job stores issues with labels and closing comments, both short and log-heavy (R1) | Integration | - | 4 | Dillon | Uses recorded API responses. Scenarios: (1) labels stored, (2) closing comments stored, (3) the corpus holds both short and log-heavy issues under the classification rule (rule UNKNOWN until architecture), (4) re-running ingest creates no duplicate rows. Idempotency is not stated in the sources, so scenario 4 is pending clarification. |
| The search page shows ranked issues with how each ended (R5) | E2E | - | 2 | Dillon | Playwright against the kind deployment. Scenarios: (1) paste a vague ticket and see a ranked list with an outcome on each result, (2) paste a multi-KB log-heavy ticket and see a ranked list. |
| A search request yields one trace with retrieval and database spans in the trace backend (R8) | E2E | - | 1 | Dillon | Send a search request with a known `traceparent`. Query the trace backend API. Assert one trace that holds both the retrieval span and the database span. Spans the API, the OTel collector, the trace backend and Postgres. |
| Retrieval and database spans follow the pinned span contract (R8, epic Done-when) | API | - | 2 | Dillon | Uses an in-memory span exporter. Scenarios: (1) the retrieval span carries the contract's attribute names, including the mode. (2) The database span is a child of the retrieval span. |

**Total P1**: 24 tests, ~20–32 hours

### P2 (Medium)

**Criteria**: Secondary behavior with narrower user reach and an acceptable workaround. Risk score
is supporting evidence and is not a required condition.

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Stored issue data stays within the corpus-terms decision | Integration | R-003 | 2 | Dillon | Mechanism: ingest stores fields the terms may not allow. Boundary: ingest writes to the owned Postgres store, so the level is Integration. Scenarios: (1) the stored columns match the allow-list, (2) every row keeps its source issue URL. Consequence: rework before the public index arrives (epic 5). Workaround: purge and re-ingest with fewer fields, which is recoverable. Reach: none until a public URL exists. |
| The retrieval API rejects invalid input | API | - | 3 | Dillon | Scenarios: (1) an empty query returns a 4xx, (2) a query over the maximum length returns the documented response (limit UNKNOWN), (3) `k` outside its bounds returns a 4xx. |
| The search page handles empty and error states (R5) | E2E | - | 2 | Dillon | Scenarios: (1) a query with no matches shows an empty state, (2) when the API is unavailable the page shows an error message and no stack trace. |
| Short versus log-heavy classification rule | Unit | - | 3 | Dillon | Tests the boundary values of the rule. The rule is UNKNOWN until the architecture run. Epic 2 reports scores split by this rule. |
| The issues API is read only (epic Boundaries) | Integration | - | 1 | Dillon | Regression check for the scope constraint: against recorded responses, the ingest client issues only `GET` requests. |
| CNPG data survives deletion of the primary pod (R3, persistent volumes) | E2E | - | 1 | Dillon | Runs nightly. Delete the primary pod, wait for the cluster to be Ready, and assert the issue row count is unchanged. Workaround: re-run ingest. Backups and drills belong to epic 5. |

**Total P2**: 12 tests, ~6–10 hours

### P3 (Low)

**Criteria**: Rare, cosmetic, or experimental behavior with minimal impact and an easy workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Long log-heavy result snippets render without breaking the page layout (R5) | Component | - | 1 | Dillon | Cosmetic. Workaround: open the source issue link. |
| Query normalisation handles Unicode input | Unit | - | 2 | Dillon | Test data: `"kubelet ❌ failed: ñode not ready"` and a query that is only emoji. Assert no exception and a normalised string. |

**Total P3**: 3 tests, ~1–2 hours

Why the bands look like this: only the kind deploy smoke test is P0. Every other scenario has a recoverable workaround: re-ingest, amend the contract, or wait for epic 3. No high risk reaches P0 for the same reason. R-001, R-002 and R-004 are P1 because they affect the core search journey or the downstream epics, and a recovery path exists for each.

---

## Execution Strategy

**Philosophy:** Run every functional scenario in pull requests while the suite stays under 15 minutes.
Defer only work with material infrastructure or duration cost. P0 through P3 are priority and are not
execution timing; this section decides when tests run and the coverage plan above decides what they are.

- **Pull request:** the run is ordered smoke first, then P0, then P1, then P2/P3, so a broken deploy fails fast. It includes all Unit, Component, Integration and API scenarios, the P0 kind deploy smoke tests, and the E2E page and trace scenarios against the kind deployment. Playwright runs in parallel with a target duration below 15 minutes. The kind and CNPG startup time is UNKNOWN. Measure it on the first PR. If the suite goes over 15 minutes, move the page E2E scenarios to a post-deploy job in the same workflow.
- **Nightly:** the CNPG primary-pod deletion test, and a live smoke ingest of one small page of real issues. This catches drift in the source API without rate-limit risk on PRs.
- **Weekly:** a full-corpus ingest. Report the share of issues with each outcome value and each ticket kind, as input for R-002 and epic 2.

Do not re-list the individual tests here. They are already in the coverage plan.

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 3 | 2.0–4.0 | ~6–12 | Setting up kind, CNPG and the chart in CI is the main cost |
| P1 | 24 | 0.8–1.3 | ~20–32 | Building the fixture corpus and the contract schema drives this |
| P2 | 12 | 0.5–0.8 | ~6–10 | Simple scenarios |
| P3 | 3 | 0.3–0.7 | ~1–2 | Cosmetic and edge input |
| **Total** | **42** | **-** | **~33–56** | **~1–1.5 weeks** |

### Prerequisites

**Test Data:**

- Recorded issues-API responses, with one fixture issue per closing path: label, linked PR, closing comment, closed with no reason, open.
- A curated fixture corpus of short and log-heavy issues with known twin pairs. Size UNKNOWN.
- A golden-query file: vague and log-heavy queries, each with the twin issue it is expected to return.

**Tooling:**

- Playwright (with playwright-utils, per the TEA config) for the page E2E scenarios.
- The test runner for the service language. The stack is UNKNOWN until the architecture run.
- An in-memory OTel span exporter for the span-contract API tests.
- kind, Helm and the CNPG operator in GitHub Actions.

**Environment:**

- A kind cluster per CI run, with the CNPG operator, pgvector, the OTel collector and the trace backend from the chart.
- A disposable Postgres with pgvector for the Integration tests. Use a container or the kind CNPG cluster; the architecture run decides.

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths**: ≥80% (ingest-to-store and query-to-ranked-result)
- **Security scenarios**: 100% (only the read-only source check; no SEC-category risk is registered)
- **Business logic**: ≥70% (outcome derivation, ticket-kind classification, query normalisation)
- **Edge cases**: ≥50%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Security tests (SEC category) pass 100% (no SEC risks registered for this epic)
- [ ] Performance targets met (PERF category): N/A for epic 1, because no threshold is set (UNKNOWN). Epic 2 owns p95.
- [ ] Planned NFR evidence exists or `nfr-assess` has documented CONCERNS/waivers

---

## Mitigation Plans

### R-001: Shared decisions not yet settled (Score: 6)

**Mitigation Strategy:** In the bmad-architecture run, write down:

- the retrieval API's mode parameter and response contract, as a machine-readable schema
- the span contract: span names, attributes and parent-child structure, following the GenAI semantic conventions
- the CI workflow layout and the chart layout
- schema ownership

The P1 API contract tests and the span tests read these files, so a change to a contract fails CI until the file and the tests agree.
**Owner:** Dillon
**Timeline:** before epic 1 stories are planned
**Status:** Planned
**Verification:** the contract files exist, and the R-001 coverage row passes against them in CI.
**Residual risk:** a later epic may still need to change a contract. The tests turn that into a visible CI failure instead of silent drift.

### R-002: Outcome source undecided (Score: 6)

**Mitigation Strategy:** Decide a precedence order between label, linked PR and closing comment. Define a closed set of outcome values, including explicit values for "closed with no reason" and "still open". The ingest job applies the rule. The weekly full ingest reports the share of issues for each value.
**Owner:** Dillon
**Timeline:** before the ingest story is planned
**Status:** Planned
**Verification:** the six R-002 integration scenarios pass, and the whole-corpus query finds zero null outcomes.
**Residual risk:** an outcome can be recorded but still be wrong for an issue whose closing path is unusual. The weekly outcome distribution report is the signal for that.

### R-004: Keyword search fails both kinds of ticket (Score: 6)

**Mitigation Strategy:** Make the acceptance check assert relevance. Each golden query must rank its known twin in the top-k, rather than only returning a non-empty list. Record vague queries that keyword mode misses as a baseline, not a failure, and pass them to epic 2's eval.
**Owner:** Dillon
**Timeline:** during the retrieval API story
**Status:** Planned
**Verification:** the four R-004 API scenarios pass on the fixture corpus.
**Residual risk:** vague queries that share no words with their twin stay weak in keyword mode until epic 3. Epic 2's eval measures that gap.

### R-003: Corpus terms unknown (Score: 4)

**Mitigation Strategy:** Check GitHub's terms for storing and serving issue text. Record the decision. Limit stored fields to an allow-list, keep the source URL on every row, and keep a purge-and-reingest path.
**Owner:** Dillon
**Timeline:** before the ingest schema is fixed
**Status:** Planned
**Verification:** the two R-003 integration scenarios pass.
**Residual risk:** the terms decision may change before epic 5 makes the index public. The purge-and-reingest path covers that.

---

## Assumptions and Dependencies

### Assumptions

1. The cluster counts as production for every epic: kind in CI until epic 5 lands (initiative Assumption).
2. The page E2E scenarios use Playwright, whatever language the service uses.
3. PR CI uses recorded issues-API responses. Live API calls run only nightly.
4. Dillon owns every test, risk and mitigation (personal project).
5. Ingest re-runs are expected to be idempotent. The sources do not say so; confirm in the architecture run.

### Dependencies

1. bmad-architecture run (contracts, stack, layouts): required before epic 1 stories are planned.
2. Outcome rule and corpus-terms decision: required before the ingest story is planned.
3. Curated fixture corpus with known twins: required before the retrieval API story is accepted.

### Risks to Plan

- **Risk**: the architecture run slips, and stories start with unwritten contracts.
  - **Impact**: the R-001 contract tests have nothing to read, and downstream epics inherit guesses.
  - **Contingency**: make writing the contract files the first story of the epic.
- **Risk**: kind and CNPG startup push the PR suite past 15 minutes.
  - **Impact**: slow feedback on every PR.
  - **Contingency**: move the page E2E scenarios to a post-deploy job, and keep the P0 smoke tests on every PR.
- **Risk**: the curated twin pairs are too few or too easy.
  - **Impact**: the R-004 checks pass while real vague queries fail.
  - **Contingency**: grow the golden set from epic 2's labelled pairs once they exist.

---

## Follow-on Workflows (Manual)

- Run `/bmad-tea-automate` in red mode to generate failing P0 tests (separate workflow; not auto-run).
- Run `/bmad-tea-automate` for broader coverage once implementation exists.
- Run `/bmad-tea-nfr` once implementation evidence exists.

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: Dillon Date: ____
- [ ] Tech Lead: Dillon Date: ____
- [ ] QA Lead: Dillon Date: ____

**Comments:**

---

## Interworking & Regression

| Service/Component | Impact | Regression Scope |
| ----------------- | ------ | ---------------- |
| **Epic 2 eval job** | Reads stored labels, closing comments and the mode parameter | R-002 outcome tests, the ingest field tests and the R-001 contract tests must stay green |
| **Epic 3 dense and hybrid modes** | Extends the mode parameter, the response contract and the spans | The R-001 contract tests and the span contract tests must pass unchanged for keyword mode |
| **Epic 4 MCP server** | Calls the retrieval API in its default mode, and extends the trace | The R-001 default-mode scenario and the trace E2E scenario |
| **Epic 5 EKS** | Deploys the same chart and images | The P0 kind deploy smoke tests |
| **Epic 7 Grafana** | Derives metrics from the spans | The span contract tests |

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization
- `nfr-criteria.md` - NFR planning
- `playwright-cli.md` - Browser exploration (skipped: no running app)

### Related Documents

- PRD: none. Initiative requirements stand in: `_bmad-output/initiative-ticketscope/initiative-ticketscope.md`
- Epic: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md`
- Architecture: not yet written (planned bmad-architecture run)
- Tech Spec: none
- Brief: `_bmad-output/initiative-ticketscope/brief-ticketscope/brief-ticketscope.md` and `addendum.md`

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `bmad-tea-test-design`
**Version**: 4.0 (BMad v6)
