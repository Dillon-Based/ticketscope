---
type: epic
title: "Claude Desktop authenticates to the live MCP server"
parent: initiative-ticketscope
covers: [R4]
sources: []
companions: []
after: []
refined: true
risk: high
---

# Claude Desktop authenticates to the live MCP server

## Description

The MCP server requires OAuth 2.1 with Client ID Metadata Documents. It acts as a resource server against an external hosted authorisation server. Claude Desktop's remote-connector flow authenticates against epic 5's live HTTPS URL and calls search_similar_issues, and unauthenticated calls are refused. Epic 8 records this session.

## Outcome

The live MCP server is authenticated as the current spec requires, and Claude Desktop still uses it (initiative R4; brief Success Criteria 2).

## Requirements

- R1 (parent R4): An unauthenticated call to the live MCP endpoint is refused. It is met when a request to `/mcp` with no token, a malformed token, an expired token, a token with the wrong issuer and a token with the wrong audience each get a 401 with a `WWW-Authenticate` header naming the protected-resource metadata, on the live hostname and in the kind integrated check.
- R2 (parent R4): The server publishes where its authorisation server is. It is met when `/.well-known/oauth-protected-resource` is served without a token over the public hostname, names the live `/mcp` URL as the resource and the external authorisation server as its issuer, and is the only path open without a token.
- R3 (parent R4): A valid token for this resource reaches both tools. It is met when a token that passes signature, issuer, audience and expiry checks can call `search_similar_issues` and `get_issue` and gets the same bodies as before auth, and one scope covers both.
- R4 (parent R4): The OAuth configuration is applied as environment values by the same deploy as epic 5, with no manual steps. It is met when `env-up` brings the live server up with auth on, from `values-eks.yaml` alone, and a kind release with auth off or on is selected by values only.
- R5 (parent R4): Claude Desktop authenticates against the live URL and calls the tool. It is met when a recorded session shows Claude Desktop's remote-connector flow completing against epic 5's live hostname, calling `search_similar_issues` and answering from its results, and the same server refusing the unauthenticated call.

## Constraints

- **Resource server only:** `mcp` validates tokens and serves the metadata. The authorisation server is an external hosted service, never deployed on the cluster or behind the public host, and `api` stays unauthenticated and in-cluster (spine AD-5).
- **Authorisation server:** WorkOS AuthKit, configured with `client_id_metadata_document_supported`, token endpoint auth method `none`, and the callback `claude.ai/api/mcp/auth_callback` (spine open items; decision 2026-11-26).
- **Validation:** tokens are verified locally as JWTs for signature, issuer, audience and expiry against cached signing keys. There is no introspection and no client secret in the cluster (decision 2026-11-26).
- **Scope:** one scope covers both tools (decision 2026-11-26).
- **Routes:** the route table is fixed: `/mcp` and `/.well-known/oauth-protected-resource` go to `mcp`, and the rest of the table is unchanged (AD-14).
- **Values:** auth on or off and the issuer are environment facts in `values-kind.yaml` and `values-eks.yaml`; `values.yaml` holds the defaults, and `mcp` has no auth default that bypasses a check (AD-25).
- **CI:** the kind integrated check mints tokens from a local stub issuer. CI never calls the hosted authorisation server and holds no credential for it (decision 2026-11-26; initiative no-stored-keys constraint).
- **Wording:** "a personal project, deployed and operated on Kubernetes", never "production" (initiative Constraints).

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

- Decision: authorisation server is WorkOS AuthKit; story 1 is a spike proving Claude Desktop completes the flow against it, with Stytch as the fallback and Cognito ruled out for lacking Client ID Metadata Documents support (user, 2026-11-26).
- Decision: `mcp` verifies JWTs locally; introspection declined (user, 2026-11-26).
- Decision: one scope covers both tools; per-tool scopes declined (user, 2026-11-26).
- Decision: only the protected-resource metadata is open; opening the handshake declined (user, 2026-11-26).
- Decision: the kind integrated check uses a local stub issuer; calling the real AuthKit from CI declined (user, 2026-11-26).
- Decision: the live Claude Desktop check is part of the epic's last story, which parks awaiting the operator; a separate hitl story declined (user, 2026-11-26).
- Waits on epic-mcp-server because: it needs the MCP server.
- Waits on epic-eks-environment because: it needs a fixed public HTTPS hostname for the OAuth redirect and Claude Desktop's connector.
- Decision: Adopted the architecture spine. The authorisation server is external and hosted, and the MCP server is only a resource server (user, 2026-11-05).
