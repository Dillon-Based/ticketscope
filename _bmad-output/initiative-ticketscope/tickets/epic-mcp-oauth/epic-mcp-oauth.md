---
type: epic
title: "Claude Desktop authenticates to the live MCP server"
parent: initiative-ticketscope
covers: [R4]
sources: []
companions: []
after: []
refined: false
risk: high
---

# Claude Desktop authenticates to the live MCP server

## Description

The MCP server requires OAuth 2.1 with Client ID Metadata Documents. It acts as a resource server against an external hosted authorisation server. Claude Desktop's remote-connector flow authenticates against epic 5's live HTTPS URL and calls search_similar_issues, and unauthenticated calls are refused. Epic 8 records this session.

## Outcome

The live MCP server is authenticated as the current spec requires, and Claude Desktop still uses it (initiative R4; brief Success Criteria 2).

## Done when

- An unauthenticated call to the live MCP endpoint is refused. `/.well-known/oauth-protected-resource` names the external authorisation server (R4).
- Claude Desktop completes the remote-connector OAuth flow against the live URL and calls `search_similar_issues` (R4).
- The OAuth configuration is applied as environment values by the same deploy as epic-eks-environment, with no manual steps.
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- This is the second epic on the brief's cut list. If it is cut, the server stays unauthenticated and epic 8 records that session.
- The authorisation server is never built or run on the cluster or the public host.
- Touch point: an external hosted OAuth authorisation server — configured, not built or run on the cluster; owner: epic-mcp-oauth

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R4)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1–AD-3, AD-5, AD-14, AD-15, AD-23, AD-25

## Notes

- Waits on epic-mcp-server because: it needs the MCP server.
- Waits on epic-eks-environment because: it needs a fixed public HTTPS hostname for the OAuth redirect and Claude Desktop's connector.
- Decision: Adopted the architecture spine. The authorisation server is external and hosted, and the MCP server is only a resource server (user, 2026-11-05).
