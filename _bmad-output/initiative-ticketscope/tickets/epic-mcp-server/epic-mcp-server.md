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

A stateless Streamable HTTP MCP server, built to the 2026-07-28 spec, runs in the chart and exposes search_similar_issues and get_issue over epic 1's retrieval API, in its default mode. An MCP client test passes in CI on kind, Claude Desktop answers from it through a tunnel, and one trace runs from the tool call through retrieval to the database. Auth comes in epic 6. Epic 5 serves this endpoint live, and epic 7 charts its telemetry.

## Outcome

An AI assistant can use ticketscope as a tool: Claude Desktop calls search_similar_issues and answers from the results, traced from end to end (initiative R4, R8; brief Success Criteria 2).

## Done when

- An MCP client test in CI on kind calls search_similar_issues and get_issue and receives structured results (R4).
- Claude Desktop, connected through a tunnel to the cluster, calls search_similar_issues and answers from the results (R4).
- One trace spans the MCP tool call, retrieval and the database, propagated through MCP's _meta trace context (R8).
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- OAuth belongs to epic-mcp-oauth, and the live URL to epic-eks-environment.
- Out: server-side LLM answers. The client writes the answer (initiative Constraints).
- Touch point: Claude Desktop — the MCP client, configured only; owner: epic-mcp-server
- Touch point: a tunnel service — exposes the kind cluster to Claude Desktop before EKS exists; owner: epic-mcp-server

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R4, R8)

## Notes

- Waits on epic-search-baseline because: it needs the retrieval API contract, the Helm chart, the CI layout, and the OTel collector, backend and span contract.
