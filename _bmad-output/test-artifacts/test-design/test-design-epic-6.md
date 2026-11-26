---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-26'
runScope: 'epic'
runKey: 'epic-6'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/epic-mcp-oauth.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
  - _bmad-output/test-artifacts/test-design/test-design-epic-5.md
  - src/ticketscope/mcp/server.py
  - src/ticketscope/mcp/main.py
  - .venv/lib/python3.14/site-packages/mcp/server/auth/ (mcp 2.3.0: middleware/bearer_auth.py, routes.py, settings.py, provider.py)
  - .venv/lib/python3.14/site-packages/mcp/server/lowlevel/server.py (streamable_http_app)
  - deploy/charts/ticketscope/templates/mcp.yaml
  - deploy/charts/ticketscope/templates/api.yaml
  - deploy/charts/platform/templates/gateway.yaml
  - deploy/charts/ticketscope/values-kind.yaml
  - .github/workflows/mcp-e2e.yml
  - .dockerignore
  - .importlinter
  - tests/mcp/
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/nfr-criteria.md
  - knowledge/playwright-cli.md
---

# Test Design: Epic 6 - Claude Desktop authenticates to the live MCP server

**Date:** 2026-11-26
**Author:** Dillon
**Status:** Draft

Epic slug: `epic-mcp-oauth`. Epic requirements R1–R5 (initiative R4). Stories 6.1 to 6.7 from `tickets/tickets.toml`. Story 6.1 is a hand-run spike, 6.2 is the tracer, 6.2 → 6.3 → 6.4 → 6.5 is one lane, 6.6 is the refactor sweep, and 6.7 is the live check that parks awaiting the operator. Criterion tags follow `ticketscope--e6-s<n>--AC-<k>`.

---

## Executive Summary

**Scope:** full test design for Epic 6, against the refined epic (`refined: true`, `risk: high`), the adopted spine (AD-5, AD-14, AD-25) and the seven entries in the epic's `tickets.toml`. Every coverage row cites the epic R ids it proves.

No epic 6 code exists. `ticketscope.mcp` has no auth, `pyproject.toml` has no JWT library, and the `mcp` HTTPRoute routes `/mcp` only. Every scenario below is planned, and none has run. The SDK statements in this plan were read from the installed `mcp` 2.3.0 source in this session. None has been exercised.

Three findings shape the plan:

- **The metadata path is not routed, and the SDK serves it somewhere else.** Story 6.4 says "The route table does not change". But `deploy/charts/ticketscope/templates/mcp.yaml` routes only `PathPrefix /mcp`, and `api.yaml` routes `/` as `Exact`, so `/.well-known/oauth-protected-resource` reaches no service today. The SDK also registers the metadata at `/.well-known/oauth-protected-resource/mcp` (RFC 9728 §3.1 path insertion, `build_resource_metadata_url`), not at the bare path in AD-14's table, and it names that URL in `WWW-Authenticate`. This is R-010, the plan's only score-9 risk. It blocks the build until stories 6.2 and 6.4 are amended (Proposed Story Updates).
- **The stub issuer is the only issuer CI ever sees.** CI never calls AuthKit (epic Constraints). So every automated check proves only that `mcp` accepts what the stub mints. The plan pins the claim shape that the spike records as a fixture. The stub signs tokens with code independent of the verifier's JWT library (Independent Oracles). Only story 6.7 tests against the real AuthKit.
- **The SDK's refusal shape differs from the epic's.** A valid token that lacks the required scope gets `403 insufficient_scope`, with a description naming the scope (`RequireAuthMiddleware`). The epic lists five refusal cases, all 401, and is silent on scope. No source says whether AuthKit's access tokens carry a scope claim at all (C-1).

**Risk Summary:**

- Total risks: 12
- High-priority risks (≥6): 7 (R-001, R-002, R-003, R-004, R-007 and R-012 at 6; R-010 at 9)
- Critical categories: SEC (fail-open configuration, token validation, leakage in telemetry and in the committed recording), TECH (metadata routing, stub fidelity)

**Coverage Summary:**

- P0 scenarios: 25 (~15–30 hours)
- P1 scenarios: 59 (~30–60 hours)
- P2/P3 scenarios: 19 (~5–11 hours)
- **Total effort**: ~50–100 hours (~1.5–3 weeks of test work, spread across the seven stories), plus two hand-run sessions (Resource Estimates)

### Spike outcome (story 6.1, 2026-11-26)

Story 6.1's plan (`tickets/spike-workos-authkit-and-claude-desktop-complete-the-oauth-flow-plan.md`, commit `5a50dfe`) landed after the risk register was scored. Scores are unchanged. Its effect on this plan:

- **R-003 is mitigated.** Claude Desktop completed the sign-in through AuthKit and called the throwaway tool. Stytch was not needed.
- **R-002's fixture source exists.** Claims `iss`, `aud`, `exp`, `iat`, `auth_time`, `jti`, `sid`, `sub`, `scope`, `client_id`; RS256 with one published key; `aud` is the resource URL exactly; access-token lifetime 300 s. The masked claim-shape fixture still has to be committed for story 6.2.
- **C-1 narrows to the spike's open "Scope name" item.** AuthKit advertises no custom scope, and tokens carry only `email offline_access openid profile`. Requiring a custom scope would refuse every real token. The spike's options (require `openid`, or check audience only) need a Decision before story 6.2.
- **C-2 is partly answered.** The throwaway server advertised the bare `/.well-known/oauth-protected-resource` in `WWW-Authenticate`, and Claude Desktop fetched it. So Claude follows the advertised URL. R-010 still stands, because the SDK advertises the path-inserted URL and neither path is routed through the Gateway.
- **C-3:** signing-key lifetime and rotation are unobserved, so story 6.3 still sets its own cache bounds.
- **New compatibility fact:** Claude Desktop sent `server/discover` and, after "method not found", fell back to `initialize`. The real server already serves `server/discover` (epic 4's captured requests), so row (E) scenario 4 covers this.

---

## Not in Scope

| Item | Reasoning | Mitigation |
| ---- | --------- | ---------- |
| **Building or running an authorisation server** | "The authorisation server is never built or run on the cluster or the public host" (Boundaries; AD-5). | R-009's row proves the test-only stub issuer never renders outside the kind release. |
| **Auth on `api`, `/v1` or the page** | "`api` stays unauthenticated and in-cluster" (Constraints; AD-5). `/` and `/v1` stay public on the Gateway (AD-14). | Row (E) checks `/v1` and `/` are unchanged. C-6 records that auth protects the tool endpoint, not the corpus. |
| **Per-tool scopes, token introspection, a client secret, opening the handshake** | Declined (epic Notes, decisions 2026-11-26). | Row (D) proves one scope reaches both tools. P0 row (B) proves there is no credential for AuthKit anywhere in the repo or the chart. |
| **Token revocation before expiry** | Local JWT verification with no introspection (decision 2026-11-26) means a token stays valid until `exp`. | Accepted by that decision. Story 6.1 records the token lifetime so the window is known. |
| **Calling the hosted AuthKit from CI** | "CI never calls the hosted authorisation server and holds no credential for it" (Constraints). | R-002's row pins the spike's claim shape. Story 6.7 is the only check against the real AuthKit. |
| **Tool-call telemetry dashboards and the README clip** | Epics 7 and 8. | R-012's row keeps the committed session recording masked, so epic 8 can reuse it. |
| **Auth latency budget** | No source states a latency target for an authenticated call. | NFR Planning marks it UNKNOWN. No scenario asserts a number. |
| **Waiver W-001 remediation** | Epic 2's open item. | Not an exit criterion of this epic. |

---

## Risk Assessment

Sources were read in this order: the epic file (Description, Requirements, Constraints, Boundaries, Notes), the epic's `tickets.toml` (stories 6.1 to 6.7), the spine's AD-5, AD-14 and AD-25, then the chart templates and the `mcp` 2.3.0 SDK auth modules. Each risk opens with the source's own words, then states the failure consequence. IDs follow the order in which each risk's gap statement first appears. Some statements describe a decided control: local JWT verification, one scope, no introspection, the stub issuer in CI, and auth on or off per environment value. Those are scope constraints. They carry coverage rows with `-` in `Risk Link`, not scored risks.

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R-001 | SEC | "`mcp` has no auth default that bypasses a check" (Constraints › Values, AD-25), while "values.yaml holds auth defaults with auth off" and "A render check refuses auth enabled with an empty issuer or audience" (story 6.4). Mechanisms: (a) `values-eks.yaml` omits or misspells the auth flag, so the EKS release inherits auth off; (b) the `Settings` field for the flag defaults to off, so a missing environment variable runs `mcp` open; (c) auth on with an empty issuer or audience starts and either admits every token or none. Consequence: the live endpoint answers tool calls with no token, while epic 8 records it as authenticated. | 2 | 3 | 6 | The process refuses to start with auth on and an empty issuer or audience, and with the flag unset (C-4). The EKS render test fails unless auth is on with a non-empty issuer and an audience equal to the live `/mcp` URL. `env-up`'s smoke check fails when a tokenless `/mcp` call is not refused. | Dillon; stories 6.2, 6.4, 6.7 | Settings refusal in 6.2; render check in 6.4; smoke check in 6.7 |
| R-002 | TECH | "the kind integrated check mints tokens from a local stub issuer. CI never calls the hosted authorisation server" (Constraints › CI). The stub imitates "the claims the spike recorded" (story 6.2). Mechanisms: the stub's `iss` spelling (trailing slash), `aud` form (string or list, resource URL or client id), `alg`, `kid`, or scope claim name differs from AuthKit's. Or the stub and the verifier share one JWT library, so a library error cancels out. Consequence: CI is green, and on the live URL every real token is refused, or the wrong one admitted, which is found only in story 6.7's live window. | 2 | 3 | 6 | Story 6.1 commits the token's claim shape as a masked fixture, with claim names, types and formats but no subject or person value. A pin test holds the stub to that fixture. The stub signs with code independent of the verifier (Independent Oracles). Story 6.7 admits a real AuthKit token. | Dillon; stories 6.1, 6.2, 6.7 | Fixture in 6.1; pin test in 6.2 |
| R-003 | BUS | "story 1 is a spike proving Claude Desktop completes the flow against it, with Stytch as the fallback" (Notes). "If the flow fails on both servers ... the epic's Notes gain a Decision to cut this epic" (story 6.1). Consequence: R5 is unmet, and the epic is cut or moves to Stytch with stories 6.2 to 6.7 replanned. | 2 | 3 | 6 | Story 6.1 reads AuthKit's `/.well-known/oauth-authorization-server` first, and runs Stytch before building the throwaway server if `client_id_metadata_document_supported` is missing. The plan records every value stories 6.2 to 6.7 use. | Dillon (hitl); story 6.1 | Before story 6.2's plan checkpoint |
| R-004 | SEC | "Hardens the verifier from story 2 so nothing invalid passes" (story 6.3), refusing a malformed token, an unpublished signing key, an expired token, a wrong issuer, a wrong audience, an unsigned or `none` algorithm and a token with no expiry. The SDK checks `exp` only when present, and checks the audience only through `AccessToken.resource` (`BearerAuthBackend`). Every other check is the verifier's. Mechanisms beyond the listed cases: an HS256 token signed with the public key as an HMAC secret (algorithm confusion), a `jku` or `x5u` header that makes the verifier fetch keys from elsewhere, a token accepted from a query string. Consequence: a forged or foreign token reaches both tools, so R1 and the epic's Outcome are false. | 2 | 3 | 6 | An explicit algorithm allow-list taken from the spike's record, `exp` required, issuer compared as an exact string, audience compared to the configured resource URL, and keys fetched only from the configured issuer's key URL, never from a token header. P0 row (R-004) covers each case. | Dillon; stories 6.2, 6.3 | Red-mode tests before story 6.3 builds |
| R-007 | SEC | "A token, an Authorization header or a signing key never appears in a log line or a span attribute" (story 6.3). Mechanisms: a debug log of request headers, an `httpx2` or OpenTelemetry instrumentation that records headers, an exception message carrying the token, the SDK's resource-mismatch warning, or the `Authorization` header forwarded on the `mcp` → `/v1` call. Consequence: tokens land in Tempo and pod logs, and the token's claims may carry a person identifier (AGENTS.md policy). | 2 | 3 | 6 | `mcp` never logs headers. The `ApiClient` builds its own headers, so nothing from the inbound request is forwarded. Row (R-007) scans captured logs and spans for the token, the header and key material, with a planted positive control. | Dillon; story 6.3 | With story 6.3 |
| R-010 | TECH | "The route table does not change" (story 6.4), while AD-14's table sends "`/mcp`, `/.well-known/oauth-protected-resource`" to `mcp`. Today `mcp.yaml` routes only `PathPrefix /mcp`, and `api.yaml` routes `/` as `Exact`. The SDK registers the metadata at `/.well-known/oauth-protected-resource/mcp` and names that URL in `WWW-Authenticate` (`build_resource_metadata_url`). On kind, the tunnel listener admits "only routes naming it ... (the /mcp route)" (`gateway.yaml`). Consequence: through the Gateway the metadata URL a client is told to fetch returns 404. Claude Desktop cannot discover AuthKit, so R2 and R5 fail on kind and live. Unit tests in process still pass. | 3 | 3 | 9 | Amend stories 6.2 and 6.4 before either is planned. `mcp` serves the metadata at both the bare and the path-inserted URL. The chart adds an HTTPRoute for `PathPrefix /.well-known/oauth-protected-resource` to `mcp` on the public listener. Every test fetches the URL from `WWW-Authenticate` instead of hard-coding a path. AD-14 gains a note that the route is a prefix (C-2). | Dillon; stories 6.2, 6.4, 6.5 | Story updates before 6.2's plan checkpoint; route in 6.4; Gateway proof in 6.5 |
| R-012 | SEC | "a screenshot or recording of the session is committed and linked from the plan, with no token or key visible" (story 6.7), under AGENTS.md: "Never write person identifiers ... keep masking of mentions, emails and secrets in every committed or published artifact". The AuthKit sign-in page, Claude Desktop's account menu and the browser's address bar (which carries `code=` and `state=`) show the person's email, name, authorisation code or WorkOS environment. Consequence: a person identifier or a credential is pushed to a public repository and stays in its history. | 2 | 3 | 6 | The person crops or masks before committing. The plan lists every frame or screenshot with what was masked. A scan of the committed image metadata finds no user name or email. The agent reviews the images before the commit, and story 6.7's done checkpoint includes that review. | Dillon (hitl); story 6.7 | Before story 6.7's commit |

Score rationale:

- **R-001:** probability 2, because story 6.4 puts the default at off, and only one key in one environment file turns it on. Impact 3, because the failure is silent: everything works, unauthenticated.
- **R-002:** probability 2, because AuthKit's token shape is unrecorded until story 6.1, and `aud` and scope conventions vary between providers. Impact 3, because the gap stays hidden until the live window.
- **R-003:** probability 2, because the Client ID Metadata Documents setting is named in AuthKit's configuration (spine open items) but has not been tried against Claude Desktop. Impact 3, because failure on both servers cuts the epic.
- **R-004:** probability 2, because the verifier is new code and several of the cases are ones the SDK does not check. Impact 3, because it is an authentication bypass.
- **R-007:** probability 2, because two instrumented HTTP clients and an SDK logger sit on the path. Impact 3, because a token in a log cannot be recalled, though it expires.
- **R-010:** probability 3, because the route is missing today and the story says the table does not change. Impact 3, because discovery fails and R2 and R5 cannot be met.
- **R-012:** probability 2, because a sign-in screen shows the account by design. Impact 3, because a pushed identifier is permanent in the history.

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-005 | OPS | "Signing keys are cached for a bounded time and refetched once when a token names an unknown key id, so a key rotation does not need a restart" (story 6.3). The bound and the refetch interval are not stated (C-3). Consequence: after an AuthKit key rotation, every valid token is refused until `mcp` restarts. Or a stream of tokens with random `kid` values makes `mcp` fetch the key set once per request, which loads AuthKit and slows every call. | 2 | 2 | 4 | A numeric cache lifetime and minimum refetch interval are set in story 6.3's plan and asserted with a fake clock. The stub counts key-set fetches. | Dillon; story 6.3 |
| R-006 | OPS | "if the keys cannot be fetched, the call is refused and never admitted, and mcp stays Ready because the probes never call the issuer" (story 6.3). Mechanisms: a fetch exception escapes the verifier and becomes a 500 (Starlette's `AuthenticationMiddleware` does not catch it), an eager fetch at startup crash-loops the pod, or a fetch with no timeout holds every request. Consequence: an AuthKit outage makes `mcp` return 500s or never become Ready, so `env-up`'s smoke check fails, and a 500 is not the 401 that R1 requires. | 2 | 2 | 4 | Keys are fetched lazily, with a bounded timeout (C-3). A fetch failure returns 401 with `WWW-Authenticate`. `/healthz` never touches the verifier. | Dillon; story 6.3 |
| R-008 | SEC | "The error body for a refused call is generic and does not say which check failed" (story 6.3). The SDK's 401 body is `{"error": "invalid_token", "error_description": "Authentication required"}` for every case. Its 403 for a missing scope says `Required scope: <name>`. Consequence: a 401 that is not generic would tell a caller which check its forged token failed. Separately, a token without the scope is refused with 403 where the epic expects 401, so the story 6.3 and 6.5 assertions disagree with the SDK. | 3 | 1 | 3 | C-1 decides the missing-scope status. Every refusal's body and `WWW-Authenticate` value is compared with one expected value per status. | Dillon; stories 6.2, 6.3 |
| R-009 | SEC | "The kind release can deploy the stub issuer from tests/mcp/ as a test-only workload ... and nothing about it renders in any other release" (story 6.4). Consequence: a token-minting service runs in the live environment. If the EKS issuer value ever pointed at it, anyone who could reach it could mint admitted tokens. | 1 | 3 | 3 | Render tests show no stub resource in the default or EKS render. The stub has no HTTPRoute in any render. The EKS issuer must be an `https` URL outside the cluster domain. `.dockerignore` already keeps `tests/` out of the app image (C-8). | Dillon; story 6.4 |
| R-011 | OPS | "it is configured in the WorkOS dashboard by a person" (story 6.7): the redirect and callback, the Client ID Metadata Documents setting, and the audience equal to the live `/mcp` URL. Consequence: a setting changed or missed in the dashboard is invisible to every repository check. The live sign-in then fails, and the cause is found only by reading the dashboard. | 2 | 2 | 4 | The runbook lists every AuthKit setting with its expected value. Before `env-up`, the person re-reads AuthKit's public metadata and records it against story 6.1's step-1 record. | Dillon (hitl); stories 6.1, 6.7 |

Score rationale:

- **R-005:** probability 2, because AuthKit's rotation cadence is unrecorded and live windows are short. Impact 2, because a restart recovers.
- **R-006:** probability 2, because a fetch error that surfaces as a 500 is the default unless it is handled. Impact 2, because the call is still refused and a retry of `env-up` recovers.
- **R-008:** probability 3, because the SDK returns 403 for a missing scope by default. Impact 1, because the scope name is public in the metadata anyway, and generic 401s are the SDK default.
- **R-009:** probability 1, because the chart already keeps environment workloads behind values and render tests exist. Impact 3, because a reachable mint would be an authentication bypass.
- **R-011:** probability 2, because the settings live only in a dashboard. Impact 2, because the failure is loud, in the live window, and the fix is a dashboard edit.

### Low-Priority Risks (Score 1-2)

No risk scored 1 or 2. Every gap statement in the sources carries a security or live-path consequence that scores at least 3.

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |

### Clarifications for the PO (not scored)

The sources are silent or unclear on these points. Each entry gives the question and a proposal. None is decided yet.

- **C-1, the scope claim and a token without it.** The epic says "one scope covers both tools" but not whether AuthKit's access tokens carry a `scope` claim, under which name, or in which format. The SDK refuses a token without the required scope with 403 `insufficient_scope`, naming the scope. If AuthKit tokens carry no scope claim, setting `required_scopes` refuses every real token. *Proposed:* story 6.1 records whether the claim is present and its format. If it is present, a missing scope gets 403 as the MCP authorization spec and the SDK do, and story 6.3's list gains that case. If it is absent, `required_scopes` stays empty, the scope appears only as `scopes_supported` in the metadata, and the epic's "one scope" decision is recorded that way.
- **C-2, which metadata URL is served and routed.** AD-14 names `/.well-known/oauth-protected-resource`. The SDK serves `/.well-known/oauth-protected-resource/mcp` and advertises that. *Proposed:* `mcp` serves both, the HTTPRoute is `PathPrefix /.well-known/oauth-protected-resource`, and AD-14 gains a one-line amendment saying so. Story 6.1 records which URL Claude Desktop fetched first, from the throwaway server's access log.
- **C-3, the reliability bounds.** "Cached for a bounded time" and "at most one refetch per interval" (story 6.3) have no values. The key-set fetch timeout and the clock-skew leeway on `exp` and `nbf` are not mentioned. *Proposed:* story 6.1 records AuthKit's token lifetime and any published rotation cadence. Story 6.3's plan sets the four values, and its tests assert them with a fake clock. Until then they are UNKNOWN.
- **C-4, what "no auth default that bypasses a check" means for `mcp`.** Story 6.4 puts the chart default at off. *Proposed:* the chart's `values.yaml` holds off for the kind and local default, but the `mcp` setting has no Python default, so the chart always sets it explicitly and a missing variable stops the process. The EKS render test fails with auth off.
- **C-5, the kind tunnel host.** Story 6.5 replays Claude Desktop's captured requests "with the tunnel host", and the tunnel listener admits only the `/mcp` route. *Proposed:* on kind the resource URL names the public-host route. The replay through the tunnel host asserts the 401 and the admitted call. The metadata is fetched on the public host only. The live check runs on EKS, so the tunnel needs no metadata route.
- **C-6, what auth protects.** `/v1` and the page stay public and unauthenticated (AD-14, AD-5), and the tools return `/v1` bodies unchanged. *Proposed:* epic 8's wording says the MCP endpoint is authenticated. It does not say the corpus or the search API is protected.
- **C-7, whether `env-up` may call AuthKit.** The "CI never calls the hosted authorisation server" rule is written for the kind check. `env-up` is a GitHub Actions run. *Proposed:* `env-up`'s smoke check reads only the live hostname: the tokenless 401 and the metadata document. It never fetches anything from AuthKit, so the rule holds for every workflow. The person's Claude Desktop session is the only check against the real AuthKit.
- **C-8, how the stub issuer runs on kind.** `.dockerignore` excludes `tests/`, so the app image cannot run code from `tests/mcp/`. *Proposed:* story 6.4's plan chooses between a test-only image built by `_kind-deploy.yml` from `tests/mcp/` and never pushed to ECR, or a stub run on the runner and reached from the cluster. Either way, nothing about it appears in the EKS render (R-009).

### Risk Category Legend

- **TECH**: Technical/Architecture (flaws, integration, scalability)
- **SEC**: Security (access controls, auth, data exposure)
- **PERF**: Performance (SLA violations, degradation, resource limits)
- **DATA**: Data Integrity (loss, corruption, inconsistency)
- **BUS**: Business Impact (UX harm, logic errors, revenue)
- **OPS**: Operations (deployment, config, monitoring)

---

## NFR Planning

**Purpose:** Capture epic-specific NFR thresholds, planned validation, and evidence expected for later `nfr-assess`. This is not a final evidence audit.

| NFR Category | Requirement / Threshold | Risk Link | Planned Validation | Evidence Needed |
| ------------ | ----------------------- | --------- | ------------------ | --------------- |
| Security | Each of R1's five cases, plus story 6.3's `none`-algorithm, unknown-key and no-expiry cases, gets 401 with `WWW-Authenticate` naming the metadata, and never reaches a tool (R1) | R-004 | API tests in process against the stub issuer; the same cases through the Gateway on kind (row (E)) | `reports/mcp.xml` from `mcp-e2e.yml`; pytest junit from `ci.yml` |
| Security | Auth is on in the EKS release, and `mcp` does not start with auth on and an empty issuer or audience (R4, AD-25) | R-001 | Settings tests, EKS render test, `env-up` smoke check | `ci.yml` charts job; `env-up` job summary |
| Security | No token, `Authorization` header or key material in any log line or span attribute (story 6.3) | R-007 | Captured-log and in-memory-span scan, with a positive control | pytest junit; scan fixture |
| Security | No person identifier, token or code in a committed recording (AGENTS.md) | R-012 | Person masks, agent reviews, image-metadata scan | Story 6.7's plan, listing each image and what was masked |
| Reliability | Key cache lifetime, minimum refetch interval, key-set fetch timeout and clock leeway: UNKNOWN (C-3) | R-005, R-006 | Fake-clock API tests once story 6.3 sets the values | pytest junit; story 6.3 plan |
| Reliability | `mcp` stays Ready while the issuer is unreachable (story 6.3) | R-006 | Readiness check with the stub stopped | pytest junit |
| Performance | Added latency of token verification on a tool call: UNKNOWN, no source states a budget | - | Not asserted. The span tree from story 6.3's tests records the verification time | Tempo trace from the kind run, for epic 7 |
| Maintainability | import-linter keeps `mcp` free of `core`, adapters, `http`, `jobs`, `psycopg` and `fastembed`; the token library is the only new dependency (story 6.2) | - | `lint-imports` and a dependency-diff check in `ci.yml` | `ci.yml` checks job |

**Unknown thresholds:** key cache lifetime, minimum refetch interval, key-set fetch timeout, clock-skew leeway (C-3), token lifetime (recorded by story 6.1), and auth verification latency (no budget). None is guessed here.

---

## Independent Oracles

Several rows compare a result with something the code under test did not produce.

| What is checked | Independent oracle | Row |
| --------------- | ------------------ | --- |
| The stub's tokens look like AuthKit's | The claim-shape fixture recorded by a person in story 6.1 from a real AuthKit token: claim names, value types, `iss` exact spelling, `aud` form, `alg`, `kid` presence and the scope claim, with no subject, email or token value. A pin test guards its bytes, as `tests/unit/test_mcp_captured_pin.py` does for the captured requests | R-002 |
| A token's signature is verified, not just parsed | The stub builds and signs each JWS with `cryptography` primitives directly (base64url header and payload, RS256 or the recorded algorithm), never with the verifier's JWT library, so a library defect cannot cancel out | R-004 |
| Admitted calls return the same bodies as before auth | A direct `POST /v1/search` and `GET /v1/issues/{number}` through the Gateway for the same request, compared as parsed JSON, as epic 4 did | Row (E) |
| The metadata URL Claude Desktop follows | The `resource_metadata` value parsed from the live `WWW-Authenticate` header, fetched as given, not a path the test hard-codes | R-010 |
| The live AuthKit configuration | AuthKit's own public `/.well-known/oauth-authorization-server`, read by a person, against story 6.1's step-1 record | R-011 |

---

## Entry Criteria

- [x] Architecture spine adopted, with AD-5's resource-server rule and AD-14's route table
- [x] Epic refined and sliced into seven entries (commits `d854c23`, `6aff82d` on branch `epic6`)
- [x] Epic 4 closed, and epic 5 closed with its integrated check (`e4aa976`)
- [ ] Branch `epic6` merged to `main`, so the epic and stories are on `main`
- [ ] C-1 to C-8 decided by the PO
- [ ] Proposed Story Updates applied, the R-010 rows on stories 6.2 and 6.4 first, before story 6.2's plan checkpoint
- [ ] Story 6.1's plan names the issuer URL, audience, signing-key URL, scope name and callback URL, and commits the masked claim-shape fixture (R-002, R-003)
- [ ] The WorkOS environment's credentials stay in the git-ignored `.env`, and `git check-ignore .env` confirms it before story 6.1 starts

## Exit Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing (or failures triaged)
- [ ] No open high-priority / high-severity bugs
- [ ] `mcp-e2e.yml` passes on a PR with auth on through values, and again with auth off (R1–R4)
- [ ] Story 6.7's live session recorded: tokenless call refused, metadata names the live `/mcp` URL and the AuthKit issuer, Claude Desktop answers from `search_similar_issues`, and `env-down`'s leftover check is clean (R1, R2, R4, R5)
- [ ] `ci.yml`, `mcp-e2e.yml` and `eval.yml` pass on the closing PR head, with `eval/baseline.json` and the captured Claude Desktop requests byte-identical to the base
- [ ] R-001, R-002, R-003, R-004, R-007, R-010 and R-012 mitigations complete

---

## Test Coverage Plan

P0, P1, P2 and P3 are priorities, not execution timing. The Execution Strategy section decides when each test runs. The Owner column names the story whose build writes the test or performs the run. The R ids column names the epic requirements each row proves.

Test Level uses the template's canonical names:

- **Unit:** functions, settings, file scans and workflow files, with no server running.
- **Integration:** one owned boundary: a chart render (`helm template` to manifests), or the telemetry pipeline into captured logs and an in-memory span exporter.
- **API:** the `mcp` ASGI app in process over HTTP (`httpx2` ASGI transport), against the stub issuer and a fake `/v1` that records its requests.
- **E2E:** kind through the Gateway (`-m kind`, `mcp-e2e.yml`), or a person's session on AuthKit and the live EKS hostname.

### P0 (Critical)

**Criteria**: Critical business, security, data-integrity, or compliance impact with no safe
workaround. Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| Configuration cannot run `mcp` open by default | R1, R4 | API | R-001 | 5 | Stories 6.2, 6.4, 6.7 | Mechanism: a missing or misspelt flag, or an empty issuer or audience, leaves the `mcp` service admitting tokenless calls. Boundary: the `mcp` HTTP contract, so API. The render scenarios are supporting checks at the chart boundary. Consequence: an authentication bypass on the live endpoint that nothing signals. No workaround, because the failure is silent. The data behind it is public (C-6), but the control is the one the epic mandates. Scenarios: (1) the app with auth on and an empty issuer, or an empty audience, refuses to build, and `main()` exits non-zero. (2) With the flag unset, the process refuses to start (C-4). (3) *Render:* `values-eks.yaml` renders auth on, a non-empty `https` issuer and an audience equal to `https://<live host>/mcp`. (4) *Render:* auth on with an empty issuer or audience fails `helm template`. (5) *Live, story 6.7:* `env-up`'s smoke check fails the job when a tokenless `POST /mcp` gets anything but 401. |
| Every invalid token is refused and never reaches a tool | R1 | API | R-004 | 12 | Stories 6.2, 6.3 | Mechanism: a verifier check missing or weaker than the SDK assumes. Boundary: the `mcp` HTTP contract, so API. Consequence: a forged token reaches both tools, an authentication bypass. No workaround. Each scenario asserts 401, a `WWW-Authenticate` naming the metadata URL, and zero requests recorded by the fake `/v1`: (1) no `Authorization` header. (2) `Bearer` with an empty or garbage value. (3) A non-`Bearer` scheme. (4) A token signed by a key the stub does not publish. (5) Expired. (6) Wrong `iss`, including the right issuer with a trailing slash changed. (7) Wrong `aud`. (8) `alg: none` with an empty signature. (9) HS256 signed with the published public key as the HMAC secret. (10) No `exp`. (11) A `jku` or `x5u` header pointing at a second stub: refused, and the second stub records no fetch. (12) A valid token sent only as an `access_token` query parameter. |
| The committed session recording shows no identifier or credential | R5 | E2E | R-012 | 4 | Story 6.7 | Mechanism: a sign-in screen or address bar captured as-is. Boundary: the person's live session, through to the committed file, so E2E. Consequence: a person identifier or code pushed to a public repository, against AGENTS.md. No workaround once pushed, short of a history rewrite. Scenarios: (1) the plan lists each committed image and what was masked: email, name, account avatar, WorkOS environment id, `code=` and `state=`. (2) The agent reviews each image before the commit and records the result in the plan. (3) A scan of the images' embedded metadata (EXIF, PNG text chunks) finds no user name, host name or email. (4) The repository's existing secret and email scan passes on the commit. |
| (B) No AuthKit credential in the repository, the chart or CI | R4 | Unit | - | 4 | Stories 6.1, 6.2, 6.4, 6.5 | Constraint: "There is no introspection and no client secret in the cluster" and "CI ... holds no credential for it" (Constraints). Story 6.1 notes: the credentials "sit in the git-ignored .env and never go in a commit or a plan". Consequence: a published WorkOS key cannot be unpublished. No workaround. Scenarios: (1) `git check-ignore .env` succeeds and `git ls-files` lists no `.env*` besides committed templates. (2) No workflow references a `WORKOS_` or AuthKit secret, and no workflow step resolves the AuthKit domain. (3) The chart renders no Secret for auth in any environment. (4) Test settings point the issuer at the stub's local URL in every `tests/mcp` and `tests/unit` module, so no test resolves the real AuthKit domain. |

**Total P0**: 25 tests, ~15–30 hours

### P1 (High)

**Criteria**: Core, frequent, or complex behavior with material user reach and a limited workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| The stub issuer matches the claim shape AuthKit issues | R3 | E2E | R-002 | 5 | Stories 6.1, 6.2, 6.7 | Mechanism: the stub and AuthKit differ in `iss`, `aud`, `alg`, `kid` or the scope claim. Boundary: the stub, `mcp` and the real AuthKit, two deployables, so E2E. Consequence: green CI and a refused live sign-in, found only in the live window. Workaround: fix the verifier or values and rerun the window, so P1. Scenarios: (1) *Story 6.1:* the masked claim-shape fixture is committed, with names, types and formats and no subject, email or token. (2) *Unit, story 6.2:* a pin test holds the fixture's bytes. (3) *Unit:* a stub-minted token decodes to exactly the fixture's claim names and types. (4) *Unit:* the stub's key-set document has the fields AuthKit's has (`kty`, `kid`, `alg`, `use`), per the fixture. (5) *Live, story 6.7:* a real AuthKit token is admitted, shown by Claude Desktop's tool answer. |
| AuthKit and Claude Desktop complete the flow against a throwaway resource server | R5 | E2E | R-003 | 5 | Story 6.1 | Mechanism: AuthKit lacks a setting Claude Desktop's remote-connector flow needs. Boundary: AuthKit, Claude Desktop and the throwaway server, so E2E. Consequence: the epic is cut or replanned to Stytch. Workaround: Stytch (epic Notes). Scenarios, by a person: (1) AuthKit's metadata shows `client_id_metadata_document_supported`, token endpoint auth method `none`, PKCE `S256`, the issuer, scopes and key URL. (2) Claude Desktop completes the sign-in against the throwaway server through the epic 4 tunnel hostname. (3) The trivial tool answers. (4) The plan names the issuer, audience, key URL, scope name, callback URL, token lifetime and which metadata URL Claude Desktop fetched (C-2). (5) If (1) or (2) fails, the same steps run against Stytch, and the result is recorded as a Decision. |
| Tokens, headers and keys never reach logs or spans | R1 | Integration | R-007 | 6 | Story 6.3 | Mechanism: header logging, HTTP client instrumentation, an exception message or a forwarded header. Boundary: the telemetry pipeline (log records and the span exporter), one owned event boundary, so Integration. Consequence: tokens in Tempo and pod logs. Workaround: tokens expire, and Tempo and Grafana are never public (AD-14). Scenarios, with every logger at DEBUG and an in-memory span exporter: (1) an admitted call leaves no token substring, no `Authorization` and no `Bearer ` in any log record, span attribute or span event. (2) Each refused call from R-004's row leaves the same. (3) The key-set fetch logs no modulus, exponent or `x5c` value. (4) The fake `/v1` records no `Authorization` header on either tool's call. (5) The SDK's resource-mismatch warning carries the resource only. (6) *Positive control:* a test that plants the token in a log record makes the scan fail. |
| The stub issuer never renders outside the kind release | R4 | Integration | R-009 | 5 | Story 6.4 | Mechanism: a template guarded by the wrong value, or a default that turns the stub on. Boundary: the chart render, so Integration. Consequence: a token mint in the live environment. Workaround: the EKS issuer points outside the cluster, so the mint is unused unless that value also breaks. Scenarios: (1) the default render has no stub resource. (2) The EKS render has none. (3) The kind render with the stub on adds only its Deployment and Service, with no HTTPRoute. (4) The EKS issuer is `https` and not a `*.svc` or `*.cluster.local` host. (5) The app image's build context has no `tests/` (`.dockerignore`), checked by the existing containers test. |
| The metadata is reachable at the URL `WWW-Authenticate` names, through the Gateway | R2, R5 | E2E | R-010 | 8 | Stories 6.2, 6.4, 6.5, 6.7 | Mechanism: no HTTPRoute for the metadata path, and the SDK's path-inserted URL. Boundary: the `platform` Gateway and the `mcp` Deployment, two deployables, so E2E. Consequence: Claude Desktop cannot find the authorisation server, and R2 and R5 fail. Workaround: none in the live window, but a chart fix and a redeploy recover it, and the failure is closed, not open, so P1. Scenarios: (1) *API, story 6.2:* the app answers both `/.well-known/oauth-protected-resource` and `/.well-known/oauth-protected-resource/mcp` with no token. (2) *Render, story 6.4:* an HTTPRoute sends `PathPrefix /.well-known/oauth-protected-resource` to `mcp` on the public hostname. (3) Through the Gateway on kind, the `resource_metadata` URL from a tokenless 401 is fetched as given and returns 200 JSON. (4) The bare path returns the same document. (5) `resource` equals the public `/mcp` URL exactly. (6) `authorization_servers` is exactly the configured issuer. (7) Both answers carry no `Set-Cookie` and need no token. (8) *Live, story 6.7:* scenarios 3 to 6 on the EKS hostname. |
| (C) The metadata document and the open-path rule, in process | R2 | API | - | 6 | Story 6.2 | Constraint: "/.well-known/oauth-protected-resource is served without a token ... and is the only path open" (story 6.2). Consequence: a wrong `resource` or issuer sends Claude Desktop to the wrong place. A second open path weakens R1. Scenarios: (1) the document is served with no token, as JSON. (2) `resource` is the configured `/mcp` URL. (3) `authorization_servers` holds the issuer only. (4) `scopes_supported` holds the one scope (or follows C-1). (5) `GET`, `POST` and `DELETE` on `/mcp` without a token are refused. (6) The app's route list holds `/mcp`, the two metadata paths and `/healthz` only, and `/healthz` is not routed by any HTTPRoute (render). |
| (D) A valid token reaches both tools with the same bodies as before auth | R3 | API | - | 5 | Story 6.2 | Constraint: "gets the same bodies as before auth, and one scope covers both" (R3). Consequence: Claude Desktop answers wrongly or not at all. Scenarios: (1) a stub-signed token calls `search_similar_issues`, and the structured content equals the auth-off result for the same fake `/v1` body. (2) The same for `get_issue`. (3) One token calls both tools. (4) `server/discover` and `tools/list` succeed with the token. (5) With auth off, every existing `tests/unit/test_mcp_*` test passes unchanged. |
| (E) The kind integrated check through the Gateway | R1, R2, R3, R4 | E2E | - | 8 | Story 6.5 | Constraint: story 6.5's `verify`. Consequence: the path that the live check depends on is unproven before the paid window. Scenarios on kind with auth on through values: (1) a tokenless `/mcp` call gets 401 and `WWW-Authenticate`. (2) R-004's cases 2 and 4 to 10 each get 401 through the Gateway. (3) A stub-signed token calls both tools, and the results equal a direct `/v1` call through the Gateway. (4) The Claude Desktop replay passes with a stub token injected at send time, the fixtures are byte-identical, and `test_mcp_captured_pin.py` is unchanged. (5) The replay through the tunnel host behaves as C-5 decides. (6) Only the metadata paths answer tokenless among `mcp`'s routed paths. (7) `/` and `/v1/search` answer as before. (8) The same suite with auth off through values passes the pre-epic checks. |
| (F) Auth is selected by values alone, per environment | R4 | Integration | - | 6 | Stories 6.4, 6.6 | Constraint: "auth on or off and the issuer are environment facts ... `values.yaml` holds the defaults" (Constraints, AD-25). Consequence: an environment that needs a manual step, against R4. Scenarios: (1) the default render has auth off. (2) The kind and EKS renders pass the flag, issuer and audience to the `mcp` container as `TICKETSCOPE_*` variables. (3) An environment file that overrides a product default is refused by the existing allowlist test, extended with the auth keys. (4) No auth key appears in `values-kind.yaml` or `values-eks.yaml` beyond the flag, issuer and audience. (5) The `api` Deployment receives no auth variable. (6) *Story 6.6:* if templates are refactored, the default, kind and EKS renders are identical before and after. |
| (G) Claude Desktop authenticates to the live server | R1, R2, R4, R5 | E2E | - | 5 | Story 6.7 | Constraint: the epic's Done when. Consequence: the epic's Outcome is unmet. Workaround: Boundaries allow epic 8 to record the unauthenticated session if the epic is cut. Scenarios, by a person in a live window: (1) `env-up` deploys with auth on from values, and its job summary shows no manual cluster step. (2) A tokenless `/mcp` call over the live hostname gets 401 and `WWW-Authenticate`. (3) Claude Desktop adds the live `/mcp` as a custom connector and completes the sign-in. (4) A triage question makes Claude call `search_similar_issues` and answer citing returned issue keys. (5) `env-down` runs and its leftover check finds nothing left. The agent only reads, through the read-only profile (AGENTS.md). |

**Total P1**: 59 tests, ~30–60 hours

### P2 (Medium)

**Criteria**: Secondary behavior with narrower user reach and an acceptable workaround. Risk score
is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| A key rotation is picked up without a restart, and refetches are bounded | R1 | API | R-005 | 4 | Story 6.3 | Mechanism: a key cache with no refetch on an unknown `kid`, or with no limit. Boundary: `mcp`'s HTTP contract and its key-set fetch, so API. Consequence: valid tokens refused until restart, or the issuer hammered. Workaround: restart the pod. Scenarios, with a fake clock and a stub that counts fetches: (1) the stub rotates, and a token with the new `kid` is admitted after one refetch. (2) 50 tokens with random unknown `kid` values inside one interval cause at most one fetch. (3) After the cache lifetime, the next call refetches. (4) A key removed from the set stops verifying after the lifetime. Values come from C-3. |
| Unreachable keys refuse the call and keep `mcp` Ready | R1 | API | R-006 | 5 | Story 6.3 | Mechanism: a fetch exception escapes as a 500, an eager fetch crashes startup, or a fetch hangs. Boundary: the `mcp` HTTP contract, so API. Consequence: 500s or an unready pod during an AuthKit outage. Workaround: retry `env-up` when AuthKit is back. Scenarios: (1) with the stub stopped before the first fetch, a tokenless call and a token call each get 401, never 500. (2) The app starts with the stub stopped. (3) `/healthz` answers 200 with the stub stopped. (4) A stub that never answers is cut off at the fetch timeout (C-3), and the call gets 401. (5) With a warm cache and the stub stopped, the behaviour matches what story 6.3's plan states for cached keys. |
| Refusals carry one generic shape per status | R1 | API | R-008 | 4 | Stories 6.2, 6.3 | Mechanism: per-check error text, or the SDK's 403. Boundary: the `mcp` HTTP contract, so API. Consequence: a refusal tells a caller which check failed. Workaround: none needed, the scope name is public. Scenarios: (1) every 401 from R-004's row has the same body and the same `error_description`. (2) Every `WWW-Authenticate` carries `resource_metadata`. (3) A token without the scope gets the status C-1 decides, with `WWW-Authenticate`. (4) No refusal body names a claim, a key id or a library error. |
| The AuthKit dashboard settings match the record | R5 | E2E | R-011 | 3 | Stories 6.1, 6.7 | Mechanism: a manual setting drifts. Boundary: AuthKit and the live session, so E2E. Consequence: the live sign-in fails. Workaround: correct the dashboard and retry in the same window. Scenarios, by a person: (1) the runbook lists each AuthKit setting with its expected value. (2) Before `env-up`, the person re-reads AuthKit's public metadata and records it against story 6.1's record. (3) The audience setting equals the live `/mcp` URL in `values-eks.yaml`. |
| (H) The refactor sweep changes no behaviour | R1, R2, R3, R4 | Unit | - | 2 | Story 6.6 | Constraint: "Behaviour, the /v1 contract, the span tree and the captured Claude Desktop requests do not change" (story 6.6). Consequence: a silent regression in cleanup. Workaround: revert the sweep. Scenarios: (1) `eval/baseline.json` and `tests/mcp/captured/*` are byte-identical to the PR base. (2) `lint-imports` keeps every contract. Render parity is row (F) scenario 6. |

**Total P2**: 18 tests, ~5–10 hours

### P3 (Low)

**Criteria**: Rare, cosmetic, or experimental behavior with minimal impact and an easy workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| (I) The metadata route answers `OPTIONS` | R2 | API | - | 1 | Story 6.2 | The SDK registers `GET` and `OPTIONS` with CORS on the metadata route. Claude Desktop does not need it. A browser-based client would. Consequence: a browser client cannot read the metadata. Workaround: none needed for this epic's client. Scenario: (1) `OPTIONS` on both metadata paths answers without a token. |

**Total P3**: 1 test, ~0.25–0.5 hours

---

## Execution Strategy

**Philosophy:** Run every functional scenario in pull requests while the suite stays under 15 minutes. Defer only work that needs a person or a paid environment. P0 through P3 are priority and are not execution timing; this section decides when tests run and the coverage plan above decides what they are.

- **Pull request, `ci.yml`:** the Unit, API and Integration rows: settings, the verifier against the in-process stub, the telemetry scan, the chart renders and `lint-imports`. They run fast and need no cluster. Within the run, the order is the existing jobs' order. A P0 failure fails the check.
- **Pull request, `mcp-e2e.yml`:** row (E) and R-010's Gateway scenarios on kind, on the existing path filter (`.github/kind-paths.yml`). The job deploys with auth on and then runs the auth-off pass. The unreachable-API case stays its own invocation, as today.
- **Hand-run, hitl:** story 6.1's spike (a person, AuthKit, Claude Desktop, the tunnel) and story 6.7's live window (a person runs `env-up` and `env-down`, and the agent only reads). Each records its findings in its plan.
- **Nightly:** none planned. Nothing here is long-running. CI never calls AuthKit, and a live environment costs money.
- **Weekly:** none planned, for the same reasons.

The coverage plan holds the individual tests. They are not repeated here.

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 25 | 0.6–1.2 | ~15–30 | Stub issuer, hand-signed tokens, refusal matrix, recording review |
| P1 | 59 | 0.5–1.0 | ~30–60 | Gateway scenarios on kind, telemetry scan, renders |
| P2 | 18 | 0.3–0.6 | ~5–10 | Fake-clock cache tests, refusal shape |
| P3 | 1 | 0.25–0.5 | ~0.25–0.5 | One `OPTIONS` check |
| **Total** | **103** | **-** | **~50–100** | **~1.5–3 weeks** |

The stub issuer and its hand-signing helper are shared setup, inside the P0 range. Story 6.2 builds them once, and stories 6.3 and 6.5 reuse them.

### Hand-run sessions

- **Story 6.1 spike:** ~3–6 person-hours, with no AWS cost (epic 4's tunnel hostname).
- **Story 6.7 live window:** one `env-up` to `env-down` window, ~1–2 environment-hours at epic 5's $0.22–$0.32 each, plus ~1–2 person-hours for the sign-in, the recording and the masking review.

### Prerequisites

**Test Data:**

- Stub issuer in `tests/mcp/`: serves a key set, mints tokens with chosen claims, rotates keys, counts fetches, and can be stopped.
- Masked claim-shape fixture from story 6.1, with a pin test.
- Captured Claude Desktop requests in `tests/mcp/captured/`, unchanged. The stub token is injected at send time.

**Tooling:**

- The token library story 6.2 adds as a direct dependency. `pyjwt` 2.15.1 is already installed through `mcp[crypto]` (`uv tree --invert --package cryptography`), so the likely choice adds no new package.
- `cryptography` 50.0.2 (installed through `pyjwt`) for the stub's independent signing. If the verifier uses `pyjwt`, the stub must not, so the two do not share a library (Independent Oracles).
- The existing `helm template` render harness, the kind deploy (`_kind-deploy.yml`) and the read-only AWS profile for story 6.7.

**Environment:**

- kind from `scripts/kind-up.sh`, with the stub issuer reachable from the cluster (C-8).
- The WorkOS environment, claimed through its dashboard link, with credentials only in the git-ignored `.env`.
- Epic 5's live environment, brought up by a person (`docs/runbooks/eks-tracer.md`).

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers. R-010 (score 9) has no waiver path: its story updates are applied before story 6.2's plan checkpoint.

### Coverage Targets

- **Critical paths**: ≥80%, measured as R1–R5 each covered by at least one passing row
- **Security scenarios**: 100% (every SEC-linked row)
- **Business logic**: ≥70% line coverage of the new `ticketscope.mcp` auth module
- **Edge cases**: ≥50% of R-004's refusal scenarios also run through the Gateway (row (E) scenario 2 runs 8 of 12)

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Security tests (SEC category) pass 100%
- [ ] Performance targets met (PERF category): N/A, no PERF risk and no stated budget
- [ ] Planned NFR evidence exists, or `nfr-assess` has documented CONCERNS or waivers

Full NFR PASS/CONCERNS/FAIL status is deferred to `nfr-assess` once evidence exists.

---

## Mitigation Plans

### R-001: Configuration runs `mcp` open by default (Score: 6)

**Mitigation Strategy:** the `mcp` auth flag has no Python default (C-4). With auth on, an empty issuer or audience stops `main()`. The EKS render test requires auth on, an `https` issuer and an audience equal to the live `/mcp` URL. `env-up`'s smoke check fails unless a tokenless `/mcp` call gets 401.
**Owner:** Dillon; stories 6.2, 6.4, 6.7
**Timeline:** settings in 6.2; render check in 6.4; smoke check in 6.7
**Status:** Planned
**Verification:** P0 row R-001, scenarios 1 to 5.

### R-002: The stub issuer drifts from AuthKit (Score: 6)

**Mitigation Strategy:** story 6.1 commits a masked claim-shape fixture from a real token. The stub is pinned to it and signs independently of the verifier's library. Story 6.7 admits a real token.
**Owner:** Dillon; stories 6.1, 6.2, 6.7
**Timeline:** fixture in 6.1; pin in 6.2
**Status:** Planned
**Verification:** P1 row R-002.

### R-003: AuthKit and Claude Desktop do not complete the flow (Score: 6)

**Mitigation Strategy:** the metadata read comes first, and Stytch runs before any build if the Client ID Metadata Documents setting is missing. The throwaway server stays outside the repo.
**Owner:** Dillon (hitl); story 6.1
**Timeline:** before story 6.2's plan checkpoint
**Status:** Planned
**Verification:** P1 row R-003; a Decision in the epic Notes either way.

### R-004: An invalid token is admitted (Score: 6)

**Mitigation Strategy:** an algorithm allow-list from the spike's record, `exp` required, exact issuer, audience against the configured resource URL, and keys only from the configured key URL. A red-mode `/bmad-tea-automate` session writes the twelve refusal tests before story 6.3 builds.
**Owner:** Dillon; stories 6.2, 6.3
**Timeline:** red tests before 6.3
**Status:** Planned
**Verification:** P0 row R-004, and row (E) scenario 2 through the Gateway.

### R-007: A token or key reaches logs or spans (Score: 6)

**Mitigation Strategy:** no header logging in `mcp`. The `ApiClient` sends only its own headers. A scan of captured logs and spans runs with a planted positive control.
**Owner:** Dillon; story 6.3
**Timeline:** with 6.3
**Status:** Planned
**Verification:** P1 row R-007.

### R-010: The metadata URL is unrouted through the Gateway (Score: 9)

**Mitigation Strategy:** amend stories 6.2 and 6.4 (Proposed Story Updates). `mcp` serves both metadata paths. The chart routes `PathPrefix /.well-known/oauth-protected-resource` to `mcp` on the public hostname. Tests follow the URL in `WWW-Authenticate`. AD-14 gains the prefix note (C-2).
**Owner:** Dillon; stories 6.2, 6.4, 6.5
**Timeline:** story updates before 6.2's plan checkpoint; route in 6.4; Gateway proof in 6.5
**Status:** Planned
**Verification:** P1 row R-010, scenarios 1 to 8.

### R-012: The committed recording leaks an identifier or code (Score: 6)

**Mitigation Strategy:** the person masks each frame. The plan lists each image and what was masked. The agent reviews the images before the commit. An image-metadata scan runs, and the review is part of story 6.7's done checkpoint.
**Owner:** Dillon (hitl); story 6.7
**Timeline:** before 6.7's commit
**Status:** Planned
**Verification:** P0 row R-012.

---

## Assumptions and Dependencies

### Assumptions

1. The SDK behaviour cited here (path-inserted metadata, 403 for a missing scope, `exp` checked only when present, the generic 401 body) is read from the installed `mcp` 2.3.0 source. It is not exercised. A `mcp` upgrade during the epic reopens R-008 and R-010.
2. Claude Desktop follows the `resource_metadata` URL from `WWW-Authenticate`. Story 6.1 records which URL it fetched (C-2).
3. AuthKit publishes its signing keys at a public URL that needs no credential, so the cluster holds no secret (story 6.4: "verification needs only public signing keys").
4. The live hostname and the Gateway behave as epic 5 recorded. This epic changes only the `mcp` routes and values.

### Dependencies

1. Story 6.1's recorded values and claim-shape fixture: required before story 6.2's plan checkpoint.
2. C-1 to C-8 decided: required before story 6.2's plan checkpoint (C-1, C-2, C-4), story 6.3's plan (C-3), story 6.4's plan (C-8) and story 6.5's plan (C-5).
3. Epic 5's `env-up` and `env-down`: required for story 6.7.

### Risks to Plan

- **Risk**: the spike moves the epic to Stytch.
  - **Impact**: the claim shape, the key URL and the dashboard settings change. R-002, R-003 and R-011 rows are rewritten.
  - **Contingency**: the rows are written against the recorded fixture, not AuthKit by name, so only the fixture and the runbook change.
- **Risk**: the epic is cut (Boundaries).
  - **Impact**: no auth code ships. Epic 8 records the unauthenticated session.
  - **Contingency**: epic 5's P0 row (C) already checks what the public hostname exposes without auth.

---

## Proposed Story Updates

These changes are for the PO to apply. This plan does not edit `tickets.toml` or the epic.

| Story | Proposed change | Why |
| ----- | --------------- | --- |
| 6.1 | Add to `verify`: "the plan records whether AuthKit's access token carries a scope claim and its format, the `aud` form, the token lifetime, the key-set document's fields, and which metadata URL Claude Desktop fetched first; a masked claim-shape fixture with no subject, email or token is committed for story 6.2 (R3, R5)." | R-002, C-1, C-2, C-3 |
| 6.2 | Replace "/.well-known/oauth-protected-resource is served without a token" with "the protected-resource metadata is served without a token at `/.well-known/oauth-protected-resource` and at the path the SDK advertises in `WWW-Authenticate`". Add to `verify`: "with auth on and an empty issuer or audience, or with the flag unset, `mcp` does not start (R4); the fake `/v1` records no `Authorization` header (R3); the stub signs independently of the verifier's JWT library and is pinned to story 6.1's fixture (R3)." | R-010, R-001, R-007, R-002 |
| 6.3 | Add to the refusal list: "an HS256 token signed with the public key, a token whose `jku` or `x5u` names another host, and a token sent only as a query parameter". Add to `verify`: "a key-set fetch failure returns 401, never 500; the cache lifetime, refetch interval, fetch timeout and clock leeway are named in the plan and asserted with a fake clock (R1)". Add the missing-scope case as C-1 decides. | R-004, R-006, R-005, R-008 |
| 6.4 | Replace "The route table does not change" with "An HTTPRoute sends `PathPrefix /.well-known/oauth-protected-resource` to `mcp` on the public hostname, completing AD-14's table; the rest of the table does not change". Add to `verify`: "the EKS render has auth on, an `https` issuer outside the cluster and an audience equal to the live `/mcp` URL (R4); the plan states how the stub issuer runs on kind without code from `tests/` in the app image (R4)". | R-010, R-001, R-009, C-8 |
| 6.5 | Add to `verify`: "the metadata is fetched at the URL a tokenless 401's `WWW-Authenticate` names, through the Gateway (R2); the replay through the tunnel host follows C-5 (R3)". | R-010, C-5 |
| 6.7 | Replace "with no token or key visible" with "with no token, code, key, email, name or WorkOS environment id visible, each masked frame listed in the plan and reviewed by the agent before the commit". Add to `verify`: "before `env-up`, the person records AuthKit's public metadata against story 6.1's record (R5); `env-up`'s smoke check fails if a tokenless `/mcp` call is not refused (R1, R4)". | R-012, R-011, R-001 |

---

## Follow-on Workflows (Manual)

- Run `/bmad-tea-automate` in red mode to generate failing P0 tests (separate workflow; not auto-run). Start with R-004's refusal matrix and R-001's settings refusals, before story 6.3 builds.
- Run `/bmad-tea-automate` for broader coverage once implementation exists.
- Run `/bmad-tea-trace` at the end of the epic to map the criterion tags to R1–R5.

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: Dillon Date:
- [ ] Tech Lead: Dillon Date:
- [ ] QA Lead: Dillon Date:

**Comments:**

---

## Interworking & Regression

| Service/Component | Impact | Regression Scope |
| ----------------- | ------ | ---------------- |
| **`mcp` Deployment** | Gains the verifier, the metadata routes and the auth settings | All `tests/unit/test_mcp_*.py` with auth off; `tests/mcp/*` under `-m kind` |
| **Captured Claude Desktop requests** | Replayed with a stub token injected at send time | `tests/unit/test_mcp_captured_pin.py` unchanged; `tests/mcp/test_claude_desktop_replay.py` |
| **`api` and `/v1`** | None; stays unauthenticated (AD-5) | Row (E) scenario 7; `ci.yml` API tests |
| **Gateway route table** | Gains the metadata route to `mcp` | `tests/unit/test_chart_mcp.py`; row (E) scenario 6 |
| **Chart values** | Gains the auth flag, issuer and audience | `tests/unit/test_chart_defaults*.py`, `test_chart_eks.py` and the allowlist test |
| **Eval gate** | None | `eval/baseline.json` byte-identical (row (H)) |
| **`env-up` and `env-down`** | Deploy with auth on; smoke check gains the tokenless refusal | Epic 5's workflow tests in `tests/unit/test_env_*_workflow.py` |

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization
- `nfr-criteria.md` - NFR planning categories

### Related Documents

- PRD: N/A (initiative: `_bmad-output/initiative-ticketscope/initiative-ticketscope.md`, R4)
- Epic: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/epic-mcp-oauth.md`
- Stories: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-oauth/tickets/tickets.toml`
- Architecture: `_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md` (AD-5, AD-14, AD-25)
- Prior epic plan: `_bmad-output/test-artifacts/test-design/test-design-epic-5.md`

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `bmad-tea-test-design`
**Version**: 4.0 (BMad v6)
