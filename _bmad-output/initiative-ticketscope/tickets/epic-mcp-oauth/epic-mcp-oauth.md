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

The MCP server requires OAuth 2.1 with Client ID Metadata Documents. Claude Desktop's remote-connector flow authenticates against epic 5's live HTTPS URL and calls search_similar_issues, and unauthenticated calls are refused. Epic 8 records this session.

## Outcome

The live MCP server is authenticated as the current spec requires, and Claude Desktop still uses it (initiative R4; brief Success Criteria 2).

## Done when

- An unauthenticated call to the live MCP endpoint is refused (R4).
- Claude Desktop completes the remote-connector OAuth flow against the live URL and calls search_similar_issues (R4).
- The OAuth configuration is applied by the same apply and deploy as epic-eks-environment, with no manual steps.
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- This is the second epic on the brief's cut list. If it is cut, the server stays unauthenticated and epic 8 records that session.
- Touch point: an OAuth authorisation server — configured, not built; owner: epic-mcp-oauth

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R4)

## Notes

- Waits on epic-mcp-server because: it needs the MCP server.
- Waits on epic-eks-environment because: it needs a public HTTPS URL for the OAuth redirect and Claude Desktop's connector.
