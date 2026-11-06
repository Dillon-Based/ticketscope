---
review: verification (were decisions web-checked, not asserted from training data)
target: _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
date: 2026-11-05
reviewer: verification lens
---

# Verification review: ticketscope architecture spine

**Verdict: Mostly sound, with one contract-breaking gap.** The version pins in the `.memlog.md` `version` entries were trusted, and nothing found here contradicts them. Most fit claims also hold up against primary sources, and the main build path for the Postgres image works. One claim, the `db.system.name` attribute in AD-10, is false under the configuration the spine prescribes. Four more claims are either unconfirmed or need narrower wording.

## Findings

### F1 — HIGH — AD-10: `db.system.name=postgresql` will not be emitted with the prescribed opt-in

- **Claim.** psycopg auto-instrumentation emits `db.system.name=postgresql`, with `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`.
- **Found.**
  - `gen_ai_latest_experimental` is a real value: `_StabilityMode.GEN_AI_LATEST_EXPERIMENTAL` in opentelemetry-python-contrib `_semconv.py`.
  - However, opt-in is per signal. `_set_db_system()` writes the new `db.system.name` only when the DATABASE signal is opted in (`database` or `database/dup`). Otherwise it writes the legacy `db.system`. psycopg instrumentation goes through dbapi, which follows this path, and its `_semconv_status` is `"migration"`.
  - HTTP spans from FastAPI and httpx likewise stay on the old HTTP semconv unless `http` is opted in. Epic 7's spanmetrics dimensions would then key on legacy attribute names.
- **Fix.** Set `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental,database,http`. Pin `opentelemetry-instrumentation-*` to 0.66b2 or later (released 2026-10-29). Add a span-contract test that asserts `db.system.name`.

### F2 — MEDIUM — AD-5 / Deferred OAuth: Claude's support for protocol 2026-07-28 is unconfirmed

- **Claim.** `mcp` speaks protocol 2026-07-28, and epic 6 must work with Claude Desktop remote connectors and CIMD.
- **Found.**
  - **CIMD is confirmed.** Anthropic's connector auth docs list `oauth_cimd` as supported by default, with these conditions:
    - Claude selects CIMD only when the authorization server metadata advertises both `client_id_metadata_document_supported: true` and `"none"` in `token_endpoint_auth_methods_supported`. Otherwise it falls back to DCR.
    - The redirect URI is `https://claude.ai/api/mcp/auth_callback`.
    - A 401 with `WWW-Authenticate: Bearer resource_metadata=…` is required.
    - Claude uses only the first `authorization_servers` entry.
    - Traffic comes from Anthropic's egress range `160.79.104.0/21`, not from the desktop machine.
  - **The protocol version is not confirmed.** The same docs cite the 2025-11-25 authorization spec. No Anthropic source says Claude clients speak 2026-07-28.
  - The mcp SDK v2 serves both eras: `HANDSHAKE_PROTOCOL_VERSIONS` covers 2024-11-05 through 2025-11-25, and `MODERN_PROTOCOL_VERSIONS` is `("2026-07-28",)`. So the approach works, provided nothing restricts the server to 2026-07-28 only.
- **Fix.** Reword AD-5 to "serves 2026-07-28 and the SDK's handshake versions (≥2025-11-25), stateless". Record the CIMD metadata requirements as epic 6 acceptance criteria.
- **Related.** SDK v2 enables DNS-rebinding protection by default on mounted apps. Unless `transport_security.allowed_hosts` includes the public host and the Service name, requests return `421 Invalid Host header`.

### F3 — MEDIUM — AD-18: "IRSA or Pod Identity" is only half documented, and the IRSA role's home is unplaced

- **Claim.** The Barman Cloud Plugin authenticates by IRSA or Pod Identity.
- **Found.**
  - The plugin 0.15.1 docs ("Object stores") document IRSA via `spec.serviceAccountTemplate.metadata.annotations["eks.amazonaws.com/role-arn"]`, and recommend it for EKS.
  - Pod Identity is not mentioned. The plugin says it "does not independently test all authentication methods supported by barman-cloud".
  - The IRSA trust policy names the cluster's OIDC issuer, and that issuer changes with every ephemeral `env` apply. The role therefore cannot sit in `bootstrap` with a fixed trust policy.
- **Fix.** Commit to IRSA. Create the backup role (or its trust policy) in the `env` stack. The bucket stays in `bootstrap`. Drop "Pod Identity" unless a spike confirms it.

### F4 — LOW — AD-13/AD-14: Gateway API CRD ownership differs per environment, and ACM uses certificate discovery

- **Found.**
  - **AWS LBC.** It supports ALB through `HTTPRoute`, with no feature flag (it auto-detects the CRDs). It is built for Gateway API v1.6.0, and requires the standard CRDs plus its own CRDs (`LoadBalancerConfiguration`, `TargetGroupConfiguration`, `ListenerRuleConfiguration`) to be applied separately. ACM certificates are found by **certificate discovery from listener and route hostnames**; `certificateRefs` is not supported.
  - **Envoy Gateway.** The v1.9.3 Helm chart installs the Gateway API CRDs itself (v1.6.1) and supports K8s 1.33–1.36. On kind, a Gateway gets no address without MetalLB or cloud-provider-kind, so it falls back to port-forward.
- **Fix.** Have the `platform` release own the Gateway API standard CRDs in both environments, and install Envoy Gateway with its CRDs skipped. Set `hostname` on the listener or `HTTPRoute` so ACM discovery finds the bootstrap cert. Name the kind LoadBalancer approach in `_kind-deploy.yml`.

### F5 — LOW — AD-10: "httpx" is the wrong client library for this SDK generation

- **Found.**
  - mcp 2.3.0 depends on `httpx2>=2.10.0` (pydantic/httpx2, 2.16.0, released 2026-10-21), not `httpx`. `httpx` 0.28.1 was last released in 2024-12.
  - `opentelemetry-instrumentation-httpx` instruments both libraries (`_instruments_any` includes `httpx2 >= 2.0.0`), but only from 0.65b0 onward, per the CHANGELOG ("add support for httpx2").
- **Fix.** Write `apiclient` on `httpx2`, so the image has one HTTP stack. Require instrumentation 0.65b0 or later. Change "httpx" to "httpx2" in AD-10.

### F6 — INFO — pg_search/vchord_bm25 conflict claim rests on secondary sources

- **Found.**
  - The pg_textsearch README does not state the conflict. Pigsty's extension catalogue does: all three register a `bm25` access method.
  - pg_search 0.25 renamed its access method to `paradedb` but keeps `bm25` as an alias.
  - The exclusion decision is still right, but the rationale should cite the access-method name clash rather than imply an upstream statement.

## Fit claims confirmed (no action)

| Claim | Evidence |
| --- | --- |
| CNPG `standard` PG18 image bundles pgvector and is multi-arch | cloudnative-pg/postgres-containers README: standard = minimal + PGAudit, Failover Slots, pgvector, all locales, LLVM JIT; `linux/amd64` + `linux/arm64`; Debian trixie/bookworm on PGDG apt |
| pg_textsearch can be added by a Dockerfile, on arm64 | **Packaged in PGDG**: `postgresql-18-pg-textsearch 1.5.1-1.pgdg13+1` in `trixie-pgdg` binary-arm64 (and amd64), alongside `postgresql-18-pgvector 0.8.7`. The Dockerfile is a one-line `apt-get install`; no source build needed. GitHub release v1.5.1 (2026-10-02) also ships pg18 amd64 and arm64 zips. |
| pg_textsearch needs `shared_preload_libraries` and CNPG allows it | README says preloading is required (since v0.6.0). CNPG release-1.30 docs: "provide additional `shared_preload_libraries` via `.spec.postgresql.shared_preload_libraries` as a list of strings", merged with the managed ones. The docs warn that a missing library stops the server from starting. |
| pg_textsearch coexists with pgvector | Different operators (`<@>` versus pgvector's `<->`/`<=>`/`<#>`) and different access methods (`bm25` versus `hnsw`/`ivfflat`). No reported conflict. Only caveat: pg_textsearch uses LWLock tranche IDs 1001–1012. |
| MCP SDK v2 emits OTel SERVER spans and propagates W3C context | SDK docs/run/opentelemetry.md: `tools/call {tool}` SERVER span with `mcp.method.name`, `mcp.protocol.version`, `gen_ai.operation.name=execute_tool`, `gen_ai.tool.name`; depends on `opentelemetry-api>=1.28`; SEP-414 propagation. If no inbound context, the span parents to the current span, so ASGI instrumentation on `mcp` adds a `POST /mcp` parent. Reflect this in the AD-10 tree or leave ASGI uninstrumented. |
| psycopg instrumentation covers async and reports postgresql | `_DATABASE_SYSTEM = "postgresql"`; supports `psycopg.AsyncConnection`; `psycopg >= 3.1.0` |
| spanmetrics connector in otelcol-contrib | opentelemetry-collector-releases otelcol-contrib manifest v0.164.0 includes `connector/spanmetricsconnector v0.164.1` |
| fastembed/onnxruntime arm64 wheels for Python 3.14 | onnxruntime 1.31.1 `cp314-manylinux_2_28_aarch64` (glibc only, no musllinux, so the app image must not be Alpine); fastembed 0.9.1 is pure Python and needs onnxruntime ≥1.24.2 on 3.14; tokenizers (abi3), py-rust-stemmers 0.1.8, numpy 2.5.4, pillow 13.0.0, mmh3 5.3.1 and psycopg-binary 3.3.8 all have cp314 aarch64 wheels |
| kind 1.36 node image | kind v0.33.0 release notes list `kindest/node:v1.36.4@sha256:099e04…`. The default is v1.37.0, so the pin must be explicit with its digest. |
| In-tree `barmanObjectStore` removed in CNPG 1.32 | CNPG release-1.30 backup.md: deprecated since 1.26; 1.31 is the last minor with native support; removed starting 1.32.0 |
| Cloudflare quick-tunnel limits | Cloudflare docs: no SSE, 200 in-flight requests (then 429), hostname changes each time |

## Sources

- pg_textsearch README and releases: https://github.com/timescale/pg_textsearch (v1.5.1 assets via `gh api repos/timescale/pg_textsearch/releases/latest`)
- PGDG apt index: https://apt.postgresql.org/pub/repos/apt/dists/trixie-pgdg/main/binary-arm64/Packages.gz
- CNPG postgres-containers: https://github.com/cloudnative-pg/postgres-containers
- CNPG 1.30 docs (postgresql_conf.md, backup.md on branch release-1.30): https://github.com/cloudnative-pg/cloudnative-pg/tree/release-1.30/docs/src
- Barman Cloud Plugin object stores (0.15.1): https://cloudnative-pg.io/plugin-barman-cloud/docs/object_stores/
- AWS LBC Gateway API guide: https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/gateway/gateway/
- Envoy Gateway quickstart and compatibility matrix: https://gateway.envoyproxy.io/docs/tasks/quickstart/ , https://gateway.envoyproxy.io/news/releases/matrix/
- kind v0.33.0 release: https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0
- MCP Python SDK OTel docs, version registry and migration guide: https://github.com/modelcontextprotocol/python-sdk (docs/run/opentelemetry.md, src/mcp-types/mcp_types/version.py, docs/migration.md)
- PyPI JSON: mcp 2.3.0, httpx2 2.16.0, httpx 0.28.1, opentelemetry-instrumentation-{httpx,psycopg,fastapi} 0.66b2, onnxruntime 1.31.1, fastembed 0.9.1 (https://pypi.org/pypi/<name>/json)
- OTel Python contrib: opentelemetry-instrumentation/_semconv.py, instrumentation/opentelemetry-instrumentation-httpx/.../package.py, dbapi/__init__.py, psycopg/__init__.py, CHANGELOG.md: https://github.com/open-telemetry/opentelemetry-python-contrib
- otelcol-contrib manifest: https://github.com/open-telemetry/opentelemetry-collector-releases/blob/main/distributions/otelcol-contrib/manifest.yaml
- Claude connector authentication: https://claude.com/docs/connectors/building/authentication
- Cloudflare quick tunnels: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/
- pg_textsearch conflict (secondary): https://pigsty.io/ext/e/pg_textsearch , https://pigsty.io/ext/e/pg_search
