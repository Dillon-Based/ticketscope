---
type: epic
title: "Dense and hybrid retrieval, scored against keyword"
parent: initiative-ticketscope
covers: [R2, R6]
sources: []
companions: []
after: []
refined: true
risk: medium
---

# Dense and hybrid retrieval, scored against keyword

## Description

Issues are embedded with a small CPU model into an `issue_embedding` table keyed by model, which this epic owns in pgvector. A scored eval chooses the model.

- **Embeddings.** Precomputed embeddings are published as Release assets, so spin-up never embeds.
- **Modes.** Dense and hybrid modes join keyword in the retriever registry under epic 1's /v1 contract and span contract.
- **Scoring.** Epic 2's gate scores all three in CI, and the results are published whatever they show.
- **Downstream.** The model's CPU and memory needs set the chart defaults that epic 5 sizes nodes for, and the final numbers feed epic 8.

## Outcome

The eval table compares keyword, dense and hybrid retrieval on short and log-heavy tickets, testing the brief's hybrid hypothesis (initiative R2, R6).

## Requirements

- R1 (parent R2): Every loaded issue has an embedding from the chosen model in `issue_embedding`, loaded from a precomputed Release asset pinned in `values.yaml`. It is met when `load` on kind fills the table from the pinned asset without computing any embedding, and `corpus_meta` records the model id.
- R2 (parent R2): Dense and hybrid retrieval are modes in the core registry, served by `/v1/search`. It is met when a vague query and a log-heavy query each return ranked issues with outcomes in dense and in hybrid mode on kind.
- R3 (parent R6): The embedding model is chosen by a scored eval. It is met when a committed record compares the candidate models on Recall@10, MRR@10 by ticket kind, embedding time and memory, and names the one chosen.
- R4 (parent R6): The CI eval table shows keyword, dense and hybrid side by side, split by ticket kind, and is published whatever it shows. It is met when the committed baseline and the README table carry all three modes from a CI run.
- R5 (parent R2): The chosen model's CPU, memory and embedding-time needs and the default retrieval mode are chart defaults in `values.yaml`. It is met when `api` runs Ready and answers a dense search on kind within those defaults, and a request that omits `mode` is served by the default mode.

## Constraints

- **Model runtime:** a small CPU model run through fastembed/ONNX behind the core `Embedder` port. Only `api` loads it at runtime (spine AD-3). The model is baked into the app image at build time, so nothing downloads at run time. The Hugging Face source is read only, at build time.
- **Embeddings are never computed in spin-up:** `load` computes them only on kind and only when the pinned asset is absent. CI and `env-up` load the asset (spine AD-21). Computing on kind is off by default and switched on for local runs.
- **Embedding asset:** keyed by snapshot, model and preprocessing, with a SHA-256. A person builds it with the committed publish script, which keeps its guards: clean `main`, never overwrites an asset, timed load under 10 minutes (spine AD-6). The pin and checksum sit in `values.yaml` beside the snapshot pin (spine AD-25).
- **Table:** `issue_embedding(issue_number, model_id, ...)` through the next ordered migration. The vector column has no fixed dimension, so a model change needs no schema change. Dense search is an exact scan with no index, which keeps eval deterministic. An index is added only if p95 demands it (spine AD-7, AD-21).
- **Preprocessing:** an issue is embedded as its title plus the start of its description, cut to the model's token limit. There is no chunking. The cut rule is part of the preprocessing version, so changing it forces a reload and a baseline update (spine AD-12, AD-21).
- **Hybrid:** reciprocal rank fusion with equal weights, in `core`, taking at least `k + |exclude|` candidates from each side. `score_kind` is `rrf`. Weights are tuned only if the scored eval justifies it (spine AD-9, AD-19).
- **Readiness:** `api` fails readiness when its configured model id differs from `corpus_meta.embedding_model_id` (spine AD-21).
- **Contract:** `/v1` and the span contract change only additively. Dense and hybrid emit the `embeddings {model}` span under `retrieval {mode}` (spine AD-4, AD-10).
- **Eval:** the eval job embeds each query's text live through the same `Embedder`, so dense p95 is honest. The run's cost is checked against the Job deadline, and the deadline is raised if needed. Dense and hybrid enter the gate as new modes, which pass and are reported (epic-eval-gate Constraints).
- **Default mode:** the mode with the best overall MRR@10, hybrid on a tie, set once in `values.yaml`. `mcp` has no default of its own (spine AD-25).

## Done when

- The embedding model is chosen by a scored eval. Every loaded issue has an embedding from it in `issue_embedding`, loaded from a precomputed Release asset (R2).
- A vague query and a log-heavy query each return ranked issues with outcomes in the dense and hybrid modes (R2).
- The CI eval table shows keyword, dense and hybrid side by side, split by ticket kind, and is published whatever it shows (R6).
- The model's CPU, memory and embedding-time needs are recorded as chart defaults in `values.yaml`, along with the default retrieval mode.
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Scoring and the gate belong to epic-eval-gate. The /v1 contract and span contract are epic-search-baseline's; this epic extends them additively and does not change them.
- In the chart, this epic owns the retrieval default-mode and `api` resource keys in `values.yaml`. Epic 4 owns the `mcp` keys.
- Out: model fine-tuning and any second vector store (initiative Boundaries).
- Touch point: the embedding model's download source (for example Hugging Face) — read only, at build time; owner: epic-hybrid-retrieval

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R2, R6)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1–AD-4, AD-6–AD-10, AD-12, AD-19–AD-21, AD-25

## Notes

- Waits on epic-search-baseline because: it needs pgvector, the retriever registry, the load job and the span contract.
- Waits on epic-eval-gate because: the eval job and CI gate score the new modes.
- Decision: Adopted the architecture spine. A model-keyed embedding table and precomputed embedding assets replace the single embedding column (user, 2026-11-05).
- Decision: Refined with Sofia's picks (user, "take your picks", 2026-11-08). The model is chosen by a spike after a tracer that uses bge-small-en-v1.5 as the default. A person builds the embedding asset with the extended publish script. The text embedded is title plus the start of the description, without chunking. Hybrid is equal-weight reciprocal rank fusion. The default mode is the best overall MRR@10, with hybrid on a tie. Dense search is an exact scan. Eval embeds queries live. The embedding asset is pinned in `values.yaml`.
- Decision: This epic starts after epic-eval-gate's stories 3 and 5 are done, so `eval/baseline.json` is not edited from two lanes (user, 2026-11-08).
- Decision: Tracer bullet is story 1, dense mode answering through `/v1` on kind, with `load` computing embeddings locally. CI stays keyword-only until the asset story lands, so PR runs never embed the corpus (user, 2026-11-08).
- Decision: A closing "Integrated check on kind" story follows the refactor sweep, as in epic-search-baseline (user, 2026-11-08).
- Decision: Embedding model is `BAAI/bge-small-en-v1.5` with preprocessing `pre1.kind2-t3.outcome3.emb1`, chosen by spike 3.3 (hybrid Recall@10 0.817, MRR@10 0.594, against keyword 0.771 / 0.550). Findings: `tickets/spike-choose-the-embedding-model-findings.md` (user, 2026-11-09).
- Decision: The refactor sweep (3.7) leaves the `CorpusStore` issue-lookup methods alone, because epic-mcp-server's 4.4 adds a by-key lookup there with no dependency path between the two (Sofia, at epic-mcp-server's set check, 2026-11-10).
