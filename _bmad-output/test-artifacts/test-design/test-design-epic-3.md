---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-08'
runScope: 'epic'
runKey: 'epic-3'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/epic-hybrid-retrieval.md
  - _bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md
  - _bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate-retrospective.md
  - _bmad-output/initiative-ticketscope/deferred-work.md
  - _bmad-output/test-artifacts/gate-waivers.md
  - src/ticketscope/core/modes.py
  - src/ticketscope/core/ports.py
  - src/ticketscope/core/fakes.py
  - src/ticketscope/core/derive.py
  - src/ticketscope/adapters/postgres.py
  - src/ticketscope/jobs/load/main.py
  - src/ticketscope/jobs/eval/main.py
  - src/ticketscope/jobs/eval/score.py
  - src/ticketscope/jobs/eval/gate.py
  - src/ticketscope/http/app.py
  - src/ticketscope/telemetry.py
  - src/ticketscope/settings.py
  - migrations/0001_init.sql
  - deploy/charts/ticketscope/values.yaml
  - .github/workflows/eval.yml
  - .github/workflows/_kind-deploy.yml
  - scripts/publish-snapshot.sh
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/nfr-criteria.md
---

# Test Design: Epic 3 - Dense and hybrid retrieval, scored against keyword

**Date:** 2026-11-08
**Author:** Dillon
**Status:** Draft

Epic slug: `epic-hybrid-retrieval`. Epic requirements R1–R5 (initiative R2, R6). Stories 3.1 to 3.8 from `tickets/tickets.toml`. Story 3.1 is the tracer. Stories 3.2 and 3.3 follow it in parallel, and 3.4 waits on the spike's model (3.3).

---

## Executive Summary

**Scope:** full test design for Epic 3, against the refined epic (`refined: true`), the adopted architecture spine (AD-1, AD-3, AD-4, AD-6 to AD-10, AD-12, AD-19 to AD-21, AD-25) and the eight entries in `tickets/tickets.toml`. Every coverage row cites the epic R ids it proves, so the end-of-epic trace can link criteria to requirements (epic-eval-gate retro, F13).

The epic file and its eight entries exist only on branch `worktree-plan-epic-3-rebased`, not yet on `main`. No epic 3 code exists. Epic 2 is closed, so `jobs.eval` scores every registered mode, `gate.py` gates Recall@10 and MRR@10 per mode and kind, and `eval/baseline.json` holds keyword only. Every scenario below is planned, and none has run.

This epic adds the first retrieval whose correctness cannot be read from the source text. Epic 2's metrics scorer has hand-computed oracles, and a committed pin test guards them. A dense or hybrid ranking has no such reference. Its numbers are committed as a baseline and "published whatever they show" (epic Description), so the plan puts the most weight on independent oracles for the ranking and for the embedding state they depend on.

**Risk Summary:**

- Total risks: 7
- High-priority risks (≥6): 3 (R-001 at 6, R-003 at 6, R-007 at 6)
- Critical categories: DATA (wrong or partial embeddings behind published scores), TECH (an oversized tracer that every later story builds on)

**Coverage Summary:**

- P0 scenarios: 28 (~17–31 hours)
- P1 scenarios: 71 (~28–57 hours)
- P2/P3 scenarios: 13 (~6–12 hours)
- **Total effort**: ~52–100 hours (~1.5–3 weeks)

---

## Not in Scope

| Item | Reasoning | Mitigation |
| ---- | --------- | ---------- |
| **Scoring and gate internals** | "Scoring and the gate belong to epic-eval-gate" (epic Boundaries). Epic 2's metric, pair and README-render tests stay as they are. | Story 3.5 adds only the three-mode rows to the gate table and the README check, and the pin test on epic 2's oracle fixture must stay green. |
| **A fixed model quality target** | The model is chosen by a scored eval (R3), and results are published "whatever they show". No test asserts a minimum Recall@k or MRR@10 for dense or hybrid. | The P0 oracle rows assert that rankings are computed correctly, not that they are good. |
| **Model fine-tuning and a second vector store** | Out in the epic Boundaries and the initiative Boundaries. | None needed. |
| **Vector index (ANN)** | "An index is added only if p95 demands it" (epic Constraints). No threshold is stated (R-005, C-4). | A P2 row records the exact scan's plan and timing. A migration that adds an index would need its own plan and the F5 reload comparison. |
| **`mcp` keys and the MCP default mode** | "Epic 4 owns the `mcp` keys" and `mcp` "has no default of its own" (epic Boundaries, AD-25). | One chart render assertion in the default-mode row: no `mcp` mode key is added. |
| **Node sizing on EKS and the dashboard panels** | Epic 5 sizes nodes from this epic's recorded needs. Epic 7 charts latency by mode. | This plan checks that the needs are recorded (R-002) and that the span shape epic 7 reads is stable. |
| **Takedown of embedding assets** | The Provenance convention says a takedown deletes "the earlier snapshot and embedding assets that hold the issue". No story owns the embedding side (C-6). | Raised as a clarification. No coverage row until a story owns it. |
| **Waiver W-001 remediation** | Epic 2's open item, owned by Dillon (epic-eval-gate retro, F1). | Not an exit criterion of this epic. |

---

## Risk Assessment

Sources were read in this order: the epic file, `tickets.toml`, the spine, epic 2's test design and retrospective, then the code named in the inputs. Each risk opens with the source's own words, then the failure consequence. IDs follow the order in which each risk's statement first appears in the epic file (Description, then Requirements, then Constraints), and `tickets.toml` after it.

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R-001 | DATA | "Epic 2's gate scores all three in CI, and the results are published whatever they show" (epic Description; R4). A dense or hybrid ranking that is wrong but plausible becomes the committed baseline, the README table and the evidence for the brief's hybrid hypothesis. No source defines a reference for the ranking itself. Mechanisms: a distance read as a score (the order inverts); an inner product where cosine is meant; the query issue not excluded or a slot lost to the exclusion (AD-19); RRF ranks counted before the exclusion, 0-based, or with the constant misapplied; a query embedded with different text, cut or prefix than the documents; a keyword-only fake that hides a missing mode. Consequence: the gate compares the code with itself, so a wrong ranking is enforced and published as a finding. | 2 | 3 | 6 | Independent oracles committed by a red-mode session before stories 3.1 and 3.2 build (section "Independent Oracles"): exact-fraction RRF, a cosine fixture, a numpy recompute of pgvector's top 10, and reference vectors for the embedder. The independent review on 3.1 checks the fixture bytes are unchanged since the red commit. | Dillon; stories 3.1, 3.2 | Fixtures before 3.1's build; fusion values before 3.2's build |
| R-003 | DATA | "Every loaded issue has an embedding from the chosen model in `issue_embedding` ... `corpus_meta` records the model id" (epic R1), and `load` "is idempotent against `corpus_meta`" (story 3.4; AD-22). `api` fails readiness on a model id difference only (epic Constraints, Readiness). Mechanisms: `load` writes issues and `corpus_meta` in one transaction today (`replace_corpus`), so embeddings written after it leave `corpus_meta` claiming a model while the table is empty or partial, and the next load is a no-op; `TRUNCATE issue` on reload fails or leaves orphan rows in `issue_embedding`; the spike loads two or three models of different dimensions into one unsized `vector` column, and pgvector raises "different vector dimensions" when a query scans another model's rows; the asset lacks an issue or carries extra ones. Consequence: dense serves a subset or errors, the eval scores that state, and the result is published. | 2 | 3 | 6 | One transaction for issues, embeddings and `corpus_meta`; an Integration row that injects each failure on a migrated Postgres container, including a second model with another dimension; the coverage rule is settled by the PO (C-5). | Dillon; stories 3.1, 3.4 | Story 3.1 (table and transaction), story 3.4 (asset) |
| R-007 | TECH | "Likely more than 800 added lines (port, adapter, migration, image, load, retriever, readiness, chart): run the independent review on it" (`tickets.toml`, story 3.1 notes). Story 3.1 also "owns the shared setup" for the other seven stories. The same flag was set on epic 2's story 2.1 and not evidenced: its plan shows `review: quick` with no second reviewer, and epic 1's retro action 9 (trigger the review by diff size) has "no evidence found" (epic-eval-gate retro, F15 and follow-through 9). Consequence: a defect in the Embedder port, the migration, the image bake or the readiness check reaches every later story, and the flag does nothing. | 3 | 2 | 6 | Story 3.1 keeps `plan_checkpoint = true`. A red-mode session writes its acceptance tests first. A person confirms the independent review ran (a named reviewer or lens list in the plan), or splits the story at the plan checkpoint. | Dillon; story 3.1 | Before 3.1 merges |

Score rationale:

- **R-001:** probability 2, because the oracles and the pin-test pattern from epic 2 are known and the dense path has few definitional choices. Impact 3, because wrong scores are committed, gated against and published, and R6, the part that survives a cut, is exactly these numbers.
- **R-003:** probability 2, because the single-transaction `replace_corpus` is the starting point and the spine names the id check, but the new table, the second model and the asset path are all unbuilt. Impact 3, because the failure is silent and its output is the published table.
- **R-007:** probability 3, because the review control was set twice and not wired once. Impact 2, because the later stories and the integrated check would catch most defects, at a later cost.

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-002 | PERF | "The model's CPU and memory needs set the chart defaults that epic 5 sizes nodes for" (epic Description; R5). Story 3.1 raises `api`'s memory limit "just enough to load the model" before any measurement; `values.yaml` has 256Mi for `api` and 512Mi for every Job today. The eval Job also embeds each query live, and the epic says "Only `api` loads it at runtime", so the Job's limit is also unmeasured (C-2). Consequence: `api` or the eval Job is OOM-killed on kind, so the required check goes red, or epic 5 sizes nodes from a wrong number. | 2 | 2 | 4 | The spike records peak memory in `api` and in the embedding step (story 3.3); story 3.6 sets the limits from the measurement; a kind row asserts no OOM kill under dense and hybrid load. | Dillon; stories 3.3, 3.6 |
| R-004 | TECH | "A person builds it with the committed publish script" (epic Constraints, Embedding asset) and "the eval job embeds each query's text live through the same `Embedder`" (Eval). Document vectors come from a person's machine, and query vectors from a CI runner of another CPU or architecture (AD-16 builds amd64 and arm64). Epic 2's retro records 2 of 10,473 ranks moving after a reload and says "if epic 3 adds vector indexes, re-run the reload comparison for each new mode" (F5). With 309 log-heavy pairs, one flipped query moves a metric by about 0.0032, so two flips pass the 0.005 tolerance. Consequence: the required `eval` check flaps on unchanged code, or a baseline built on one machine fails on the runner. | 2 | 2 | 4 | A parity and determinism row: asset vectors against a recompute inside the CI image, two fresh processes with identical bytes, and the F5 reload comparison for dense and hybrid. | Dillon; stories 3.4, 3.5 |
| R-006 | PERF | "The run's cost is checked against the Job deadline, and the deadline is raised if needed" (epic Constraints, Eval). The eval Job's `activeDeadlineSeconds` is 1800 and `_kind-deploy.yml` allows 45 minutes. Epic 2 measured 14 minutes 37 seconds for keyword only (retro F8). Dense and hybrid add 20,946 live query embeddings and two more scans of 10,473 queries. The added time is UNKNOWN. Consequence: the required check times out on every PR, and the workaround is an edit that the same check blocks. | 2 | 2 | 4 | Story 3.5 records the Job's `wall_seconds` and the job duration, then sets the deadline and workflow timeout from the record. | Dillon; story 3.5 |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |
| R-005 | PERF | "Dense search is an exact scan with no index ... An index is added only if p95 demands it" (epic Constraints, Table). No p95 threshold is stated, and `api` runs one replica on 50m CPU requests. Consequence: slow dense or hybrid searches on the live URL, with no number that triggers the index decision. p95 is reported and never gated (AD-12), so the harm is bounded. | 2 | 1 | 2 | Record dense and hybrid p95 and the plan on a synthetic corpus of the loaded size. The threshold is UNKNOWN (C-4). |

### Clarifications for the PO (not scored)

The sources are silent or disagree on these points. This plan tests the stated assumption, and "Proposed Story Updates" carries the wording to the PO.

- **C-1, readiness on a keyword-only deployment.** Epic Constraints: "`api` fails readiness when its configured model id differs from `corpus_meta.embedding_model_id`". Story 3.1 says "CI stays keyword-only: the default load computes nothing", so `corpus_meta.embedding_model_id` stays null in CI. *Assumption:* with no model configured and a null id, `api` is Ready and dense is unavailable; with a model configured and a null id, `api` is not Ready.
- **C-2, who loads the model.** Epic Constraints say "Only `api` loads it at runtime (spine AD-3)". The same section says the eval Job embeds queries live. AD-3 says `api` is the only *long-running* process that loads it. *Assumption:* the eval Job loads the model too, so `jobs.resources` must hold it, and story 3.6 sizes it.
- **C-3, fusion and query text.** "A fixed constant" for RRF is not given, and the sources do not say whether ranks count before or after the exclusion. The Preprocessing constraint cuts a *document* to the model's token limit, while eval's `query_text` is the title plus the full body today. *Assumption:* constant 60; ranks are positions in each side's list with the excluded issue removed; the query gets the same preprocessing as a document. The oracle takes the constant as a parameter.
- **C-4, p95 threshold and tie.** (a) No dense or hybrid p95 budget exists, so the index decision has no trigger. (b) "Hybrid on a tie" for the default mode does not say how close two MRR@10 values must be. *Assumption:* a tie is a difference under the gate tolerance of 0.005, matching `gate.py`.
- **C-5, partial asset and coverage.** The sources do not say what `load` does when the pinned asset lacks an issue, carries an extra one, or holds another dimension, nor whether readiness checks row coverage. *Assumption:* `load` fails and keeps the previous state; readiness stays keyed on the model id, and `dense` is unavailable when coverage is short.
- **C-6, takedown of embedding assets.** The Provenance convention names embedding assets in a takedown. Story 3.4 "never overwrites" and has no takedown step. *Assumption:* out of scope here; a takedown ticket owns it.
- **C-7, unavailable modes and model identity.** (a) The sources do not say what `/v1/search` returns for a registered mode that is unavailable, or for an unavailable default mode (the current handler builds the retriever without calling `available`). *Assumption:* 503 problem+json for an unavailable mode, and `api` not Ready when the default mode is unavailable. (b) "Model id" is a string such as `BAAI/bge-small-en-v1.5`; fastembed ships its own ONNX export, and a revision or runtime bump changes vectors under the same id. *Assumption:* the findings file and the asset manifest record the model file's SHA-256 beside the id.

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
| Security and compliance | Embedding assets hold no text or person identifier (Provenance). `api` and `eval` read `issue_embedding` as `ticketscope_ro` and cannot write it (AD-7). The Hugging Face source is read at build time only. | - | Integration: asset schema and source checks; the read-only role; the image runs with no network. | Test report; asset manifest; image run log |
| Performance | Dense and hybrid p95 is reported, never gated (AD-12); the index trigger is UNKNOWN. `load` stays under 600 s with the asset (story 3.4, publish guard). `api` and Job resources come from measurement. The eval run fits the Job deadline. | R-002, R-005, R-006 | Integration: exact-scan plan and timing on a synthetic corpus. E2E: p95, `wall_seconds`, peak memory and the timed load in the artifact and job summary. | Results artifact; job summary; spike findings |
| Reliability | Rankings reproduce across runs and machines within the 0.005 tolerance. A load is all-or-nothing and idempotent. `api` is Ready only on a matching model. | R-003, R-004 | Integration: failure injection on `load`; two fresh-process embeds; the F5 reload comparison. API: readiness cases. | CI test report; `eval.yml` run logs |
| Maintainability | `core` imports no embedding runtime (AD-1, import-linter). One source of truth for the model id and preprocessing version. New modes need no change to `jobs.eval` (AD-19). No `time.sleep` in `tests/`. | R-001, R-007 | Unit: layering and single-source parse tests; the fake-mode registry test already in `tests/unit`. CI: `lint-imports`. | CI test report |

**Unknown thresholds:**

- dense and hybrid p95 budget, and the point at which an index is added (C-4);
- `api` and Job memory and CPU for the chosen model (R-002; set by stories 3.3 and 3.6);
- the eval run's added wall-clock time, and the margin the Job deadline needs (R-006);
- the maximum image size growth from the baked model;
- the tie width for the default mode (C-4).

Stories 3.3 and 3.5 produce the first recorded values.

---

## Independent Oracles

Risk R-001 exists because a ranking and the tests written in the same session can agree on a wrong answer. Each check below uses a reference that does not come from the code under test.

**Protocol:**

1. Before story 3.1's build, a `/bmad-tea-automate` red-mode session commits the cosine fixture and the embedder reference vectors. Before story 3.2's build, it commits the fusion fixture. The build session does not author them.
2. Expected values are exact fractions (`fractions.Fraction`) and compared to floats within 1e-9. A pin test guards the fixture bytes, as `tests/unit/test_eval_oracle_pinned.py` does for epic 2.
3. The independent review on story 3.1 checks the fixtures are unchanged since the red commit. Any change in a later diff is a review finding.

**Cosine fixture** (query vector `(1, 0)`; vectors are 2-dimensional, which the unsized column allows):

| Issue | Vector | Cosine to the query | Expected dense order |
| ----- | ------ | ------------------- | -------------------- |
| 1 | `(1, 0)` | 1 | 1st |
| 2 | `(1, 1)` | 1/√2 ≈ 0.7071 | 2nd |
| 3 | `(0, 1)` | 0 | 3rd |
| 4 | `(-1, 0)` | -1 | 4th |

`score_kind` is `cosine` and `score` is higher-is-better (AD-4). A distance returned as the score reverses the order. An inner product gives issues 1 and 2 both a score of 1.

**Fusion fixture** (RRF with constant 60 and equal weights; C-3). Keyword ranking `[A, B, C, D]`, dense ranking `[C, A, E, B]`:

| Issue | Keyword rank | Dense rank | Exact score |
| ----- | ------------ | ---------- | ----------- |
| A | 1 | 2 | 1/61 + 1/62 = 123/3782 |
| C | 3 | 1 | 1/63 + 1/61 = 124/3843 |
| B | 2 | 4 | 1/62 + 1/64 = 63/1984 |
| E | - | 3 | 1/63 |
| D | 4 | - | 1/64 |

Expected fused order: `[A, C, B, E, D]`. Issue C ranks first in dense and third in keyword, and it falls behind A, which is near the top of both.

| Case | Setup | Expected |
| ---- | ----- | -------- |
| Tie | Issue 7 is keyword rank 5 only, and issue 3 is dense rank 5 only; both score 1/65 | Issue 3 before issue 7 (tie broken by issue number) |
| Exclusion keeps the slot | `k = 2`, `exclude = {9}`; each side returns 3 candidates: keyword `[9, B, C]`, dense `[C, 9, E]` | Ranks count after removal: keyword `[B, C]`, dense `[C, E]`; scores B = 1/61, C = 123/3782, E = 1/62; result `[C, B]`, two results |
| Short sides | `k = 10`, keyword 2 hits, dense 1 hit | Union of the hits, in fused order, no padding |

**Other oracles:**

| What is checked | Independent oracle | Row |
| --------------- | ------------------ | --- |
| pgvector returns the true nearest neighbours | A numpy brute-force cosine over the same vectors, on a seeded synthetic corpus and on 200 sampled issues of the real asset | P0 Integration (B) |
| The embedder implements the model | Reference vectors for five committed sentences, produced by the model's reference implementation outside the repo's code path; cosine ≥ 0.999 (threshold proposed) | P0 Integration (B) |
| Query and document text share one preprocessing | A case where an issue's embedding text equals its live query text after the cut (C-3; Preprocessing constraint) | P0 Unit (A) |
| The loaded state matches `corpus_meta` | `count(issue_embedding)` for the model against `count(issue)`, read separately with `psql` on kind | P0 Integration (C); P1 E2E |
| Asset against the image | The asset's recorded vectors for sampled issues against a recompute inside the built app image | P1 Integration (drift) |
| Default mode | `eval/baseline.json`, read by a separate script, gives the mode with the best overall MRR@10 | P2 default-mode row |

---

## Entry Criteria

- [x] Architecture spine adopted (AD-1 to AD-26)
- [x] Epic refined, with eight entries planned in `tickets.toml`
- [x] Epic 2 closed, so `eval/baseline.json` has one editor (epic Notes, Decision 2026-11-08)
- [ ] Branch `worktree-plan-epic-3-rebased` merged to `main`, so the epic file and entries are on `main`
- [ ] C-1, C-2, C-3, C-5 and C-7 answered by the PO, or the stated assumptions accepted
- [ ] The cosine fixture and embedder reference vectors committed by a red-mode session before story 3.1's build, and the fusion fixture before story 3.2's build
- [ ] The independent review for story 3.1 named in its plan (R-007)

## Exit Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing (or failures triaged)
- [ ] No open high-priority / high-severity bugs
- [ ] `eval.yml` passes on a PR with keyword, dense and hybrid in the artifact, and `ci.yml`'s integrated-check passes on the same PR head
- [ ] `eval/baseline.json` carries all three modes with the chosen model id and preprocessing version in its lineage
- [ ] R-001, R-003 and R-007 mitigations complete
- [ ] The findings file, `values.yaml`, the image bake, the asset name and the baseline lineage name the same model (single-source row)

---

## Test Coverage Plan

P0, P1, P2 and P3 are priorities, not execution timing. The Execution Strategy section decides when each test runs. The Owner column names the story whose build writes the test. The R ids column names the epic requirements each row proves. Test Level uses the template's canonical names: Unit, Integration, API and E2E. Here, E2E means a run on kind through `_kind-deploy.yml`, and API means `/v1` through the app factory with the in-repo fakes.

### P0 (Critical)

**Criteria**: Critical business, security, data-integrity, or compliance impact with no safe
workaround. Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| (A) Dense and hybrid ranking logic equals the hand-computed oracles | R2, R4 | Unit | R-001 | 10 | Stories 3.1, 3.2 | Mechanism: the ranking code and its tests share one wrong reading. Boundary: none; `core` modes over the in-memory store and the hash `Embedder`, so Unit. Scenarios, on the fixtures in "Independent Oracles": (1) cosine fixture order `[1, 2, 3, 4]` with scores 1, 0.7071, 0, -1. (2) A distance returned as the score fails (1). (3) An inner product fails (1): issues 1 and 2 would both score 1. (4) Fusion fixture order `[A, C, B, E, D]` with the exact fractions. (5) Tie broken by issue number. (6) Exclusion keeps the slot: `[C, B]`. (7) `k` larger than either side's hits. (8) Hybrid is available only when keyword and dense are, and is absent from the results when dense is not (`skipped_modes`). (9) Fusion takes at least `k + |exclude|` candidates from each side (a spy store records the requested count). (10) An issue's embedding text equals its live query text after the same cut, and the cut is part of the preprocessing version. Consequence: wrong rankings become the baseline and the published table. Workaround: none; the gate compares the code with itself. |
| (B) pgvector and the embedder match independent recomputes through the real adapter | R2, R4 | Integration | - | 6 | Stories 3.1, 3.2 | Boundary: Postgres with pgvector, through `PostgresCorpusStore`, on a migrated container from the in-repo image. Scenarios: (1) cosine fixture through SQL gives the same order and scores as the Unit fixture. (2) pgvector's top 10 equals numpy's for 200 seeded queries over 2,000 vectors of 384 dimensions, ties broken by issue number. (3) The query issue is excluded and the 10 slots stay filled. (4) Hybrid through the real adapter equals the hand-computed fusion of the real keyword and dense lists for a seeded pair. (5) Reference vectors for the five sentences from the baked model: cosine ≥ 0.999 each. (6) Long input is cut to the model's token limit and the result equals the embedding of the manually cut text. Consequence and workaround: as row (A). |
| (C) Embedding state is consistent with `corpus_meta` and survives failure | R1 | Integration | R-003 | 8 | Stories 3.1, 3.4 | Mechanism: `corpus_meta` is written apart from the embeddings, or other models' rows share the column. Boundary: one owned store (Postgres) and one file (the asset), so Integration. Scenarios: (1) `load` with the pinned asset gives exactly one `issue_embedding` row per loaded issue for the model, `corpus_meta.embedding_model_id` set, and an `Embedder` fake that fails the test if called. (2) A second `load` is a no-op (`reload_reason` is `None`). (3) A failure after issues are copied (a truncated asset, a bad row) rolls back issues, embeddings and `corpus_meta` together, and the previous corpus answers. (4) A wrong checksum fails with its reason and changes nothing. (5) Rows of another model with another dimension sit beside the pinned model's, inserted both before and after; `dense_search` for the pinned model returns results and no dimension error. (6) A reload to a new snapshot leaves no embedding for an issue that left the corpus, and `TRUNCATE issue` does not fail on the new table. (7) A changed preprocessing version forces a reload even when snapshot and model match (AD-21). (8) An asset with a missing or extra issue, or a wrong dimension, fails the load and keeps the previous state (C-5). Consequence: dense serves a subset or errors, silently, and the scores are published. Workaround: a manual `corpus_meta` reset; the state shows no failure until the table is read. |
| (D) The embedding asset holds no text or person identifier | R1 | Integration | - | 4 | Story 3.4 | Compliance: the Provenance convention lists embedding assets among artifacts that must carry no identifiers, and a published Release asset may be cached or indexed even after deletion. Boundary: the publish script reads one file and writes one file. Scenarios: (1) the script's input is the checksum-verified published snapshot asset, never the raw dump. (2) Every asset record holds only the issue number, model id and vector; no title, body, key, URL or author. (3) Every text field in the asset's manifest and notes passes the mask sweep (no `[~user]`, email or secret pattern). (4) The Release notes carry the attribution line. Consequence: an irreversible publication of identifiers. Workaround: a takedown deletes the asset, but the copy may remain cached (C-6). |

**Total P0**: 28 tests, ~17–31 hours

### P1 (High)

**Criteria**: Core, frequent, or complex behavior with material user reach and a limited workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| `/v1/search` serves dense and hybrid under the existing contract | R2, R5 | API | - | 7 | Stories 3.1, 3.2, 3.6 | Boundary: the HTTP contract of `api`. Scenarios: (1) `mode=dense` and `mode=hybrid` return ranked results with outcomes, `score_kind` `cosine` and `rrf`, and `corpus_version`, for a vague query and a log-heavy query (the real answer on kind is in the integrated row). (2) A request that omits `mode` gets the configured default's `score_kind`, including a default of `hybrid`. (3) An unknown mode returns 422 problem+json. (4) A registered but unavailable mode returns 503 problem+json, not 500 (C-7). (5) An unavailable default mode makes `api` not Ready (C-7). (6) Keyword responses are byte-identical to epic 1's golden bodies, so the change is additive (AD-4, AD-20). (7) The search page still answers with keyword (`PAGE_MODE`). Consequence: callers see a 500 or a changed shape. Workaround: request keyword. |
| Readiness follows the model id | R1, R5 | API | - | 4 | Story 3.1 | Boundary: `/readyz` of `api`. Scenarios (C-1): (1) configured model equals `corpus_meta.embedding_model_id` → Ready. (2) A different id → 503 with the reason. (3) No model configured and a null id (the CI keyword-only path) → Ready, and keyword works. (4) A model configured and a null id → not Ready. Consequence: CI goes red on the keyword-only path, or `api` serves dense with the wrong model. Workaround: align the values. |
| Embedding drift between where the asset is built and where queries are embedded | R1, R4 | Integration | R-004 | 5 | Stories 3.4, 3.5 | Mechanism: different CPU, architecture, runtime version or model file between the person's machine and the runner. Boundary: the asset file against the built app image, so Integration. Scenarios: (1) for 200 sampled issues, the asset's vector against a recompute inside the CI app image: cosine ≥ 0.9999 (threshold proposed). (2) Top-10 lists from the asset vectors and from the recomputed vectors are identical for 50 sampled queries. (3) Two fresh processes embed the same 20 texts to identical bytes. (4) The asset manifest records the model file's SHA-256 and the runtime versions, and the image's model file matches (C-7). (5) The F5 comparison: two forced reloads and eval runs on the same snapshot give dense and hybrid metrics within 0.001. Consequence: the required check flaps, or a baseline fails on the runner. Workaround: re-run; merges wait. |
| Spans keep the AD-10 contract | R2 | API | - | 6 | Stories 3.1, 3.2 | Boundary: the app factory with an in-memory span exporter. Scenarios: (1) dense emits `retrieval dense` with an `embeddings {model}` child and `gen_ai.request.model`. (2) Hybrid emits one `retrieval hybrid` span with the embeddings span and the database query spans as children, and no nested `retrieval {mode}` span, which would double-count in epic 7's `spanmetrics`. (3) The `embeddings` span is emitted by the adapter, and `core` imports no telemetry (import-linter). (4) No span carries query text unless `trace_query_text` is set. (5) `/readyz` and the eval Job stay untraced. (6) An embedding error sets span status ERROR. Consequence: epic 7's latency by mode breaks. Workaround: change the span code. |
| One source of truth for the model and the preprocessing version | R1, R3, R5 | Unit | - | 5 | Stories 3.3, 3.4, 3.6 | Boundary: parse tests over files. Scenarios: (1) the chosen model id in the findings file's Decision line equals the app image's build argument, `api`'s settings, the asset name and the asset pin in `values.yaml`. (2) The preprocessing version in `values.yaml`, the asset name and `corpus_meta` come from the same function. (3) The baseline lineage equals both. (4) A one-line model change (the spike's follow-up) touches one value. (5) The model's file SHA-256 is recorded in the findings file (C-7). Consequence: a model swap leaves one place stale and readiness fails late. Workaround: edit the stale value. |
| The image bakes the model and runs with no network | R1 | Integration | - | 3 | Story 3.1 | Boundary: one container. Scenarios: (1) the app image embeds a text with the network disabled and `HF_HUB_OFFLINE=1`. (2) The Dockerfile reads the Hugging Face source only in a build stage. (3) The image size is recorded and compared with epic 2's image (budget UNKNOWN). Consequence: pods fail or download at run time. Workaround: rebuild the image. |
| The asset pin and the publish script keep their guards | R1 | Unit | - | 6 | Story 3.4 | Boundary: files and the script, run against a temporary git repository as `tests/unit/test_publish_script.py` does for the snapshot script. Scenarios: (1) `values.yaml` pins the asset version and SHA-256 beside the snapshot pin, through the shared pin parser, and no environment file overrides it (AD-25). (2) The script refuses a branch other than `main` and an unclean checkout. (3) It never overwrites an existing asset. (4) The asset name carries snapshot, model and preprocessing. (5) The generated notes carry the commit, counts and attribution. (6) The pin test fails on an empty checksum. Consequence: an unpinned or overwritten asset. Workaround: publish the next version. |
| The timed load with the asset stays under 10 minutes | R1 | Integration | - | 2 | Story 3.4 | Boundary: a Postgres container from the in-repo image, as `scripts/time-load.sh` does. Scenarios: (1) `load` of the pinned asset at about 32,000 issues × 384 dimensions finishes within 600 s (`BUDGET_SECONDS`). (2) The `load report:` line carries the time and `within_budget=true`. Consequence: the spin-up budget is spent on load. Workaround: none after the script's guard passes. |
| Readable by the read-only role, writable only by `load` | R1, R2 | Integration | - | 2 | Story 3.1 | Boundary: Postgres roles (AD-7). Scenarios: (1) `dense_search` succeeds as `ticketscope_ro` on the new table, without a per-table grant (default privileges from migration 0001). (2) An `INSERT` into `issue_embedding` as `ticketscope_ro` fails. Consequence: `api` and eval cannot read the table. Workaround: add a grant. |
| The gate and the README handle three modes | R4 | Unit | - | 7 | Story 3.5 | Boundary: pure functions over results JSON, plus the README check. Scenarios, added to epic 2's decision table: (1) a run with dense and hybrid, a baseline without them → both pass and are reported as new modes (the first PR). (2) A baseline with all three, and a run where dense is skipped as unavailable → fail with "missing from this run". (3) Dense log-heavy MRR@10 drops 0.006 → fail. (4) The embedding model id changes without a baseline update → fail, naming the field. (5) A changed baseline equal to the run, with all three modes → pass. (6) A hand-edited dense value in the baseline → fail. (7) The README check renders three mode rows by kind and fails a hand edit. Consequence: a regressing dense ranking merges, or a missing mode passes. Workaround: a reviewer reads the artifact. |
| `eval.yml` scores keyword, dense and hybrid on a PR | R4 | E2E | - | 5 | Story 3.5 | Boundary: workflow, chart and cluster. Scenarios: (1) the artifact holds Recall@1, @5, @10, MRR@10 and p95 for each mode, split short, log-heavy and overall, with `pairs_scored` 10,473 and 309 for every mode. (2) The lineage holds the chosen model id and the preprocessing version, equal to the `corpus_meta` row read with `psql`. (3) A throwaway PR that regresses the dense ranking fails the check; the same PR passes once it updates the baseline. Run URLs go in the story plan (epic-eval-gate retro, F3). (4) The baseline commit follows a CI run, as epic 2's PR #29 did. (5) The artifact is uploaded when a later step fails. Consequence: no CI-produced three-mode numbers. Workaround: none in CI. |
| `api` and the Jobs run inside the chart's measured resources | R5 | E2E | R-002 | 5 | Stories 3.3, 3.6 | Mechanism: limits set before measurement. Boundary: pods on kind. Scenarios: (1) `api` is Ready under the new limits. (2) After 200 dense and hybrid searches, `restartCount` is 0 and no container state is `OOMKilled`. (3) The eval Job completes under its memory limit (C-2). (4) `values.yaml` comments name the measured peak memory and the embedding time. (5) The limits exceed the spike's measured peak by a margin the story states (UNKNOWN until 3.3). Consequence: a crash loop on kind, or a wrong number for epic 5. Workaround: raise the limit. |
| Story 3.1's shared setup works on a fresh and an existing cluster | R1, R2 | E2E | R-007 | 5 | Story 3.1 | Mechanism: an oversized tracer breaks wiring other stories rely on. Boundary: image, chart, migration and cluster. Dense runs on kind only locally until story 3.4 (CI is keyword-only). Scenarios: (1) with the compute flag on, `load` computes embeddings and a dense search returns ranked issues. (2) With the flag off (default), `load` computes nothing, `api` is Ready, and dense is unavailable, as in CI. (3) An in-place upgrade from the epic 2 release: `migrate` applies the new migration, the changed preprocessing version forces a reload, `api` rolls and is Ready. (4) A second `load` is a no-op. (5) `ci.yml`'s integrated-check and `eval.yml` pass on the PR head, with `eval/baseline.json` unchanged. Consequence: a defect reaches every later story. Workaround: fix on the next story. |
| The closing integrated check covers each Done when line | R1, R2, R3, R4, R5 | E2E | - | 6 | Story 3.8 | Boundary: a fresh kind cluster in CI. The row asserts wiring only, because lower rows hold the logic. Scenarios: (1) `load` fills `issue_embedding` from the pinned asset with no embedding computed (the log has no compute line), and the count equals the issue count. (2) Dense and hybrid answer a vague query and a log-heavy query with ranked issues and outcomes. (3) A request with no `mode` returns the default's `score_kind`. (4) A `helm upgrade` with a different model id makes `api` not Ready. (5) The eval artifact holds all three modes. (6) The spike's findings file and the epic Decision line exist. Consequence: the epic is unproved on the cluster. Workaround: none. |
| The refactor sweep changes no behaviour or score | R2, R4 | E2E | - | 3 | Story 3.7 | On story 3.7's PR: (1) the eval check passes and `git diff` of `eval/baseline.json` against the base is empty. (2) `ci.yml` and its integrated-check pass. (3) `lint-imports` keeps every contract. Consequence: a silent score change. Workaround: revert. |

**Total P1**: 71 tests, ~28–57 hours

### P2 (Medium)

**Criteria**: Secondary behavior with narrower user reach and an acceptable workaround. Risk score
is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| Dense search is an exact scan, and its timing is recorded | R2 | Integration | R-005 | 3 | Story 3.1 | Mechanism: no stated p95 trigger for an index. Boundary: the Postgres query. Scenarios: (1) `EXPLAIN` shows a sequential scan ordered by distance then issue number, and the migration creates no vector index. (2) On a seeded corpus of the loaded size, dense and hybrid p95 are recorded (no threshold; C-4). (3) The query filters by `model_id`. Consequence: slow searches with no trigger. Workaround: p95 is reported, so a later epic adds the index. |
| The eval run's wall-clock cost is recorded and fits its limits | R4 | E2E | R-006 | 2 | Story 3.5 | Mechanism: 20,946 live embeddings and two more scans inside a 45-minute job. Boundary: the Job on kind. Scenarios: (1) `wall_seconds` and the job duration are in the artifact and the job summary. (2) `activeDeadlineSeconds` and the workflow timeout exceed the recorded duration; the margin is UNKNOWN until the first run. Consequence: a timed-out required check. Workaround: the epic states the deadline is raised if needed, so P2. |
| The spike's findings file is complete | R3 | Unit | - | 3 | Story 3.3 | A parse test: (1) the table lists each candidate with Recall@10 and MRR@10 by kind and overall, embedding time per issue and for the snapshot, peak memory in `api` and in the embedding step, and image size. (2) A chosen model id, preprocessing version and reason are named. (3) The hardware used is stated, so the numbers are comparable. Consequence: a model chosen without evidence. Workaround: redo the spike. |
| The default mode is the best overall MRR@10 | R5 | Unit | - | 4 | Story 3.6 | A parse test over `eval/baseline.json` and `values.yaml`: (1) `retrieval.defaultMode` equals the mode with the best overall MRR@10. (2) A difference under 0.005 is a tie and gives `hybrid` (C-4). (3) The default is in the registry. (4) No `mcp` mode key exists in the chart. Consequence: users get a worse default. Workaround: change one value. |

**Total P2**: 12 tests, ~6–12 hours

### P3 (Low)

**Criteria**: Rare, cosmetic, or experimental behavior with minimal impact and an easy workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| Outward README text avoids "vector database" without a claims-ledger row | R4 | Unit | - | 1 | Story 3.5 | A text check in `ci.yml`'s `checks` job (Wording convention). Workaround: review catches it. |

**Total P3**: 1 test, ~0.5 hours

Why the bands look like this:

- **P0.** Only ranking correctness, the embedding state and the asset's content are P0. A wrong ranking or a partial state is a data-integrity failure that no later check sees, because the gate compares the code with itself and the epic publishes the result. The asset row is a compliance failure that cannot be fully undone once published.
- **P1 for the contract, drift and resources.** Each is recoverable by an edit or a re-run, with material reach (every dense request, the required check, the pods).
- **P1 for the tracer.** R-007's row is P1: the harm is a defect that later stories and the integrated check catch, at a cost.
- **P2 for the plan, cost, findings and default.** Each has an explicit remedy in the sources: p95 is reported only, the epic says the deadline is raised if needed, and a wrong default is one value.

P0 count per story: stories 3.1 and 3.2 share rows (A) and (B) with 16; story 3.1 and 3.4 share row (C) with 8; story 3.4 has row (D) with 4; stories 3.3, 3.5, 3.6, 3.7 and 3.8 have none.

---

## Execution Strategy

**Philosophy:** Run every functional scenario in pull requests while the suite stays under 15 minutes.
Defer only work with material infrastructure or duration cost. P0 through P3 are priority and are not
execution timing; this section decides when tests run and the coverage plan above decides what they are.

- **Pull request, `ci.yml`:**
  - `checks` runs ruff, pyright, import-linter and every Unit, API and Integration test that needs no model: the fusion and cosine oracles, `/v1` and readiness cases, the span tests, the gate and README tests, chart render tests and the Postgres-container tests with the fake `Embedder`.
  - The model-dependent Integration rows (reference vectors, drift, offline run) run inside the built app image, because the model is baked into it and a runtime download is not allowed. Where they run (the image job or `integrated-check`) is UNKNOWN until story 3.1 builds the image.
  - `integrated-check` stays keyword-only until story 3.4 pins the asset, then loads it.
- **Pull request, `eval.yml`:**
  - Brings up kind, runs the eval Job with all three modes, then the gate. The E2E rows for stories 3.5, 3.6 and 3.8 run here. Combined duration with `ci.yml` is UNKNOWN until story 3.5 records it (R-006).
- **Local, stories 3.1 to 3.3:** dense on kind needs `load` to compute embeddings, which CI never does, and the spike runs the eval for each candidate model on a person's machine. Their run output is the evidence.
- **One-off, story 3.4 and story 3.5:** a person runs the publish script and merges the pin. Throwaway PRs show a regressed dense ranking failing and passing with a baseline update. Run URLs are the evidence.
- **Nightly:** none planned.
- **Weekly:** none planned.

Do not re-list the individual tests here. They are already in the coverage plan.

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 28 | 0.6–1.1 | ~17–31 | The three oracle fixtures by hand, the failure-injection harness for `load`, and the numpy recompute are the main cost |
| P1 | 71 | 0.4–0.8 | ~28–57 | Most rows are cheap with the fakes; the kind rows, the image-based rows and the throwaway PRs are not |
| P2 | 12 | 0.5–1.0 | ~6–12 | Mostly reading the first recorded runs |
| P3 | 1 | 0.25–0.5 | ~0.5 | One text check |
| **Total** | **112** | **-** | **~52–100** | **~1.5–3 weeks** |

### Prerequisites

**Test Data:**

- The cosine and fusion fixtures with exact-fraction expected values (red-mode session, before stories 3.1 and 3.2).
- Reference vectors for five sentences, from the model's reference implementation (before story 3.1).
- A seeded synthetic corpus: 2,000 vectors of 384 dimensions for the numpy comparison, and a corpus of the loaded size for timing.
- Rows of a second model with another dimension, for the dimension-error case.
- The pinned snapshot asset, the published embedding asset and its SHA-256 (after story 3.4).
- Gate fixture result JSONs for three modes, including a skipped dense mode.

**Tooling:**

- pytest, ruff, pyright, import-linter, `helm template` (installed here; chart render tests run).
- numpy as a dev-only dependency for the independent recompute (proposed).
- `kubectl wait` and `tests/waiting.py`'s `eventually` for every wait on kind; `tests/unit/test_no_sleep_in_tests.py` guards `time.sleep`.
- An in-memory OTel span exporter for the span rows.

**Environment:**

- kind through `scripts/kind-up.sh` and `_kind-deploy.yml`, with a flag that turns embedding computation on for local runs only.
- A Postgres container from the in-repo image (pgvector included) for Integration rows.
- A runner or image without network access for the offline row.

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths**: ≥80% (snapshot → asset → `load` → `issue_embedding` → dense and hybrid → `/v1` → eval Job → gate → README)
- **Security and compliance scenarios**: 100% (the asset's content, the read-only role and the offline image)
- **Business logic**: ≥90% of the new `core` modes and fusion functions, because they are the thing under test
- **Edge cases**: ≥50%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Compliance tests for the embedding asset pass 100% (no SEC risk is open for this epic)
- [ ] Performance targets met (PERF category): no gated threshold; p95, wall clock and peak memory are recorded
- [ ] Planned NFR evidence exists or `nfr-assess` has documented CONCERNS/waivers

---

## Mitigation Plans

### R-001: Wrong dense or hybrid rankings published (Score: 6)

**Mitigation Strategy:**

1. A red-mode session commits the cosine fixture and the embedder reference vectors before story 3.1's build, and the fusion fixture before story 3.2's build.
2. The oracles separate the common mistakes: a distance as the score, an inner product, ranks counted before the exclusion, a lost slot, a missing tie-break.
3. A numpy recompute checks pgvector's top 10, and the reference vectors check the embedder.
4. One preprocessing function serves documents and queries, and a test shows the two texts match after the cut.
5. A pin test guards the fixture bytes, and the independent review on story 3.1 checks them.

**Owner:** Dillon (stories 3.1 and 3.2)
**Timeline:** fixtures before each build
**Status:** Planned
**Verification:** rows (A) and (B) pass against values the build session did not author.
**Residual risk:** C-3 (the RRF constant and the rank rule) is an assumption; a wrong answer would be encoded in the code and the oracle alike. The oracle checks the mechanics, not the quality of the chosen model.

### R-003: Partial or mismatched embeddings behind a matching `corpus_meta` (Score: 6)

**Mitigation Strategy:**

1. `load` writes issues, embeddings and `corpus_meta` in one transaction, and a failure keeps the previous state.
2. The asset's coverage and dimension are checked before the transaction commits (C-5).
3. Queries filter by `model_id` before the distance is computed, tested with a second model of another dimension.
4. Row (C) injects each failure on a migrated container.

**Owner:** Dillon (stories 3.1 and 3.4)
**Timeline:** story 3.1 for the table and transaction; story 3.4 for the asset path
**Status:** Planned
**Verification:** row (C) passes, and the integrated check shows `count(issue_embedding)` equal to `count(issue)` on kind.
**Residual risk:** readiness is keyed on the model id, so a hand-edited table is not detected until C-5 is settled.

### R-007: The oversized tracer ships unreviewed (Score: 6)

**Mitigation Strategy:**

1. Story 3.1 keeps `plan_checkpoint = true`, and the plan names the independent review before the build.
2. A red-mode session writes the acceptance tests first, so the build does not author its own oracle.
3. If the plan estimates well over 800 lines, split at the checkpoint: the Embedder port and migration first, then the retriever and readiness.
4. A person confirms in the PR that the review ran (reviewer or lens list), since the loop does not trigger it by size (epic-eval-gate retro, follow-through 9).

**Owner:** Dillon (story 3.1)
**Timeline:** before 3.1 merges
**Status:** Planned
**Verification:** the plan lists the reviewer and the findings, and the tracer row passes on an existing cluster.
**Residual risk:** the size trigger stays unwired in the loop; this epic relies on a person's check.

---

## Assumptions and Dependencies

### Assumptions

1. C-1 to C-7 hold as stated under "Clarifications for the PO".
2. kind in CI is production for this epic (initiative Assumption, carried from epics 1 and 2).
3. The embedding model, once chosen, is a small CPU model that fits `api` and the Jobs within limits that fit the kind node.
4. The ONNX runtime gives the same vectors for the same text on the person's machine and the runner to within the thresholds in the drift row; if not, the asset is built in the CI image instead, which the PO would need to approve.

### Dependencies

1. Branch `worktree-plan-epic-3-rebased` merges to `main`. Required before story 3.1 starts.
2. The red-mode oracle sessions run before stories 3.1 and 3.2 build.
3. The PO answers C-1, C-2, C-3, C-5 and C-7, or accepts the assumptions.
4. A person runs the publish script and merges the pin for story 3.4.
5. Story 3.3's chosen model, before story 3.4 and the later stories can fix their values.

### Risks to Plan

- **Risk**: the model-dependent rows need the baked model, so they cannot run in a plain `checks` job without a download.
  - **Impact**: those rows run later in the pipeline, or someone adds a runtime download that the epic forbids.
  - **Contingency**: run them inside the built app image in the image job or `integrated-check`.
- **Risk**: the eval run plus kind-up exceeds `_kind-deploy.yml`'s 45 minutes (R-006).
  - **Impact**: the required check always times out.
  - **Contingency**: story 3.5's recorded cost raises the timeout and the Job deadline, or reduces the live embedding cost by caching query vectors within a run.
- **Risk**: story 3.5's baseline can only be committed after a CI run produces it.
  - **Impact**: a one-PR plan cannot pass the gate.
  - **Contingency**: follow epic 2's sequence: the code PR passes with dense and hybrid reported as new modes, then a baseline commit from that run's artifact.

---

## Proposed Story Updates

These changes are for the PO to apply. This plan does not edit `tickets.toml` or the epic.

| Story | Proposed change | Why |
| ----- | --------------- | --- |
| 3.1 | Add to `verify`: "readiness is Ready on a keyword-only deployment and not Ready on a model id mismatch (R1, R5); a registered but unavailable mode returns 503 problem+json (R2); the migration applies to an existing cluster and forces a reload (R1); the image embeds with no network (R1); `ticketscope_ro` can read and cannot write `issue_embedding` (R1)." | C-1, C-7, R-003, R-007. The current verify does not say what happens off the happy path. |
| 3.1 | Name the independent reviewer (or lens list) in the plan, or split at the plan checkpoint. | R-007. The flag has not been honoured before. |
| 3.1 | Description: say whether `api` or the eval Job also loads the model, and fix "Only `api` loads it at runtime". | C-2. |
| 3.2 | Description: state the RRF constant and that ranks count after the exclusion; add the hand-computed fusion case to `verify`. | C-3, R-001. |
| 3.3 | Add to `verify`: the findings record the model file's SHA-256, the runtime versions and the hardware used. | C-7, R-004. |
| 3.4 | Add to `verify`: "the asset holds only issue number, model id and vector (R1); an asset that lacks or adds an issue, or holds another dimension, fails the load and keeps the previous state (R1); issues, embeddings and `corpus_meta` are written in one transaction (R1)." | R-003, C-5, Provenance. |
| 3.5 | Add to `verify`: "a run where dense is unavailable fails the gate (R4); the first PR reports dense and hybrid as new modes and a following baseline commit carries them (R4)." | C-3 (epic 2) and R-001. |
| 3.6 | Description: define a tie for the default mode as a difference under 0.005. | C-4. |
| 3.6 | Description: size `jobs.resources` for the eval Job as well as the load Job. | C-2, R-002. |

---

## Follow-on Workflows (Manual)

- Run `/bmad-tea-automate` in red mode to commit the cosine and embedder fixtures before story 3.1's build, and the fusion fixture before story 3.2's build (separate workflow; not auto-run).
- Run `/bmad-tea-automate` for broader coverage once implementation exists.
- Run `/bmad-tea-nfr` once story 3.5 records p95, `wall_seconds` and peak memory.
- Run `/bmad-tea-trace` at epic closure.

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
| **Epic 1 `load`, adapter and `/v1`** | Story 3.1 changes `replace_corpus`, `corpus_meta` handling, the `CorpusStore` port and `/readyz` | Epic 1's load, `/v1` contract and smoke tests; the keyword golden bodies; `scripts/v1_parity.py` |
| **Epic 2 eval job, gate and README** | Dense and hybrid enter `jobs.eval`; story 3.5 rewrites `eval/baseline.json` and the README table | Epic 2's oracle pin test, cluster-oracle tests, gate decision table and README render check |
| **Epic 1 and 2 workflows** | `kind-up.sh` gains the compute flag; the eval Job may need a longer deadline | `ci.yml` integrated-check and `eval.yml` on every story PR; the workflow parse tests |
| **Epic 4 MCP** | `mcp` forwards `mode` and has no default | The chart assertion that no `mcp` mode key exists |
| **Epic 5 EKS** | Sizes nodes from this epic's recorded needs and loads the pinned asset | The recorded resource and timed-load values in `values.yaml` and the spike |
| **Epic 7 dashboard** | Reads `retrieval {mode}` spans and `ticketscope.retrieval.mode` | The span-tree row (no nested retrieval spans) |
| **Epic 8 reviewer package** | Publishes the three-mode table | README render row |

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization
- `nfr-criteria.md` - NFR categories and evidence

### Related Documents

- PRD: `_bmad-output/initiative-ticketscope/initiative-ticketscope.md` (R2, R6)
- Epic: `_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/epic-hybrid-retrieval.md`
- Stories: `_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/tickets.toml`
- Architecture: `_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md`
- Prior test design: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/test-design-epic-2.md`
- Prior retrospective: `_bmad-output/initiative-ticketscope/tickets/epic-eval-gate/epic-eval-gate-retrospective.md`

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `bmad-tea-test-design`
**Version**: 4.0 (BMad v6)
