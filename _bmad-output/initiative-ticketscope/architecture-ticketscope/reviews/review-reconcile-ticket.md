# Review — reconcile spine against initiative ticket and epics

- Spine: `architecture-ticketscope/architecture-ticketscope.md` (draft, 2026-11-05)
- Inputs: `initiative-ticketscope.md` (R1–R13, Constraints, Done when, Boundaries, Notes), `tickets/tickets.toml`, `tickets/*/epic-*.md`
- Lens: what did not land in the spine, what the spine contradicts, and where the spine overrides a ticket so the ticket needs an update.

## Verdict

Mostly reconciled. All six shared decisions from the ticket Notes have a home: stack (Stack table, AD-2), retrieval API contract (AD-4), span conventions (AD-10), chart and CI layout (AD-13, AD-17), schema ownership (AD-7), and corpus reload versus restore (AD-6 picks reload from snapshot). Every `needs` edge in tickets.toml maps to an AD or a Deferred entry. The spine still needs one blocking fix and a few significant ones. It keeps one Done-when item (the R3 drills) only on a cuttable epic. It leaves the $10/month and under-30-minute constraints without an architectural guard. It also changes what several epics say, so those epics need ticket updates.

## Findings

### F1 — critical — R3 drills and backups exist only on EKS, which is cuttable

AD-18 says "The restore drill and the failure drill are run and recorded on EKS", and the only backup target is the bootstrap S3 bucket (AD-15, owned by epic 5). EKS is third on the cut list. If it is cut, the CloudNativePG backups, the restore drill and the failure drill have no home. That leaves the R3 Done-when line ("the CloudNativePG restore and failure drills are recorded") and Success Criteria 5 unmet, and epic 8's edge `{ epic = 5, needs = "... the recorded CloudNativePG drills" }` has no fallback. Compare the 8←6 edge, which states one.

Also missing: an instance-failure drill needs a CloudNativePG `Cluster` with at least 2 instances. The spine does not fix the instance count per environment, and on EKS that count drives cost.

**Fix:** Add a kind fallback to AD-18. For example, run an S3-compatible object store such as MinIO in `values-kind.yaml` so the Barman plugin and both drills can run on kind. Record the drills on whichever environment survives the cuts. Pin `instances` per values file, with at least 2 wherever the failure drill runs. Update the 8←5 edge in tickets.toml with an "if epic 5 is cut" clause.

### F2 — high — The under-30-minute spin-up has no budget, and corpus embedding sits on the spin-up path

AD-6 chooses reload over restore, and AD-7 makes `load` the only writer, embeddings included. Every `env-up` therefore runs EKS creation (often 10–15 minutes), the add-ons, both Helm releases, migration, load and, after epic 3, CPU embedding of the whole corpus. The embedding cache location is deferred to epic 3, but epic 5 owns the 30-minute Done-when. The spine never splits the 30 minutes between these steps.

**Fix:** Settle the cache in the spine instead of deferring it. For example, `load` reads precomputed embeddings keyed by `(snapshot version, model id, preprocessing version)` from a Release asset or from bootstrap S3, and computes them only on a cache miss. That keeps `load` the only writer. Add a timing budget to AD-15 or AD-17 and an `env-up.yml` step that fails past 30 minutes.

### F3 — high — "From nothing" and "destroy leaves nothing billing" are redefined, and the $10/month cap has no guard

AD-15 moves DNS, the certificate, ECR, OIDC and S3 into a persistent `bootstrap` that the author applies locally. It also redefines "nothing billing" as "only bootstrap remains". That contradicts:

- R10 and the epic 5 description: "Terraform provisions short-lived EKS with a public HTTPS URL (DNS name and certificate)" and "from nothing".

AD-15 may well be the right design, but the ticket does not say it, and the bootstrap's cost is not counted against the $10/month cap. That cost includes the Route53 zone ($0.50/month), domain registration, ECR storage, and S3 storage for state and backups.

The spine also has no invariant for:

- **Leftover billing resources.** Nothing covers the ALB the controller creates from the `HTTPRoute`, the EBS volumes from PVCs, the EKS KMS key, or the CloudWatch log groups. Epic 5's Done-when names all four. The fix is ordered teardown: uninstall the Helm releases and delete the PVCs before `terraform destroy`, and turn off the module's KMS key and cluster logging, or put them under Terraform.
- **An environment left running.** Nothing stops the cluster outliving the demo. The EKS control plane alone costs about $73/month if always on. The fix is a TTL or a scheduled `env-down`, plus an AWS Budgets alarm in bootstrap.

**Fix:** Add a cost-and-teardown AD with these rules. Update R10, epic 5's description and its Done-when to name `bootstrap` as persistent, exempt from "destroy", and inside the $10/month cap. Add the domain registrar to the ticket's touch points.

### F4 — high — The corpus is redistributed publicly before the terms question is settled

AD-6 publishes the full corpus snapshot as a GitHub Release asset from epic 1. Epic 4 then exposes the data through a public tunnel. The spine defers "Corpus licensing and terms of serving GitHub issue text publicly" to epic 8 ("before the live URL is shared"). By then the text has already been redistributed twice. Epic 8 does not own this open question in the ticket either.

**Fix:** Make the terms question a gate on epic 1's `snapshot.yml` (the first public redistribution), or keep the Release private or store the snapshot in a private location until it is resolved. Add the GitHub Release touch point to the ticket under owner epic-search-baseline.

### F5 — medium — Epic descriptions and `needs` edges the spine overrides need ticket updates

- **Epic 1** (description and Done-when): "The ingest job stores Kubernetes issues with labels, closing comments and how each ended", and "ingest job loads ... each with ... an outcome". The spine splits this work:
  - `ingest` writes a snapshot only.
  - `load` writes the database.
  - `outcome` and `kind` are computed in `core` at load time (AD-6, AD-8).
- **Epic 1:** the spine adds Grafana (Explore over Tempo), Envoy Gateway and the Barman plugin to the epic 1 platform release (AD-11, AD-13, AD-14). The epic names only "an OTel collector and a trace backend".
- **Epic 2:** "pairs extracted from the corpus epic 1 stored". The spine derives the pairs from the snapshot and versions them with it (AD-12).
- **Epic 2's `needs`:** this edge cites "the retrieval API's mode parameter". Under AD-1, eval calls `core` and does not go through the API, so p95 excludes HTTP. The edge should name the `core` mode registry.
- **Epic 2 / R7:** "a PR that lowers a score fails". AD-12 gates Recall@k and MRR only, within an epsilon. It reports p95 but never gates it. R6 lists p95 as a score, so the ticket should state that latency is not gated.
- **Epic 4:** "exposes search_similar_issues ... in its default mode". AD-5 exposes an optional `mode` and `k`.
- **Epic 4's Done-when:** "propagated through MCP's `_meta` trace context". AD-10 roots the trace at the `mcp` SERVER span and propagates only `traceparent` over HTTP from `mcp` to `api`. The spine never covers `_meta` extraction. Either add `_meta` extraction to AD-10 or drop it from the epic.
- **Edge 7←6:** its stated reason is "both edit the live ingress and chart values". Under AD-14, Grafana is never public and is reached by port-forward, so epic 7 does not edit the ingress. Restate the edge or drop it. It is cut-safe either way, because 7 is cut before 6.

### F6 — medium — Epic 4 (never cut) may hide a dependency on a cuttable epic

The Deferred section tells epic 4 to use a named tunnel, which needs a domain the tunnel provider manages. The only domain in the spine is the Route53 zone in epic 5's `bootstrap`. If epic 4 reuses that domain, the never-cut MCP epic depends on the cuttable EKS epic.

**Fix:** State in the Deferred tunnel entry that epic 4's tunnel needs nothing from `bootstrap`, for example by using its own tunnel domain or JSON-response mode on a quick tunnel. If the domain is shared, move the domain or zone outside epic 5.

### F7 — low — Quiet constraints with no explicit invariant

- **No server-side LLM generation.** No AD states it. Add one line, for example to AD-1 or AD-3: `api` and `mcp` never call a generative model; the only model is the embedder.
- **Public material only.** Nothing excludes youscope's names, keys, database, logs or .env files, or DTU or employer names, from the repo, fixtures or ADRs. Add a row to the Consistency Conventions.
- **Wording.** The convention row gives the approved phrase but leaves out "never as production". Add it so the claim-discipline check in epic 8 has the full rule. The ticket's internal Assumption ("the cluster counts as production") should stay out of any outward text.
- **Eval gate cut (last).** AD-4 sets the post-epic-3 default mode to "whatever epic 3's eval picks". If the eval gate is cut, that choice has no source. Add a fallback, such as keeping `keyword` or letting the author choose and record it in an ADR.

## Checked and found landed

- **Touch points:** GitHub API (AD-6, epic 1), Claude Desktop (AD-5, epic 4), tunnel (Deferred, epic 4), AWS/S3/ECR/DNS (AD-15, epic 5), OAuth AS (AD-5 + Deferred, epic 6), claims ledger (Capability map R13, epic 8).
- **Cut-safety of AD-11:** the R12 trace screenshot does not depend on epic 7, because Tempo and the Grafana Explore view ship in epic 1.
- **Cut-safety of AD-13:** the kind-only fallback survives an EKS cut, because the chart uses no AWS-only feature.
- **Cut-safety of AD-5:** auth sits behind a chart value, so cutting epic 6 leaves `mcp` unauthenticated without code changes.
- **MCP spec 2026-07-28**, stateless Streamable HTTP and OAuth 2.1 with CIMD: AD-5 and Deferred.
- **No stored cloud keys:** OIDC deploys and IRSA or Pod Identity for backups (AD-15, AD-18, Conventions).
- **No second vector store:** pgvector only. pg_textsearch is a BM25 provider, not a vector store.
- **`needs` edges with a home:** 2←1 (AD-6, AD-17), 3←1 (AD-4, AD-9, AD-10), 3←2 (AD-12), 4←1 (AD-4, AD-10, AD-13, AD-17), 5←1 (AD-13, AD-16), 5←3 (Deferred), 5←4 (AD-3, AD-14), 6←4 (AD-5), 6←5 (AD-15 fixed hostname), 7←3 and 7←4 (AD-10, AD-11), 7←5 (AD-13), 8←3 (AD-12), 8←6 (AD-14).
