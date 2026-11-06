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

The platform baseline and the first working search, built to the spine's contracts.

- **Repo and CI.** One workflow per concern, plus a reusable kind-deploy step that epics 2 and 4 build on.
- **Releases on kind.** Two Helm releases, which epic 5 later deploys to EKS:
  - The platform release holds the operators, the Gateway, the OTel Collector, Tempo and Grafana.
  - The app release holds a two-instance CloudNativePG Postgres 18 with pgvector and pg_textsearch, backing up to SeaweedFS.
- **Corpus.** An ingest job publishes a versioned corpus snapshot of Kubernetes issues as a GitHub Release asset. A load job, the only writer, loads it with each issue's kind and outcome. Epic 2 derives its labelled pairs from that snapshot, and epic 3 adds its embedding table.
- **Search.** A keyword (BM25) retrieval API serves the one search page under the /v1 contract and retriever registry, which epic 3 extends and epic 4 calls.
- **Tracing.** Retrieval and database spans follow the span contract, which epics 3, 4 and 7 build on.

## Outcome

A triage engineer pastes a vague or log-heavy ticket into the page on the kind-deployed chart and sees ranked Kubernetes issues with how each ended (initiative R1, R2, R5).

## Done when

- CI deploys the platform and app releases to kind on every PR. CloudNativePG Postgres runs with pgvector, pg_textsearch, two instances, persistent volumes, and backups to SeaweedFS (R3, R11).
- A published corpus snapshot holds short and log-heavy Kubernetes issues with labels, comments and timeline events. The load job stores each issue with its kind and an outcome (R1).
- A vague query and a log-heavy query to the keyword mode of /v1/search return ranked issues with outcomes, and the page shows them (R2, R5).
- A search request yields one trace with retrieval and database spans in Tempo, viewable in Grafana (R8).
- import-linter enforces the spine's layer rules in CI, and the code follows its /v1, span, Helm and CI contracts.
- The corpus-terms open question is settled before the first snapshot is published.
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Dense and hybrid modes and the embedding table belong to epic-hybrid-retrieval; extracting labelled pairs and scoring belong to epic-eval-gate.
- The MCP server belongs to epic-mcp-server. EKS, S3 backups and the recorded drills belong to epic-eks-environment.
- Touch point: GitHub issues API — the source of the corpus, read only; owner: epic-search-baseline
- Touch point: GitHub Releases — hosts the versioned corpus snapshot and precomputed embeddings; owner: epic-search-baseline

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R1, R2, R3, R5, R8, R11)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1–AD-4, AD-6–AD-11, AD-13, AD-14, AD-16–AD-22

## Notes

- Decision: Adopted the architecture spine. The snapshot/load split, the platform release with Tempo and Grafana, pg_textsearch for BM25, and SeaweedFS backups on kind replace this epic's earlier wording (user, 2026-11-05).
