---
title: 'Tracer: dense search answers through /v1 on kind'
type: 'feature'
ticket: '1'
created: '2026-11-09'
status: done
baseline_revision: '6b6e2340b4747eb8d6322c54f51d44040d5247e7'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'thorough'
review_source: 'pinned'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
review_loop_iteration: 2
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/test-design-epic-3.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md'
warnings: ['oversized']
deferred:
  - summary: >-
      Embedder reference vectors (test-design oracle) are not committed; they need the model run outside this code path.
    evidence: |-
      No red-mode session ran; the cosine fixture was committed, reference vectors were not producible in-code.
    severity: medium
  - summary: >-
      Kind run (EMBEDDINGS_COMPUTE=1 and flag-off kind-up), Tempo trace check, OOM and api memory measurement on kind were not run.
    evidence: |-
      Verified instead with a local Docker run of migrate, load, api and a --network none embed; ci.yml and eval.yml have not run on a PR.
    severity: medium
  - summary: >-
      tests/postgres (the only tests of the dense SQL, vector literal and embedding transaction) skip in CI because nothing sets TICKETSCOPE_TEST_PG_IMAGE.
    evidence: |-
      grep of .github, scripts and pyproject finds no setter; a regression in _DENSE_SQL would stay green.
    location: >-
      tests/postgres/conftest.py
    severity: medium
  - summary: >-
      Model download has no revision pin or file checksum (test-design C-7), and fastembed resolves a quantized Qdrant export.
    evidence: |-
      images/app.Dockerfile downloads BAAI/bge-small-en-v1.5 unpinned; a changed upstream file would change retrieval under the same model_id.
    location: >-
      images/app.Dockerfile
    severity: medium
  - summary: >-
      Corpus identity and retrieval use separate connections, so a concurrent reload can label results with the previously read corpus version.
    evidence: |-
      The API reads corpus_version before mode availability and retrieval, each using a separate Postgres connection. Baseline keyword requests already have the same race. A concurrent old/new snapshot reload can therefore interleave with a response; request-snapshot consistency needs its own design.
    location: >-
      src/ticketscope/http/app.py:224; src/ticketscope/adapters/postgres.py
    severity: medium
---

<intent-contract>

## Intent

**Problem:** Only keyword retrieval exists. Epic 3 needs the thinnest path from a loaded issue to a dense result, and every later story (hybrid, spike, asset, eval) builds on this story's shared setup: the `Embedder` port, `issue_embedding`, the baked model, readiness.

**Approach:** Add the `Embedder` port with a hash fake, a fastembed adapter (bge-small-en-v1.5 baked into the app image), migration `0002`, `CorpusStore` dense reads, and a `DenseRetriever` in the registry. `load` computes embeddings only behind `embeddings.computeOnKind` (default off, `kind-up.sh` flag), so CI stays keyword-only. `/v1` serves `mode=dense`, readiness follows the model id, and dense emits `embeddings {model}` under `retrieval {mode}`.

## Boundaries & Constraints

**Always:**
- Layering (AD-1): `core` imports only stdlib and pydantic, so no telemetry and no fastembed in `core`; the `embeddings {model}` span is emitted by the adapter side. `import-linter` and `test_layer_imports` stay green.
- `load` is the only writer (AD-7): issues, `issue_embedding` rows and `corpus_meta` go in ONE transaction (`replace_corpus`), so a failure leaves the previous corpus whole.
- `issue_embedding.embedding` is an unsized `vector`; dense search is an exact scan filtered by `model_id`, ordered by distance then issue number, with no index (AD-21, AD-7).
- `score` is cosine similarity (`1 - cosine distance`), higher is better; `score_kind` `cosine`. Over-fetch `k + |exclude|` (AD-19).
- Document and query text share one preprocessing function in `core` (title, blank line, description cut at a fixed character count; the model's token limit remains the backstop).
- Keep the default load path byte-identical: with the flag off, `corpus_meta.embedding_model_id` is null and `preprocessing_version()` is unchanged (`pre1.kind2-t3.outcome3`), so `eval/baseline.json` lineage still matches and the gate is untouched.
- The Hugging Face source is read only in an image build stage; runtime is offline (`HF_HUB_OFFLINE=1`).

**Never:**
- No hybrid mode, no asset download or pin, no eval changes, no `eval/baseline.json` edit, no vector index, no `pgvector` Python package (send vectors as text literals), no second vector store.
- Do not change the `/v1` shape (additive only); the page stays on `PAGE_MODE = "keyword"`.
- Do not author the red-mode oracle fixtures if the red-mode session has committed them (see Code Map); never edit them once committed.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Dense, vague query | flag on, embeddings loaded, `mode=dense` | 200, `score_kind=cosine`, ranked results with outcomes | - |
| Dense, log-heavy query | same, stack-trace-like query | 200, ranked results (text cut by the shared preprocessing) | - |
| Flag off (default, CI) | no embeddings, `embedding_model_id` unset | `dense` not available; keyword unchanged; api Ready | `mode=dense` returns 503 problem+json (not 500) |
| Model id matches | api model == `corpus_meta.embedding_model_id` | `/readyz` 200 | - |
| Model id differs | api model != `corpus_meta` (incl. null) | `/readyz` 503 with a reason naming both ids | - |
| Exclusion | `exclude={n}` | n never returned, `k` slots still filled | - |
| Load fails mid-embedding | embedder raises after issues copied | rollback of issues, embeddings, `corpus_meta`; previous corpus answers | `load` exits 1, logs reason |
| Other model's rows | a second model, other dimension, in the table | dense for the configured model returns results, no dimension error | - |

</intent-contract>

## Code Map

- `src/ticketscope/core/ports.py` -- `CorpusStore`/`Retriever` Protocols. Add `Embedder` (`model_id: str`, `embed(texts: Sequence[str]) -> list[list[float]]`) and to `CorpusStore`: `dense_search(model_id, vector, k) -> list[Scored]`, `has_embeddings(model_id) -> bool`, `embedding_model_id() -> str | None` (the `corpus_meta` value).
- `src/ticketscope/core/fakes.py` -- `InMemoryCorpusStore` (add optional `embeddings` mapping and the three methods; exact cosine, ties by issue number) plus a new deterministic `HashEmbedder` (token-hash into a small fixed dimension, L2-normalised, no model).
- `src/ticketscope/core/modes.py` -- `Mode`, `REGISTRY`, `KeywordRetriever`. Add `DenseRetriever` and a `dense` entry (`score_kind` `cosine`). `Mode.build`/`available` currently take only `store`: widen to `(store, embedder: Embedder | None)`; unavailable when `embedder is None` or `not store.has_embeddings(embedder.model_id)`.
- `src/ticketscope/core/derive.py` -- `search_text`, `preprocessing_version()`. Add `embedding_text(title, body)` and `EMBEDDING_RULE_VERSION`; `preprocessing_version(embeddings: bool = False)` appends the embedding rule version only when true (so the default string is unchanged).
- `src/ticketscope/adapters/postgres.py` -- `PostgresCorpusStore` (per-call connections), `replace_corpus` (`TRUNCATE issue`), `CorpusMeta`, `read_corpus_meta`. Add the dense SQL, `has_embeddings`, `embedding_model_id`; `replace_corpus` takes optional embeddings and does `TRUNCATE issue, issue_embedding`, then `COPY issue_embedding`, then `corpus_meta`, in the same transaction.
- `src/ticketscope/adapters/embedder.py` (new) -- `FastEmbedEmbedder` (lazy fastembed import, cache dir and offline from settings) and the traced wrapper that emits `embeddings {model}`.
- `src/ticketscope/telemetry.py` -- `retrieval_span` is the pattern; add `embeddings_span(tracer, model)` (INTERNAL, `gen_ai.operation.name=embeddings`, `gen_ai.request.model`, ERROR on exception). Cross-cutting: imports no ticketscope layer (contract enforced).
- `src/ticketscope/http/app.py` -- `create_app` composition root, `retrieve()`, `/readyz`, `/v1/search`. Pass the embedder to `REGISTRY[...].build`; check `available` before serving (503 problem+json via `HTTPException`); readiness per Design Notes. `contract/search.py` already allows `mode=dense`: no change.
- `src/ticketscope/settings.py` -- add `embedding_model_id: str = ""`, `embeddings_compute: bool = False`, `embedding_cache_dir: Path`.
- `src/ticketscope/jobs/load/main.py` -- `pinned_meta`, `reload_reason`, `run`. With compute on: model id into `corpus_meta`, vectors computed in batches from `embedding_text`, same transaction. Report line gains embedding count/seconds.
- `src/ticketscope/jobs/eval/score.py` -- calls `mode.available(store)`/`mode.build(store)`: pass `None` for the embedder so dense is skipped. No other eval change.
- `migrations/0002_issue_embedding.sql` (new) -- table; default privileges from `0001` already grant `ticketscope_ro` SELECT.
- `images/app.Dockerfile`, `pyproject.toml`, `uv.lock` -- `fastembed~=0.9.1` resolves on cp314 for linux amd64/arm64 (verified: onnxruntime 1.31.1); bake the model in the build stage into `/models`, set `FASTEMBED_CACHE_PATH`, `HF_HUB_OFFLINE=1`.
- `deploy/charts/ticketscope/values.yaml`, `templates/api.yaml`, `templates/jobs.yaml`, `scripts/kind-up.sh` -- `embeddings.{computeOnKind,modelId}`; api memory raise; load job env and memory; `EMBEDDINGS_COMPUTE=1` flag.
- Tests to update: every `pre1...` assertion stays valid (default unchanged); `tests/unit/test_modes.py` (`set(REGISTRY) == {"keyword"}` becomes keyword plus dense); `tests/unit/test_load_main.py` `FakeDb.replace_corpus` signature; chart tests style in `tests/unit/test_chart_pin.py`; eval tests that call `Mode.build/available`.
- Red-mode fixtures (test-design "Independent Oracles"): the cosine fixture (query `(1,0)`; vectors `(1,0) (1,1) (0,1) (-1,0)` give order 1,2,3,4 and scores 1, 1/sqrt2, 0, -1) and embedder reference vectors should already be committed by a red-mode session. None are in the repo at this baseline: if still absent, commit the cosine fixture from the table in the test design with exact `Fraction` values and a pin test like `test_eval_oracle_pinned.py`, and record under Implementation Notes that no red-mode session ran. Reference vectors need the model outside this code path: record them as `deferred` if they cannot be produced.

## Tasks & Acceptance

**Execution:**
- [ ] `src/ticketscope/core/ports.py`, `core/fakes.py` -- `Embedder` port, `CorpusStore` dense methods, `HashEmbedder`, in-memory dense -- the fakes keep unit tests model- and database-free
- [ ] `src/ticketscope/core/derive.py` -- `embedding_text`, `EMBEDDING_RULE_VERSION`, `preprocessing_version(embeddings)` -- the cut lives in the preprocessing version; default string unchanged
- [ ] `src/ticketscope/core/modes.py` -- `DenseRetriever`, `dense` entry, widened `build`/`available`; update `jobs/eval/score.py` callers -- availability gates the mode
- [ ] `migrations/0002_issue_embedding.sql` -- `issue_embedding(issue_number integer REFERENCES issue(number) ON DELETE CASCADE, model_id text, embedding vector NOT NULL, PRIMARY KEY (issue_number, model_id))`, no index -- unsized column, exact scan
- [ ] `src/ticketscope/adapters/postgres.py` -- dense SQL (`WHERE model_id = %s ORDER BY embedding <=> %s::vector, issue_number`, score `1 - distance`, vector sent as text), `has_embeddings`, `embedding_model_id`, transactional embedding write in `replace_corpus` -- one transaction, readable by `ticketscope_ro`
- [ ] `src/ticketscope/adapters/embedder.py`, `telemetry.py` -- fastembed adapter plus traced wrapper and `embeddings_span` -- AD-10 span from the adapter side
- [ ] `src/ticketscope/settings.py`, `jobs/load/main.py` -- compute behind the flag, model id and embedding rule in `corpus_meta`, batched, same transaction, timing in the report line
- [ ] `src/ticketscope/http/app.py` -- embedder wiring (eager model load at startup when configured), availability check, readiness rule, dense span nesting under `retrieval {mode}`
- [ ] `pyproject.toml`, `uv.lock`, `images/app.Dockerfile` -- dependency and model bake in a build stage; model id as one build arg, equal to the chart's `embeddings.modelId`
- [ ] `deploy/charts/ticketscope/*`, `scripts/kind-up.sh` -- values, env, memory (start `api` limit at 768Mi and trim to the measured need; load Job limit raised only when `computeOnKind`), `EMBEDDINGS_COMPUTE=1` adds `--set embeddings.computeOnKind=true` and a longer Helm timeout
- [ ] `tests/unit/...` (+ one Postgres-backed test module if a container is available, marked like `tests/eval`) -- cases below, plus the cosine oracle, a chart render test (flag off: no model env on api and load; on: both set), and a test that the Dockerfile and `values.yaml` name the same model

**Acceptance Criteria:**
- Given kind with `computeOnKind` set and a fresh load, when `POST /v1/search` is called with `mode=dense` for a vague query and for a log-heavy query, then each returns 200 with ranked issues, `score_kind` `cosine` and outcomes.
- Given `computeOnKind` off (the default), when the registry is read and `/v1/search` is called, then `dense` is unavailable (`mode=dense` returns 503 problem+json), keyword results are unchanged, and `api` is Ready.
- Given api configured with a model id, when `corpus_meta.embedding_model_id` differs or is null, then `/readyz` returns 503 and `api` is not Ready; when they match, then it is Ready.
- Given a dense search on kind, when its trace is read in Tempo, then `retrieval dense` has a child `embeddings {model}` span with `gen_ai.request.model`, and `/readyz` and eval stay untraced.
- Given the hash fake, when the unit suite runs with no model and no database, then it passes, including the cosine oracle (order 1,2,3,4; `1 - distance`, not distance or inner product), exclusion keeping `k` slots, and a load rollback leaving the previous corpus.
- Given the built app image, when it embeds a text with the network disabled, then it succeeds, and `ruff`, `pyright`, `lint-imports` and the full `pytest` pass.
- Given the PR, when CI runs, then `ci.yml` (including `integrated-check`) and `eval.yml` pass with `eval/baseline.json` unchanged.

## Implementation Notes

- Follow-up repair: actual pinned-corpus kind load at batch 64 was OOMKilled under 2Gi before replacement, leaving the previous keyword corpus intact. ONNX workspace, rather than only accumulated output vectors, was the immediate pressure. Batch 8 bounds that workspace; a disk-backed JSONL spool also bounds corpus-wide vector memory while keeping inference outside the write transaction. Regression tests prove bounded live vectors, float round trips, pretransaction inference and cleanup on failure.
- Follow-up repair:16 simultaneous real-model HTTP requests reproduced an API OOM at 384Mi. Per-instance inference locking now covers the entire lazy generator and vector conversion; the same real-image workload returns 16 responses with status 200 with no OOM. The cgroup peak can touch384Mi due to reclaimable cache. Liveness now runs directly on the event loop so queued synchronous inference workers cannot hold its constant response.
- Follow-up tests: `tests/integrated/test_dense_kind.py` opts in with `TICKETSCOPE_DENSE_ENABLED=1` (or0 after flag-off upgrade), checks vague/log-heavy Gateway queries against persisted outcomes, Tempo parentage,16 concurrent requests, complete embedding coverage, Ready status, zero restarts and the 384Mi API budget.

- No red-mode session ran before this build. The cosine fixture was committed from the test design table as `tests/dense_oracle.py` (exact `Fraction` values; issue 2 is 1/sqrt(2) as a float) with a pin test, `tests/unit/test_dense_oracle_pinned.py`. Embedder reference vectors are deferred: they need the model's reference implementation outside this code path.
- Verified outside kind: app image built with the model baked in a build stage; with `--network none` it embeds to 384 dimensions. Image size 482MB (epic 2 image: 222MB). Migrate, then `load` with the real model (8 fixture issues, 0.5s embedding), then `api` against a real Postgres container from `images/postgres.Dockerfile`: `mode=dense` returned 200 with `score_kind=cosine` for a vague and a log-heavy query; flag off returned 503 problem+json and api Ready. api used about 202MiB after a dense search, so the 768Mi limit has headroom and can be trimmed (not measured on kind).
- fastembed resolves `BAAI/bge-small-en-v1.5` to the quantized Qdrant ONNX export (`Qdrant/bge-small-en-v1.5-onnx-Q`); C-7's model-file SHA-256 is not recorded here.
- Postgres-backed tests live in `tests/postgres/` and skip unless `TICKETSCOPE_TEST_PG_IMAGE` names a built postgres image; they ran green locally (8 tests).
- A configured model id the image does not hold fails api startup (eager model load) instead of reaching the `/readyz` mismatch path; readiness mismatch is for a `corpus_meta` that was loaded with another model.

## Plan Change Log

### 2026-11-09 — Follow-up repair of kind load OOM

- Trigger: Blind Hunter's materialized-embedding memory concern reproduced on the actual pinned 32,153-issue corpus: load pod `ticketscope-load-mvhnh` terminated `OOMKilled`, exit 137, at 14:54:37 UTC under the 2Gi limit.
- Amendment: replace the unbounded embedding list before `replace_corpus` with a bounded disk spool. Finish embedding before opening the write transaction; stream the spool into `replace_corpus`. Bound model inference batch memory as necessary based on the observed long-description corpus. Keep `embeddings.loadMemoryLimit` at 2Gi. Verify the actual kind load passes before accepting this repair.
- Known-bad state to avoid: retaining every vector as Python floats or embedding lazily while TRUNCATE holds ACCESS EXCLUSIVE.
- KEEP: all existing dense behavior, preprocessing/oracle bytes, one atomic corpus transaction, offline model bake, keyword-only CI/default path, existing user-provided expanded tests.
- Repair scope: the feature is already implemented. Implement only this repair and appropriate regression coverage; run targeted tests. Preserve existing deferred items and every deferred-work ledger byte. Do not change plan status, ticket status, or run tickets.py mark; these belong to the parent/orchestrator. Do not commit; parent verifies and commits.
- Parent also reduced the API limit from 768Mi to 384Mi based on measured model startup high-water RSS of 263400 KiB (about 258Mi); verify dense requests at the revised limit.


### 2026-11-09 — Bound concurrent model inference

- Trigger: follow-up Blind Hunter reproduced a real API OOM with 16 concurrent long queries at 384Mi.
- Amendment: serialize the complete inference operation within each `FastEmbedEmbedder` instance with an internal lock; `TextEmbedding.embed` returns a lazy iterable, so hold the lock through vector materialization. Add regression coverage proving concurrent calls never overlap underlying inference, still return all results, and release the lock after failure.
- KEEP: bounded disk spool and inference batch 8; offline model initialization; no public configuration or protocol change;384Mi API budget; all prior behavior and oracle bytes. No source reversion is needed for the bounded-spool repair, which is verified to keep load memory near 600Mi; only amend the unbounded concurrent-inference behavior in the existing adapter.
- Parent owns actual Docker concurrency/kind tests, final verification and commits. Do not change plan or ticket status, deferred entries/ledgers, or run tickets.py mark.

## Review Triage Log

### 2026-11-09 — Review pass
- verdicts: 40 findings — high 0, medium 4, low 11, false 0, maybe-false 25
- findings:
  - `[medium]` `[patch]` Blind Hunter: TRUNCATE holds ACCESS EXCLUSIVE while embeddings compute lazily inside the transaction, blocking the live api — confirmed in `jobs/load/main.py` run; fixed by materializing embedding rows before `replace_corpus`.
  - `[low]` `[patch]` Blind Hunter and Verification Gap: `test_load_with_the_flag_off_computes_nothing` passes `None`, so its assertion is vacuous — fixed by passing the embedder.
  - `[low]` `[patch]` Verification Gap: `test_chart_embeddings.py` is not in the helm-equipped CI step — added to the chart render tests command.
  - `[medium]` `[defer]` Verification Gap: `tests/postgres` never runs in CI — recorded in `deferred`.
  - `[medium]` `[defer]` Blind Hunter: model download unpinned, no checksum — recorded in `deferred` (C-7).
  - `[medium]` `[defer]` Intent Alignment: kind, Tempo and PR CI checks not run — recorded in `deferred`.
  - `[low]` `[reject]` /readyz reports a database error as a model mismatch (Blind Hunter, Edge Case): `corpus_version()` runs first and fails the same way; misleading text only.
  - `[low]` `[reject]` Extra `has_embeddings` query per dense request (Blind Hunter, Edge Case): the plan requires the availability check; the cost is one cheap query.
  - `[low]` `[reject]` Dimension mismatch for one model id, zero/NaN vectors, non-finite or mixed-dimension embedder output, zero-issue embedding count, injected-embedder model id mismatch (Blind Hunter, Edge Case): not reachable with one baked model; fix adds guards.
  - `[low]` `[reject]` Oracle issue 2 is a float, and the cosine test runs against the fake (Blind Hunter, Edge Case): disclosed in Implementation Notes; the Postgres test covers the SQL.
  - `[low]` `[reject]` Helm timeout equals the Job deadline, `HELM_TIMEOUT` overwrite, nil `limits`, api memory raise with flag off, fastembed as a core dependency, importlinter ignores, ruff line length (Blind Hunter, Edge Case): plan-mandated or verified clean (ruff format and lint-imports pass; values define limits; 50m exceeds the 40m eval timeout).
  - `[low]` `[reject]` Eager model load fails api startup; `_build_dense` raises with no embedder (Edge Case): documented in Implementation Notes; callers gate on `available`.
  - `[low]` `[reject]` Stale result file and plan header, empty task checkboxes, `ticket: '1'` (Blind Hunter): orchestrator-owned artifacts; the plan fix is out of scope.
  - `[maybe-false]` `[reject]` Intent Alignment readings A to F (25 descriptive points): descriptive, none a defect beyond the deferred kind checks; the chart cannot produce a mismatch by design (one `embeddings.modelId`).


### 2026-11-09 — Follow-up review pass 1
- verdicts: 20 findings — high 1, medium 10, low 4, false 4, maybe-false 1
- findings:
  - `[medium]` `[defer]` Blind 1: mutable model download — carried: same download/checksum claim as prior triage; keep the existing deferred item, no ledger or status edits.
  - `[medium]` `[defer]` Blind 2: Postgres assertions skip in CI — carried: exact prior CI wiring finding; local eight-test run passes but does not alter CI coverage.
  - `[medium]` `[defer]` Blind 3: no embeddings-on automated Gateway acceptance — carried: prior kind/Tempo evidence finding; explicit ticket keeps CI keyword-only. Parent is exercising local kind, not adding inference to CI.
  - `[low]` `[reject]` Blind 4: static offline test does not run the image — Actual image was exercised with --network none this pass; one text produces a 384-dimensional vector. A static test alone is not the sole evidence.
  - `[medium]` `[defer]` Blind 5: no numerical reference-vector contract — carried: prior reference-vector oracle finding; existing deferred item preserved.
  - `[high]` `[bad_plan]` Blind 6: unbounded embedding materialization — Confirmed on pinned kind corpus: load OOMKilled exit 137 under 2Gi. Plan Change Log requires bounded spool and bounded inference memory while preserving pretransaction computation and atomic replacement.
  - `[false]` `[reject]` Blind 7: host thread pools necessarily exceed kind allocations — No CPU limit is configured, only a 50m scheduling request. Observed API has ten threads; no demonstrated throttling/probe failure. The actual failing load is memory exhaustion, addressed separately.
  - `[maybe-false]` `[reject]` Blind 8: eager startup can exceed liveness window — Would require startup exceeding the roughly 30-second liveness window on supported resources. Model startup succeeded on kind without restart. No everyday failure demonstrated; adding probe policy is not a direct correction. If true severity low for this measured deployment.
  - `[false]` `[reject]` Blind 9: matching metadata with zero embeddings should fail readiness — Ticket explicitly requires Ready when model ids match; availability separately gates dense on rows. Empty/damaged hand-edited tables do not establish a defect in the loader transaction.
  - `[low]` `[reject]` Blind 10: fake zero-vector cosine differs from pgvector — carried: prior zero-vector triage. Baked model emits nonzero vectors; adding production guards for arbitrary fake outputs is not justified by a reachable production input.
  - `[low]` `[reject]` Edge 1: nonpositive HashEmbedder dimensions — All callers use default or positive dimensions; developer-only fake misuse is not encountered in ordinary use. Adding validation adds a branch for an undemonstrated state.
  - `[low]` `[reject]` Edge 2: all-zero query embedding serializes NaN — carried: prior zero-vector finding; real model has no demonstrated zero-vector output. API hash fake uses in-memory store, not pgvector.
  - `[medium]` `[defer]` Verification 1: CI skips dense SQL assertions — carried: pre-verified exact prior Postgres CI coverage finding; existing deferred item retained once.
  - `[medium]` `[defer]` Verification 2: actual model lacks independent numerical vectors — carried: pre-verified prior reference-vector finding; existing deferred item retained once.
  - `[medium]` `[defer]` Intent 1: named environment evidence missing in diff — carried: prior kind/Tempo/PR evidence finding. Record new observations under Auto Run Result; ledger resolution remains orchestrator-owned.
  - `[medium]` `[patch]` Intent 2: API memory unmeasured and oversized — Measured model startup VmHWM 263400 KiB on kind; directly trim 768Mi to 384Mi and update chart assertion. Final dense request checks must validate this budget.
  - `[false]` `[reject]` Intent 3: unconditional image bake adds PR build cost — Ticket explicitly requires the model baked at build time. Its CI constraint names no corpus computation during default load, which remains disabled; image cost does not contradict that requirement.
  - `[medium]` `[defer]` Intent 4: hash API tests do not prove vague/log-heavy kind behavior — carried: prior environment-evidence finding; actual pinned-corpus Gateway scenarios are being exercised this pass. No duplicate deferred item or ledger rewrite.
  - `[medium]` `[defer]` Intent 5: database verification optional in CI — carried: exact prior CI Postgres test finding; eight real SQL tests passed locally this run.
  - `[false]` `[reject]` Intent 6: new import-linter exceptions change the allowed graph — Composition-root embedder adapter import and telemetry FastAPI type import are the documented seams. All seven named contracts pass; no forbidden dependency was identified.


### 2026-11-09 — Follow-up review pass 2
- verdicts: 19 findings — high 1, medium 10, low 5, false 3, maybe-false 0
- findings:
  - `[medium]` `[defer]` Blind 1: model download mutable — carried: identical previous model pin/checksum finding; existing deferred unchanged.
  - `[medium]` `[defer]` Blind 2: real SQL tests skip in CI — carried: identical prior CI wiring finding; existing deferred unchanged.
  - `[false]` `[reject]` Blind 3: opt-in dense kind variable undocumented — Module docstring documents TICKETSCOPE_DENSE_ENABLED=1/0 and required -m kind/Gateway variables. CI intentionally stays keyword-only; explicit local command will be recorded in Verification.
  - `[medium]` `[defer]` Blind 4: missing real numerical vectors — carried: previous reference-vector finding; existing deferred unchanged.
  - `[high]` `[bad_plan]` Blind 5: concurrent inference exceeds API memory — Reproduced with real baked model, real /v1 app and 16 simultaneous 2000-character queries in a 384Mi container: OOMKilled=true exit137 at15:03:07 UTC. Amend plan to serialize per-instance FastEmbed inference and verify same workload.
  - `[low]` `[patch]` Blind 6: memory check can miss prior OOM restart — Added API container restartCount==0 and previous OOMKilled checks so a restart cannot reset evidence unnoticed.
  - `[low]` `[reject]` Blind 7: injected embedder id and Settings mismatch — carried: initial review rejected injected model-id mismatch; production composition constructs embedder from settings and cannot diverge.
  - `[low]` `[patch]` Blind 8: generic outcome assertion misses mapping regression — Added comparison of every returned outcome field with the same persisted Postgres issue rows.
  - `[low]` `[reject]` Blind 9: offline test static only — carried: actual --network none inference succeeds (384 dimensions). Required CI model numerical contract remains separately deferred.
  - `[medium]` `[defer]` Blind 10: reload race can mislabel response corpus version — Pre-existing API reads version then performs retrieval on separate connections in baseline; dense adds availability but does not create this identity race. Record as a new plan deferred item, no existing ledger changes.
  - `[low]` `[patch]` Edge 1: incomplete Tempo spans cause unpack ValueError — Assert exact span counts before unpacking so eventually retries AssertionError while ingestion completes.
  - `[medium]` `[defer]` Verification 1: dense SQL skipped by normal CI — carried: same pre-verified CI wiring gap; existing deferred unchanged.
  - `[medium]` `[defer]` Verification 2: real model lacks numerical oracle — carried: same pre-verified reference-vector gap; existing deferred unchanged.
  - `[medium]` `[defer]` Intent 1: real kind query and Tempo run not yet evidenced — carried: existing environment evidence item; in-progress full-corpus run and new assertions are not reported as passed prematurely.
  - `[medium]` `[defer]` Intent 2: kind mismatch scenario not in permanent test — carried: environment-evidence finding; parent observed actual pod NotReady and /readyz503 naming baked model vs None during load; application tests cover another stored id.
  - `[false]` `[reject]` Intent 3: static registry and keyword golden surface — Static dense registration with availability predicate matches available-modes wording. Existing unit availability tests pass; final flag-off run also runs keyword golden integrated checks.
  - `[false]` `[reject]` Intent 4: image bake adds PR cost — carried: required bake and keyword-only load are compatible. No corpus inference in CI.
  - `[medium]` `[defer]` Intent 5: PR CI and dense SQL execution not established — carried: existing PR evidence/SQL coverage deferred items; local full suite includes eight real Postgres tests.
  - `[medium]` `[patch]` Intent 6: API memory now measured but requests must validate budget — Shares pass1 API budget patch; parent verifies revised budget with real inference and kind. Concurrent workload revealed separate bad_plan above.


### 2026-11-09 — Follow-up review pass 3
- verdicts: 16 findings — high 0, medium 10, low 3, false 2, maybe-false 1
- findings:
  - `[medium]` `[defer]` Blind 1: mutable model bytes — carried: prior checksum/revision finding; existing deferred unchanged.
  - `[medium]` `[patch]` Blind 2: dense inference waiters occupy HTTP workers — Liveness previously shared the synchronous worker pool with queued inference. Make the constant healthz handler async so it returns directly on the event loop, independent of worker occupancy; no public surface or inference policy change.
  - `[false]` `[reject]` Blind 3: readiness must validate configured default mode — Ticket readiness rule is corpus/model identity; default mode remains keyword. Explicit dense on flag-off is documented unavailable/503, not a requirement to fail keyword readiness.
  - `[false]` `[reject]` Blind 4: one row exposes partial embeddings — carried: prior incomplete/hand-edited corpus claim. Production loader writes every issue, embedding and metadata atomically, and inference-count mismatches fail before transaction.
  - `[medium]` `[defer]` Blind 5: SQL tests skip in CI — carried: identical prior CI wiring finding; existing deferred unchanged.
  - `[medium]` `[defer]` Blind 6: no independent numerical reference — carried: identical previous reference-vector finding; existing deferred unchanged.
  - `[low]` `[reject]` Blind 7: no committed offline image inference check — carried: actual image successfully embeds 384 dimensions with --network none; required CI numerical oracle remains separately deferred.
  - `[low]` `[patch]` Blind 8: concurrency regression test does not run ONNX — Real final image passed16 simultaneous long-query HTTP requests at 384Mi without OOM; add the same16-request workload to opt-in kind checks and inspect restart/peak evidence afterwards. Peak may equal the limit due to reclaimable cache, so accept <= with zero restarts.
  - `[medium]` `[defer]` Blind 9: response lineage race — carried: exact previous new deferred item; no duplicate appended and no ledger mutation.
  - `[medium]` `[defer]` Blind 10: no permanent kind mismatch transition — carried: prior environment-evidence finding; actual configured-model pod returned503 naming None metadata and remained NotReady during precompute. Permanent unit tests also cover another stored id.
  - `[maybe-false]` `[reject]` Edge 1: startup may exceed liveness window — carried: same prior startup timing claim; real kind model initialization succeeds without restart, no observed supported deployment needs extra startup allowance. Additional probe policy rejected as low if true without demonstrated reachability.
  - `[medium]` `[defer]` Verification 1: SQL oracle not normally run by CI — carried: exact pre-verified DW-5 finding. Local full suite executes all eight SQL tests; existing deferred untouched.
  - `[medium]` `[defer]` Intent 1: complete kind/Tempo/PR results not yet recorded — carried: existing environment-evidence item; parent will record completed tests, and will not label PR CI executed locally.
  - `[medium]` `[defer]` Intent 2: permanent mismatch test uses application seam — carried: existing environment-evidence item; parent recorded actual Kubernetes mismatch during load, so application seam is not the only run evidence.
  - `[medium]` `[defer]` Intent 3: SQL coverage optional in CI — carried: exact prior CI coverage finding; existing deferred untouched.
  - `[low]` `[patch]` Intent 4: final memory results absent from staged narrative — Shares actual-model concurrency and kind memory verification entry above; record final measurements under Auto Run Result. Actual16-request final image run returned 16 responses with status 200, no OOM; pending kind run is not prematurely declared passed.

## Design Notes

- **Readiness (test-design C-1, C-7):** configured id empty and `corpus_meta` id null: Ready (CI path). Configured id set: Ready only when equal; a null or different stored id is 503 naming both. `has_embeddings` guards partial state: dense is unavailable when no rows exist for the model.
- **Wiring:** the chart passes `TICKETSCOPE_EMBEDDING_MODEL_ID` to `api` and `load`, and `TICKETSCOPE_EMBEDDINGS_COMPUTE=true` to `load`, only when `computeOnKind` is true. Later stories add the asset pin as the other trigger; this story has no asset, so "no asset pinned" is always true now.
- **Preprocessing version:** a flag-off load keeps `pre1.kind2-t3.outcome3`; a flag-on load records `pre1.kind2-t3.outcome3.emb1` (illustrative). The toggle changes `corpus_meta`, so the next load reloads (AD-21), and the eval gate's lineage check is untouched in CI.
- **Vector transport:** text literal `'[0.1,0.2]'` through `COPY` and `%s::vector`; avoids a new dependency. The `<=>` operator is cosine distance, so `score = 1 - distance`.
- **Spike for the implementer:** `onnxruntime` has no cp314 wheels before 1.24.1; `uv lock` resolves 0.9.1 / 1.31.1 on linux and macOS arm64. If pyright strict rejects untyped fastembed, wrap it in a thin typed adapter, not a blanket ignore.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports` -- expected: all pass
- `uv run pytest` -- expected: all pass with no model or database
- `helm template t deploy/charts/ticketscope --set-string image.app.tag=t --set-string image.postgres.tag=18-t --set backup.enabled=false [--set embeddings.computeOnKind=true]` -- expected: renders; model env present only with the flag
- `docker build -f images/app.Dockerfile -t ticketscope-app:dev . && docker run --rm --network none ticketscope-app:dev python -c "<embed one text>"` -- expected: 384-dimension vector, no network access
- `EMBEDDINGS_COMPUTE=1 scripts/kind-up.sh`, then a `mode=dense` search through the Gateway for a vague and a log-heavy query -- expected: 200 with ranked outcomes; `kubectl -n ticketscope get pod` shows no OOMKilled; `psql` `count(issue_embedding)` equals `count(issue)` for the model
- `scripts/kind-up.sh` (flag off) -- expected: api Ready, `mode=dense` returns 503, keyword golden queries unchanged

**Follow-up execution commands (Gateway env points at the kind-up output):**
- `TICKETSCOPE_TEST_PG_IMAGE=ticketscope-postgres:18-local uv run pytest -q` — includes all eight real SQL/rollback/privilege checks.
- `TICKETSCOPE_DENSE_ENABLED=1 TICKETSCOPE_GATEWAY_URL=http://127.0.0.1:18080 TICKETSCOPE_GATEWAY_HOST=ticketscope.kind.internal uv run pytest -m kind tests/integrated/test_dense_kind.py -q` — run after embeddings-on kind-up completes.
- `TICKETSCOPE_DENSE_ENABLED=0 TICKETSCOPE_GATEWAY_URL=http://127.0.0.1:18080 TICKETSCOPE_GATEWAY_HOST=ticketscope.kind.internal uv run pytest -m kind tests/integrated tests/smoke -q` — run after flag-off kind-up; includes keyword golden queries and existing integrated/smoke checks.

**Manual checks (if no CLI):**
- Tempo: one dense search trace shows `retrieval dense` with an `embeddings {model}` child.
- `kubectl -n ticketscope top pod` after a dense search: the `api` limit holds with headroom; record the number in Implementation Notes.

## Auto Run Result

Hand-back status: built. Ticket completion and deferred-ledger resolution remain with the orchestrator. Plan frontmatter status stayed `built` throughout this follow-up; no `tickets.py mark` command was run.

### Implemented change

- Repaired two reproduced memory failures: the real pinned-corpus load was OOMKilled at batch 64 under 2Gi; the real API was OOMKilled by 16 concurrent long queries at 384Mi.
- Load now finishes inference in batches of 8 into a disk-backed temporary JSONL spool, then streams that spool into the existing atomic replacement transaction. The previous corpus stays available during inference. The spool closes on success and failures.
- Each fastembed instance serializes the full lazy inference operation, including vector conversion. Liveness responds on the event loop independently of synchronous inference workers. API memory was trimmed from 768Mi to the measured 384Mi budget.
- Added bounded-memory, transaction-timing, cleanup, concurrency and failure-release regressions, plus opt-in real-model kind checks. Preserved and included the preceding automation run's expanded tests and summary.

### Files changed in this follow-up

- `src/ticketscope/jobs/load/main.py`: bounded disk spool and inference batches.
- `src/ticketscope/adapters/embedder.py`: per-instance inference lock through lazy materialization.
- `src/ticketscope/http/app.py`: nonblocking constant liveness response.
- `deploy/charts/ticketscope/values.yaml`: measured 384Mi API limit.
- `tests/unit/test_dense.py`: bounded live vectors, lossless float round trips, inference before writes and spool cleanup.
- `tests/unit/test_embedder_concurrency.py`: 16 concurrent callers and lock release after eager/lazy/conversion failures.
- `tests/unit/test_chart_embeddings.py`: revised API budget assertion.
- `tests/integrated/test_dense_kind.py`: vague/log-heavy Gateway results, persisted outcomes, Tempo span nesting, 16 concurrent searches, coverage, readiness and memory/restart checks; explicit flag-off assertions.
- `tests/unit/test_dense_expanded.py`, automation summary and tea result: preserved preceding-run artifacts, reviewed and verified here.
- This plan: repair amendments, all follow-up triage decisions and execution evidence; existing deferred items preserved.

### Review outcome

Three thorough follow-up passes ran all four lenses: blind-hunter, edge-case-hunter, verification-gap and intent-alignment. All 55 reported findings have individual rows above: 2 high, 30 medium, 12 low, 9 false and 2 maybe-false.

Two high findings required plan amendments and implementation repair (load OOM, concurrent API OOM). Eight finding rows produced six patch groups: measured API budget, Tempo retry, persisted-outcome comparison, restart evidence, independent liveness response and real-model concurrency verification. Twenty-seven rows carry existing deferrals or the single new pre-existing corpus-lineage race. Eighteen findings were rejected, with individual reasons in the triage log: unreachable fake/injection states, atomic-loader guards, documented readiness/availability semantics, required image-bake cost, already documented opt-in settings, actual offline verification, or unobserved startup/probe policy concerns.

The four original frontmatter deferred items and every existing deferred-work ledger entry are unchanged. One new pre-existing issue is recorded only in the plan's deferred list: corpus version and retrieval can straddle a concurrent reload. No existing deferred item was re-added, reopened, resolved or rewritten.

Final-pass patched entry counts after grouping: high 0, medium 1 (liveness), low 1 (concurrency verification). Follow-up review recommended: false. The two reproduced OOM risks were tested after repair; no remaining unverified high repair risk requires another pass.

### Verification performed

- Ruff check/format, pyright: pass. Import-linter: all 7 contracts kept.
- `TICKETSCOPE_TEST_PG_IMAGE=ticketscope-postgres:18-local uv run pytest -q`: **977 passed, 45 deselected**. All 8 real Postgres cosine/model-dimension/transaction/privilege tests ran; they did not skip. The remaining deselected tests require kind.
- README results-table check and diff whitespace check: pass. `eval/baseline.json` unchanged.
- Final app image built successfully; with `--network none`, the real baked model embeds one text into 384 dimensions.
- Actual Docker concurrency reproduction before repair: 16 simultaneous long-query HTTP requests killed the 384Mi API container (`OOMKilled=true`, exit 137). Same workload after repair: **16 responses with status 200, no OOM**.
- `TAG=story-3-1-verify EMBEDDINGS_COMPUTE=1 scripts/kind-up.sh`: **pass** after load repair. Snapshot 2026.11.1 loaded **32,153 issues and 32,153 embeddings**, all for `BAAI/bge-small-en-v1.5`. Load completed with exit 0, API Ready, no API restarts. The final API image (`story-3-1-final2`) was loaded and deployed before Gateway checks.
- Kind compute report: embedding 1,972.4 seconds; total load 2,010.4 seconds; overall kind-up to Ready 2,073 seconds, within the 3,000-second embeddings Job deadline. Last observed load cgroup peak before completion: 887,238,656 bytes (about 846Mi), below 2Gi. The optional local compute pass exceeds the normal 600-second load-report budget; CI/default load does not compute embeddings.
- Before the load committed, the actual configured-model pod was **NotReady** and `/readyz` returned **503**, explicitly naming `BAAI/bge-small-en-v1.5` versus `None`. After the atomic commit it became Ready. Unit tests also establish mismatch against another stored model id.
- `TICKETSCOPE_DENSE_ENABLED=1 ... uv run pytest -m kind tests/integrated/test_dense_kind.py -q`: **4 passed**. Both query shapes returned ten ranked cosine results whose outcomes match Postgres; both traces in Tempo contain an `embeddings BAAI/bge-small-en-v1.5` child under `retrieval dense`; 16 concurrent real-model Gateway searches passed. API cgroup peak after these requests: **351,531,008 bytes (about 335Mi)** under 384Mi; **zero restarts**.
- `TAG=story-3-1-final2 scripts/kind-up.sh`: **pass**, flag off. API Ready in 38 seconds; Cluster Ready and Gateway available in 64 seconds. Load took **9.2 seconds**, within its 600-second budget, with no embeddings computed.
- `TICKETSCOPE_DENSE_ENABLED=0 ... uv run pytest -m kind tests/integrated tests/smoke -q`: **35 passed, 1 skipped** in 312.88 seconds. The intentional skip is concurrent dense inference when embeddings are off. Includes dense 503 problem responses, cleared embedding state, unchanged keyword golden results (vague rank 5; log-heavy rank 9), schema/outcomes, traces, backups and upgrades.
- I/O matrix audit: all rows have passing checks. Vague/log-heavy and flag-off behavior passed on kind; matching and mismatched readiness passed application tests plus actual pre/post-load Kubernetes observations; exclusion and mixed dimensions passed real Postgres tests; inference failure and post-copy database rollback passed their dedicated tests.

### Residual risks and ownership

Actual GitHub PR CI/eval workflow runs were not launched or claimed; no push was performed. Existing model revision/checksum, independent numerical oracle and CI SQL-test wiring items remain as recorded for the orchestrator. The successful local kind/Tempo evidence is reported here without changing the existing ledger's status or resolution. The optional CPU compute pass is slow on this four-core Docker VM; the default keyword-only load stays fast. The new pre-existing corpus-lineage race remains deferred.
