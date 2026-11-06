---
title: "Reconcile review: architecture spine vs brief addendum"
reviewed: _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
against:
  - _bmad-output/initiative-ticketscope/brief-ticketscope/addendum.md
  - _bmad-output/initiative-ticketscope/brief-ticketscope/brief-ticketscope.md
date: 2026-11-05
verdict: mostly reconciled; teardown and cost guards are the real gap
---

# Reconcile review: spine vs addendum

## Verdict

Most of the addendum landed in the spine: no NAT and public subnets (AD-15), the persistent/ephemeral Terraform split, `get_issue` plus structured output that mirrors `/v1` (AD-5), the stateless 2026-07-28 protocol and CIMD (AD-5, Deferred), claim wording (Conventions), S3 Vectors out of scope (initiative), and the AWS account question (Deferred, epic 5). The real gaps are the addendum's **ephemeral-EKS gotchas** and the **$10/month cap**. The spine takes on "destroy leaves nothing billing" but gives no rule that guarantees it, and gives no cost model or guard for the cap. Smaller gaps: the MCP `_meta` trace leg, the tool-call eval, and the youscope rules are each missing or only implicit.

## Coverage table

| Addendum / brief item | In spine? | Where / gap |
| --- | --- | --- |
| Avoid NAT; public subnets or VPC endpoints | Yes | AD-15, seed diagram |
| Control plane takes 12–15 min | No | R10's 30-min budget is cited only for snapshot load (Deferred). No allocation across control plane, nodes, add-ons, CNPG init, migrate and load |
| LB controller / EBS CSI create resources outside TF state; delete Services/PVCs before destroy | **No** | AD-15 defines "nothing billing" but not the teardown order. AD-17 `env-down.yml` is just "terraform destroy" |
| KMS keys and log groups linger | **No** | Not mentioned |
| Extended support at $0.60/hr; Auto Mode +12% | Partial | AD-16 pins 1.36 but has no "standard support only" rule. Auto Mode is implicitly excluded (separate LB controller and EBS CSI) but not stated |
| Fargate unfit (no DaemonSets, no EBS) | Implicit | "node group" in AD-15. Not recorded as a rejected option (useful ADR material for epic 8) |
| Cost figures vs $10/month cap | **No** | No hour budget, no persistent-cost line items, no budget alarm or forgotten-env guard |
| "apply from nothing" (R10, brief SC3) | **Reinterpreted** | AD-15 makes `bootstrap` persistent and redefines "nothing billing" as "only bootstrap remains". The initiative's R10 still says "from nothing" |
| MCP: `search_similar_issues` + `get_issue`, structured output | Yes | AD-5 |
| MCP: stateless Streamable HTTP, OAuth 2.1 + CIMD | Yes | AD-5; provider deferred to epic 6 |
| MCP: OTel trace context in `_meta` | **No** | AD-10 starts the trace at the mcp SERVER span and propagates only mcp→api over HTTP. It doesn't say whether mcp extracts `traceparent` from request `params._meta` |
| MCP: eval of tool-call behaviour | **No** | `mcp-e2e.yml` tests the protocol, not model tool-selection or argument behaviour. Not in the initiative's R-list either |
| Claim discipline wording | Yes | Conventions "Wording" row |
| "vector database" pre-commit block | Partial | The wording rule is there, but nothing says whether this repo enforces it (pre-commit/CI) or only the external ledger does. It also doesn't say whether generated text (README eval table, ADRs) counts as outward-facing |
| CI numbers are the first claimable retrieval figures | Yes | AD-12 lineage supports it |
| youscope: must not carry over names, identifier keys, DB/logs/.env | **No** (in initiative constraints only) | No Conventions row. Build agents read the spine, not the initiative constraints |
| youscope: non-ML baseline (regex-key + co-occurrence) | No | Not decided. BM25 keyword mode may stand in as the baseline, but that should be stated |
| youscope: dummy-client fallback, runs with no credentials | Implicit | AD-6 (only `ingest` calls GitHub; envs load a public snapshot) and the local fastembed model mean no creds are needed at runtime. Not stated as an invariant, and no fake adapters are named for the ports |
| youscope: question-first query; run logging as relevance labels | No | UX and label-source choices. Epic-level; AD-10's "query text not recorded unless opted in" constrains run-log labels and should be acknowledged |
| Free plan auto-close at 6 months | Yes | Deferred "AWS account plan", epic 5 |
| S3 Vectors comparison | Yes (out) | Initiative scope Out |

## Findings

### F1 — HIGH: no teardown invariant behind "destroy leaves nothing billing"

The addendum's gotcha applies directly. The ALB (created by the LB controller from the Gateway/HTTPRoute) and the EBS volumes (created by EBS CSI from CNPG PVCs) live outside Terraform state. `terraform destroy` will either hang on VPC/subnet deletion (because of the ALB, its security groups and ENIs) or leave orphaned, billing EBS volumes. The EKS module's KMS key and CloudWatch log group can also linger. This cuts across epics 1, 5 and 7 (chart shape, env workflow) and is exactly R10's acceptance condition, so it belongs at spine altitude.

**Fix:** add a rule to AD-15 (or AD-17):
- `env-down.yml` runs `helm uninstall ticketscope` then `platform`, deletes remaining PVCs, and waits until the ALB, target groups and EBS volumes tagged for the cluster are gone. Only then does it run `terraform destroy`.
- `env` creates no customer KMS key (or accepts and records the pending-deletion window), and keeps control-plane logging off, or keeps the log group in state with short retention.
- After destroy, a tag-scoped sweep step confirms that only `bootstrap` remains.

The exact commands belong to epic 5. The ordering rule is architecture.

### F2 — MEDIUM-HIGH: the $10/month cap has no model and no guard

The spine never reconciles the addendum's figures with the cap. Ephemeral EKS runs ~$0.25–0.30 per hour, and the ALB and public IPv4 add more. That is roughly 25–30 env-hours a month, minus the persistent `bootstrap` costs:
- Route53 zone ~$0.50/month
- ECR storage, which grows with every multi-arch SHA tag
- S3 CNPG WAL and base backups, which grow continuously

A forgotten env (~$100+/month always-on) blows the cap in about 3 days.

**Fix:**
- State the env-hour budget in AD-15.
- Put an AWS Budgets alarm in `bootstrap`.
- Add an ECR lifecycle policy and a backup retention policy.
- Add an auto-destroy guard (scheduled `env-down`, or a TTL tag check).

Spot vs on-demand and exact sizing stay deferred to epic 5, as now.

### F3 — MEDIUM: "apply from nothing" was silently reinterpreted

R10 and brief SC3 say `terraform apply` brings up EKS and the live URL "from nothing". AD-15 adds a persistent, locally applied `bootstrap` (zone, cert, OIDC, ECR, state bucket). This is a sound design, but it changes the meaning of a success criterion and of a claim the README will make. Claim discipline means the outward wording must match.

**Fix:** mark it explicitly in AD-15 as a reinterpretation of R10 ("from nothing" = from `bootstrap`, which costs cents a month), and raise it back to the initiative (Sofia) so R10's wording and the claims-ledger row agree.

### F4 — MEDIUM: 30-minute spin-up has no budget given the 12–15 min control plane

The control plane alone uses about half the R10 budget. After it come the node group, the LB controller, EBS CSI, the platform release, CNPG operator and cluster init, migrate, load and (from epic 3) embeddings. The spine defers only the snapshot size to epic 1. AD-7 has `load` write embeddings, and the embedding-cache location is deferred to epic 3, but if embeddings are computed on CPU at spin-up they could break R10.

**Fix:** add an R10 time-budget line to AD-15 or AD-6, for example "control plane ~15 min; everything after cluster-ready ≤ 12 min; embeddings are never computed at spin-up, only loaded precomputed". That turns the epic 3 deferral into a constrained one.

### F5 — MEDIUM: MCP portfolio shape is only partly landed (`_meta` trace context, tool-call eval)

- **`_meta` trace context.** The addendum names OTel propagation in `_meta` as part of the credible shape. AD-10 should say whether the mcp SERVER span extracts `traceparent`/`tracestate` from request `_meta` and becomes a child when one is present, and is the root otherwise. The span contract is cross-epic (4, 7), so this is spine-level. **Fix:** one sentence in AD-10.
- **Tool-call eval.** The addendum lists "an eval of tool-call behaviour". It appears in neither the initiative R-list nor the spine. **Fix:** add it to the spine's Deferred list as an open initiative question (owner epic 4 or 8), or record it as explicitly out. Don't let it vanish.

### F6 — LOW-MEDIUM: youscope rules and reusable patterns are not in the spine

- **Do-not-carry-over.** This is an initiative constraint, but the spine's Conventions are what build agents read. **Fix:** add a "Provenance" row: no youscope app, team or wizard names, no identifier keys, no DB, log or .env content; public material only.
- **Non-ML baseline.** **Fix:** one Deferred line, either "BM25 keyword mode is the non-ML baseline" or "a regex-key/co-occurrence baseline is out".
- **Dummy-client fallback.** It is already satisfied by AD-6 plus local fastembed. **Fix:** state it as an invariant ("a fresh clone runs on kind with no secrets; `CorpusStore` and `Embedder` have in-memory fakes for unit tests") so no epic introduces a credential dependency.
- **Run-log labels and question-first query.** These are epic-level. Note only that AD-10's query-text opt-out constrains run-log labels.

### F7 — LOW: support-tier and option hygiene

- **Extended support.** Add "pinned version must be in EKS standard support" to AD-16. Extended support is $0.60/hr, about 6× the control plane rate. It's low risk through 2026-12-31, but the rule is cheap.
- **Auto Mode.** State "managed node group, no EKS Auto Mode".
- **Fargate.** Record it as a rejected option (no DaemonSets, no EBS for CNPG). This is useful ADR material for epic 8.
- **Wording enforcement.** Say whether this repo's CI or pre-commit greps outward-facing files (README, docs/adr, generated eval table) for "vector database", or whether enforcement lives only in the external ledger.

## Not findings (correctly handled)

- Hiring-vocabulary table: it informs README wording (epic 8) and needs no spine decision.
- Vector-store posting ratios and S3 Vectors: correctly out.
- AWS credits and the Free plan: correctly deferred to epic 5 as an open question.
