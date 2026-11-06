---
type: epic
title: "Keyword search over Kubernetes issues, deployed on kind"
parent: initiative-ticketscope
covers: [R1, R2, R3, R5, R8, R11]
sources: []
companions: []
after: []
refined: false
risk: high
---

# Keyword search over Kubernetes issues, deployed on kind

## Description

The platform baseline and the first working search. The repo and CI are in place, with one workflow per concern and a reusable kind-deploy step. Images and a Helm chart run on kind with CloudNativePG Postgres and the pgvector extension enabled. The ingest job stores Kubernetes issues with labels, closing comments and how each ended. A keyword (BM25) retrieval API, with a pinned mode parameter and response contract, serves the one search page. An OTel collector and a trace backend ship in the chart, and retrieval and database spans follow a pinned span contract. Every later epic builds on these contracts.

## Outcome

A triage engineer pastes a vague or log-heavy ticket into the page on the kind-deployed chart and sees ranked Kubernetes issues with how each ended (initiative R1, R2, R5).

## Done when

- CI deploys the Helm chart to kind with CloudNativePG Postgres (pgvector enabled) and persistent volumes, on every PR (R3, R11).
- The ingest job loads short and log-heavy Kubernetes issues, each with labels, closing comments and an outcome (R1).
- A vague query and a log-heavy query to the keyword mode of the retrieval API return ranked issues with outcomes, and the page shows them (R2, R5).
- A search request yields one trace with retrieval and database spans in the trace backend (R8).
- The API's mode parameter and response contract, the span contract, the CI workflow layout and the chart layout are written down for epics 2–7.
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Dense and hybrid modes and the embedding column belong to epic-hybrid-retrieval; extracting labelled pairs and scoring belong to epic-eval-gate.
- The MCP server belongs to epic-mcp-server; EKS, S3 backups and drills belong to epic-eks-environment.
- Touch point: GitHub issues API — the source of the corpus, read only; owner: epic-search-baseline

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R1, R2, R3, R5, R8, R11)
