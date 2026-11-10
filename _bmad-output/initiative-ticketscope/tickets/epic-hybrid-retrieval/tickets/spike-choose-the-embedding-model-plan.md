---
title: 'Spike 3.3: choose the embedding model'
type: 'chore'
ticket: '3'
created: '2026-11-09'
status: 'done'
baseline_revision: '90364f5e77d0d9259da2f5b517f471cb063a83d0'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 1 baked bge-small-en-v1.5 in as a default; R3 needs a scored comparison that picks the model. The eval job passes no embedder (`score.py` skips dense), so it cannot score dense today.

**Approach:** A throwaway harness, `scripts/embedding_spike.py`, embeds the loaded kind corpus with each candidate, stores vectors under each model id in `issue_embedding`, and scores dense and hybrid with core's own retrievers and `score.py` tallies on the committed pairs file. A findings file beside the epic records the table, the chosen model id and preprocessing version, and the reason.

## Boundaries & Constraints

**Always:** Reuse `core.modes` retrievers, `first_member_rank` and the `_ModeTally` logic so numbers match the future gate. Same pairs file, k=10, query excluded, kinds `short`/`log_heavy`. Candidates: `BAAI/bge-small-en-v1.5` (default), `snowflake/snowflake-arctic-embed-xs`, `sentence-transformers/all-MiniLM-L6-v2`. The 2000-char cut is tested against each model's token limit (count truncated issues), and cut variants are named by preprocessing version.

**Never:** Change product code, chart values, the Dockerfile, `baseline.json` or the `/v1` contract. No decision is recorded in the epic (a person does that). No model is published as a Release asset.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Happy path | kind corpus loaded, three models | JSON results per model with Recall@10, MRR@10 by kind and overall, embed seconds, peak RSS | n/a |
| Model absent from fastembed | unknown id | that candidate is reported as failed, others continue | non-zero exit if none ran |
| No corpus | `corpus_meta` empty | stops before embedding | message names `kind-up.sh` |

</frozen-after-approval>

## Code Map

- `src/ticketscope/core/modes.py` -- `DenseRetriever`, `HybridRetriever`, `KeywordRetriever`; build directly with an embedder.
- `src/ticketscope/jobs/eval/score.py` -- `first_member_rank`, `_Tally`/`_ModeTally`, `K`, kinds; skips dense because `available(store, None)` is False. Do not change.
- `src/ticketscope/core/derive.py` -- `embedding_text`, `cut_for_embedding`, `EMBEDDING_MAX_CHARS=2000`, `EMBEDDING_RULE_VERSION=emb1`.
- `src/ticketscope/adapters/embedder.py` -- `FastEmbedEmbedder(model_id, cache_dir)`.
- `src/ticketscope/adapters/postgres.py` -- `PostgresCorpusStore` (`dense_search`, `has_embeddings`), `replace_corpus` (replaces all rows: do not use); embeddings table is `issue_embedding(issue_number, model_id, embedding)`.
- `eval/pairs/2026.11.1.jsonl` -- 10,473 pairs; `images/app.Dockerfile` -- model baked at `/models`.
- kind cluster `ticketscope` is up with CNPG `ticketscope-db`; reach it with `kubectl port-forward`.

## Tasks & Acceptance

**Execution:**
- [ ] `scripts/embedding_spike.py` -- embed issues per model (batch 8, as `load`), insert rows, score keyword/dense/hybrid, record embed seconds per issue and total, peak RSS (`resource`) for load-model and embed step, model dir size, truncated-issue count at the token limit; print JSON -- the measurements R3 names.
- [ ] Run it against kind (`kubectl port-forward` to `ticketscope-db`, read-write credential from the cluster secret) for all three models; delete the spike's `issue_embedding` rows afterwards.
- [ ] `_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/spike-choose-the-embedding-model-findings.md` -- table, chosen model id, preprocessing version, reason, and the one-line follow-up if the pick differs from the default.

**Acceptance Criteria:**
- Given the findings file, when a person reads it, then it holds Recall@10 and MRR@10 by kind and overall for every candidate, embedding time per issue and total, peak memory, image-size impact and the cut test.
- Given the pick differs from bge-small-en-v1.5, then the findings state the one-line change and where.
- Given the run, then no tracked file outside `scripts/embedding_spike.py` and the findings file changed.

## Design Notes

Deviation from the ticket's wording, to approve: the harness runs on the host against kind's Postgres instead of rebuilding the app image and rerunning `load` per model on kind (three image builds, three ~50 minute loads). Quality and embedding time are model-bound and measured the same way. Peak memory is the harness process RSS around model load and embedding, a proxy for api and load. Image size is the model directory size added to the 190 MB app image. Query embedding is live, as the eval will do.

## Verification

**Commands:**
- `uv run python scripts/embedding_spike.py --help` -- expected: usage prints
- `uv run ruff check scripts/embedding_spike.py` -- expected: clean

**Manual checks:**
- Findings file numbers match the JSON the harness printed; `select count(*) from issue_embedding` is 0 afterwards for spike model ids.
