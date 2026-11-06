---
review: adversarial (spine attack)
target: architecture-ticketscope.md (AD-1..AD-18)
units: epics 1-8 (tickets/tickets.toml)
date: 2026-11-05
verdict: NOT YET SAFE TO BUILD AGAINST. The spine fixes the right seams (the /v1 shape, the span tree, the single writer), but it leaves 12 places where two epics can each follow every AD to the letter and still build things that do not fit together. One of them (H1) breaks the first install on kind no matter how carefully it is built.
---

# Adversarial review: two lawful builds that do not fit together

Method: for each hole, two epics each pick a build that obeys every AD as written. The two builds still conflict. Each hole ends with the smallest AD tightening that closes it. Holes are ordered by severity and likelihood.

---

## H1. CRITICAL: Job lifecycle. migrate as a pre-install hook cannot reach a Cluster that does not exist yet

**Epics:** 1 (chart, migrate, load) × 5 (env-up deploy), and also 2 (eval Job) and 3 (embedding load)

**ADs obeyed:** AD-7 (migrate runs as a Helm pre-install/pre-upgrade hook), AD-13 (the CNPG `Cluster` and the migrate, load and eval Jobs are all in the `ticketscope` release).

**Why the spine contradicts itself:** Helm runs pre-install hooks before it creates any of the release's ordinary resources. On a first install, which is every kind PR and every `env-up`, the `Cluster` CR does not exist yet. CNPG's `ticketscope-db-app` Secret does not exist either. The migrate pod therefore fails with CreateContainerConfigError or waits forever on a missing `-rw` Service.

**Divergent lawful builds:**
- **Epic 1** finds a workaround: it makes the `Cluster` itself a pre-install hook with weight -10. Helm does not track hook resources, so `helm uninstall` and `env-down` leave the Cluster and its EBS PVCs behind. That breaks epic 5's "destroy leaves nothing billing".
- **Epic 5** finds a different workaround: in `env-up.yml` it applies the Cluster with `kubectl` before `helm install`. That breaks AD-13's rule that installs are identical everywhere, and `_kind-deploy.yml` never does the same.
- **load and eval are ordinary Jobs** in the chart (AD-13 does not say they are hooks). Job `spec.template` is immutable, so the second `helm upgrade` with a new SHA tag fails with "field is immutable". Epic 1 never sees this, because kind is always a fresh install. Epic 5 hits it on the first redeploy.
- **Epic 2's eval Job** is rendered on EKS as well. It then runs against production traffic, and its retrieval spans appear in epic 7's latency-by-mode panel (see H6).

**Fix (tighten AD-7 and AD-13):**
- The `Cluster` is an ordinary release resource.
- `migrate` and `load` are **post-install/post-upgrade** hooks with weights 0 and 10 and `hook-delete-policy: before-hook-creation`.
- Each gets an initContainer that waits until the Cluster's `-rw` Service accepts connections.
- `load` is idempotent: it does nothing when `corpus_meta` (see H3) already matches the pinned snapshot, model and preprocessing.
- `eval` is not rendered unless `eval.enabled` is set. It is true only in `values-kind.yaml`, and it runs as a hook or through `kubectl create job --from`.
- Helm's hook timeout must cover epic 3's embedding load. Pin `--timeout` in `_kind-deploy.yml` and `env-up.yml`.

---

## H2. HIGH: Snapshot schema and where the labelled pairs come from

**Epics:** 1 (ingest, snapshot format, load) × 2 (pair extraction)

**ADs obeyed:** AD-6 (the snapshot carries "every raw field downstream needs (labels, comments, cross-references)", and its format is deferred to epic 1), AD-12 (pairs are "derived from the snapshot and versioned with it").

**Divergent lawful builds:**
- **Epic 1** stores what its own consumers use:
  - from each issue: number, title, body, state, labels, and comments as text;
  - "cross-references" as the timeline's `cross-referenced` events, which is all the outcome function needs for `linked_pr`.
  - It never fetches the `marked_as_duplicate` timeline event or `state_reason`.
- **Epic 2** extracts pairs from the duplicate links. Those are not in the snapshot. AD-6 forbids calling GitHub from anywhere except ingest, so epic 2 regex-scrapes "Duplicate of #N" from comment text. The result is a different and noisier pair set than ingest could have recorded.
- **Where pairs live:**
  - Epic 2 reads them directly from the Release asset in the eval Job, which means parsing epic 1's private file format.
  - Or epic 2 adds a `labelled_pair` table and writes it from eval. That breaks AD-7's "load is the only writer of corpus tables" in spirit, because AD-7 does not say whether pairs count as corpus.
  - Or epic 2 commits `eval/pairs.json`. Then the pairs are versioned by git, not by the snapshot.

**Fix (new AD-6a, snapshot schema):**
- The snapshot is JSONL with a `schema_version` header.
- The required fields for each issue:
  - `number, title, body, state, state_reason, created_at, closed_at`
  - `labels[]`
  - `comments[{author_association, body, created_at}]`
  - `timeline[{event, source_number|target_number, commit_id?, created_at}]`, covering at least `marked_as_duplicate`, `cross-referenced` and `closed`.
- Pair extraction is one function in `core` (or `eval/`), and it reads only these fields.
- `snapshot.yml` publishes `pairs.jsonl` as a second asset of the same Release.
- The eval Job reads the pairs from that asset. Pairs never go into Postgres.

---

## H3. HIGH: Corpus and model identity. `corpus_version`, the snapshot version, the embedding column and a model change

**Epics:** 1 (`corpus_version` in /v1 and in spans) × 3 (embedding column) × 2 (baseline) × 5 (load on EKS)

**ADs obeyed:** AD-4 (`corpus_version` in the response, meaning not defined), AD-10 (`ticketscope.corpus.version`), the conventions (snapshot version `YYYY.MM.N`), AD-12 (`baseline.json` records the snapshot, model id and preprocessing version), AD-7 ("epic 3 adds the embedding column"), the ER diagram (EMBEDDING is a separate 0..1 entity).

**Divergent lawful builds:**
- **Where `api` reads `corpus_version`:**
  - Epic 1 reads it from env `TICKETSCOPE_SNAPSHOT_VERSION`, which is the chart value AD-6 pins.
  - When a PR bumps that value and load has not yet re-run (or is skipped, per H1), the API reports a version the database does not hold.
- **What `corpus_version` means:**
  - Epic 3 knows dense results depend on the model, so it reports `corpus_version = "2026.11.1+bge-small-en-v1.5/p2"`.
  - Epic 1's page, the span attribute and the eval's baseline comparison all expect bare `YYYY.MM.N`.
- **Embedding storage:**
  - Epic 3 adds `issue.embedding vector(384)`, which is what AD-7 says.
  - The ER diagram suggests a separate table. Either reading obeys the spine.
  - With a column, switching to a 768-dimension model needs an `ALTER COLUMN TYPE` and an index rebuild, and the table cannot hold old and new embeddings during a comparison. Epic 3's own model-selection eval needs exactly that.
- **No startup check:**
  - `api` loads model X from a chart value, while `load` wrote embeddings with model Y from another chart value.
  - Dense mode returns plausible-looking junk, and nothing fails.

**Fix (tighten AD-6, AD-7 and AD-12):**
- `load` writes one `corpus_meta` row: `snapshot_version, snapshot_schema_version, embedding_model_id, embedding_dim, preprocessing_version, loaded_at`.
- `api` reads `corpus_version` from that row, and it is exactly `snapshot_version`. Add the additive fields `embedding_model` in `/v1` and `ticketscope.embedding.model` in spans.
- `api` fails its readiness check if its configured model id differs from `corpus_meta`.
- Embeddings go in `issue_embedding(issue_number, model_id, preprocessing_version, embedding vector(N))`. A model change is a new migration.
- The eval gate refuses to compare when `corpus_meta` differs from `baseline.json`.

---

## H4. HIGH: Ownership of the public edge. The Gateway object, OAuth well-known paths and where the authorization server lives

**Epics:** 1 (HTTPRoute) × 5 (ALB and ACM) × 6 (OAuth) × 7 (the tickets say it "edits the live ingress")

**ADs obeyed:**
- AD-13: `platform` holds the GatewayClass *implementation*, and `ticketscope` holds the `HTTPRoute`.
- AD-14: one host. `/` → page, `/v1`, `/mcp`.
- AD-5: `mcp` is a resource server only, and the authorization server (AS) is deferred to epic 6.

**Divergent lawful builds:**
- **No AD names an owner for the `Gateway` resource:**
  - Epic 1 puts a `Gateway` in the `ticketscope` chart.
  - Epic 5 puts a second `Gateway`, with ALB and ACM settings, in `platform`.
  - The result is two ALBs, or an HTTPRoute whose `parentRef` points at the wrong Gateway.
  - An ALB that the controller created outside Terraform state and that outlives `env-down` is exactly the "destroy leaves nothing billing" failure.
- **Protected-resource metadata:**
  - RFC 9728 and MCP discovery look for it at `https://host/.well-known/oauth-protected-resource[/mcp]`.
  - AD-14's `/` prefix sends that request to `api`, which returns the page or a 404.
  - Epic 6 adds a route for `/.well-known/*` to `mcp`, editing epic 1's HTTPRoute.
  - Epic 1's page later adds `/.well-known/security.txt`, and the two collide.
- **The authorization server:**
  - If epic 6 runs an in-cluster AS (Dex, Keycloak), it needs a public path on the one host. AD-13's list of `platform` contents does not allow it, and AD-14 does not route it.
  - If epic 6 uses an external SaaS AS instead, the token audience and redirect settings live in values that epic 7 also edits.

**Fix (tighten AD-13 and AD-14):**
- One `Gateway` named `ticketscope-public` lives in `platform`. It carries the listener, TLS and per-environment class.
- `ticketscope` owns only `HTTPRoute`s, and their `parentRef` comes from a value.
- The route table is fixed:
  - `/mcp` and `/.well-known/oauth-protected-resource` → `mcp`
  - `/v1` and `/` → `api`
  - nothing else
- The AS is external: no in-cluster AS and no AS path on the host. `mcp` sets `WWW-Authenticate: resource_metadata=` to an absolute URL.
- Epic 7 never touches routes, because Grafana is reached by port-forward (AD-14). Remove the "both edit the live ingress" edge from the tickets, or explain it.

---

## H5. HIGH: Who owns which chart values. The default mode, resources and auth across `values.yaml`, `values-kind.yaml` and `values-eks.yaml`

**Epics:** 3 (default mode, model resources) × 5 (`values-eks.yaml`) × 6 (auth) × 7 (observability) × 4 (mcp default)

**ADs obeyed:** AD-4 (the default mode is "a chart value"), AD-13 (per-environment differences live only in the two env files), AD-5 (auth "behind a chart value"). Epic 3's Done-when says resources are "recorded in the chart values on kind".

**Divergent lawful builds:**
- **Model resources and the default mode go into different files:**
  - Epic 3 records the model's requests and limits in `values-kind.yaml`, following its literal Done-when, and sets `api.defaultMode: hybrid` in `values.yaml`.
  - Epic 5 writes `values-eks.yaml` from a copy of the kind file taken before epic 3, including `defaultMode: keyword`. The EKS environment serves keyword, and the env file silently overrides the base file.
  - Or epic 5 never sees the resources at all, and `api` runs on EKS with no memory request and is killed for running out of memory while loading the model.
- **mcp invents its own default:**
  - Epic 4 reads "in its default mode" and adds `mcp.defaultMode`, then fills an omitted `mode` before calling `/v1`.
  - Now there are two defaults, and epic 3's change does not reach MCP.
- **Auth goes into the wrong file:**
  - Epic 6 sets `mcp.auth.enabled: true` in `values.yaml`, and the kind `mcp-e2e.yml` (epic 4) starts failing.
  - Or epic 6 sets it only in `values-eks.yaml`, and the kind fallback after an EKS cut (memlog assumption) runs unauthenticated with no record that it does.

**Fix (new AD on values ownership):**
- Publish a key table: key prefix → owning epic → which files may set it.
  - `api.defaultMode` and all `resources` exist **only** in `values.yaml`. Env files may not override them.
  - Env files may set only the listed keys: host, gateway class, image registry, storage class, backup, auth issuer and audience, `eval.enabled`.
- `mcp` forwards an omitted `mode` as omitted and has no mode setting of its own.
- `mcp.auth.enabled` is true in `values-eks.yaml` and false in `values-kind.yaml`. Epic 6's CI check uses a stub token issuer on kind.

---

## H6. MEDIUM: Tool-call and error telemetry is not defined tightly enough for spanmetrics

**Epics:** 4 (mcp spans) × 7 (spanmetrics dashboard), plus 1, 2 and 3 (service names, eval spans)

**ADs obeyed:** AD-10 (the tree: the mcp SERVER span comes from the SDK, span names), AD-11 (every metric is derived from spans).

**Divergent lawful builds:**
- **Span kind and name:**
  - Epic 4 adds Starlette ASGI auto-instrumentation to `mcp` "for completeness", so the SERVER span becomes `POST /mcp` and the SDK's `tools/call …` span becomes its INTERNAL child.
  - Epic 7 filters `span.kind=SERVER, span.name=~"tools/call.*"` and gets zero tool calls.
- **Errors:**
  - Epic 4 returns `is_error: true` results (per the conventions) but never sets span status to ERROR.
  - Epic 1 returns 422 and other 4xx responses, which HTTP semconv does not mark as span errors.
  - Epic 7's errors panel, built on `status.code=ERROR`, shows zero during a broken demo.
- **Service names are not pinned:**
  - Epic 1 sets `OTEL_SERVICE_NAME=api`, and epic 4 sets `ticketscope-mcp`.
  - Epic 7 has to guess both.
- **Eval traffic:**
  - Epic 2's eval Job calls `core` and emits the same `retrieval {mode}` spans.
  - On any cluster where eval runs (H1), the latency-by-mode panel is mostly eval traffic.

**Fix (tighten AD-10 and AD-11):**
- `service.name` ∈ {`ticketscope-api`, `ticketscope-mcp`, `ticketscope-job-<name>`}.
- The SDK's `tools/call {tool}` span is the only SERVER span in `mcp`; there is no ASGI instrumentation there.
- An `is_error` tool result sets span status ERROR and `error.type`, and `api` sets ERROR on every 5xx response.
- Pin the spanmetrics dimensions: `service.name, span.name, span.kind, status.code, ticketscope.retrieval.mode, gen_ai.tool.name`.
- The dashboard filters to `service.name ∈ {api, mcp}`.

---

## H7. MEDIUM: `score` means something different in each mode

**Epics:** 1 (keyword) × 3 (dense, hybrid) × 4 (MCP consumers) and the page

**ADs obeyed:** AD-4 (`score` is in the contract with no meaning or direction), AD-9 (BM25 through pg_textsearch, fusion in `core`).

**Divergent lawful builds:**
- **Epic 1:** pg_textsearch's `<@>` operator returns a *negative* BM25 score so that it sorts ascending. Epic 1 passes it through, so lower is better.
- **Epic 3:**
  - dense returns cosine *similarity*, where higher is better;
  - hybrid returns RRF sums of about 0.01–0.03.
- **The page:** epic 1 draws relevance bars that assume lower is better, so dense results look reversed.
- **MCP consumers:** Claude reads "score: -12.4" and "score: 0.83" as comparable numbers.
- **Eval:** epic 2's tie-break sorts by score in one direction.

**Fix (tighten AD-4):**
- `score` is a float where **higher is better within one response**. It cannot be compared across modes or queries.
- `results` is ordered by `rank`, and `rank` alone is the ordering contract.
- Add `score_kind: "bm25"|"cosine"|"rrf"` additively.

---

## H8. MEDIUM: Who creates the read-only role and its grants

**Epics:** 1 (migration 001, api connection) × 3 (new table or column) × 5 (EKS secrets)

**ADs obeyed:**
- AD-7: `api` connects as a read-only role.
- The Secrets convention: secrets are created "by CNPG or by the deploy workflow".

**Divergent lawful builds:**
- **How the role is created:**
  - Epic 1 creates `ticketscope_ro` in CNPG `spec.managed.roles`. CNPG does not generate passwords for managed roles, so the Secret must come from the deploy workflow.
  - Epic 1 adds it to `_kind-deploy.yml`. Epic 5 has to reinvent it in `env-up.yml`, possibly under a different name.
  - Alternatively, epic 1 creates the role in migration SQL, which needs either a password in a committed file or a second Secret.
- **How grants are made:**
  - Epic 1 grants with `GRANT SELECT ON ALL TABLES` in migration 001.
  - Epic 3's later `issue_embedding` table (H3) gets no grant.
  - Dense mode fails in `api` with "permission denied" while the eval passes, because the eval Job connects as the owner.

**Fix (tighten AD-7):**
- The role is `ticketscope_ro` through CNPG `managed.roles`. Its Secret `ticketscope-db-ro` is created by the chart with `lookup` and generate-once.
- Migration 0001 runs `ALTER DEFAULT PRIVILEGES … GRANT SELECT ON TABLES TO ticketscope_ro`.
- The **eval Job connects as `ticketscope_ro`**, so eval uses the same permissions as the API.

---

## H9. MEDIUM: The wire model is defined twice, once for `http` and once for `apiclient`

**Epics:** 1 (http response models) × 4 (apiclient, mcp outputSchema) × 3 (additive fields)

**ADs obeyed:**
- AD-1 and the layer table: `mcp` may import only `apiclient`. Whether `apiclient` may import `core` is not stated.
- AD-4: additive changes only.
- AD-5: the tool output *is* the `/v1` body.

**Divergent lawful builds:**
- Epic 4 redefines the response as pydantic models in `apiclient` with `extra="forbid"` (strict typing). It then generates the MCP `outputSchema` from those models.
- Epic 3 adds a field that AD-4 allows, such as `score_kind` or `embedding_model`. The result:
  - `apiclient` validation fails, and every MCP call errors;
  - or, with `extra="ignore"`, the field silently disappears from MCP output, and "MCP mirrors the API" stops being true.

**Fix:**
- The `/v1` request and response models live in one module, `ticketscope.contract` (pydantic only), which `http`, `apiclient` and `eval` all import.
- The MCP `outputSchema` is generated from that module.
- Unknown fields are allowed, and they are passed through.

---

## H10. MEDIUM: The core retriever interface, and excluding the query issue in eval

**Epics:** 2 (eval) × 3 (dense, hybrid in `core`)

**ADs obeyed:**
- AD-1: modes are in `core`, and eval calls `core`.
- Epic 2's Done-when: eval "picks up any new mode with no change to the job".

**Divergent lawful builds:**
- **How eval enumerates modes:** epic 2 hard-codes the AD-4 enum, while epic 3 registers modes in a dict. Either way the job has to change, or it scores modes the database cannot serve.
- **Excluding the query issue:**
  - A pair's query issue is itself in the corpus, so every mode ranks it first. Epic 2 needs to exclude it.
  - Epic 2 adds `exclude: set[int]` to the keyword function's signature in `core`.
  - Epic 3's dense and hybrid functions take `(query, k)`, so the eval either crashes or scores self-matches as hits.
  - Hybrid has a second problem: epic 3 fuses the top-k from each side, so after exclusion it returns fewer than k results.

**Fix (new AD on the core port):**
- Every mode implements `Retriever.search(query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]` and registers in `core.modes.REGISTRY`.
- `/v1` validates `mode` against the registry.
- Eval iterates over the registry, skipping a mode only when that mode's `available(store)` returns false.
- Hybrid fetches at least `k + |exclude|` candidates per side.

---

## Lower-severity notes (pin when convenient)

- **H11. Embedding input text.** AD-8 lists `kind` and `outcome` as the derived fields, but not "the text that gets embedded". Epic 3 could truncate title+body in `load` and normalise the query differently in `api`'s adapter. Fix: add `embedding_text(issue)` and `embedding_query(q)` to `core` under the `preprocessing_version` constant.
- **H12. The Barman Cloud Plugin needs cert-manager.** AD-13's `platform` list leaves it out. Epic 1 installs the plugin (AD-13) and finds cert-manager is missing, while epic 5 assumes it is not needed. Fix: add cert-manager to `platform` (its chart is the same on kind and EKS), or move the plugin to epic 5 and say so.
- **The embedding cache artifact (memlog).** Its location is deferred to epic 3. If epic 3 picks S3, kind CI needs AWS credentials, which AD-16 forbids. If it picks none, epic 5 recomputes embeddings inside the 30-minute budget. Fix: require the cache to be a GitHub Release asset next to the snapshot, keyed `(snapshot, model_id, preprocessing_version)`.
- **The 7 → 6 edge in tickets.toml** ("both edit the live ingress") conflicts with AD-14 (Grafana is never public). Either the edge is unnecessary, or epic 7 plans to expose Grafana. Resolve this in the tickets, and close the ownership question with H4/H5.

## Summary table

| # | Sev | Epics | Gap |
|---|-----|-------|-----|
| H1 | Critical | 1×5 (2,3) | pre-install migrate before Cluster exists; Jobs not hooks are immutable; eval runs on EKS |
| H2 | High | 1×2 | snapshot schema and pair source not pinned |
| H3 | High | 1×2×3×5 | `corpus_version` source and meaning; column vs table; no model match check |
| H4 | High | 1×5×6(7) | Gateway owner; OAuth well-known routing; where the AS lives |
| H5 | High | 3×4×5×6×7 | values key ownership; default mode and resources overridden by env files |
| H6 | Medium | 4×7 (1,2) | span kind, error status, service.name, eval pollution of spanmetrics |
| H7 | Medium | 1×3×4 | score direction and scale per mode |
| H8 | Medium | 1×3×5 | RO role, its Secret, and default grants |
| H9 | Medium | 1×3×4 | duplicated wire models break additive changes |
| H10 | Medium | 2×3 | retriever interface, mode registry, self-exclusion |
