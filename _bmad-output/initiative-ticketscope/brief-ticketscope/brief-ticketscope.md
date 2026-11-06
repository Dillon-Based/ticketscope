---
title: "Product Brief: ticketscope"
status: final
created: 2026-11-05
updated: 2026-11-05
---

# Product Brief: ticketscope

## Executive Summary

ticketscope answers a triage engineer's first question about any ticket: *has anyone seen this before, and what did we do about it?* It is a hybrid keyword-and-embedding search service over past issues. You can query it from a web page, or from Claude Desktop through a remote MCP server. Either way it returns the most similar past issues and how they ended.

It is a personal portfolio project, built in public on Kubernetes GitHub issues and designed around a real gap: a triage team (called DTU here) with no tools team of its own. The original version stalled inside a company for organisational reasons. This version is built to be finished, measured and shown by 2026-12-31.

The point is what it proves. The author can:
- build a RAG retrieval system and measure it in CI, publishing the results even when they're unflattering
- expose that system to AI agents through a remote MCP server with auth and traces
- run the system on Kubernetes they provisioned themselves with Terraform, rebuilt from zero for each demo

## The Problem

DTU is a tier-2 triage team at a large platform company. Tickets come in written by whoever filed them. Some are one vague line ("login failing for some users"). Others are pages of pasted logs. Either way, the engineer who picks it up asks the same first question: *has anyone seen this before, and what did we do about it?*

Today the answer lives in people's memories and in a ticket tracker whose keyword search fails both kinds of ticket. Vague tickets share no words with their earlier twins. Log-heavy tickets drown the signal in noise. So engineers re-investigate solved problems, duplicates pile up, and new team members can't use the team's history at all.

DTU has no tools team. Nobody is going to build this for them.

## Who This Serves

- **In the story: the DTU triage engineer.** They are mid-ticket and want "tickets like this one, and how they ended" in seconds. They ask from wherever they already work: a search page, or an AI assistant such as Claude Desktop calling ticketscope as a tool.
- **In reality: a hiring manager or interviewer** for AI-platform, platform and DevOps roles. They read the README, follow the live URL, and look for proof of the three abilities listed above. The project is built for this reader first. When serving DTU and serving this reader conflict, this reader wins.

## The Solution

ticketscope is reachable two ways: a single web page, and a **remote MCP server** that Claude Desktop (or any MCP client) can call as a tool. Ask it about a ticket, vague or log-heavy, and it returns the most similar past issues and how each one ended.

- **Corpus.** Public Kubernetes GitHub issues stand in for DTU's tickets. Like DTU's, they range from one-liners to pages of logs, and issues closed as duplicates supply labelled ground truth.
- **Retrieval is the product.** Hybrid search combines keyword (BM25) and dense embeddings. Keyword search catches the exact error strings and identifiers in logs. Embeddings catch vague tickets that share meaning but not words. ticketscope does not generate answers itself: the MCP client's model writes the answer from what ticketscope retrieves. That split is deliberate: ticketscope owns retrieval quality, the client owns generation.
- **Vector store.** Postgres + pgvector, run on the cluster by the CloudNativePG operator. This shows a stateful database operated on Kubernetes (volumes, backups), not only a vector index.
- **Measured, not asserted.** An eval job scores keyword, dense and hybrid retrieval (Recall@k, MRR, latency) on labelled duplicate pairs. It reports short and log-heavy tickets separately, and CI blocks merges that regress the scores.
- **Observable end to end.** OpenTelemetry traces, using the GenAI semantic conventions, follow one request from the MCP tool call through retrieval to the database.
- **Rebuildable from zero.** Terraform provisions an EKS cluster on demand, Helm deploys the app, and GitHub Actions deploys through OIDC, so no cloud keys are stored. `apply` brings up the live URL for a demo, and `destroy` takes it down, so it costs a few dollars a month. CI runs the same chart on a local kind cluster.

## What Makes This Different

None of the technology is novel, and the brief doesn't pretend otherwise. Most RAG portfolio demos are a notebook or a single container calling an LLM. ticketscope differs in three ways:
- **Measured:** retrieval quality is scored in CI on labelled data, and the results are published whatever they show.
- **Operated:** the whole stack is reproducible from Terraform, and traced from agent tool call to database row.
- **Agent-ready:** a remote, authenticated MCP server built to the current spec, not a local stdio toy.

The moat is evidence, not technology.

## Success Criteria

By 2026-12-31:

1. **The eval gate runs on every pull request.** It scores keyword, dense and hybrid retrieval (Recall@k, MRR, p95 latency), split by short and log-heavy tickets. A regression blocks the merge. The README's results table comes from CI output and is published as-is, even if hybrid doesn't win. There's no target number. The eval tests a hypothesis, not a goal.
2. **Claude Desktop connects to the live MCP server,** authenticates, calls `search_similar_issues`, and answers from the results. One trace shows that call end to end.
3. **`terraform apply` brings up the live URL from nothing,** and `destroy` leaves nothing billing. Spin-up in under 30 minutes. Hosting cost under $10/month.
4. **A reviewer gets it in 5 minutes:** README with an architecture diagram, the CI eval table, a short recorded clip of Claude Desktop using ticketscope, a trace screenshot, and two or three decision records.
5. **Interview test:** the author can answer these from first-hand experience:
   - why hybrid retrieval, and what the eval showed
   - how Postgres runs on Kubernetes through an operator (storage, backups, failure)
   - how an agent's tool call is traced across services
   - how to stand up and tear down EKS safely and cheaply
6. **Claims stay honest.** Every claim the project supports gets a row in the author's claims ledger, backed by repo or CI records. The project is described as "a personal project, deployed and operated on Kubernetes", never as production.

## Scope

**In (done by 2026-12-31):**
- Ingest job and hybrid retrieval API.
- Remote MCP server with auth.
- One search page.
- Eval gate in CI.
- OTel traces plus one Grafana dashboard.
- Terraform/Helm/Actions for short-lived EKS.
- README with an architecture diagram and two or three decision records.

**Out:**
- Server-side LLM answers.
- DTU's real data, or any integration with their tracker.
- Handover work.
- Always-on hosting.
- Multi-tenancy, autoscaling experiments, model fine-tuning.
- Any UI beyond one page.

**If behind schedule, cut in this order:** Grafana dashboard → MCP OAuth → EKS (fall back to kind only) → eval gate. The eval gate is cut last because its CI numbers are the project's only claimable retrieval figures.

## Open Questions

- **Ground truth volume:** do Kubernetes issues closed as duplicates (`triage/duplicate` label, "duplicate of #N" comments) give a large enough labelled test set, especially for short tickets?
- **Corpus fit:** many Kubernetes issues are developer bug reports, not support requests. How far does that gap weaken the DTU story, and should the eval set favour support-style issues?
- **"How it ended":** where does each issue's outcome come from: the closing comment, the linked PR, or the label?
- **Corpus terms:** what do GitHub's terms allow when issue text is stored and served in a public demo index?
- **MCP auth:** which OAuth provider or authorisation server should the MCP server use, and does it work with Claude Desktop's remote-connector flow?
- **AWS account:** do the new-account credits cover EKS, or does the account need upgrading to the paid plan?
- **Embedding model:** which small CPU model, and should the choice itself be a scored eval?

## After 2026-12-31

If it's finished, ticketscope is the evidence behind the AI-platform claims in the author's job search. It could later be handed to the real team as a starting point, running on their own data inside their own environment. That is an option, not a commitment, and not a claim. Before any handover, check the separation and IP terms.
