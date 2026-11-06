---
type: epic
title: "Claude Desktop calls search_similar_issues on a remote MCP server"
parent: initiative-ticketscope
covers: [R4, R8]
sources: []
companions: []
after: []
refined: false
risk: medium
---

# Claude Desktop calls search_similar_issues on a remote MCP server

## Description

A stateless Streamable HTTP MCP server, built to the 2026-07-28 spec, runs as its own Deployment in the chart.

- **Tools.** It exposes `search_similar_issues` and `get_issue`. They call epic 1's /v1 API over HTTP and return its bodies, with an optional mode argument.
- **Checks.** An MCP client test passes in CI on kind. Claude Desktop answers from the server through a named tunnel.
- **Trace.** One trace runs from the tool call through retrieval to the database.
- **Auth.** There is none yet; epic 6 adds it.

Epic 5 serves this endpoint live, epic 7 charts its telemetry, and epic 8 uses its trace screenshot.

## Outcome

An AI assistant can use ticketscope as a tool: Claude Desktop calls search_similar_issues and answers from the results, traced from end to end (initiative R4, R8; brief Success Criteria 2).

## Done when

- An MCP client test in CI on kind calls `search_similar_issues`, with and without a mode, and `get_issue`. It receives structured results whose schema is generated from the /v1 contract module (R4).
- Claude Desktop, connected through a named tunnel to the cluster, calls `search_similar_issues` and answers from the results (R4).
- One trace spans the MCP tool call, the HTTP hop to the API, retrieval and the database. It continues the caller's trace context from MCP's `_meta` when present (R8).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- The MCP server holds no database connection and no model; it reaches retrieval only through the /v1 API.
- OAuth belongs to epic-mcp-oauth, and the live URL to epic-eks-environment.
- In the chart, this epic owns the `mcp` keys. Retrieval defaults and `api` resources are epic-hybrid-retrieval's.
- Out: server-side LLM answers. The client writes the answer (initiative Constraints).
- Touch point: Claude Desktop — the MCP client, configured only; owner: epic-mcp-server
- Touch point: a tunnel service — exposes the kind cluster to Claude Desktop before EKS exists, as a named tunnel (quick tunnels lack SSE and get a random hostname each time); owner: epic-mcp-server

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R4, R8)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1–AD-5, AD-10, AD-11, AD-13, AD-14, AD-17, AD-20, AD-25

## Notes

- Waits on epic-search-baseline because: it needs the /v1 API and contract module, the Helm releases, the CI layout, and the OTel Collector, Tempo and span contract.
- Decision: Adopted the architecture spine. The tools take an optional mode argument rather than always using the API default, and the server is a separate Deployment calling /v1 over HTTP (user, 2026-11-05).
