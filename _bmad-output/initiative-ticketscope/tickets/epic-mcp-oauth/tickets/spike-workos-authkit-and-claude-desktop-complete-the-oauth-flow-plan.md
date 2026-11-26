---
title: 'Spike: WorkOS AuthKit and Claude Desktop complete the OAuth flow against a throwaway resource'
type: 'spike'
ticket: '1'
created: '2026-11-26'
status: 'in-progress'
baseline_revision: '6aff82df692de67f318424b51bbe1a462ad402ee'
route: 'full'
risk: 'high'
context: []
---

## Intent

**Problem:** The epic assumes WorkOS AuthKit works with Claude Desktop's remote-connector flow. Nothing has shown it, and stories 2 to 7 need the issuer, audience, signing-key URL, scope and callback values it would settle.

**Approach:** Read AuthKit's authorisation-server metadata, then run a throwaway resource server outside the repo behind the epic 4 tunnel hostname. A person adds it to Claude Desktop as a custom connector and signs in. Record what the flow needed and what the token carried. Stytch is the fallback only if AuthKit fails.

## Outcome

**AuthKit works. Stytch was not needed.** Claude Desktop completed the remote-connector sign-in through AuthKit against the throwaway server and called its one tool, which answered "pong" (2026-11-26).

## Step 1: AuthKit metadata

Read from `https://euphoric-oath-33-sandbox.authkit.app/.well-known/oauth-authorization-server`.

| Field | Value |
|---|---|
| `issuer` | `https://euphoric-oath-33-sandbox.authkit.app` |
| `authorization_endpoint` | `…/oauth2/authorize` |
| `token_endpoint` | `…/oauth2/token` |
| `jwks_uri` | `https://euphoric-oath-33-sandbox.authkit.app/oauth2/jwks` |
| `client_id_metadata_document_supported` | `true` (after the setting below; absent before) |
| `registration_endpoint` | absent; dynamic client registration is off |
| `token_endpoint_auth_methods_supported` | `none`, `client_secret_post`, `client_secret_basic` |
| `code_challenge_methods_supported` | `S256` |
| `scopes_supported` | `email`, `offline_access`, `openid`, `profile` |

**What AuthKit needed turned on.** Client ID Metadata Document support is off by default and the metadata omits the field until it is enabled. It is in the WorkOS dashboard under Connect → Configuration → MCP Auth: Client ID Metadata Document enabled, Dynamic Client Registration left disabled. The same page holds the MCP resource indicator, set to `https://blitz-utmost-jarring.ngrok-free.dev/mcp` (set through the `setAuthkitOauthResources` operation). Neither setting is reachable from the WorkOS MCP server's other operations, so story 7 repeats them by hand in the dashboard for the live hostname.

## Step 2: throwaway resource server

Kept outside the repo and not committed. It served `/.well-known/oauth-protected-resource` (resource = the tunnel's `/mcp`, `authorization_servers` = the issuer), answered `/mcp` without a valid token with 401 and `WWW-Authenticate: Bearer resource_metadata="…/.well-known/oauth-protected-resource"`, verified RS256 signature, issuer, audience and expiry against the issuer's JWKS, and answered one tool, `ping`. It ran behind ngrok on `blitz-utmost-jarring.ngrok-free.dev`.

Observed sequence in its log: a tokenless `/mcp` call got 401, Claude fetched the metadata, the sign-in ran, and every later call carried a token that passed all four checks. Methods seen: `server/discover` (protocol 2026-07-28), `initialize`, `notifications/initialized`, `tools/list`, `tools/call` (protocol 2025-11-25). The throwaway server answered `server/discover` with "method not found" and Claude fell back without error, so the real server must tolerate it too.

## Values for stories 2 to 7

| Item | Value |
|---|---|
| Issuer URL | `https://euphoric-oath-33-sandbox.authkit.app` |
| Audience | the resource indicator, exactly: `<public host>/mcp`. Here `https://blitz-utmost-jarring.ngrok-free.dev/mcp`; the live value is the EKS hostname's `/mcp` |
| Signing-key URL | `https://euphoric-oath-33-sandbox.authkit.app/oauth2/jwks` |
| Algorithm | RS256; one key (`use: sig`) published |
| Token claims | `iss`, `aud`, `exp`, `iat`, `auth_time`, `jti`, `sid`, `sub`, `scope`, `client_id` |
| `scope` claim | `email offline_access openid profile` |
| `client_id` claim | `https://claude.ai/oauth/mcp-oauth-client-metadata` (the CIMD URL) |
| Access-token lifetime | 300 s (`exp` − `iat`) |
| Signing-key lifetime | not stated: the JWKS response has no cache headers and no rotation was observed. Story 3 picks its own bounded cache time and one refetch on an unknown key id |
| Callback URL | **not observed** (see Open) |
| Scope name | **no custom scope exists** (see Open) |

The stub issuer in story 2 imitates the claim names, the `client_id` form, the 300 s lifetime and RS256 above. No `sub` or other identifier from the session is recorded here.

## Open

- **Scope name.** AuthKit advertises no custom scope, and the token carries only the OIDC scopes. The epic decided one scope covers both tools, but there is no value to name. Options for the user: (a) the server requires `openid`, which every token has, and the audience is the real gate; (b) the server checks audience only and the epic's "one scope" wording is reworded. This needs a Decision in the epic's Notes before story 2.
- **Callback URL.** AuthKit's redirect happens between Claude and AuthKit and never reaches the resource server, so the server log cannot show it. The `client_id` is the `claude.ai` metadata document, consistent with `claude.ai/api/mcp/auth_callback`, but that is not observed. A person reads the redirect URI from the AuthKit sign-in request (browser address bar during sign-in) and records it here.
- **Signing-key lifetime and rotation** unobserved; see above.
- **ngrok free-plan bandwidth** is irrelevant to the live check (it uses the EKS hostname).

## Verification

- Metadata fields above read from the live AuthKit domain: done.
- Claude Desktop completed the flow and the tool answered: done (server log and the ngrok request list agree: `POST /mcp` 200 and 202 after the sign-in).
- No secret, token or API key committed; nothing from the throwaway server committed: the server and its log live in the session scratchpad only. `.env` (WorkOS credentials) is git-ignored.
- Stytch run: not needed, AuthKit passed both steps.

## Cleanup

Stop the throwaway server and ngrok. The sandbox resource indicator may stay; story 7 replaces it with the live hostname.
