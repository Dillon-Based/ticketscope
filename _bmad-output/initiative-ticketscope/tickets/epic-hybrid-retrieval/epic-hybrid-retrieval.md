---
type: epic
title: "Dense and hybrid retrieval, scored against keyword"
parent: initiative-ticketscope
covers: [R2, R6]
sources: []
companions: []
after: []
refined: false
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
