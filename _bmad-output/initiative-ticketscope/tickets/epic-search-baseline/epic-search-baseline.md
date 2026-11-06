---
type: epic
title: "Keyword search over Kubernetes issues, deployed on kind"
parent: initiative-ticketscope
covers: [R1, R2, R3, R5, R8, R11]
sources: []
companions: []
after: []
refined: true
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

## Requirements

- R1 (parent R1): An ingest job publishes a versioned corpus snapshot of closed `kubernetes/kubernetes` issues (not PRs) from about the last three years, capped at 20,000. The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues.
- R2 (parent R1): A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome.
- R3 (parent R2): Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes.
- R4 (parent R5): One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries.
- R5 (parent R3): CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes.
- R6 (parent R8): One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace.
- R7 (parent R11): Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR.

## Constraints

- **Outcome precedence:**
  1. duplicate: a `marked_as_duplicate` event or the `triage/duplicate` label
  2. fixed: closed by a merged linked PR
  3. not_planned: from `state_reason`
  4. stale: a `lifecycle/rotten` or `lifecycle/stale` label
  5. answered: a support issue closed after a maintainer comment
  6. unknown

  Changing the precedence requires a reload and a baseline update (spine AD-8, AD-12).
- **Outcome terms:**
  - A support issue carries the `kind/support` label.
  - A maintainer comment has an `author_association` of OWNER, MEMBER or COLLABORATOR.
  - The `/v1` outcome `source` by branch: duplicate → `label`; fixed → `linked_pr`; answered → `closing_comment`; not_planned, stale and unknown → `null`.
- **Example queries:** one vague and one log-heavy query, picked by the load story from the real snapshot and recorded in Notes; the page, sweep and integrated-check stories use them.
- **Corpus scope:** closed `kubernetes/kubernetes` issues only, no PRs, about the last three years, capped at 20,000. The ingest story tunes the window so the load finishes within 10 minutes, its share of the 30-minute spin-up (initiative R10). Published snapshots are never overwritten.
- **Corpus terms:** a human-in-the-loop spike story settles them before any snapshot is published. Ingest's publish step waits on it.
- **Public repo:** the repo is public on GitHub, so Release assets are public.
- **Kind rule:** a deterministic core function over the issue body that counts fenced blocks and log-like lines. The load story sets the threshold and reports the split. Changing it requires a reload and a baseline update (spine AD-8).
- **Snapshot format:** compressed JSONL, one issue per line, with its JSON Schema committed in the repo as epic-eval-gate's contract (spine AD-6).
- **Toolchain:** ruff for lint and format, pyright and pytest. Test-framework depth goes to `bmad-tea-framework`.

## Done when

- CI deploys the platform and app releases to kind on every PR. CloudNativePG Postgres runs with pgvector, pg_textsearch, two instances, persistent volumes, and backups to SeaweedFS, and a backup completes (R5, R7).
- The corpus-terms spike has settled the terms. A published corpus snapshot then validates against the committed JSON Schema and holds short and log-heavy issues with labels, comments and timeline events (R1).
- The load job stores every issue with its kind and an outcome, and reports the share of each (R2).
- A vague query and a log-heavy query to the keyword mode of `/v1/search` return ranked issues with outcomes, and the page shows them (R3, R4).
- A search request yields one trace with retrieval and database spans in Tempo, viewable in Grafana (R6).
- import-linter enforces the spine's layer rules in CI. The code follows the spine's /v1, span, Helm and CI contracts.
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
- Decision: Refined. The outcome precedence rule and the corpus scope are settled now; corpus terms go to a human-in-the-loop spike before ingest publishes; the repo is public (user, 2026-11-06).
- Decision: The kind-rule shape, the snapshot format and the toolchain are settled at refinement as Sofia's picks, unopposed. The page is left to its story: one server-rendered page from `api`, with no JS framework (user, 2026-11-06).
- Assumption: A GitHub-hosted runner fits kind with the platform release, two Postgres instances and SeaweedFS. The tracer story proves it first.
- Decision: Stories planned (11 entries). The tracer bullet is story 1, "Tracer: keyword search answers through the Gateway on kind", kept whole with the repo and CI setup inside it rather than split out, because it proves the riskiest path (user, 2026-11-06).
- Decision: Sequencing. The corpus-terms spike (2) comes second as the least certain part. Three lanes run after the tracer: data 2 → 4 → 3 → 5, API 6 → 7, platform 8; they meet at the trace story (9). Stories sharing code wait on each other through `after` (user, 2026-11-06).
- Decision: The tracer uses a synthetic fixture snapshot with no real issue text until the corpus terms are settled (user, 2026-11-06).
- Decision: The outcome terms and the example-query owner are settled as Sofia's picks (see Constraints) (user, 2026-11-06).
- Decision: The refactor sweep (10) and a closing integrated check on kind (11) are kept (user, 2026-11-06).
- Decision: The epic builds unattended through the loop; stories 1, 3 and 5 carry `plan_checkpoint`, and no story carries `done_checkpoint` (user, 2026-11-06).
