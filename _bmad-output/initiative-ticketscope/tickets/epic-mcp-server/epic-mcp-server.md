---
type: epic
title: "Claude Desktop calls search_similar_issues on a remote MCP server"
parent: initiative-ticketscope
covers: [R4, R8]
sources: []
companions: []
after: []
refined: true
risk: medium
---

# Claude Desktop calls search_similar_issues on a remote MCP server

## Description

A stateless Streamable HTTP MCP server, built to the 2026-07-28 spec, runs as its own Deployment in the chart.

- **Tools.** It exposes `search_similar_issues` and `get_issue`. They call epic 1's /v1 API over HTTP and return its bodies. `search_similar_issues` takes an optional mode; `get_issue` takes the readable issue key (`MCL-6629`).
- **Checks.** An MCP client test passes in CI on kind. Claude Desktop answers from the server through a tunnel with a fixed hostname.
- **Trace.** One trace runs from the tool call through retrieval to the database.
- **Auth.** There is none yet; epic 6 adds it.

Epic 5 serves this endpoint live, epic 7 charts its telemetry, and epic 8 uses its trace screenshot.

## Outcome

An AI assistant can use ticketscope as a tool: Claude Desktop calls search_similar_issues and answers from the results, traced from end to end (initiative R4, R8; brief Success Criteria 2).

## Requirements

- R1 (parent R4): An MCP client calls `search_similar_issues` with a query and an optional mode and k on the remote server at `/mcp`, and receives the `/v1/search` body as structured output whose schema is generated from `ticketscope.contract`. It is met when the CI client test on kind calls it with and without a mode and the results validate against that schema.
- R2 (parent R4): An MCP client calls `get_issue` with an issue's readable key and receives that issue and its outcome as structured output. It is met when the CI client test takes a key from a search result, fetches it, and gets the issue with that key back.
- R3 (parent R4): A failed tool call comes back as an MCP tool error carrying the API's problem detail, never as a protocol failure or an empty result. It is met when an unknown mode, an unknown key and an unreachable API each return a tool error with that detail in the CI client test.
- R4 (parent R4): Claude Desktop, connected through a tunnel with a fixed hostname to the kind cluster, calls `search_similar_issues` and answers from its results. It is met when a recorded session shows the tool call and an answer citing returned issues.
- R5 (parent R8): One trace spans the MCP tool call, the HTTP hop to the API, retrieval and the database, and continues the caller's trace context from the MCP request's `_meta` when present. It is met when a CI check on kind finds one trace in Tempo with that span tree under a `ticketscope-mcp` root, and a call carrying a `traceparent` in `_meta` lands in the caller's trace.

## Constraints

- **Protocol:** the official `mcp` SDK v2 (`MCPServer`) over stateless Streamable HTTP at `/mcp`, serving protocol 2026-07-28 plus the SDK's handshake-era versions. Stateless means safe at any replica count; kind runs two replicas (spine AD-3, AD-5).
- **Topology:** `mcp` is its own Deployment from the one app image, selected by a `ticketscope-mcp` entrypoint. It holds no database connection and no model, and reaches `api` only through `ticketscope.apiclient` (httpx2) over the in-cluster Service. import-linter enforces that `mcp` and `apiclient` import only `contract` and `apiclient` (spine AD-1, AD-2, AD-3).
- **Contract:** tool output is the `/v1` body unchanged, built from `ticketscope.contract` models that pass unknown fields through (spine AD-4, AD-20). The issue `key` joins `/v1` additively and is read from the issue's `url`; no column is added, nothing is reloaded and the preprocessing version does not change (spine AD-21, Identifiers convention).
- **Mode:** `mcp` has no default mode. An omitted mode is omitted on the `/v1` call, so the server default applies (spine AD-25).
- **Routing:** a `/mcp` HTTPRoute on the `platform` Gateway, and `transport_security.allowed_hosts` from values so the gateway's and the tunnel's host headers are accepted (spine AD-5, AD-14).
- **Values:** this epic owns the `mcp` keys in `values.yaml`. Environment files hold only environment facts: hostname, allowed hosts and replica counts (spine AD-25).
- **Telemetry:** `service.name` is `ticketscope-mcp`, spans follow the AD-10 tree and attributes, export is OTLP to the in-cluster collector only, and query text is recorded only when a value opts in (spine AD-10, AD-11).
- **Errors:** a tool error sets `is_error` with the problem `detail`, and its span status is `ERROR` (spine Errors convention).
- **CI:** `mcp-e2e.yml` runs on PRs through `_kind-deploy.yml`, with the same path filter the other kind jobs use. This epic's tests live in `tests/mcp/` (spine AD-17).
- **Tunnel:** ngrok's free static domain, with Tailscale Funnel as the fallback if ngrok's free plan fails a check. It runs on a person's machine, never in CI, and no tunnel credential is committed.

## Done when

- An MCP client test in CI on kind calls `search_similar_issues`, with and without a mode, and `get_issue` by key. It receives structured results whose schema is generated from the /v1 contract module, and failures come back as tool errors with the API's detail (R4).
- Claude Desktop, connected through a tunnel with a fixed hostname to the cluster, calls `search_similar_issues` and answers from the results (R4).
- One trace spans the MCP tool call, the HTTP hop to the API, retrieval and the database. It continues the caller's trace context from MCP's `_meta` when present (R8).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- The MCP server holds no database connection and no model; it reaches retrieval only through the /v1 API.
- OAuth belongs to epic-mcp-oauth, and the live URL to epic-eks-environment.
- In the chart, this epic owns the `mcp` keys. Retrieval defaults and `api` resources are epic-hybrid-retrieval's.
- Out: server-side LLM answers. The client writes the answer (initiative Constraints).
- Out: tool-call metrics and the dashboard (epic-grafana-dashboard), and an eval of tool-call behaviour (initiative Boundaries).
- Touch point: Claude Desktop — the MCP client, configured only; owner: epic-mcp-server
- Touch point: a tunnel service (ngrok static domain; Tailscale Funnel as fallback) — exposes the kind cluster to Claude Desktop before EKS exists on a fixed hostname; owner: epic-mcp-server

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R4, R8)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1–AD-5, AD-10, AD-11, AD-13, AD-14, AD-17, AD-20, AD-21, AD-25, and Open questions (MCP `get_issue` argument)

## Notes

- Waits on epic-search-baseline because: it needs the /v1 API and contract module, the Helm releases, the CI layout, and the OTel Collector, Tempo and span contract.
- Decision: Adopted the architecture spine. The tools take an optional mode argument rather than always using the API default, and the server is a separate Deployment calling /v1 over HTTP (user, 2026-11-05).
- Decision: Refined with Sofia's picks (user, "your picks", 2026-11-10). `get_issue` takes the readable key, read from `url`, with no new column or reload; a real `key` column was declined because it would force a reload, a baseline update and a new embedding asset. This settles the spine's open question on the `get_issue` argument.
- Decision: The tunnel is ngrok's free static domain, with Tailscale Funnel as the fallback. A Cloudflare named tunnel was declined: it needs the domain's DNS on Cloudflare, which conflicts with epic 5's Route53 zone (user, 2026-11-10).
- Decision: Tracer bullet is story 1, an MCP client calling `search_similar_issues` through the Gateway on kind in CI. Story 2, Claude Desktop through the tunnel, follows as the least certain part (user, 2026-11-10).
- Decision: Stories 1–5 form one lane, because each edits the `mcp` server module. Story 2 comes before 3 so any server change Claude Desktop needs lands before the error, key and trace work (user, 2026-11-10).
- Decision: The epic builds unattended in the bmad-loop, with a plan checkpoint on stories 1, 2 and 4. It closes with a refactor sweep and an integrated check on kind, as in epic-search-baseline and epic-hybrid-retrieval (user, 2026-11-10).
- Decision: This epic runs alongside epic-hybrid-retrieval's stories 3.5–3.8 with no `after` between them. The only shared file is `values.yaml`, where the keys are split per Boundaries, and this epic's tests live in `tests/mcp/` (user, 2026-11-10).
- Decision: Story 4.4 adds an issue lookup by key to the `CorpusStore` port, its fake and the Postgres adapter. epic-hybrid-retrieval's refactor sweep (3.7) leaves those lookup methods alone, so the two epics need no `after` between them (Sofia's pick after the set check, under the user's "your picks", 2026-11-10).
- Decision: The tunnel's hostname is an environment value added to both the `/mcp` route's hostnames and `allowed_hosts`, so it works for ngrok or Tailscale Funnel without rewriting the Host header (Sofia's pick after the set check, 2026-11-10).
