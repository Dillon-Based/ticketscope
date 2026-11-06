# Rubric review: architecture-ticketscope.md (initiative spine, 8 epics)

Reviewed 2026-11-05 against: initiative-ticketscope.md (R1–R13, constraints), tickets/tickets.toml (epics 1–8), .memlog.md.

**Verdict:** A strong spine. The application seams are covered well: API contract, span contract, write ownership, derived fields, eval lineage and Helm layout. It needs one more pass before epic 1 stories are planned. There is one real ordering bug (the migrate hook runs before the database exists). The operational envelope also has gaps that two epics could fill in incompatible ways: DNS record ownership, teardown ordering and orphaned resources, Terraform vs Helm ownership of in-cluster releases, cost guardrails, and the local dev loop.

---

## 1. Divergence points fixed / missed

Fixed well: dependency direction (AD-1), one image (AD-2), api/mcp topology (AD-3), the `/v1` shape (AD-4), MCP mirroring (AD-5), the snapshot as source of truth (AD-6), single writer and single migration track (AD-7), derived fields (AD-8), the BM25 provider (AD-9), spans (AD-10/11), eval lineage (AD-12), two releases (AD-13), one host (AD-14), Terraform layering (AD-15), images (AD-16), workflow layout (AD-17) and backups (AD-18).

Missed divergence points:

- **[HIGH] Who deploys the in-cluster releases on EKS: Terraform or the workflow?** The infra diagram puts "LB controller · EBS CSI · platform + ticketscope releases" inside the Terraform `env` stack, and the memlog says the env stack includes in-cluster releases. AD-17 says `env-up.yml` runs "terraform env apply … + helm deploy". AD-13 puts the GatewayClass implementation (the LB controller) in the `platform` Helm release, while the diagram puts it in Terraform add-ons. Epic 5 and epics 1, 4 and 7, which edit the charts, can wire this differently. Fix: pick one owner. Recommended: Terraform owns AWS resources plus EKS managed add-ons (EBS CSI, Pod Identity agent). The workflow runs `helm upgrade --install platform` and then `ticketscope`. The LB controller goes in `platform`, with its IAM role created in `env` Terraform. Then align the diagram.
- **[HIGH] Ownership of the DNS record for the fixed hostname.** `bootstrap` fixes the zone and the hostname, but the ALB is created per spin-up by the LB controller, so its DNS name changes every time. Nothing says who writes the alias record: external-dns in `platform`, a Terraform data lookup after Helm, or a workflow step. That choice also affects teardown (see section 6). Fix: add it to AD-15 or AD-14. Recommended: external-dns in `platform`, scoped to the bootstrap zone with Pod Identity, and `--policy=sync` so the record is removed on teardown.
- **[MED] Ownership of the `Gateway` resource.** The `HTTPRoute` is in `ticketscope` and the GatewayClass is in `platform`. Nobody owns the `Gateway` object, with its listeners, TLS/ACM binding and ALB config. Fix: state that `platform` owns one `Gateway`, parameterized per environment in values files.
- **[MED] Composition root.** The layer table lets `http` import only `core`, and jobs import core plus driven adapters. Something has to construct `adapters.postgres` and `adapters.embedder` and inject them into `core` for the api process. As written, that is either impossible or left for each epic to improvise. Fix: name a composition root, for example `ticketscope.http.app:create_app` and the `jobs.*` entrypoints, which may import adapters. Enforce the table with import-linter contracts in `ci.yml` (see section 2).
- **[LOW] The `eval` Job is in the `ticketscope` chart, which is identical on EKS.** Fix: state that it is disabled by default and enabled by `_kind-deploy` / `eval.yml`.

## 2. Are the rules enforceable, and do they prevent the stated divergence?

- **[HIGH] AD-7 is self-contradictory with AD-13.** `migrate` is a Helm **pre-install**/pre-upgrade hook, but the CNPG `Cluster` is created by the same `ticketscope` release. On first install, pre-install hooks run before any release resources exist, so there is no database to migrate. `load` also has no stated trigger or ordering: is it a hook, a post-install Job, or a workflow step? Fix: make `migrate` a post-install/pre-upgrade hook that waits for the Cluster to be ready, and `load` a post-install/post-upgrade hook with a higher hook weight. Alternatively, move the `Cluster` into its own release installed first. State the order explicitly: platform → Cluster ready → migrate → load → api ready.
- **[MED] AD-1 has no mechanical check.** Its import rules are the most important in the spine, and none is enforced. Fix: add "import-linter (or equivalent) layer contracts run in `ci.yml`" to the Rule.
- **[LOW] AD-3 says api is "the only long-running process" holding the DB/model.** The `load` and `eval` Jobs hold both, which is fine. The wording is correct, but say "jobs may" so nobody reads it as a contradiction.
- **[LOW] AD-4 `score` is not comparable across modes** (BM25, cosine, fusion). Fix: one line saying `score` is mode-specific and only `rank` is comparable, so the page and MCP don't present it as a percentage.
- AD-8, AD-9, AD-12, AD-14 and AD-16 have crisp, checkable Rules.

## 3. Could a Deferred item let two epics diverge?

- **[MED] Corpus licensing is deferred to epic 8, which is too late.** Epic 1 stores the text and epic 5 serves it publicly. If the terms force trimming fields (for example, bodies or comments), that changes the snapshot, the AD-8 derived fields and every eval baseline. Fix: move ownership to epic 1, and gate the public URL in epic 5 on it.
- **[MED] OAuth authorization server deferred to epic 6 vs AD-14's "one public host".** If epic 6 self-hosts an AS (Keycloak, for example), it needs a host or path. That either breaks AD-14 or needs an HTTPRoute pattern nobody has fixed. Fix: in the deferral, state "external/SaaS AS, or served under the one host at a fixed path prefix".
- **[LOW] The kind/threshold deferral names "epics 1 and 2" jointly.** Fix: give the threshold to epic 1 and pair extraction to epic 2, and say that later changes go through AD-8 reload plus AD-12 baseline.
- **[LOW] The CNPG instance count is undeferred.** The R3 failure drill needs at least 2 instances on EKS, and that also affects the cost and node sizing epic 5 owns. Add it to epic 5's node-sizing deferral.
- **[LOW] Cut fallback for R3.** AD-18 runs the drills on EKS. If epic 5 is cut, the kind fallback has no S3 path without stored keys. State what happens: the drill is dropped, or MinIO is used in kind.
- The other deferrals are safe: each sits behind a fixed seam (port, chart value, or baseline file).

## 4. Tech currency (flag only; web verification is separate)

The memlog claims PyPI/GitHub verification on 2026-11-05. Items worth a second look:

- `mcp` 2.3 with `MCPServer`, and the FastMCP import removed: a major API rename, so pin it carefully.
- fastembed 0.9 on Python 3.14: the memlog checked onnxruntime wheels, but not that fastembed declares support for 3.14.
- CNPG `standard` image bundling pgvector, and the claim that in-tree `barmanObjectStore` is removed in 1.32.
- AWS LB Controller Gateway API GA in v3.x with ACM binding, and Tempo charts having moved to `grafana-community/helm-charts`.
- pg_textsearch 1.5.1 coexisting with pgvector in the same `shared_preload_libraries` on PG18.
- Helm 4.3: hook semantics carried over from v3 matter for AD-7.
- `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` is a real, documented value.

Nothing looks fabricated, but these are load-bearing.

## 5. Requirement coverage R1–R13

Every requirement maps to an AD. Weak spots:

- **R10 "destroy leaves nothing billing"** is defined (AD-15) but not *ensured*. See section 6, teardown.
- **R10 "`terraform apply` brings up … the live URL"**: the spine splits this into terraform plus helm in a workflow. That is acceptable, but say explicitly that `env-up.yml` is the R10 interface, so the README claim and the claims ledger (R13) match.
- **R3**: drills are recorded, but where? Name an artifact location (for example `docs/drills/`) so R13 rows can point at it.
- **R12**: the clip and the screenshot have no home in the repo tree (for example `docs/media/`). This is minor.

## 6. Operational envelope (owned at initiative altitude)

| Dimension | Status | Note |
| --- | --- | --- |
| Environments | Decided | kind (CI/local) and EKS. Values files per environment. |
| Infra/provider strategy | Decided | bootstrap/env split, ECR, OIDC. |
| Spin-up ordering | **Partial / wrong** | The release order (platform with CRDs, then ticketscope) is implied, not stated. The hook order is broken (section 2). |
| Teardown ordering | **Missing [HIGH]** | `terraform destroy` of `env` will hang or orphan resources. The ALB, target groups and security groups are created by the LB controller from the Gateway. EBS volumes come from CNPG PVCs through EBS CSI. A Route53 record is written if external-dns is used. None of these are in Terraform state, so leftover ALB/ENIs block VPC deletion and orphaned EBS volumes keep billing. Fix: in AD-15/AD-17, `env-down.yml` runs `helm uninstall ticketscope` (and deletes PVCs), then `helm uninstall platform`, then waits for the ALB/ENIs to be gone, then runs `terraform destroy`. Add a post-destroy check for tagged leftovers (ELB, EBS, ENI, EIP) that fails the workflow. |
| Secrets | Decided | Conventions table. OAuth client secrets (epic 6) are not mentioned, but the convention covers them. |
| Cost guardrails | **Missing [MED]** | The <$10/month figure relies on remembering to run env-down. There is no AWS Budget alarm (bootstrap), no max-lifetime or scheduled auto-destroy, and no cost tagging. Fix: add an AWS Budget with an alert in bootstrap, plus a scheduled `env-down` (for example nightly or after N hours) or a TTL tag check. |
| Backups | Decided | AD-18. S3 retention and lifecycle are unspecified (low): bootstrap S3 costs grow with WAL archives. Add a lifecycle rule or CNPG retention policy. |
| Failure handling | **Partial [LOW]** | Nothing on a partial `env-up` failure: is env-down idempotent from any state? Nothing on `load` Job failure or retry, or how api readiness depends on load completing. |
| Local dev loop | **Missing [MED]** | `_kind-deploy.yml` is CI-only. Developers will write their own kind script, and it will drift from CI. Fix: put the kind-up steps in one repo script or `make`/`just` target that `_kind-deploy.yml` calls, and mention the fast loop (uvicorn plus a port-forwarded Postgres). |
| Terraform state | Partial [LOW] | The S3 backend is stated; locking is not. Use S3 native locking (`use_lockfile`). |
| Observability access | Decided | Port-forward only. |

## 7. Leanness

Mostly lean, with Rules phrased as decisions. Minor bloat:

- The Cloudflare quick-tunnel facts in Deferred are rationale. Keep the decision ("named tunnel or JSON-response mode") and drop the specs.
- "Costs cents a month" in AD-15 is rationale.
- The "Prevents" lines are appropriately short.
- The layout tree is useful and earns its space.

## 8. Mermaid validity

All four flowcharts and the erDiagram parse as written: subgraph ids, `&` fan-out, `-.label.->`, `[[ ]]` and `[( )]` shapes, and quoted labels containing `{}`, `()`, `=` and `,`. Nodes first referenced outside a subgraph and declared inside it (`api`, `mcp` in the Structural Seed) render inside the subgraph, which is the intended result. No syntax issues.

## 9. Internal inconsistencies

1. The infra diagram puts the LB controller and the app releases in Terraform `env`. AD-13 puts the LB controller in `platform`, and AD-17 has the workflow run helm (section 1).
2. AD-7's pre-install migrate hook conflicts with the Cluster being in the same release (section 2).
3. The ER diagram shows `CORPUS_SNAPSHOT ||--|{ ISSUE`, which implies multiple snapshots in the database. The conventions say issues are keyed by number alone, which implies one snapshot per database. Fix: state one snapshot per database (load replaces), or key by (snapshot, number).
4. The memlog's earlier "one image tagged by git SHA" (ECR decision) is superseded by AD-16's two images. The spine is consistent; only the log is stale.
5. AD-11 says apps emit "traces and JSON logs only", but logs never leave stdout ("no log shipping"). That is consistent, but it means Grafana has no logs. That is fine for R9, but state it so epic 7 doesn't add Loki unasked.

## Priority fix list

1. Fix the AD-7/AD-13 hook ordering and state the full spin-up sequence.
2. Add teardown ordering and an orphan check to AD-15/AD-17 (R10).
3. Decide Terraform vs Helm ownership of in-cluster components, plus DNS record and `Gateway` ownership, and align the infra diagram.
4. Add cost guardrails (Budget alarm, auto-destroy) and a shared local/CI kind script.
5. Move corpus licensing to epic 1. Constrain the epic 6 AS to the one-host rule.
6. Name the composition root and enforce AD-1 with import-linter.
