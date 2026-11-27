---
title: 'Tracer: mcp refuses a tokenless call and answers a call with a stub-signed token'
type: 'feature'
ticket: '2'
created: '2026-11-27'
status: ready-for-dev
baseline_revision: '9268912509a665e1a2d8e47dc956794f82baa2e3'
route: 'full'
route_source: 'auto'
risk: 'high'
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** `mcp` answers any caller. The epic needs it to be an OAuth 2.1 resource server: refuse a request without a valid token, publish where its authorisation server is, and still answer both tools for a valid token.

**Approach:** A pure-ASGI auth middleware in `ticketscope.mcp` wraps the existing Starlette app when auth is on. It verifies RS256 JWTs (signature, issuer, audience, expiry) against signing keys fetched from the issuer and cached. The metadata route is served by the same app. A stub issuer in `tests/mcp/` mints tokens. Server code only: no chart, no cluster.

## Boundaries & Constraints

**Always:**
- Auth off (the default) leaves behaviour byte-identical: `build_app(settings, client)` and every existing mcp test pass unchanged.
- No scope check; the audience equal to the `/mcp` URL is the gate (epic Notes, 2026-11-27).
- Auth settings (`TICKETSCOPE_MCP_AUTH_ENABLED`, `_AUTH_ISSUER`, `_AUTH_AUDIENCE`) are read in `ticketscope.mcp.main` and nowhere else. `main` builds a frozen `AuthConfig` and passes it to `build_app(settings, client, auth=None)`. Auth on with an empty issuer or audience exits at startup, like `api_base_url`.
- Algorithm pinned to RS256; `iss`, `aud`, `exp` required. Keys: found via `<issuer>/.well-known/oauth-authorization-server` `jwks_uri`, cached with a bounded lifetime (10 min), one refetch on an unknown `kid`, refetches rate-limited so a stream of bad `kid`s cannot hammer the issuer.
- Refusal is 401 with `WWW-Authenticate: Bearer resource_metadata="<origin of audience>/.well-known/oauth-protected-resource"`; a present-but-bad token adds `error="invalid_token"`. The response never says why a token failed.
- `/.well-known/oauth-protected-resource` returns `{"resource": <audience>, "authorization_servers": [<issuer>], "bearer_methods_supported": ["header"]}` with no token. `/healthz` stays open: the kubelet probes it and the Gateway never routes it (AD-14), so it is not reachable publicly.
- The only new dependency is the token library: declare `pyjwt[crypto]` explicitly (already in `uv.lock` via `mcp`). Keys are fetched with `httpx2`.

**Never:** a scope check; introspection; a client secret; touching `api`, the chart, values, `ci.yml` wiring or the epic/ticket files; adding `mcp` imports of `core`, `adapters`, `http`, `jobs`, `psycopg` or `fastembed`; any default that lets `mcp` run with auth half-configured; writing token or `sub` values to logs or committed files; `tickets.py mark`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid token | `Authorization: Bearer <stub-signed, right iss/aud, exp future>` to `/mcp` tools/call | Same body as auth off for `search_similar_issues` and `get_issue` | n/a |
| No token | `/mcp` with no header | 401 + `WWW-Authenticate` naming metadata URL | no `error=` param |
| Malformed / non-bearer | `Bearer abc`, `Basic x` | 401, `error="invalid_token"` | no exception escapes |
| Expired / wrong iss / wrong aud / unsigned / wrong key / `alg=none` / HS256 | each | 401 | logged as a reason code, not the token |
| Unknown `kid` | token signed by a key issued after the cache fill | one refetch, then accepted | refetch rate-limited; still unknown → 401 |
| Issuer unreachable | keys cannot be fetched | 503, no WWW-Authenticate | cache of earlier good keys still serves |
| Metadata | GET `/.well-known/oauth-protected-resource`, no token | 200 JSON as above | n/a |
| Other path | tokenless `/`, `/v1/search`, `/nope`, `/.well-known/other` | 401 | n/a |
| Auth off | any | today's behaviour (metadata path 404) | n/a |

</intent-contract>

## Code Map

- `src/ticketscope/mcp/server.py` -- `build_app` (line ~144) wraps `streamable_http_app(...)`; `build_server` registers `/healthz` via `custom_route`. Add the optional `auth` argument; register the metadata route there.
- `src/ticketscope/mcp/main.py` -- composition root; the only place auth settings are read and validated.
- `src/ticketscope/settings.py` -- add `mcp_auth_enabled: bool = False`, `mcp_auth_issuer: str = ""`, `mcp_auth_audience: str = ""` beside the other mcp fields.
- `src/ticketscope/mcp/auth.py` -- new: `AuthConfig`, `TokenVerifier`, `AuthMiddleware`, `metadata_url`.
- `pyproject.toml` / `uv.lock` -- add `pyjwt[crypto]~=2.15`; refresh with `uv lock`.
- `.importlinter` -- unchanged; the `mcp` contract already forbids the listed layers. `pyjwt`/`cryptography` are allowed.
- `tests/unit/test_mcp_server.py` -- `_run` pattern (fake `/v1` through `httpx2.MockTransport`, `ASGITransport`, `Host: ticketscope.test`) to reuse; `_rpc`, `_result`, `HEADERS`.
- `tests/mcp/` -- files here are `kind`-marked per module. The new stub and test module carry no `kind` marker, so they run in the default pytest.
- Do not edit `tests/mcp/captured/*` (bytes pinned).

## Tasks & Acceptance

**Execution:**
- [ ] `pyproject.toml`, `uv.lock` -- add `pyjwt[crypto]~=2.15`, run `uv lock` -- explicit dependency for what `mcp` already pulls in
- [ ] `src/ticketscope/settings.py` -- add the three `mcp_auth_*` fields -- one settings module per process
- [ ] `src/ticketscope/mcp/auth.py` -- implement config, key cache, verifier, middleware per the matrix -- the resource-server behaviour
- [ ] `src/ticketscope/mcp/server.py` -- `build_app(..., auth: AuthConfig | None = None)`: when set, serve the metadata route and wrap the app in `AuthMiddleware`; pass the key-fetch `httpx2` client in via an optional parameter so tests inject a transport -- keep auth off unchanged
- [ ] `src/ticketscope/mcp/main.py` -- build `AuthConfig` from settings, exit on empty issuer or audience when enabled -- sole reader of auth settings
- [ ] `tests/mcp/stub_issuer.py` -- RSA key generation (`cryptography`), `mint(**claim_overrides)` imitating the spike's claims (`iss`, `aud`, `exp`/`iat` 300 s, `auth_time`, `jti`, `sid`, `scope` = `email offline_access openid profile`, `client_id` = the CIMD URL; no real `sub`), metadata + JWKS served through `httpx2.MockTransport`, key rotation helper, request counter -- the epic's stub issuer
- [ ] `tests/mcp/test_auth.py` -- unit tests for every matrix row, including both tools returning identical bodies auth on vs off; the cache and refetch rules; startup validation in `main`; tag with `criterion` ids `ticketscope--e6-s2--AC-1..AC-5` for the five ACs below -- the ticket's verify
- [ ] `tests/unit/test_import_linter_enforcement.py` -- no change expected; confirm `lint-imports` passes -- R3

**Acceptance Criteria:**
- AC-1: Given auth on, when `/mcp` is called with no token, then the response is 401 with `WWW-Authenticate` naming `<origin>/.well-known/oauth-protected-resource` (R1).
- AC-2: Given a stub-signed token with the right issuer, audience and a future expiry, when `search_similar_issues` and `get_issue` are called, then each returns the same body as with auth off (R3).
- AC-3: Given auth on, when `/.well-known/oauth-protected-resource` is requested with no token, then it returns the `/mcp` URL as `resource` and the issuer in `authorization_servers`, and every other tokenless path except `/healthz` gets 401 (R2).
- AC-4: Given auth off, when the existing mcp unit tests run, then they pass unchanged (R3).
- AC-5: Given the change, when `lint-imports` and `scripts/check.sh` run, then every contract holds and the script passes (R3).

## Implementation Notes

## Plan Change Log

## Review Triage Log

## Design Notes

`/healthz` is the one exception to "only path open": the kubelet probes it with no token (`deploy/charts/ticketscope/templates/mcp.yaml:44,49`), and the Gateway routes only `/mcp` and the metadata path to `mcp`, so it is never public. The epic says the metadata is "the only path open without a token over the public hostname"; this holds. Story 4/5's integrated check should assert `/healthz` is not routed. Append this to `deferred-work.md` only if review finds the probe needs a different treatment.

Middleware sketch (pure ASGI, so streaming responses are untouched):

```python
async def __call__(self, scope, receive, send):
    if scope["type"] != "http" or scope["path"] in OPEN_PATHS: return await self.app(...)
    token = bearer(scope["headers"])
    ... verify -> 401/503 or pass through
```

`aud` may be a string or list; accept when the configured audience is the string or a member. Leeway 0.

## Verification

**Commands:**
- `uv run pytest tests/mcp/test_auth.py tests/unit/test_mcp_server.py tests/unit/test_mcp_expanded.py tests/unit/test_mcp_trace.py -q` -- expected: all pass
- `uv run lint-imports` -- expected: all contracts kept
- `uv run pyright` and `uv run ruff check . && uv run ruff format --check .` -- expected: clean
- `scripts/check.sh` -- expected: passes

## Auto Run Result

Status: ready-for-dev
Halted after planning as instructed. No code written; the plan meets the Ready for Development standard. One open call for the reviewer: `/healthz` stays open because the kubelet probes it and the Gateway never routes it (see Design Notes).
