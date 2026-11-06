---
type: initiative
title: ticketscope
parent: none
sources:
  - _bmad-output/initiative-ticketscope/brief-ticketscope/brief-ticketscope.md
  - _bmad-output/initiative-ticketscope/brief-ticketscope/addendum.md
companions:
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
after: []
risk: high
---

# ticketscope

## Description

ticketscope is a hybrid keyword-and-embedding search service over public Kubernetes GitHub issues. It answers a triage engineer's first question about a ticket: *has anyone seen this before, and what did we do about it?* It is reachable from one web page and from a remote MCP server that Claude Desktop calls as a tool. It is a personal portfolio project, due 2026-12-31. What it has to prove is that the author can do three things: build and measure a RAG retrieval system in CI, expose it to agents through an authenticated and traced remote MCP server, and run it on EKS rebuilt from zero with Terraform. The brief and its addendum are the sources.

## Outcome

A hiring manager for AI-platform, platform or DevOps roles can verify all three abilities from the README, the live URL, CI output and a trace within 5 minutes, as measured by the brief's Success Criteria 1–6.

## Requirements

- R1 (brief Solution: Corpus; Scope In: ingest job): An ingest job loads public Kubernetes GitHub issues, both short and vague and long and log-heavy, each with how it ended. It is met when the index holds both kinds, with an outcome recorded for every issue.
- R2 (brief Solution: Retrieval is the product; Scope In: hybrid retrieval API): Given ticket text, a retrieval API returns the most similar past issues and how each ended, using keyword (BM25), dense or hybrid retrieval. It is met when a vague query and a log-heavy query each return ranked issues with outcomes in every mode.
- R3 (brief Solution: Vector store; Success Criteria 5): Issues and embeddings are stored in Postgres + pgvector, which CloudNativePG runs on the cluster with persistent volumes and backups. It is met when a backup has been restored and an instance failure has been survived, and both are recorded.
- R4 (brief Solution; Success Criteria 2; Scope In: remote MCP server with auth): A remote MCP server exposes `search_similar_issues`. It is met when Claude Desktop connects to the live server, authenticates, calls the tool and answers from its results.
- R5 (brief Scope In: one search page): One web page takes ticket text and shows the similar past issues and how each ended.
- R6 (brief Solution: Measured; Success Criteria 1): An eval job scores keyword, dense and hybrid retrieval on labelled duplicate pairs, using Recall@k, MRR and p95 latency. Short tickets and log-heavy tickets are reported separately.
- R7 (brief Success Criteria 1; Scope In: eval gate in CI): The eval runs on every pull request, and a score regression blocks the merge. The README results table is generated from CI output and published as-is, whatever it shows.
- R8 (brief Solution: Observable; Success Criteria 2): OpenTelemetry traces, using the GenAI semantic conventions, follow one request from the MCP tool call through retrieval to the database. It is met when one trace spans all three.
- R9 (brief Scope In: one Grafana dashboard): One Grafana dashboard shows the service's telemetry.
- R10 (brief Solution: Rebuildable; Success Criteria 3): Starting from a persistent bootstrap layer (DNS zone, certificate, OIDC deploy role, state and backup bucket, image registry), `terraform apply` of the environment brings up EKS and the live URL in under 30 minutes, and destroying the environment leaves only that bootstrap layer billing. It is met when a recorded spin-up finishes in under 30 minutes and a post-destroy check finds nothing but the bootstrap layer.
- R11 (brief Solution: Rebuildable): Helm deploys the app. GitHub Actions deploys to EKS through OIDC, with no stored cloud keys. CI runs the same chart on a local kind cluster.
- R12 (brief Success Criteria 4; Scope In: README): A reviewer understands the project in 5 minutes from the README, which has an architecture diagram, the CI eval table, a recorded clip of Claude Desktop using ticketscope, a trace screenshot, and two or three decision records.
- R13 (brief Success Criteria 6): Every claim the project supports has a row in the author's claims ledger, backed by a repo or CI record.

## Constraints

- The deadline for a working, linkable version is 2026-12-31 (brief Scope).
- There is no server-side LLM generation. ticketscope returns retrieval results only, and the MCP client's model writes the answer (brief Solution, Scope Out).
- The vector store is Postgres + pgvector, operated on the cluster by CloudNativePG (brief Solution: Vector store).
- EKS is short-lived: applied for a demo and destroyed afterwards, never always-on. Hosting, including the persistent bootstrap layer, costs under $10/month (brief Success Criteria 3, Scope Out).
- No cloud keys are stored. Deploys authenticate through GitHub Actions OIDC (brief Solution: Rebuildable).
- The remote MCP server follows the current spec (2026-07-28): stateless, Streamable HTTP and OAuth 2.1, not local stdio (brief What Makes This Different; addendum MCP state).
- Only public material is used. That means no real DTU data or tracker integration, no real team or employer names, and nothing from youscope's work-derived names, identifier keys, database, logs or .env files (brief Scope Out; addendum youscope reference).
- The project is described as "a personal project, deployed and operated on Kubernetes", never as production. Outward-facing README text may not say "vector database" until the claims ledger has a row for it (brief Success Criteria 6; addendum Claim discipline).
- If the project falls behind schedule, cut in this order: Grafana dashboard, MCP OAuth, EKS (fall back to kind only), eval gate. The eval gate is cut last (brief Scope).
- When serving DTU and serving the hiring-manager reader conflict, the reader wins (brief Who This Serves).

## Done when

- The eval gate runs on every PR, scoring keyword, dense and hybrid retrieval split by ticket kind. A regression blocks the merge, and the README table comes from CI output (R6, R7).
- Claude Desktop connects to the live MCP server, authenticates, calls `search_similar_issues` and answers from the results. One trace shows that call from end to end (R4, R8).
- From the bootstrap layer, `terraform apply` brings up the live URL in under 30 minutes, destroying the environment leaves only the bootstrap layer billing, and hosting costs under $10/month (R10, R11).
- A reviewer gets the project within 5 minutes from the README, the diagram, the eval table, the clip, the trace screenshot and the decision records (R12).
- Every supported claim has a backed row in the claims ledger, and the CloudNativePG restore and failure drills are recorded (R3, R13).

## Boundaries

- Out: server-side LLM answers, DTU's real data or any tracker integration, handover work, always-on hosting, multi-tenancy, autoscaling experiments, model fine-tuning, and any UI beyond one page (brief Scope Out).
- Out: S3 Vectors or any second vector store (addendum Vector stores lists it only as a possible comparison).
- Out: an eval of tool-call behaviour, and a youscope-style non-ML recommender baseline; keyword BM25 is the baseline (addendum MCP state, youscope reference; spine Deferred).
- Touch point: GitHub issues API — the source of the corpus, read only; owner: epic-search-baseline
- Touch point: GitHub Releases — hosts the versioned corpus snapshot and precomputed embeddings; owner: epic-search-baseline
- Touch point: Claude Desktop — the MCP client, configured only; owner: epic-mcp-server
- Touch point: a tunnel service — exposes the kind cluster to Claude Desktop before EKS exists; owner: epic-mcp-server
- Touch point: AWS account, S3, ECR and DNS — consumed and configured by Terraform; owner: epic-eks-environment
- Touch point: an external hosted OAuth authorisation server — configured, not built or run on the cluster; owner: epic-mcp-oauth
- Touch point: the author's claims ledger — rows added outside this repo; owner: epic-reviewer-package
- Tracer path: an issue is ingested into a corpus snapshot and loaded into Postgres + pgvector, the retrieval API ranks it for a query, the result is returned through the page or the MCP tool to Claude Desktop, and the request is traced and deployed by Helm on the cluster.

## References

- brief — _bmad-output/initiative-ticketscope/brief-ticketscope/brief-ticketscope.md, sections The Solution, Success Criteria, Scope, Open Questions
- addendum — _bmad-output/initiative-ticketscope/brief-ticketscope/addendum.md, sections AWS Kubernetes cost options, MCP state, Claim discipline, youscope reference
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, adopted companion; its AD ids are stable and every epic cites the ones that bind it

## Notes

- Decision: Sliced into 8 epics, one capability each, and every cut-list item (Grafana, MCP OAuth, EKS, eval gate) is a whole epic so a cut drops an epic cleanly (user, 2026-11-05).
- Decision: MCP OAuth and the Grafana dashboard are their own epics, not part of epic-mcp-server or the observability work (user took Sofia's pick, 2026-11-05).
- Decision: epic-mcp-server is built before epic-eks-environment, because the MCP server is never cut and EKS is; Claude Desktop reaches it through a tunnel until EKS lands (user took Sofia's pick, 2026-11-05).
- Decision: The platform baseline (scaffold, CI, Helm on kind, CloudNativePG) is the first stories of epic-search-baseline rather than its own epic; the epic stays whole despite its likely 10–12 stories (user took Sofia's pick, 2026-11-05).
- Decision: Shared decisions (stack, retrieval API contract, span conventions, chart and CI layout, schema ownership, corpus reload versus restore at spin-up) are settled in a bmad-architecture run before epic-search-baseline's stories are planned (user took Sofia's pick, 2026-11-05).
- Decision: The bmad-architecture spine is adopted as a companion, and every epic cites the AD ids that bind it. R10, the cost constraint and the drills assumption now follow its persistent-bootstrap and ephemeral-environment split (user, 2026-11-05).
- Decision: Cutting epic-eval-gate drops only R7's blocking merge check. The eval job, baseline and README table (R6) survive, because epic-hybrid-retrieval chooses its model by the eval and epic-reviewer-package publishes the table (user, 2026-11-06).
- Decision: If epic-eks-environment is cut, epic-reviewer-package records the CloudNativePG restore and failure drills on kind (user, 2026-11-06).
- Assumption: The cluster counts as production for every epic: kind in CI until the EKS epic lands, and EKS after that.
- Assumption: Success Criteria 5 (the interview test on CloudNativePG storage, backups and failure) is evidenced by a recorded restore drill and failure drill (R3), run on EKS, or on kind if epic-eks-environment is cut.
- Open question: Ground truth volume. Do `triage/duplicate` labels and "duplicate of #N" comments give a large enough labelled set, especially for short tickets? (brief Open Questions)
- Open question: Corpus fit. Should the eval set favour support-style issues over developer bug reports? (brief Open Questions)
- Open question: How it ended. Does an issue's outcome come from the closing comment, the linked PR or the label? The spine fixes the outcome's shape and computes it once at load; the rules are epic-search-baseline's. (brief Open Questions)
- Open question: Corpus terms. What do GitHub's terms allow when issue text is stored and republished as a public GitHub Release asset and demo index? epic-search-baseline settles it before the first snapshot is published. (brief Open Questions)
- Open question: MCP auth. Which external hosted OAuth authorisation server should be used, and does it work with Claude Desktop's remote-connector flow and Client ID Metadata Documents? The spine rules out running one on the cluster. (brief Open Questions)
- Open question: AWS account. Do the new-account credits cover EKS, or must the account move to the paid plan? (brief Open Questions; addendum AWS cost)
- Open question: Embedding model. Which small CPU model should be used? The spine settles that a scored eval chooses it, behind one embedder interface. (brief Open Questions)
