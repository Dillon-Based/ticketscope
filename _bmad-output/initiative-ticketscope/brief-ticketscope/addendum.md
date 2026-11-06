---
title: "Addendum: ticketscope brief"
created: 2026-11-05
updated: 2026-11-05
---

# Addendum: ticketscope brief

Detail that belongs downstream (architecture, PRD) and was kept out of the brief. Figures were researched 2026-11-05, us-east-1. Verify them before quoting.

## AWS Kubernetes cost options

| Setup | Contents | ~$/mo |
|---|---|---|
| Always-on EKS, minimal | Control plane $73, 2× t4g.medium spot ~$20, EBS ~$4, IPv4 ~$7; no NAT or LB | ~$105 (~$155 with ALB + NAT) |
| Ephemeral EKS, ~10 h/mo | ~$0.25–0.30 per spin-up hour, plus ECR/S3 state/Route53 | ~$5 |
| k3s on one t4g.large, always-on | Instance, 30 GB gp3, IPv4 | ~$55 on-demand / ~$25 spot |

- EKS has no free tier. Extended-support versions cost $0.60/hr, so keep the version current. EKS Auto Mode adds ~12% to the per-instance price.
- New accounts created after 2025-07-15 get up to $200 in credits, valid for 12 months. The Free plan closes the account automatically at 6 months unless you upgrade. Whether EKS is allowed on the Free plan is unconfirmed.
- Ephemeral EKS gotchas:
  - The control plane takes 12–15 min to create.
  - The LB controller and the EBS CSI driver create resources outside Terraform state. Delete Services/PVCs before `terraform destroy`.
  - Avoid NAT: use public subnets or VPC endpoints.
  - KMS keys and log groups can linger after destroy.
- Fargate is a poor fit: it supports neither DaemonSets (OTel agents) nor EBS volumes (CloudNativePG).
- Hiring-perception evidence on k3s versus EKS is anecdotal only; EKS matches the vocabulary used in postings.

## MCP state (late 2026)

- The current spec version is 2026-07-28. It is stateless (no initialize handshake; `server/discover`) and uses Streamable HTTP as the remote transport and OAuth 2.1 with Client ID Metadata Documents. OTel trace-context propagation in `_meta` is documented.
- Governance sits with the Linux Foundation's Agentic AI Foundation. Major clients support MCP: Claude, ChatGPT, Cursor, Gemini, Copilot, and VS Code.
- A credible portfolio shape: a stateless remote server behind the cluster ingress, exposing `search_similar_issues` and `get_issue` with structured output, plus OAuth, OTel spans linked to the RAG spans, and an eval of tool-call behaviour.

## Vector stores

- A May 2026 analysis of 3,449 AI-engineer postings ranks vector stores as a differentiator (5–20% of postings), not table stakes.
- Amazon S3 Vectors went GA on 2025-12-02. At this corpus size it costs pennies, so it is a possible Terraform-managed backend to compare against pgvector.

## Target-posting vocabulary (sweep of 2026-11-03, ~64 roles)

| Signal | Postings |
|---|---|
| AWS | 44 |
| Kubernetes | 39 |
| Terraform | 35 |
| Agentic / agents | 17 |
| LLM / GenAI | ~13 |
| Grafana | 12 |
| Prometheus | 10 |
| OpenTelemetry | 5 |
| RAG | 4 |
| Vector DB | 4 |
| MCP | 4 |
| pgvector | 0 |

AI-heavy roles stress observability and evaluation of AI systems more than any particular store. README wording could mirror these phrases:

- "observability and evaluation for agentic systems: tracing, token and cost telemetry, latency, quality/eval harnesses"
- "infrastructure supporting LLMs, RAG, embeddings, vector stores, and AI agents"

## Claim discipline (from the author's claims ledger)

- The project's CI numbers (Recall@k, MRR, latency) are a valid system of record. They would be the author's first claimable retrieval figures.
- Earlier work-era retrieval figures stay unclaimable.
- README text marked outward-facing cannot say "vector database" until the claims ledger has a new row; until then, its pre-commit check blocks the phrase.
- The project is described as "a personal project, deployed and operated on Kubernetes", never as production.

## youscope reference (~/youscope, June 2025)

- Patterns to reuse:
  - A regex-key plus co-occurrence recommender, usable as a non-ML baseline.
  - The question-first query ("what are you trying to learn?").
  - A dummy-client fallback, so the app runs with no credentials.
  - Run logging as a source of relevance labels.
- Must not carry over: any of youscope's app, team or wizard names, its domain-specific identifier keys, or its local DB, log and .env contents. These are work-derived and stay out of this public repo.
