---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-06'
runScope: 'epic'
runKey: 'epic-1'
supersedes: '_bmad-output/test-artifacts/test-design/test-design-epic-1.md (removed; written before refinement)'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-ingest-publishes-a-versioned-corpus-snapshot.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus-findings/outcome-mapping.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/spike-choose-the-jira-corpus-findings/terms.md
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
  - _bmad-output/initiative-ticketscope/initiative-ticketscope.md
  - _bmad-output/initiative-ticketscope/brief-ticketscope/brief-ticketscope.md
  - _bmad-output/initiative-ticketscope/brief-ticketscope/addendum.md
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/nfr-criteria.md
---

# Test Design: Epic 1 - Keyword search over Kubernetes issues, deployed on kind

**Date:** 2026-11-06
**Author:** Dillon
**Status:** Draft

Epic slug: `epic-search-baseline`. Epic requirements R1–R7 (initiative R1, R2, R3, R5, R8, R11). This plan replaces the pre-refinement plan that lived in `_bmad-output/test-artifacts/test-design/`.

---

## Executive Summary

**Scope:** full test design for Epic 1, against the refined epic (`refined: true`), the adopted architecture spine and the 11 planned entries in `tickets/tickets.toml`. Rows for stories 13 and 14, added by the spike 12 replan, were added in an edit on 2026-11-06.

No application code exists yet. Every scenario below is planned, and none has run. Most scenarios are the stories' own `verify` lines broken into atomic tests; this plan assigns their levels and priorities and adds the relevance checks the stories do not yet carry.

**Risk Summary:**

- Total open risks: 1 (R-004)
- High-priority risks (≥6): 1 (R-004)
- Critical categories: BUS (keyword ranking can pass the epic's checks on irrelevant results)
- Closed since the previous plan: R-001 (shared contracts), R-002 (outcome rule), R-003 (corpus terms). Their regression coverage stays in the plan.

**Coverage Summary:**

- P0 scenarios: 3 (~6–12 hours)
- P1 scenarios: 71 (~43–71 hours)
- P2/P3 scenarios: 17 (~7–13 hours)
- **Total effort**: ~56–97 hours (~1.5–2.5 weeks)

---

## Not in Scope

| Item | Reasoning | Mitigation |
| ---- | --------- | ---------- |
| **Dense and hybrid modes, the `issue_embedding` table** | Owned by epic-hybrid-retrieval (epic Boundaries, spine AD-21). | The `/v1` contract tests (story 6) pin the mode registry and the additive-only rule, so epic 3 extends keyword without breaking it. |
| **Recall@k, MRR, p95 latency, labelled pairs** | Owned by epic-eval-gate (epic Boundaries, spine AD-12). | The R-004 golden-query checks are a relevance smoke test, not a metric. They are never quoted as retrieval quality. |
| **MCP server** | Owned by epic-mcp-server (epic Boundaries). | `GET /v1/issues/{number}` and the AD-10 span tree are tested here because epic 4 calls them. |
| **EKS, S3 backups, restore and failure drills** | Owned by epic-eks-environment (epic Boundaries, spine AD-18). | Epic 1 tests only that a backup to SeaweedFS completes on kind (story 8). |
| **Grafana dashboard and spanmetrics** | Owned by epic-grafana-dashboard (spine AD-11). | Epic 1 checks the trace through the Tempo API; viewing it in Grafana Explore is one manual P3 step. |

---

## Risk Assessment

Sources were read in this order: the epic file, `tickets.toml`, the two written story files, the spine, the initiative and the brief. One gap statement from the previous plan is still open; three are settled by the refined sources (see Closed Risks).

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R-004 | BUS | Keyword search fails both kinds of ticket (brief, The Problem): vague tickets share no words with their twins, and log-heavy tickets drown the signal in noise. Epic 1 ships keyword mode only. Its met criteria ask that the example queries "return ranked issues with outcomes" (epic R3) and render "a ranked list where every row shows an outcome" (stories 7, 11); the sweep checks only that `/v1` responses do not change (story 10). None says which issues must come back, so every check passes on an irrelevant list. Only the tracer asserts relevance, and only on the synthetic fixture (story 1). | 3 | 2 | 6 | Story 5 writes a golden-query file from the pinned real snapshot: each vague and log-heavy example query names its twin issue. The integrated check (story 11) asserts each twin appears in the top-k through `/v1/search`. | Dillon; story 5 writes the file, story 11 gates on it | Story 5 (file), story 11 (gate) |

Score rationale: probability 3, because the brief states the failure as fact and nothing in the refined sources checks result identity on real data. Impact 2, because the triage engineer sees irrelevant matches, but search still works and epic 3 adds dense and hybrid modes.

### Medium-Priority Risks (Score 3-4)

No medium-priority risks are open.

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |

### Low-Priority Risks (Score 1-2)

No low-priority risks are open.

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |

### Closed Risks (regression-covered, not scored)

| Risk ID | Settled by | Regression coverage |
| ------- | ---------- | ------------------- |
| R-001 | The spine is adopted: `/v1` contract (AD-4), span contract (AD-10), two releases (AD-13), CI layout (AD-17), Retriever port and registry (AD-19), one wire contract module (AD-20), values ownership (AD-25). | P1 `/v1` contract tests (story 6), P1 span-attribute tests (story 9), P1 import-linter check (story 1). |
| R-002 | The epic's Constraints fix the outcome precedence and outcome terms, and story 4 computes them in core (AD-8). | P1 outcome unit tests, one per branch plus ties (story 4); P1 Jira outcome unit tests, one per resolution class plus the answered rule (story 14); P1 load check that no issue lacks an outcome (story 5). |
| R-003 | Story 2's spike settles the corpus terms, and story 3's publish waits on it. If the answer is no, story 3 stops and the epic is replanned. | P1 ingest check that story 2's conditions are applied to the snapshot (story 3). P1 Jira ingest checks that spike 12's conditions are applied: no identities, masking, exclusion and attribution (story 13). |

### Tracked Assumption (not scored)

- **Runner fit** (epic Notes, Assumption): a GitHub-hosted runner fits kind with the platform release, two Postgres instances and SeaweedFS. Story 1 proves it first and records peak memory, free disk and kind-up-to-`api`-Ready time in the `_kind-deploy` job summary. It is listed under NFR Planning as evidence, not as a scored risk.

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
| Security | Ingest reads with a read-only token stored as a repo secret (story 3). `api` connects as `ticketscope_ro` (AD-7). Query text is recorded on spans only when a value opts in (AD-10). | - | Integration: ingest issues only `GET`; a write through `ticketscope_ro` is refused. API: retrieval span carries no query text by default. | CI test report |
| Performance | A load of the candidate snapshot finishes within 10 minutes on the runner (story 3, initiative R10). Search latency on kind: UNKNOWN; p95 is reported, never gated, by epic 2 (AD-12). | - | Timed load in `snapshot.yml` before publish. | Release notes with measured load time |
| Reliability | CNPG runs two instances with persistent volumes, and an on-demand backup to SeaweedFS completes (R5, story 8). Ingest resumes after a rate limit or job timeout (story 3). | - | E2E: two ready instances; Backup phase `completed` and objects listed in the bucket. Integration: resume from a simulated rate-limit response. | `_kind-deploy` job log, CI test report |
| Maintainability | import-linter enforces the AD-1 layer rules. Spans follow the AD-10 tree and attributes. | - | Unit: a deliberate core-imports-adapter change fails. API: in-memory span exporter. E2E: Tempo API returns the tree. | CI test report, Tempo API output |
| Capacity | Runner fit (epic Assumption). Numeric runner limits: UNKNOWN. | - | Story 1's `_kind-deploy` job summary records peak memory, free disk and kind-up-to-Ready time. | Job summary |

**Unknown thresholds:** search latency on kind; CI duration budget for `_kind-deploy`; the `k` each golden query is checked at (default 10 under AD-4 unless the golden-query file sets it); the golden-query file's path. Story 5 sets the last two.

---

## Entry Criteria

- [x] Architecture spine adopted (AD-1 to AD-25)
- [x] Epic refined and its 11 entries planned
- [ ] Story 2's corpus-terms decision recorded before story 3 publishes
- [ ] Story 5's entry names the golden-query file and its twin field (see Dependencies)
- [ ] kind bring-up proven on a GitHub-hosted runner (story 1)

## Exit Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing (or failures triaged)
- [ ] No open high-priority / high-severity bugs
- [ ] Test coverage agreed as sufficient
- [ ] The integrated check (story 11) passes on a PR, including the R-004 twin checks, and fails when any one of its checks is broken on purpose
- [ ] R-004 mitigation complete

---

## Test Coverage Plan

P0, P1, P2 and P3 are priorities, not execution timing. The Execution Strategy section decides when each test runs. The Owner column names the story whose build writes the test.

### P0 (Critical)

**Criteria**: Critical business, security, data-integrity, or compliance impact with no safe
workaround. Risk score is supporting evidence and is not a required condition.

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| Both releases deploy to kind on every PR and keyword search answers through the Gateway (R5, R7) | E2E | - | 3 | Story 1; re-run by story 11 | Scenarios: (1) `_kind-deploy` brings up the `platform` and `ticketscope` releases and every pod reaches Ready. (2) The Cluster reports two ready instances, and both `vector` and `pg_textsearch` extensions exist. (3) `POST /v1/search` with mode `keyword` through the Gateway returns ranked results in the `/v1` shape with `corpus_version` set. Consequence: if this fails, nothing is delivered on the cluster and no other kind scenario runs. Workaround: none in CI. Spans the platform release, the operator and the app, so the level is E2E. |

**Total P0**: 3 tests, ~6–12 hours

### P1 (High)

**Criteria**: Core, frequent, or complex behavior with material user reach and a limited workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| The vague and log-heavy example queries return relevant issues, not just ranked ones (R3) | API | R-004 | 4 | Story 5 (golden-query file), story 11 (assertions) | Mechanism: BM25 ranking returns an irrelevant or noise-drowned list that still satisfies "ranked issues with outcomes". Boundary: the `/v1/search` HTTP contract, so the level is API. Each golden-query entry records the query text, its kind, how it was chosen, its source issue and its twin issue number from the pinned snapshot. Scenarios: (1) the log-heavy query's twin appears in the top-k. (2) The vague query's twin appears in the top-k. (3) A file check: every twin exists in the pinned snapshot, differs from the query's source issue, and the file's snapshot version equals the pin, so the check cannot pass by the query matching its own text. (4) Running each query twice returns the same `rank` order; story 10's no-change check relies on this. If no vague pair ranks its twin under keyword, story 5 records that as a known keyword miss, and scenario 2 is reported, not gated, until epic 3. Consequence: the triage engineer sees irrelevant matches. Workaround: none in epic 1. The fixture-level check stays in story 1: the fixture issue written to match best is at rank 1. |
| `/v1` contract completion (R3; regression for closed R-001) | API | - | 6 | Story 6 | Against the in-memory fake, with one run on kind: (1) `GET /v1/issues/{number}` returns the issue with body and outcome. (2) `k=0` returns 422 `application/problem+json`. (3) `k=51` returns 422. (4) An unknown `mode` returns 422 `application/problem+json`. (5) An issue in `exclude` never appears in results (AD-19). (6) Contract models accept unknown fields (AD-20). |
| Outcome derivation in core (R2; regression for closed R-002) | Unit | - | 9 | Story 4 | One case per branch with its `source`: duplicate → `label`, fixed → `linked_pr`, not_planned → `null`, stale → `null`, answered → `closing_comment`, unknown → `null`. Plus: (7) a duplicate also closed by a merged PR is duplicate. (8) A `kind/support` issue whose only comment after `closed_at` is from a CONTRIBUTOR is not answered. (9) A cross-referenced PR that was not merged does not make an issue fixed. |
| Kind rule in core (R2) | Unit | - | 3 | Stories 4, 5 | (1) A body just below the threshold is `short`. (2) Just above is `log_heavy`. (3) For every fixture issue, the computed kind equals its expected kind (story 5). |
| Load the pinned snapshot (R2) | Integration | - | 5 | Story 5 | (1) An asset whose checksum differs from the pinned checksum is refused. (2) A SQL check finds no issue without a kind or an outcome. (3) The job log reports each kind's and each outcome's share. (4) A second load with the same pin is a no-op. (5) `corpus_meta` holds the pinned snapshot version, and `api` returns it as `corpus_version`. |
| Load fits its spin-up share (R1, initiative R10) | Integration | - | 1 | Story 3 | `snapshot.yml` times a load of the candidate snapshot into the in-repo Postgres image on the runner. The time must be within 10 minutes before the snapshot is published. |
| Ingest writes a valid snapshot (R1; regression for closed R-003) | Integration | - | 4 | Story 3 | Against recorded GitHub API responses: (1) the output validates against the committed JSON Schema. (2) After a simulated rate-limit response, ingest resumes where it stopped. (3) An issue with 100 or more comments is fetched in full. (4) Story 2's conditions, such as excluded fields or attribution, are applied. Story 3's 20-issue sample against github.com stays a manual check. |
| Jira outcome derivation in core (R2; regression for closed R-002) | Unit | - | 12 | Story 14 | On synthetic Jira-shaped issues, per spike 12's `outcome-mapping.md`. One case per class with its `source`: (1) `Duplicate` → duplicate, `label`, with `ref` pointing at the duplicate target. (2) `Fixed` → fixed, `null`. (3) `Won't Fix` → not_planned, `null`. (4) `Timed out` → stale, `null`. (5) `Answered` → answered, `closing_comment`. (6) No resolution → unknown, `null`. (7) An unmapped resolution such as `Triaged` → unknown. (8) A resolution is matched case-insensitively after trimming, so ` fixed ` → fixed. The answered rule: (9) a Question type issue resolved `Done` with the non-reporter-comment flag set → answered, `closing_comment`. (10) The same issue with the flag unset → fixed. (11) A Support type issue resolved `Duplicate` with the flag set stays duplicate. (12) Core's derivation version differs from story 4's, so a load reloads. Story 4's GitHub outcome tests keep running beside these. |
| Jira kind rule in core (R2) | Unit | - | 3 | Story 14 | (1) A body whose `{code}` and `{noformat}` blocks put it just below the threshold is `short`. (2) Just above is `log_heavy`. (3) A `{code:java}` toggle with parameters counts the same as `{code}`. How an unclosed toggle counts: UNKNOWN; the sources do not say. |
| Ingest writes a valid Jira snapshot (R1) | Integration | - | 8 | Story 13 | Against a recorded slice of The Public Jira Dataset v7: (1) the output validates against the committed JSON Schema v2. (2) Schema v2 mirrors core's snapshot model as story 14 extends it: a v2 record parses into the model, and the two name the same fields. (3) A repeated issue key is kept once, and the first document wins. (4) Only resolved MCL, REALMS and MCD issues and the unresolved issues their duplicates point to are written; an unresolved issue no duplicate points to, and a resolved issue from another project, are absent. (5) Each record carries its Jira id, its readable key, its `bugs.mojang.com` URL built from the key, and the duplicate link to its target. The non-reporter-comment flag: (6) set when someone other than the reporter commented at or before the resolution time; (7) unset when only the reporter commented; (8) unset when the only non-reporter comment came after the resolution time. The person-run publish itself stays story 13's manual verify. |
| The Jira snapshot carries no identities and applies spike 12's terms (R1; regression for closed R-003) | Integration | - | 5 | Story 13 | Against the recorded slice: (1) no reporter, assignee, creator or comment-author id from the slice appears anywhere in the output. (2) Planted emails and secrets are masked. (3) `[~user]` and `[~accountid:…]` mentions are masked. (4) An issue on the exclusion list is absent. (5) The generated Release notes and the README carry spike 12's attribution line from `terms.md`. |
| The fixture and load move to schema v2 (R1) | Integration | - | 2 | Story 13 | (1) The synthetic fixture validates against schema v2 and still records each issue's expected kind outside the schema. (2) `jobs.load` reads the v2 fixture through story 1's load path and stores every issue. Story 1's P0 bring-up then re-runs on the v2 fixture. |
| The Jira snapshot load fits its spin-up share (R1, initiative R10) | Integration | - | 1 | Story 13 | Before the person-run publish, ingest times a load of the candidate snapshot into the in-repo Postgres image, and the time must be within 10 minutes. It runs on the person's machine, not the runner (epic Decision, story 13 runs locally); spike 12 measured 3.9 s for the subset. |
| The search page shows both example queries (R4) | E2E | - | 2 | Story 7 | Through the Gateway on kind: the vague and the log-heavy example query each render a ranked list where every row shows title, link, kind and outcome. |
| One search request yields one trace in Tempo (R6) | E2E | - | 1 | Story 9 | One `POST /v1/search` produces a trace that the Tempo API returns with the `ticketscope-api` SERVER span, the `retrieval keyword` INTERNAL span and the `db query` CLIENT span in the AD-10 tree. |
| Span attributes follow AD-10 (R6; regression for closed R-001) | API | - | 3 | Story 9 | In-memory span exporter: (1) `service.name` is exactly `ticketscope-api`. (2) The retrieval span carries `gen_ai.operation.name=retrieval`, `gen_ai.data_source.id=ticketscope-k8s-issues`, `ticketscope.retrieval.mode`, `.k`, `ticketscope.corpus.version` and `ticketscope.result.count`. (3) The query text is absent unless the opt-in value is set. |
| Backup to SeaweedFS completes (R5) | E2E | - | 1 | Story 8 | In `_kind-deploy`, an on-demand CNPG Backup reaches phase `completed`, and its objects are listed in the SeaweedFS bucket. |
| Layer rules are enforced (Done when; regression for closed R-001) | Unit | - | 1 | Story 1 | A deliberate change that makes `core` import an adapter fails import-linter. |

**Total P1**: 71 tests, ~43–71 hours

### P2 (Medium)

**Criteria**: Secondary behavior with narrower user reach and an acceptable workaround. Risk score
is supporting evidence and is not a required condition.

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| The integrated check catches each broken part (R1–R7) | E2E | - | 5 | Story 11 | Story 11's verify: break each of its five checks on purpose (schema, kind/outcome, `/v1` and page, trace, backup) and confirm the job fails. Runs on story 11's PR and whenever the check changes. |
| Page empty and error states (R4) | API | - | 2 | Story 7 | On the in-memory fake: (1) a query with no matches renders the empty state, (2) a store failure renders the error state with no stack trace. |
| The page escapes echoed text (R4) | API | - | 1 | Story 7 | Query text and issue titles containing `<script>` render escaped. Not stated in the sources; added because the page echoes user input. |
| Log-heavy input is accepted by BM25 (R3) | API | - | 2 | Story 6 | (1) A query containing full-text operator characters (`&`, `\|`, `!`, `:`, `(`) returns 200 with ranked results. (2) A multi-KB pasted log returns 200. |
| Database roles and source access are read-only where stated (AD-7, story 3) | Integration | - | 2 | Stories 1, 3 | (1) A write through `ticketscope_ro` is refused. (2) Against recorded responses, ingest issues only `GET` requests. |
| Published snapshots are never overwritten (R1) | Unit | - | 1 | Story 3 | The next version is the next free `YYYY.MM.N`; an existing version is never chosen. Story 3's second-dispatch check stays its manual verify. |
| The Jira Release notes report the subset and its counts (R1) | Unit | - | 2 | Story 13 | On the recorded slice: (1) the in-subset duplicate pairs by kind equal a hand count, and a duplicate whose target is outside the subset is not counted. (2) The generated Release notes state the subset, the issue count, the in-subset duplicate pairs by kind, the kind split and the measured load time. |
| Logs carry trace context (R6) | Unit | - | 1 | Story 9 | A log line emitted inside a span is JSON with `trace_id` and `span_id`. |

**Total P2**: 16 tests, ~6–13 hours

### P3 (Low)

**Criteria**: Rare, cosmetic, or experimental behavior with minimal impact and an easy workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ---------- | --------- | ---------- | ----- | ----- |
| The trace is viewable in Grafana Explore (R6) | E2E | - | 1 | Story 9 | Manual step via port-forward. Workaround: the Tempo API check (P1) already proves the trace exists. |

**Total P3**: 1 test, ~0.5 hours

Why the bands look like this: only the kind bring-up is P0, because every other failure has a recovery path. A wrong outcome or kind is fixed by a reload (AD-8). A contract slip fails CI before it ships. A weak ranking is the expected keyword baseline that epic 3 improves on. R-004 is P1 because it affects the core search journey but has no data-integrity or security consequence.

---

## Execution Strategy

**Philosophy:** Run every functional scenario in pull requests while the suite stays under 15 minutes.
Defer only work with material infrastructure or duration cost. P0 through P3 are priority and are not
execution timing; this section decides when tests run and the coverage plan above decides what they are.

- **Pull request:** `ci.yml` runs ruff, pyright, import-linter and every Unit, Integration and API test on the in-memory fake or a Postgres container. `_kind-deploy` then runs the P0 bring-up first, so a broken deploy fails fast, followed by the load checks on the pinned real snapshot, the R-004 golden-query checks, the page, trace and backup scenarios. Playwright is not needed: the page is server-rendered with no JS framework, so page checks are HTTP requests. The duration of `_kind-deploy` is UNKNOWN until story 1 records it.
- **Person-run (story 13):** the Jira ingest's timed load runs on the person's machine before the publish. Story 13's Unit and Integration tests on the recorded slice run in `ci.yml` on every PR.
- **On dispatch:** `snapshot.yml` runs the ingest checks against the live API and the 10-minute load timing before it publishes.
- **Nightly:** none planned. Every scenario fits the PR or dispatch runs.
- **Weekly:** none planned.

Do not re-list the individual tests here. They are already in the coverage plan.

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 3 | 2.0–4.0 | ~6–12 | kind, CNPG and Gateway bring-up in CI is the main cost |
| P1 | 71 | 0.6–1.0 | ~43–71 | Most are story verify lines; the golden-query file adds the curation work |
| P2 | 16 | 0.4–0.8 | ~6–13 | Simple scenarios |
| P3 | 1 | 0.25–0.5 | ~0.5 | Manual |
| **Total** | **91** | **-** | **~56–97** | **~1.5–2.5 weeks** |

### Prerequisites

**Test Data:**

- The synthetic fixture snapshot with expected kinds (story 1).
- The pinned real snapshot and its checksum (stories 3, 5).
- The golden-query file with each query's source issue and twin issue (story 5).
- Recorded GitHub API responses, including a rate-limit response and an issue with 100 or more comments (story 3).
- A recorded slice of The Public Jira Dataset v7 with a repeated issue key, a duplicate pointing outside the subset, planted emails, secrets and mentions, an excluded issue, and Question/Support issues with comments before and after resolution (story 13).

**Tooling:**

- pytest, ruff, pyright and import-linter (epic Constraints, Toolchain). Test-framework depth goes to `bmad-tea-framework`.
- An in-memory OTel span exporter for the span-attribute tests.
- The Tempo HTTP API for the trace check.

**Environment:**

- kind through `scripts/kind-up.sh` and `_kind-deploy` (AD-17), with both releases.
- A Postgres container from the in-repo image for Integration tests outside kind.

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths**: ≥80% (snapshot → load → `/v1/search` → page)
- **Security scenarios**: 100% (the read-only and escaping checks; no SEC risk is open)
- **Business logic**: ≥70% (outcome and kind derivation in core)
- **Edge cases**: ≥50%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Security tests (SEC category) pass 100% (no SEC risk is open for this epic)
- [ ] Performance targets met (PERF category): the 10-minute load budget is the only threshold
- [ ] Planned NFR evidence exists or `nfr-assess` has documented CONCERNS/waivers

---

## Mitigation Plans

### R-004: Keyword search fails both kinds of ticket (Score: 6)

**Mitigation Strategy:**

1. Story 5 picks the vague and log-heavy example queries from the pinned real snapshot, as its entry already says.
2. Story 5 writes them to a committed golden-query file. Each entry records the query text, its kind, how it was chosen, its source issue and its twin issue number.
3. Story 11's integrated check asserts each twin appears in the top-k of `/v1/search` in keyword mode.
4. Story 10's sweep compares `rank` order for the golden queries before and after.
5. The file is a relevance smoke check. Retrieval quality claims come only from epic 2's CI numbers (addendum, Claim discipline).

**Owner:** Dillon (stories 5 and 11)
**Timeline:** story 5 writes the file; story 11 gates on it
**Status:** Planned
**Verification:** the four R-004 scenarios pass in `_kind-deploy` on the pinned real snapshot.
**Residual risk:** vague queries that share no words with their twin stay weak in keyword mode until epic 3. Epic 2 measures that gap across all labelled pairs.

---

## Assumptions and Dependencies

### Assumptions

1. The cluster counts as production for every epic: kind in CI until epic 5 lands (initiative Assumption).
2. A GitHub-hosted runner fits kind with both releases (epic Assumption). Story 1 proves it.
3. Page checks are HTTP-level because the page is server-rendered with no JS framework (epic Notes).

### Dependencies

1. **Story 5's entry needs a change** before it is built. It currently records the example queries in the epic's Notes. It should also write the golden-query file with each query's source issue and twin issue, and story 11's entry should assert the twins. This plan does not edit tickets.
2. Story 2's corpus-terms decision: required before story 3 publishes.

### Risks to Plan

- **Risk**: story 2 decides the text may not be republished.
  - **Impact**: story 3 stops, and every real-snapshot scenario (load, R-004, integrated check) has no data.
  - **Contingency**: the epic is replanned (story 3 Notes). The fixture-level checks from story 1 keep running.
- **Risk**: `_kind-deploy` with the real snapshot load goes over 15 minutes.
  - **Impact**: slow feedback on every PR.
  - **Contingency**: keep the P0 bring-up and R-004 checks on every PR, and move the backup and trace scenarios behind a path filter.

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
| **Epic 2 eval gate** | Reads the snapshot schema, kind and outcome, the mode registry and `exclude` | Snapshot schema validation, load checks, `/v1` contract tests (`exclude`) |
| **Epic 3 dense and hybrid** | Extends the registry, `/v1` additively, and the span tree | `/v1` contract tests, span-attribute tests, R-004 golden queries in keyword mode |
| **Epic 4 MCP server** | Calls `GET /v1/issues/{number}` and `/v1/search`; continues the AD-10 trace | `/v1` contract tests, trace E2E |
| **Epic 5 EKS** | Deploys the same two releases | P0 bring-up |
| **Epic 7 Grafana** | Derives metrics from AD-10 span attributes | Span-attribute tests |

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization
- `nfr-criteria.md` - NFR planning

### Related Documents

- PRD: none. Initiative requirements stand in: `_bmad-output/initiative-ticketscope/initiative-ticketscope.md`
- Epic: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md`
- Stories: `_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/tickets.toml`
- Architecture: `_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md`
- Tech Spec: none

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `bmad-tea-test-design`
**Version**: 4.0 (BMad v6)
