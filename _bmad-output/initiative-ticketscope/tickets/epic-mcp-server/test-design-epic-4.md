---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-11-10'
runScope: 'epic'
runKey: 'epic-4'
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/tickets/epic-mcp-server/.memlog.md
  - _bmad-output/initiative-ticketscope/tickets/tickets.toml
  - _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md
  - _bmad-output/test-artifacts/test-design/test-design-epic-3.md
  - _bmad-output/test-artifacts/gate-waivers.md
  - src/ticketscope/contract/search.py
  - src/ticketscope/http/app.py
  - src/ticketscope/telemetry.py
  - src/ticketscope/settings.py
  - src/ticketscope/core/ports.py
  - src/ticketscope/core/fakes.py
  - src/ticketscope/core/derive.py
  - src/ticketscope/adapters/postgres.py
  - .importlinter
  - pyproject.toml
  - uv.lock
  - deploy/charts/ticketscope/values.yaml
  - deploy/charts/ticketscope/values-kind.yaml
  - deploy/charts/ticketscope/templates/api.yaml
  - deploy/charts/platform/values-kind.yaml
  - deploy/charts/platform/templates/gateway.yaml
  - .github/workflows/ci.yml
  - .github/workflows/eval.yml
  - .github/workflows/_kind-deploy.yml
  - .github/kind-paths.yml
  - scripts/kind-up.sh
  - scripts/v1_parity.py
  - scripts/fault-inject.sh
  - tests/conftest.py
  - tests/target.py
  - tests/waiting.py
  - tests/smoke/test_gateway.py
  - knowledge/risk-governance.md
  - knowledge/probability-impact.md
  - knowledge/test-levels-framework.md
  - knowledge/test-priorities-matrix.md
  - knowledge/nfr-criteria.md
---

# Test Design: Epic 4 - Claude Desktop calls search_similar_issues on a remote MCP server

**Date:** 2026-11-10
**Author:** Dillon
**Status:** Draft

Epic slug: `epic-mcp-server`. Epic requirements R1–R5 (initiative R4, R8). Stories 4.1 to 4.7 from `tickets/tickets.toml`. Story 4.1 is the tracer. Stories 4.1 to 4.5 form one lane, because each one edits `ticketscope.mcp`. Story 4.2 is the one human-in-the-loop story.

---

## Executive Summary

**Scope:** full test design for Epic 4, against the refined epic (`refined: true`), the adopted architecture spine (AD-1 to AD-5, AD-10, AD-11, AD-13, AD-14, AD-17, AD-20, AD-21, AD-25, and the open question on the `get_issue` argument) and the seven entries in `tickets/tickets.toml`. Every coverage row cites the epic R ids it proves, so the end-of-epic trace can link criteria to requirements.

The epic file and its seven entries exist on branch `epic-4-plan-mcp-server` (commit 3cb8a82), not yet on `main`. No epic 4 code exists: there is no `ticketscope.mcp` or `ticketscope.apiclient`, and `uv.lock` holds neither the `mcp` SDK nor an httpx OpenTelemetry instrumentor. Every scenario below is planned, and none has run.

This epic adds the first process that reaches retrieval only over HTTP, and its one human-run check: Claude Desktop through a public tunnel. The plan puts the most weight on three things the CI client test alone would not catch:

- a key that silently resolves to a different issue;
- a tunnel host that the kind Gateway's listener never admits;
- Claude Desktop compatibility, which is checked once by hand and never again.

**Risk Summary:**

- Total risks: 11
- High-priority risks (≥6): 3 (R-003 at 6, R-006 at 6, R-007 at 6)
- Critical categories: DATA (`get_issue` returns a different issue than the key names), TECH and OPS (Claude Desktop and the tunnel, which no CI run exercises)

**Coverage Summary:**

- P0 scenarios: 23 (~14–28 hours)
- P1 scenarios: 82 (~33–66 hours)
- P2/P3 scenarios: 17 (~6–12 hours)
- **Total effort**: ~53–106 hours (~1.5–3 weeks)

---

## Not in Scope

| Item | Reasoning | Mitigation |
| ---- | --------- | ---------- |
| **OAuth and `/.well-known/oauth-protected-resource`** | "OAuth belongs to epic-mcp-oauth" (epic Boundaries). "There is no auth yet; epic 6 adds it" (Description). | R-001 limits what the unauthenticated tunnel exposes. No auth scenario is planned here. |
| **The live URL on EKS** | "the live URL [belongs] to epic-eks-environment" (Boundaries). | The chart rows check that hostnames and allowed hosts come from environment values, so epic 5 sets them without a template change. |
| **Tool-call metrics and the dashboard** | Out per the epic Boundaries (epic-grafana-dashboard). | The span rows pin the attribute names epic 7's `spanmetrics` dimensions read (R-010). |
| **An eval of tool-call behaviour; server-side LLM answers** | Out per the epic and initiative Boundaries. "The client writes the answer." | None needed. Claude's answer is checked only for citing returned issues (R4). |
| **Retrieval quality, default mode and `api` resources** | "Retrieval defaults and `api` resources are epic-hybrid-retrieval's" (Boundaries). | Tests read `retrieval.defaultMode` from `values.yaml` and never hard-code it, because story 3.6 may change it while this epic runs. |
| **Load or latency targets for `/mcp`** | No source states a throughput or latency budget for `/mcp`. | NFR Planning lists the missing thresholds as UNKNOWN. No scenario asserts a number. |
| **Claude Desktop in CI** | "Claude Desktop through the tunnel (R4) is evidenced by story 2's recorded session, not re-run in CI" (story 4.7). The tunnel "runs on a person's machine, never in CI" (Constraints). | R-003's row replays Claude Desktop's captured requests against `/mcp` in CI. |
| **Waiver W-001 remediation** | An open item from epic 2, owned by Dillon. | Not an exit criterion of this epic. |

---

## Risk Assessment

Sources were read in this order: the epic file, `tickets.toml`, the memlog, the initiative `tickets.toml`, the spine, epic 3's test design and the waivers, then the code named in the inputs. Each risk opens with the source's own words, then states the failure consequence. IDs follow the order in which each risk's statement first appears in those sources.

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- | -------- |
| R-003 | TECH | Claude Desktop compatibility is "the least certain part" (epic Notes). Story 4.2 says "Any server change Claude Desktop turns out to need (protocol version, response format) is made here". Story 4.7 says R4 "is evidenced by story 2's recorded session, not re-run in CI". After story 4.2, stories 4.3 to 4.5 change the error results, add `get_issue` and add `_meta` trace handling. No automated check sends Claude Desktop's request shapes. Mechanisms: a protocol version the client sends is no longer served; a tool result has `structuredContent` but no text content block; an output schema the client rejects; a JSON-RPC error where the client expects `isError`. Consequence: the epic Outcome (R4, brief Success Criteria 2) is false at close while CI is green, and epics 6 and 8 build on it. | 2 | 3 | 6 | Story 4.2 captures Claude Desktop's handshake and tool-call requests and commits them with credentials stripped. `mcp-e2e.yml` replays them against `/mcp` on every later PR. A person repeats the Claude Desktop session once at epic close (Proposed Story Updates). | Dillon; stories 4.2, 4.7 | Capture in story 4.2; replay from story 4.3 onward |
| R-006 | OPS | "Envoy otherwise 404s the tunnel's Host header before the server sees it" (story 4.2). The story and the epic Decision add the tunnel's hostname to "the `/mcp` route's hostnames and to the allowed-hosts value" only. The kind Gateway's listener sets `hostname: ticketscope.kind.internal` (`deploy/charts/platform/values-kind.yaml`, `templates/gateway.yaml`). Under the Gateway API, a route hostname that does not match its listener's hostname is ignored. Consequence: with both of the story's changes in place, Envoy still 404s the tunnel's requests. Story 4.2 is blocked at its human step, after the person has already reserved the tunnel and started the session. | 3 | 2 | 6 | Add the tunnel hostname to the platform Gateway as well, either as a second listener or by dropping the listener hostname on kind, from the same environment value. CI rehearses this with a stand-in host set in kind values, so the check runs before any tunnel exists. | Dillon; stories 4.1, 4.2 | Before story 4.2's human step |
| R-007 | DATA | Story 4.4: the key is "read from the issue's url by one function ... and gives null when the url is not a browse URL", and the lookup is on "the Postgres adapter (by url)". The spine's open question names the hazard: an agent "may call `get_issue(6629)`, silently getting a different issue". Mechanisms: (a) `apiclient` builds `/v1/issues/by-key/{key}` from an unescaped key, so `../6629` resolves to `GET /v1/issues/6629`. A local check on 2026-11-10 confirmed that `httpx2` 2.16 does this (C-4). (b) The lookup url built from the key differs from the stored url (case, trailing slash, scheme), so a real issue is not found. (c) The parser accepts a url with a suffix and returns a wrong key. (d) An issue with a null key cannot be fetched. (e) The tool returns the body without checking that its key equals the requested key. Consequence: Claude answers about a different issue than the one it named, and cites that issue's outcome, with no error anywhere. | 2 | 3 | 6 | Commit an independent key oracle (snapshot `key` against url-derived key) before story 4.4's build. `apiclient` percent-encodes the key as one path segment. `api` accepts only the key pattern (C-4). The tool checks that the returned key equals the requested key. The P0 API row runs every hostile key. | Dillon; story 4.4 | Oracle before 4.4's build; row (A) before 4.4 merges |

Score rationale:

- **R-003:** probability 2, because the SDK supports handshake-era versions and the spec has a single structured-output shape, but three later stories change exactly the surfaces a client depends on. Impact 3, because R4 is the epic's Outcome and later epics consume it.
- **R-006:** probability 3, because the listener hostname is set today and the story text omits it. Impact 2, because the fix is a values change once found, but it is found only at the human step.
- **R-007:** probability 2, because the hazard is named, the story chose a key, and C-4 now specifies the pattern and the encoding. The dot-segment path is confirmed in `httpx2`, and the code that would guard against it is unbuilt. Impact 3, because the failure is silent and changes the facts an assistant reports.

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ----- |
| R-001 | SEC | "There is none yet; epic 6 adds it" (epic Description, Auth), while "Claude Desktop answers from the server through a tunnel with a fixed hostname". While the tunnel runs, the kind cluster's `/mcp` is reachable from the internet with no authentication. Anything else the tunnel host can reach on the Gateway (`/v1`, the page, a future route) is exposed too, along with the person's bandwidth and machine. The data served is the public CC BY corpus and both tools are read-only, which bounds the harm. Consequence: unauthenticated public use of the person's cluster, beyond `/mcp` if a route admits the tunnel host. | 2 | 2 | 4 | The tunnel host reaches only `/mcp`. Grafana, Tempo and SeaweedFS have no route (AD-14). `allowed_hosts` is never a wildcard. The tunnel runs only while the script runs. | Dillon; stories 4.1, 4.2 |
| R-002 | TECH | "Tailscale Funnel as the fallback if ngrok's free plan fails a check" (epic Constraints, Tunnel). Story 4.2 first checks for "no interstitial page, no buffering of streamed responses" and that the "bandwidth limit covers a demo". The spine's Deferred list says "Cloudflare quick tunnels lack SSE". Consequence: Claude Desktop's connector fails or hangs on streamed responses, and R4 slips while the fallback is set up. | 2 | 2 | 4 | Story 4.2 runs the non-browser `curl` check through the tunnel before connecting Claude Desktop and records the result and the choice in its plan. Tailscale Funnel is the documented fallback. | Dillon; story 4.2 |
| R-004 | TECH | "Likely more than 800 added lines (two packages, entrypoint, chart templates, workflow, tests): run the independent review on it" (story 4.1 notes). Story 4.1 "owns the shared setup (mcp and apiclient packages, entrypoint, chart keys, route, mcp-e2e.yml)" (`tickets.toml` header). Epic 3's oversized tracer (3.1) shows `review: thorough` with two follow-up passes in its plan, so the control has now run once. Consequence: a defect in the shared setup reaches stories 4.2 to 4.7. | 2 | 2 | 4 | Story 4.1 keeps `plan_checkpoint = true`, names the independent review in its plan, or splits at the checkpoint (packages and unit tests first, then chart, route and workflow). | Dillon; story 4.1 |
| R-005 | BUS | "The tool's mode input is a plain string, not the contract's Literal, so an invalid mode reaches the API" (story 4.1). The same story builds `apiclient` "on ticketscope.contract", whose `SearchRequest.mode` is the Literal `ModeName` (`contract/search.py`). If `apiclient` serialises through `SearchRequest`, an unknown mode raises a pydantic `ValidationError` inside `mcp`. The tool error then carries pydantic's text, not the API's detail, and story 4.3's "rather than by a separate list in mcp" is broken by the contract itself. Consequence: R3's unknown-mode case returns the wrong detail, or a protocol error. | 2 | 2 | 4 | `apiclient` sends `mode` exactly as given and builds no `SearchRequest` for the request body. An API row compares the tool's error detail with the detail the real app factory returns. | Dillon; stories 4.1, 4.3 |
| R-009 | OPS | "an unreachable API (made by scaling api to zero as the suite's last step)" (story 4.7). Mechanisms: the step runs before other tests (test order, a rerun, a `-k` selection) and they fail against no `api`. If `mcp`'s readiness probe calls `api`, the `mcp` pods leave the Service when `api` is at zero, and Envoy answers 503 instead of a tool error. Without a restore, a local rerun on the same cluster fails. Consequence: R3's unreachable case is unproved or flaky. In a real `api` outage, clients would get a Gateway 503 rather than a tool error. | 2 | 2 | 4 | `mcp` readiness checks only its own process. The scale-down runs as its own pytest invocation after the main suite, and a finalizer scales `api` back. | Dillon; stories 4.1, 4.7 |
| R-011 | OPS | `scripts/kind-up.sh` "waits for api to be Ready" and, on "app image rebuilt under the deployed tag", restarts only `api`. Story 4.1 adds an `mcp` Deployment from the same image and names no change to `kind-up.sh`. Consequence: `mcp-e2e.yml` can start before the `mcp` pods are Ready, so it fails intermittently. A local same-tag rebuild leaves `mcp` on old code, so local runs test stale code. | 2 | 2 | 4 | `kind-up.sh` waits for, and on a same-tag rebuild restarts, `ticketscope-mcp` as well. | Dillon; story 4.1 |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------ |
| R-008 | TECH | "The Tempo lookup the check needs lives in tests/mcp/ and does not touch tests/smoke/ ... unifying it with tests/smoke's private helpers is left for a later sweep" (story 4.5). Two copies of the Tempo parsing (base64 or hex span ids, `intValue` as a string). Consequence: a fix in one copy is missed in the other, and trace checks fail intermittently. | 2 | 1 | 2 | Unit tests for the `tests/mcp` helper on recorded Tempo bodies. Story 4.6 records whether it unified the helpers or deferred them. |
| R-010 | TECH | "GenAI semconv drift ... Revisit at the next telemetry change (epic 7 at the latest)" (spine, Open questions). Story 4.5 is a telemetry change that adds `mcp.method.name`, `gen_ai.operation.name=execute_tool` and `gen_ai.tool.name` from the same experimental conventions. Consequence: epic 7's `spanmetrics` dimension `gen_ai.tool.name` or the span names drift from the conventions in use. | 2 | 1 | 2 | Keep the tool-span attribute names in one constants list that cites the semconv version. Story 4.5's plan records whether the open question was revisited. |

### Clarifications for the PO (not scored)

The sources were silent or disagreed on these points. Dillon decided all nine on 2026-11-10. Each entry gives the question, then the decision this plan tests. "Proposed Story Updates" carries the wording into the stories.

- **C-1, httpx2 instrumentation.** AD-10: "`apiclient` uses `httpx2`, the `mcp` SDK's client, with OTel httpx instrumentation." `uv.lock` has no `opentelemetry-instrumentation-httpx`, and that package instruments the `httpx` module. *Decision:* story 4.5 first tries `opentelemetry-instrumentation-httpx` on an `httpx2` client. If no CLIENT span or `traceparent` header appears, `apiclient` opens the CLIENT span itself, with the HTTP semconv attributes, and injects `traceparent` in an `httpx2` event hook. Either way, a unit test captures the outgoing header.
- **C-2, finding a trace that has no caller context.** R5 requires a `ticketscope-mcp` root span, so the check cannot inject a trace id it knows in advance. *Decision:* the check searches Tempo with TraceQL, `{resource.service.name="ticketscope-mcp" && name="tools/call search_similar_issues"}`, within the call's start and end time. The check makes its calls one at a time, so exactly one match falls in that window. The server does not return its trace id in `_meta`.
- **C-3, HTTP header against `_meta`.** A Streamable HTTP POST can carry a W3C `traceparent` header as well as `_meta.traceparent`. AD-10 names only `_meta`. *Decision:* `mcp` continues `_meta.traceparent` only and ignores an HTTP `traceparent` header (no ASGI server instrumentation on `mcp`). A test sends both with different trace ids and checks that `_meta` wins.
- **C-4, key format and normalisation.** The sources did not say whether `mcl-6629`, ` MCL-6629 ` or a key containing path characters is accepted, or which status a malformed key gets. A local check on 2026-11-10 showed that `httpx2` 2.16 turns `/v1/issues/by-key/../6629` into `GET /v1/issues/6629`, and `MCL-6629?x=1` into a query string, unless the key is percent-encoded. *Decision:* a key matches `^[A-Z][A-Z0-9]*-[1-9][0-9]*$` exactly, with no case or whitespace normalisation. `apiclient` percent-encodes the key as one path segment. `api` returns a 404 problem+json for any key that does not match, or matches no issue, and the tool returns that as a tool error. The tool also returns a tool error when the returned `issue.key` differs from the requested key.
- **C-5, the unreachable-API detail and the timeout.** R3 says each failure carries "the API's problem detail", but an unreachable API returns no body, and no timeout value was given. *Decision:* the detail is `ticketscope API unreachable: connection refused` or `ticketscope API unreachable: timed out after 10s`, with no stack trace. The timeout is `TICKETSCOPE_API_TIMEOUT_SECONDS`, with a chart default of 10.
- **C-6, error responses that are not problem+json.** For example an HTML 502, a truncated body, or a 200 that fails contract validation. *Decision:* the tool returns `isError` with text that names the HTTP status and a generic reason, for example `ticketscope API returned 502 without a problem body`. It never includes the response body, never raises a protocol error and never returns an empty result.
- **C-7, the evidence pipeline.** `ci.yml`'s `evidence` job builds `live-verification-results.json` from its own run's `reports-*` only. `mcp-e2e.yml` is a separate workflow, so its `criterion` markers never reach that file. *Decision:* the closing trace cites `mcp-e2e.yml` run URLs. No workflow change.
- **C-8, `key` optionality.** `contract.Issue` gains `key`, and v1-shaped fixtures give null. *Decision:* `key: str | None = None`, optional and nullable. `apiclient` then still validates a body from an `api` that predates the field, and the output schema does not require it.
- **C-9, the protocol version Claude Desktop sends.** "Serving protocol 2026-07-28 plus the SDK's handshake-era versions" (Constraints). The version Claude Desktop sends is unknown until story 4.2. *Decision:* story 4.2 commits the captured `initialize`, `tools/list` and `tools/call` requests, with the protocol version and headers and no credentials, and `mcp-e2e.yml` replays them from story 4.3 on (R-003).

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
| Security | No auth until epic 6. `allowed_hosts` from values refuses any other host (DNS-rebinding protection). No tunnel credential is committed. `mcp` holds no database credential (AD-3). Query text is on spans only when a value opts in (AD-10). | R-001, R-006 | E2E: the tunnel host reaches only `/mcp`, and a host outside `allowed_hosts` is refused. Unit: chart render (no DB Secret in `mcp`, no wildcard host) and a credential scan of the tunnel script. API: no query text on spans by default. | `mcp-e2e.yml` report; chart test report; story 4.2's plan |
| Performance | No `/mcp` latency or throughput target. The `apiclient` timeout is 10 s by default (`TICKETSCOPE_API_TIMEOUT_SECONDS`, C-5). `mcp` CPU and memory and the tunnel's bandwidth limit are UNKNOWN. | R-002 | Recorded only: the runner-fit summary with two `mcp` replicas, and the tunnel's bandwidth limit in story 4.2's plan. | Job summary (`runner-fit.json`); story 4.2's plan |
| Reliability | `mcp` is "safe at any replica count; kind runs two replicas". Every failed call is a tool error, "never ... a protocol failure or an empty result" (R3). `mcp` readiness does not depend on `api` (assumption, R-009). | R-005, R-009 | API: each failure class against a fake `/v1`. E2E: 20 calls spread over both replicas, and the scale-to-zero case. | `mcp-e2e.yml` report; pod logs |
| Maintainability | import-linter keeps `mcp` and `apiclient` to `contract`, `apiclient`, `settings` and `telemetry`, and nothing imports `mcp`. One wire contract module (AD-20). No `time.sleep` in `tests/`. | R-004, R-008 | Unit: import-linter contracts with an enforcement test; the existing no-sleep test; Tempo helper unit tests. | `ci.yml` report |
| Observability (project) | One trace from the tool call to the database under a `ticketscope-mcp` root, continuing `_meta` context (R5, AD-10). | R-010 | API: spans from an in-memory exporter. E2E: the trace in Tempo on kind. | `mcp-e2e.yml` report; the Tempo trace id in the report |

**Unknown thresholds:**

- `mcp` CPU and memory requests and limits (no source sets them);
- the tunnel's bandwidth limit, and the traffic one demo session needs (story 4.2);
- the time Tempo takes to ingest an `mcp` trace on kind (the smoke check's `TRACE_TIMEOUT_SECONDS` is the starting value);
- the added wall-clock time of a third kind deployment per PR.

Story 4.1 records the first values for the last two. Story 4.2 records the tunnel figures.

---

## Independent Oracles

Several rows compare the server's output with something the server under test did not produce. Each oracle below comes from a different code path or source.

**Protocol:**

1. Before story 4.4's build, a `/bmad-tea-automate` red-mode session commits the key oracle table below and the hostile-key cases. The build session does not author them.
2. Story 4.2 commits Claude Desktop's captured requests. Later stories do not edit that file. A change to it is a review finding.
3. Pin tests guard both fixtures' bytes, as `tests/unit/test_eval_oracle_pinned.py` does for epic 2.

**Key oracle** (the snapshot v2 `key` field is independent of the url parser):

| `url` | Snapshot `key` | Expected `issue.key` |
| ----- | -------------- | -------------------- |
| `https://bugs.mojang.com/browse/MCL-6629` | `MCL-6629` | `MCL-6629` |
| `https://bugs.mojang.com/browse/REALMS-12` | `REALMS-12` | `REALMS-12` |
| `https://bugs.mojang.com/browse/MCD-1` | `MCD-1` | `MCD-1` |
| `https://github.com/o/r/issues/7` (v1-shaped fixture) | - | `null` |
| `https://bugs.mojang.com/browse/MCL-6629/extra` | - | `null` |
| `http://bugs.mojang.com/browse/MCL-6629` | - | `null` (not `MOJANG_BROWSE_URL`) |

For every issue in `snapshot/fixture.jsonl` that carries a `key`, the url-derived key equals the snapshot's `key`.

**Hostile keys** (each must return no issue, or only the issue whose key equals the input):

| Input to `get_issue` | Expected |
| -------------------- | -------- |
| `6629` | Tool error; never issue number 6629 |
| `../6629`, `..%2F6629`, `MCL-6629/..` | Tool error; never `GET /v1/issues/6629` |
| `mcl-6629`, ` MCL-6629 ` | Tool error, per C-4 |
| `MCL-6629?x=1`, `MCL-6629#a`, empty string | Tool error |
| `MCL-1' OR '1'='1` | Tool error; the SQL takes the key as a parameter |

**Other oracles:**

| What is checked | Independent oracle | Row |
| --------------- | ------------------ | --- |
| The tool returns the `/v1` body unchanged | A direct `POST /v1/search` through the Gateway with the same body, compared as parsed JSON | P0 E2E (C) |
| Structured output matches its schema | `jsonschema` (Draft 2020-12) validating against the tool's advertised `outputSchema`, not pydantic | P0 E2E (C) |
| An omitted mode gets the server default | `retrieval.defaultMode` read from `values.yaml` by the test | P0 E2E (C) |
| A tool error carries the API's detail | Problem bodies recorded from the real `create_app` with the in-memory store, not hand-written in the `mcp` test | P1 API (tool errors; R-005) |
| One trace spans both services | Tempo's stored parent ids for each span | P1 E2E (span tree) |
| Claude Desktop compatibility | The handshake and calls captured from Claude Desktop in story 4.2 | P0 E2E (B) |

---

## Entry Criteria

- [x] Architecture spine adopted (AD-1 to AD-26)
- [x] Epic refined, with seven entries planned in `tickets.toml`
- [x] Epic 1's `/v1` contract, Helm releases, CI layout, OTel Collector and Tempo exist on `main`
- [ ] Branch `epic-4-plan-mcp-server` merged to `main`, so the epic file and entries are on `main`
- [x] C-1 to C-9 decided (Dillon, 2026-11-10)
- [ ] The C-1 to C-9 decisions written into stories 4.1 to 4.7 (Proposed Story Updates)
- [ ] Story 4.2's description names the Gateway listener as well as the route and `allowed_hosts` (R-006)
- [ ] The key oracle and hostile-key fixtures committed by a red-mode session before story 4.4's build (R-007)
- [ ] The independent review for story 4.1 named in its plan (R-004)

## Exit Criteria

- [ ] All P0 tests passing
- [ ] All P1 tests passing (or failures triaged)
- [ ] No open high-priority / high-severity bugs
- [ ] `mcp-e2e.yml`'s integrated suite passes on a fresh kind cluster, and `ci.yml` and `eval.yml` pass on the same PR head with `eval/baseline.json` unchanged
- [ ] Story 4.2's recorded session and the captured Claude Desktop requests are committed and linked from the epic Notes, and the replay passes on story 4.7's PR
- [ ] R-003, R-006 and R-007 mitigations complete

---

## Test Coverage Plan

P0, P1, P2 and P3 are priorities, not execution timing. The Execution Strategy section decides when each test runs. The Owner column names the story whose build writes the test. The R ids column names the epic requirements each row proves.

Test Level uses the template's canonical names:

- **Unit:** functions, scripts and chart renders with no service.
- **Integration:** one owned store (a Postgres container from the in-repo image).
- **API:** one service's protocol boundary in process. That is the MCP server over Streamable HTTP against a fake `/v1`, or `/v1` through the app factory with the in-memory store.
- **E2E:** a run on kind through `_kind-deploy.yml`, or a person's run through the tunnel.

### P0 (Critical)

**Criteria**: Critical business, security, data-integrity, or compliance impact with no safe
workaround. Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| (A) `get_issue` returns exactly the issue its key names, or a tool error | R2, R3 | API | R-007 | 10 | Story 4.4 | Mechanism: the key reaches the wrong route or matches the wrong row. Boundary: the `/v1` by-key contract of `api`, with `apiclient`'s path building in front of it, run in process: the MCP server and `apiclient` call `create_app` with the in-memory store over an ASGI transport. Level: API. Scenarios, on the fixtures in "Independent Oracles": (1) the url-to-key table, including `null` for v1-shaped and suffixed urls. (2) For every v2 fixture issue, the derived key equals the snapshot `key`. (3) Every `/v1/search` and `GET /v1/issues/{number}` result carries `issue.key` equal to the oracle. (4) `GET /v1/issues/by-key/MCL-6629` returns the same body as `GET /v1/issues/{number}` for that issue. (5) An unknown well-formed key returns a 404 problem+json, and the tool returns `isError` with its detail. (6) `6629` never returns issue number 6629. (7) Each dot-segment key never reaches `/v1/issues/{number}`; a spy transport records the request path `apiclient` sent. (8) Each case-, space-, query- or fragment-variant returns a tool error (C-4). (9) The tool returns `isError` when the body's `issue.key` differs from the requested key, using a fake `/v1` that answers with another issue. (10) The SQL-shaped key returns a tool error and no issue. Consequence: Claude reports a different issue's facts and outcome, silently. Workaround: none, because nothing signals the error. |
| (B) Claude Desktop answers from ticketscope, and its requests keep working | R4 | E2E | R-003 | 6 | Stories 4.2, 4.7 | Mechanism: Claude Desktop's request shapes are checked only by a person, once. Boundary: Claude Desktop, the tunnel and `mcp`, which are two or more deployables. Level: E2E. Scenarios: (1) *Manual, story 4.2:* a person adds the tunnel's `/mcp` as a custom connector with no auth, asks a triage question, and the recording shows a `search_similar_issues` call and an answer that cites issue keys or urls present in the tool result. The screenshot is committed and linked from the plan. (2) *Manual, story 4.2:* the session's `initialize`, `notifications/initialized`, `tools/list` and `tools/call` requests are captured and committed with no credential, together with the protocol version, client info and headers (C-9). (3) `mcp-e2e.yml` replays the captured requests against `/mcp` on kind: the protocol version is accepted, `tools/list` returns both tools with schemas, and `tools/call` returns `structuredContent`. (4) Each tool result also carries a text content block with the serialised JSON, for clients that ignore `structuredContent`. (5) The replay runs on every PR from story 4.3 onward, so the error path, `get_issue` and `_meta` handling are checked against Claude Desktop's real shapes. (6) The replay succeeds for each handshake-era version the SDK serves, sent to both replicas. Consequence: the epic Outcome fails while CI is green. Workaround: none; the CI client test is not Claude Desktop. |
| (C) `search_similar_issues` returns the `/v1/search` body through the Gateway on kind | R1 | E2E | - | 7 | Story 4.1 | Boundary: Gateway, `mcp`, `api` and Postgres on kind. The client test runs from `tests/mcp/` under `mcp-e2e.yml`. Scenarios: (1) `tools/list` lists `search_similar_issues` (and `get_issue` from story 4.4). Its `inputSchema` has `query` required and `mode` and `k` optional, and its `outputSchema` equals the schema generated from `ticketscope.contract.SearchResponse`. (2) A vague query without a mode returns `mode` equal to `retrieval.defaultMode` from `values.yaml`, never a hard-coded value, because story 3.6 may change it. (3) With `mode=keyword`, `structuredContent` equals the direct `POST /v1/search` body for the same request. (4) Each result validates with `jsonschema` against the advertised `outputSchema`. (5) A field the API adds passes through to the tool output: `issue.key` after story 4.4 (AD-20). (6) 20 calls on fresh connections all succeed, and both `mcp` pods' logs show tool calls, which proves both replicas served. (7) A `tools/call` sent on a connection that never ran `initialize` on that replica succeeds (stateless). Consequence: the epic's one tool does not work. Workaround: none. |

**Total P0**: 23 tests, ~14–28 hours

### P1 (High)

**Criteria**: Core, frequent, or complex behavior with material user reach and a limited workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| The tunnel's host reaches `/mcp` through the listener, the route and `allowed_hosts` | R4 | E2E | R-006 | 5 | Stories 4.1, 4.2 | Mechanism: three places must admit a host, and the story names two. Boundary: the platform Gateway (Envoy) and `mcp`, which are two deployables. Level: E2E. CI uses a stand-in host, `tunnel.ticketscope.test`, set from kind values. Scenarios: (1) a `tools/list` with `Host: tunnel.ticketscope.test` reaches `/mcp` and gets 200. (2) A host on the route and listener but not in `allowed_hosts` is refused by `mcp`, which proves the SDK check is live. (3) A host in `allowed_hosts` but not on the listener gets Envoy's 404, which records which layer refuses. (4) `Host: ticketscope.kind.internal` still works. (5) With the tunnel value empty, the chart renders no extra hostname, listener or allowed host. Consequence: story 4.2 stalls at its human step. Workaround: a values edit once the cause is found, or ngrok's host-header rewrite, which the epic Decision declined. |
| The tunnel host exposes nothing but `/mcp` | R4 | E2E | R-001 | 4 | Stories 4.1, 4.2 | Mechanism: no auth while the tunnel runs. Boundary: the Gateway's routes across the `platform` and `ticketscope` releases. Level: E2E. Scenarios: (1) `Host: tunnel.ticketscope.test` to `/v1/search`, `/v1/issues/1`, `/` and `/healthz` returns 404. (2) No HTTPRoute exists for Grafana, Tempo or SeaweedFS on any host (`kubectl get httproute -A`). (3) The chart refuses `*` or an empty-means-any value in `allowed_hosts`. (4) *Manual, story 4.2:* after the script exits, the tunnel hostname no longer reaches the cluster. Consequence: unauthenticated public use of more than the read-only tools. Workaround: stop the tunnel. |
| Story 4.1's shared setup works on a fresh and an upgraded cluster | R1 | E2E | R-004 | 4 | Story 4.1 | Mechanism: an oversized tracer breaks wiring that later stories rely on. Boundary: image, chart, workflow and cluster. Scenarios: (1) On a fresh cluster, `mcp-e2e.yml` passes. (2) After an in-place `helm upgrade`, `mcp` is Ready and the client test passes again. (3) `ci.yml`'s integrated-check and `eval.yml` pass on the same PR head, with `eval/baseline.json` unchanged. (4) The plan names the independent review and its findings, or records the split. Consequence: defects reach stories 4.2 to 4.7. Workaround: fix in a later story. |
| An unknown mode or `k` comes back with the API's own 422 detail | R1, R3 | API | R-005 | 5 | Stories 4.1, 4.3 | Mechanism: `apiclient`'s request model holds the contract's Literal. Boundary: the MCP tool over Streamable HTTP against a fake `/v1` that serves problem bodies recorded from `create_app`. Level: API. Scenarios: (1) `mode="bogus"` returns `isError` whose text equals the recorded 422 `detail`. (2) A spy on the fake records that `apiclient` sent `"mode": "bogus"` unchanged, and sent no `mode` key when it was omitted. (3) `mode=""` and `mode=" keyword"` also reach the API. (4) `k=0`, `k=51` and `k="ten"` return the API's 422 detail, unless the tool's `inputSchema` bounds `k`, in which case the SDK's error is a tool error and not a protocol error. (5) `src/ticketscope/mcp` contains no list of mode names and no default mode (AD-25). Consequence: the wrong detail or a protocol error for a common agent mistake. Workaround: the agent retries with a valid mode, if the detail says which modes exist. |
| An unreachable `api` yields a tool error on kind, and `mcp` stays Ready | R3 | E2E | R-009 | 4 | Stories 4.1, 4.7 | Mechanism: a destructive step inside the suite, and readiness that may depend on `api`. Boundary: `mcp`, the `api` Service and the Gateway on kind. Scenarios: (1) With `api` scaled to zero, the `mcp` pods stay Ready and `tools/list` still answers through the Gateway. (2) `tools/call search_similar_issues` returns `isError` with the unreachable detail (C-5) within the `apiclient` timeout plus a margin, and never a Gateway 503. (3) The case runs as a separate pytest invocation after the main suite in the workflow's `check` command, never by test order. (4) A finalizer scales `api` back, waits for it to be Ready, and one call then succeeds. Consequence: R3's unreachable case is unproved, and a real outage shows a 503. Workaround: rerun the job. |
| Every failed call is a tool error, never a protocol error or an empty result | R3 | API | - | 9 | Story 4.3 | Boundary: the MCP server in process against a fake `/v1`. Scenarios: (1) 422, (2) 404, (3) 500 and (4) 503 problem+json each give `isError` with that `detail`. (5) A refused connection and (6) a read timeout give the unreachable detail (C-5). (7) An HTML 502 gives `isError` with the status (C-6). (8) A 200 that fails contract validation gives `isError`, not an exception. (9) For all of these, the JSON-RPC response has `result.isError: true` and no `error` member, and no stack trace appears in the text. Consequence: a client sees a protocol failure. Workaround: the user retries. |
| `get_issue` round-trips a key taken from a search on kind | R2, R3 | E2E | - | 3 | Story 4.4 | Boundary: Gateway, `mcp`, `api` and Postgres. Scenarios: (1) The key of a `search_similar_issues` result, passed to `get_issue`, returns the issue with that key, the same `number`, and an `outcome` equal to the search hit's. (2) The result validates with `jsonschema` against the schema generated from `IssueResponse`. (3) An unknown key returns `isError` with the API's detail. Consequence: R2 is unproved on the cluster. Workaround: none in CI. |
| The by-key lookup works through the Postgres adapter and agrees with the fake | R2 | Integration | - | 5 | Story 4.4 | Boundary: Postgres, through `PostgresCorpusStore`, on a migrated container from the in-repo image. Scenarios: (1) The lookup returns the `IssueDetail` with its body for a loaded key. (2) An unknown key returns `None`. (3) `ticketscope_ro` can run it. (4) The key is passed as a parameter, so the SQL-shaped key returns `None`. (5) The in-memory fake and the adapter return the same results for the same fixture. Consequence: `get_issue` fails or diverges on the cluster. Workaround: none. |
| `/v1` gains `issue.key` additively and nothing else changes | R2 | API | - | 5 | Story 4.4 | Boundary: `/v1` through the app factory. Scenarios: (1) `scripts/v1_parity.py compare` gains an option that drops exactly `issue.key`, and passes against a capture from before the change. (2) The same comparison fails when any other field differs, which a planted change proves. (3) The page HTML for each golden query is byte-identical before and after. (4) `GET /v1/issues/{number}` is unchanged except for `key`. (5) A body without `key` still validates in `apiclient` (C-8). Consequence: the page, eval or other callers break. Workaround: revert. |
| One MCP call yields one trace from the tool call to the database in Tempo | R5 | E2E | - | 6 | Story 4.5 | Boundary: `mcp`, `api`, the collector and Tempo on kind, using a copy of `tests/smoke`'s Tempo pattern in `tests/mcp/`. Scenarios: (1) `mode=hybrid` gives one trace whose root is the `ticketscope-mcp` SERVER span `tools/call search_similar_issues`. Under it sit the CLIENT POST, `api`'s SERVER `POST /v1/search`, `retrieval hybrid`, `embeddings {model}` and the db query, each child linked to its parent by Tempo's parent ids (C-2 finds the trace). (2) A call with `_meta.traceparent` lands in that trace id, and the tool span's parent is the caller's span id. (3) Both a header and `_meta` with different ids: `_meta` wins (C-3). (4) An unknown mode gives a tool span with status ERROR. (5) `get_issue` gives its own trace: tool span, CLIENT GET, `api`'s `GET /v1/issues/by-key/{key}`, db query. (6) Exactly one `ticketscope-mcp` SERVER span per call, and no query text on any span. Consequence: R8 is unproved and epic 8 has no screenshot. Workaround: fix instrumentation. |
| The `mcp` process emits the AD-10 tool span and propagates context | R5 | API | - | 6 | Story 4.5 | Boundary: the MCP server in process with an in-memory span exporter and a fake `/v1` that records request headers. Scenarios: (1) The tool span is SERVER, named `tools/call {tool}`, with `mcp.method.name`, `gen_ai.operation.name=execute_tool` and `gen_ai.tool.name`, and `service.name` is `ticketscope-mcp`. (2) The outgoing request's `traceparent` carries the tool span's trace id (C-1). (3) `_meta.traceparent` is continued, and a malformed one starts a new trace without an error. (4) Query text appears only when `trace_query_text` is set. (5) An empty OTLP endpoint creates no exporter. (6) A tool error sets status ERROR. Consequence: the trace breaks at the service boundary. Workaround: fix instrumentation. |
| The `ticketscope` chart renders the `mcp` Deployment, Service and route as the spine requires | R1 | Unit | - | 10 | Stories 4.1, 4.2 | Boundary: `helm template` over `values.yaml` and `values-kind.yaml`. Scenarios: (1) The `mcp` Deployment uses the app image with the `ticketscope-mcp` command. (2) Its probes hit an endpoint of `mcp` itself, never `api` (R-009). (3) Replicas come from `values-kind.yaml` (2). (4) A Service and an HTTPRoute for `/mcp` attach to the `platform` Gateway, with hostnames from values. (5) `allowed_hosts` comes from values and includes the hostname. (6) There is no `mcp` mode key (AD-25). (7) The API base URL is the in-cluster `ticketscope-api` Service, never the public host (AD-14). (8) The OTLP endpoint and the opt-in variables are set. (9) No database Secret or credential is mounted (AD-3). (10) The new chart test files are listed in `ci.yml`'s `charts` job, so they run with the pinned Helm 4.3.1. Consequence: a misconfigured deployment. Workaround: a values edit. |
| `mcp` and `apiclient` keep the AD-1 layering | R1 | Unit | - | 3 | Story 4.1 | Scenarios: (1) import-linter forbids `mcp` and `apiclient` from importing `core`, `adapters`, `http`, `jobs`, `psycopg` and `fastembed`. (2) Nothing imports `mcp`. (3) An enforcement test plants a forbidden import and shows `lint-imports` fails, as `tests/unit/test_import_linter_enforcement.py` does. Consequence: retrieval logic leaks into `mcp`. Workaround: review catches it. |
| `mcp-e2e.yml` runs on the right PRs with the shared kind path | R1 | Unit | - | 4 | Story 4.1 | A parse test over the workflow files, as `tests/unit/test_eval_workflow.py` does. Scenarios: (1) It runs on `pull_request` and calls `_kind-deploy.yml`. (2) It uses `.github/kind-paths.yml`, which includes `tests/mcp/**`. (3) Its `check` runs `pytest -m kind tests/mcp` with a JUnit report, then the unreachable case as a separate invocation. (4) Its reports are uploaded when a step fails. Consequence: the client test silently stops running. Workaround: none until noticed. |
| The closing integrated check covers each Done when line CI can run | R1, R2, R3, R5 | E2E | - | 6 | Story 4.7 | Boundary: a fresh kind cluster in CI. The row asserts wiring only, because lower rows hold the logic. Scenarios: (1) Both tools, with and without a mode. (2) `get_issue` by a key taken from a search. (3) The unknown-mode and unknown-key tool errors. (4) The unreachable case, last. (5) One trace from the tool call to the database. (6) The epic Notes link story 4.2's recorded session for R4. Consequence: the epic is unproved on the cluster. Workaround: none. |
| The refactor sweep changes no behaviour, contract or span | R1, R2, R3, R5 | E2E | - | 3 | Story 4.6 | On story 4.6's PR: (1) `mcp-e2e.yml`, including the Claude Desktop replay, passes; shared Tempo helper extraction also preserves both suites' parsing and search behavior, with any new shared directory covered by the kind path filter. (2) `ci.yml` passes; the eval job passes when the PR matches the eval path filter, otherwise its filtered skip is accepted with the reason recorded in the plan. In either case, `eval/baseline.json` is byte-identical to the PR base revision. Chart template refactoring includes before/after render comparisons for default, kind, and tunnel-host values. (3) `lint-imports` keeps every contract. Consequence: a silent change of behaviour. Workaround: revert. |

**Total P1**: 82 tests, ~33–66 hours

### P2 (Medium)

**Criteria**: Secondary behavior with narrower user reach and an acceptable workaround. Risk score
is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| The tunnel serves Streamable HTTP unaltered to a non-browser client | R4 | E2E | R-002 | 4 | Story 4.2 | Mechanism: a free tunnel may insert a page or buffer streams. Boundary: the tunnel service and `mcp`. *Manual, recorded in story 4.2's plan.* Scenarios: (1) `curl` to the tunnel's `/mcp` with a non-browser User-Agent gets a JSON-RPC body with `application/json` or `text/event-stream`, and no interstitial HTML. (2) A streamed response arrives with every event and the final result, identical to the same request sent to kind directly. (3) The plan records the tunnel's free-tier bandwidth limit against one session's measured traffic (UNKNOWN until measured). (4) The plan records which tunnel was chosen and why. Consequence: Claude Desktop fails or hangs. Workaround: the documented Tailscale Funnel fallback. |
| `kind-up.sh` waits for and restarts `mcp` as it does `api` | R1 | E2E | R-011 | 3 | Story 4.1 | Mechanism: bring-up waits only for `api`. Boundary: the script against a cluster. Scenarios: (1) `kind-up.sh` runs `rollout status deploy/ticketscope-mcp` before returning. (2) A same-tag rebuild restarts `ticketscope-mcp`, and the new pods run the new image ID. (3) The runner-fit summary records peak memory with two `mcp` replicas. No threshold is set. Consequence: intermittent CI failures, or local runs against stale code. Workaround: rerun, or restart `mcp` by hand. |
| `mcp` settings come only from `TICKETSCOPE_*` | R1 | Unit | - | 3 | Story 4.1 | Scenarios: (1) The API base URL, allowed hosts, OTLP endpoint and timeout are read by the one settings module. (2) A missing API base URL fails startup with a clear message. (3) No config file is read. Consequence: a misconfigured pod. Workaround: fix the value. |
| The tunnel script commits no credential and fails clearly without one | R4 | Unit | - | 3 | Story 4.2 | Scenarios: (1) The script reads the credential and hostname from the environment and exits non-zero, with a message, when either is missing. (2) It never prints the credential. (3) A repository scan finds no tunnel credential pattern, and `shellcheck` passes. Consequence: a leaked credential. Workaround: rotate it. |

**Total P2**: 13 tests, ~5–10 hours

### P3 (Low)

**Criteria**: Rare, cosmetic, or experimental behavior with minimal impact and an easy workaround.
Risk score is supporting evidence and is not a required condition.

| Requirement | R ids | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | ----- | ---------- | --------- | ---------- | ----- | ----- |
| The `tests/mcp` Tempo helper parses Tempo bodies correctly | R5 | Unit | R-008 | 2 | Stories 4.5, 4.6 | Mechanism: a second copy of the smoke helpers. Boundary: test code only, so Unit. Scenarios: (1) Recorded Tempo `/api/v2/traces` bodies with base64 and hex span ids and string `intValue`s parse into the same spans as `tests/smoke`'s helper would produce. (2) Story 4.6's plan records whether the helpers were unified or deferred. Consequence: an intermittent trace check. Workaround: fix the copy. |
| Tool-span attribute names come from one list that cites the semconv version | R5 | API | R-010 | 2 | Story 4.5 | Mechanism: experimental conventions drift. Boundary: spans from one service, so API. Scenarios: (1) The attribute keys on the tool span equal one committed constants list that names the semconv version. (2) `gen_ai.tool.name`, epic 7's `spanmetrics` dimension, is on every tool span, errors included. Consequence: epic 7's dimensions miss tool calls. Workaround: rename in one place. |

**Total P3**: 4 tests, ~1–2 hours

Why the bands look like this:

- **P0.** Three rows. A key that resolves to another issue is a silent data-integrity failure. Claude Desktop and the one search tool are the epic's Outcome, and nothing else stands in for them.
- **P1 for R-006 even at score 6.** The consequence is a blocked human step that a values edit recovers. Its workaround is limited (the Decision declined header rewriting), so the row is P1 rather than P2.
- **P1 for the rest of the contract, errors, traces, chart and layering.** Each is core behaviour with material reach and a recoverable failure.
- **P2 for the tunnel's fidelity and bring-up.** The tunnel has a documented fallback, and a bring-up race is fixed by a rerun.
- **P3 for the test helper and the attribute list.** Each is a one-place fix.

P0 count per story: story 4.4 has row (A) with 10; stories 4.2 and 4.7 have row (B) with 6; story 4.1 has row (C) with 7; stories 4.3, 4.5 and 4.6 have none.

---

## Execution Strategy

**Philosophy:** Run every functional scenario in pull requests while the suite stays under 15 minutes.
Defer only work with material infrastructure or duration cost. P0 through P3 are priority and are not
execution timing; this section decides when tests run and the coverage plan above decides what they are.

- **Pull request, `ci.yml`:**
  - `checks` runs ruff, pyright, import-linter, and every Unit, API and Integration row: the MCP server in process against fake `/v1` servers, `/v1` through the app factory, the Postgres-container lookup, the span rows and the workflow parse tests.
  - `charts` runs the chart render tests. The new `mcp` chart test files must be added to its explicit list.
  - `integrated-check` and `eval.yml` keep running unchanged. They are this epic's regression guard for `/v1` and `eval/baseline.json`.
- **Pull request, `mcp-e2e.yml`:** brings up kind through `_kind-deploy.yml` and runs every E2E row except the manual ones. That includes the Claude Desktop replay from story 4.3 onward, the stand-in tunnel host, the Tempo trace and, as a separate final invocation, the unreachable case. Its duration is UNKNOWN until story 4.1 records it. A PR that touches kind paths now runs three kind deployments.
- **Manual, story 4.2:** a person runs the tunnel checks and the Claude Desktop session, and commits the screenshot, the captured requests and the plan record. Repeating the session once at epic close is proposed for story 4.7.
- **Nightly:** none planned.
- **Weekly:** none planned.

Do not re-list the individual tests here. They are already in the coverage plan.

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| -------- | ----- | ---------- | ----------- | ----- |
| P0 | 23 | 0.6–1.2 | ~14–28 | The key oracle and hostile keys, the in-process MCP-to-app harness, and capturing and replaying Claude Desktop's requests are the main cost |
| P1 | 82 | 0.4–0.8 | ~33–66 | Most rows are cheap with a fake `/v1`; the kind rows, the Tempo search and the stand-in tunnel host are not |
| P2 | 13 | 0.4–0.8 | ~5–10 | Two rows are manual records in story 4.2's plan |
| P3 | 4 | 0.25–0.5 | ~1–2 | Small parse and constant checks |
| **Total** | **122** | **-** | **~53–106** | **~1.5–3 weeks** |

### Prerequisites

**Test Data:**

- The key oracle table and hostile-key cases (red-mode session, before story 4.4).
- Problem bodies recorded from `create_app` with the in-memory store, for 422, 404, 500 and 503.
- Claude Desktop's captured requests, with credentials stripped (story 4.2).
- Recorded Tempo `/api/v2/traces` bodies with base64 and hex ids.
- The pinned snapshot on kind, with v2 keys in `url`; `snapshot/fixture.jsonl` for API rows.

**Tooling:**

- pytest, ruff, pyright, import-linter, and `helm template` (pinned Helm 4.3.1 in the `charts` job).
- `jsonschema`, already in the `ingest` dev group, for independent schema validation.
- The official `mcp` SDK v2 client, for the CI client test and the replay.
- An in-memory OTel span exporter; `tests/waiting.eventually` for every wait on kind (`tests/unit/test_no_sleep_in_tests.py` guards `time.sleep`).
- A tunnel account and Claude Desktop on a person's machine (story 4.2 only).

**Environment:**

- kind through `scripts/kind-up.sh` and `_kind-deploy.yml`, with two `mcp` replicas and a stand-in tunnel host in kind values.
- A Postgres container from the in-repo image for the Integration row.
- Tempo reached through the API server's service proxy, as `tests/smoke` does.

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths**: ≥80% (Claude Desktop or the CI client → Gateway → `mcp` → `apiclient` → `/v1` → retrieval → Postgres, and the trace across them)
- **Security scenarios**: 100% (host admission and refusal, tunnel exposure, credential handling, no DB credential in `mcp`)
- **Business logic**: ≥90% of `apiclient`'s error mapping and the key derivation, because they are the thing under test
- **Edge cases**: ≥50%

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Security tests (R-001 and the host checks) pass 100%
- [ ] Performance targets met (PERF category): no gated threshold; runner-fit and tunnel figures are recorded
- [ ] Planned NFR evidence exists or `nfr-assess` has documented CONCERNS/waivers

---

## Mitigation Plans

### R-003: Claude Desktop compatibility checked once, by hand (Score: 6)

**Mitigation Strategy:**

1. Story 4.2 captures the requests Claude Desktop sends (handshake, `tools/list`, `tools/call`), with the protocol version and headers, and commits them with no credential.
2. `mcp-e2e.yml` replays them against `/mcp` on every PR from story 4.3 onward, against both replicas.
3. Every tool result carries a text content block beside `structuredContent`.
4. A person repeats the Claude Desktop session once on story 4.7's head and links it from the epic Notes.

**Owner:** Dillon (stories 4.2 and 4.7)
**Timeline:** capture in story 4.2; replay from story 4.3; repeat at close
**Status:** Planned
**Verification:** row (B) passes, including the replay on story 4.7's PR.
**Residual risk:** the replay checks request shapes only. A Claude Desktop update after the capture can still change them, and only the closing manual session would see it.

### R-006: The tunnel host is not admitted by the Gateway listener (Score: 6)

**Mitigation Strategy:**

1. One environment value names the tunnel hostname. The platform release adds it to the Gateway (a second listener, or no listener hostname on kind). The `ticketscope` release adds it to the `/mcp` route's hostnames and to `allowed_hosts`.
2. CI sets a stand-in host in kind values, so the admission path is tested on every PR before any tunnel exists.
3. Story 4.2's description is updated to name the listener (Proposed Story Updates).

**Owner:** Dillon (stories 4.1 and 4.2)
**Timeline:** before story 4.2's human step
**Status:** Planned
**Verification:** the R-006 row passes with the stand-in host, and story 4.2's `curl` through the real tunnel gets 200.
**Residual risk:** the platform chart belongs to epic 1. The listener change must keep `ticketscope.kind.internal` working, which scenario (4) of the row checks.

### R-007: `get_issue` silently returns a different issue (Score: 6)

**Mitigation Strategy:**

1. A red-mode session commits the key oracle and hostile keys before story 4.4's build.
2. `apiclient` percent-encodes the key as a single path segment. `api` accepts only `^[A-Z][A-Z0-9]*-[1-9][0-9]*$` and returns 404 otherwise (C-4).
3. The lookup is an exact, parameterised url match built from `MOJANG_BROWSE_URL`.
4. The tool checks that the returned `issue.key` equals the requested key, and returns a tool error otherwise.

**Owner:** Dillon (story 4.4)
**Timeline:** oracle before the build; row (A) before 4.4 merges
**Status:** Planned
**Verification:** row (A) passes against values the build session did not author.
**Residual risk:** issues whose url is not a browse url have a null key and cannot be fetched by `get_issue`. On the v2 corpus every url is a browse url (spine Identifiers convention: the key "lives in the snapshot and in `url`"), so this affects v1-shaped fixtures only.

---

## Assumptions and Dependencies

### Assumptions

1. The C-1 to C-9 decisions under "Clarifications for the PO" (2026-11-10) reach the stories before each one builds.
2. kind in CI is production for this epic (initiative Assumption, carried from epics 1 to 3).
3. The `mcp` SDK v2 serves stateless Streamable HTTP with DNS-rebinding protection driven by `transport_security.allowed_hosts`, as AD-5 describes.
4. Every v2 snapshot issue's `url` is a browse url, so every loaded issue has a key.

### Dependencies

1. Branch `epic-4-plan-mcp-server` merges to `main`. Required before story 4.1 starts.
2. The red-mode key-oracle session runs before story 4.4 builds.
3. The PO writes the C-1 to C-9 decisions into the stories and updates story 4.2 for R-006.
4. A person creates the tunnel account, reserves the hostname and runs the Claude Desktop session (story 4.2).
5. Epic 3's stories 3.5 to 3.8 run alongside. The only shared file is `values.yaml`, and tests read the default mode from it.

### Risks to Plan

- **Risk**: no OpenTelemetry instrumentor supports `httpx2` (C-1).
  - **Impact**: the CLIENT span and `traceparent` propagation need hand-written code, and R5's trace breaks until it exists.
  - **Contingency**: a client event hook or transport wrapper that opens the CLIENT span and injects the header, tested by the API span row.
- **Risk**: three kind deployments per PR exceed runner capacity or the time people will wait.
  - **Impact**: slow PRs, or `mcp-e2e.yml` gets skipped.
  - **Contingency**: story 4.1 records the duration. If needed, run the `tests/mcp` suite inside `ci.yml`'s `integrated-check` deployment instead, as one check command.
- **Risk**: Claude Desktop changes its requests between story 4.2 and epic close.
  - **Impact**: the replay passes while the real client fails.
  - **Contingency**: the closing manual session (R-003, step 4).

---

## Proposed Story Updates

These changes are for the PO to apply. This plan does not edit `tickets.toml` or the epic.

| Story | Proposed change | Why |
| ----- | --------------- | --- |
| 4.1 | Add to `verify`: "`mcp`'s probes do not call `api` (R3); `apiclient` sends `mode` as given and builds no request through the contract's Literal (R3); `kind-up.sh` waits for and restarts `ticketscope-mcp` (R1); `mcp` mounts no database Secret and calls `api` through the in-cluster Service (R1); the new chart tests are listed in `ci.yml`'s `charts` job (R1)." | R-005, R-009, R-011 |
| 4.1 | Name the independent review in the plan, or split at the plan checkpoint. | R-004 |
| 4.2 | Description: add the tunnel hostname to the `platform` Gateway's listener as well as the `/mcp` route and `allowed_hosts`, from one environment value, and have CI rehearse it with a stand-in host. | R-006 |
| 4.2 | Add to `verify`: "the Claude Desktop session's requests and protocol version are captured and committed with no credential (R4); through the tunnel host, `/v1` and `/` return 404 (R4); the tunnel stops when the script exits (R4)." | R-001, R-003, C-9 |
| 4.3 | Description: an unreachable API gives `ticketscope API unreachable: connection refused` or `... timed out after 10s`; the timeout is `TICKETSCOPE_API_TIMEOUT_SECONDS`, chart default 10. An error response without problem+json gives `isError` naming the status, never the body. | C-5, C-6 |
| 4.4 | Description: a key matches `^[A-Z][A-Z0-9]*-[1-9][0-9]*$` exactly; `apiclient` percent-encodes it as one path segment; `api` returns 404 problem+json for a non-matching or unknown key; `key` is `str \| None = None` in the contract; the tool returns a tool error when the returned key differs from the requested key. Add to `verify`: "the hostile-key cases, including `../6629`, return tool errors and never issue 6629 (R2, R3); the parity script's drop option removes exactly `issue.key` (R2)." | R-007, C-4, C-8 |
| 4.5 | Description: the check finds the no-context trace by a TraceQL search on `ticketscope-mcp` and the tool span name within the call's time window, with calls made one at a time; `mcp` continues `_meta.traceparent` only and ignores the HTTP header; `apiclient` tries `opentelemetry-instrumentation-httpx` and otherwise opens the CLIENT span and injects `traceparent` in an `httpx2` event hook. Keep the tool-span attribute names in one list that cites the semconv version. | C-1, C-2, C-3, R-010 |
| 4.6 | Scope: decide whether the `tests/mcp` Tempo helper is unified with `tests/smoke`'s, and record the decision. | R-008 |
| 4.7 | Add to `verify`: "the unreachable case runs as its own invocation after the suite and restores `api` (R3); the Claude Desktop replay passes (R4); a person repeats the Claude Desktop session on this story's head and links it (R4)." | R-003, R-009 |

---

## Follow-on Workflows (Manual)

- Run `/bmad-tea-automate` in red mode to commit the key oracle and hostile-key fixtures before story 4.4's build (separate workflow; not auto-run).
- Run `/bmad-tea-automate` for broader coverage once implementation exists.
- Run `/bmad-tea-nfr` once story 4.1 records the runner fit and story 4.2 records the tunnel figures.
- Run `/bmad-tea-trace` at epic closure, linking `mcp-e2e.yml` run URLs (C-7).

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: Dillon Date: ____
- [ ] Tech Lead: Dillon Date: ____
- [ ] QA Lead: Dillon Date: ____

**Comments:**

---

## Interworking & Regression

| Service/Component | Impact | Regression Scope |
| ----------------- | ------ | ---------------- |
| **Epic 1 `/v1`, contract and page** | Story 4.4 adds `issue.key` to `contract.Issue` and `GET /v1/issues/by-key/{key}` | Epic 1's `/v1` and smoke tests; `scripts/v1_parity.py` with the key dropped; the page's golden HTML |
| **Epic 1 `CorpusStore`, fake and Postgres adapter** | Story 4.4 adds a lookup by key | `tests/unit/test_postgres_store*.py`, the fake's tests, and the read-only role test |
| **Epic 1 `platform` release** | The Gateway listener admits the tunnel host (R-006) | `tests/smoke/test_gateway.py` with `Host: ticketscope.kind.internal` |
| **Epic 1 and 3 workflows and `kind-up.sh`** | A third kind workflow; `kind-up.sh` waits for `mcp`; `kind-paths.yml` gains `tests/mcp/**` | `ci.yml` integrated-check, `eval.yml`, and the workflow parse tests |
| **Epic 2 eval and baseline** | `contract` changes; the eval reads `/v1` models | `eval.yml` with `eval/baseline.json` unchanged on every story PR |
| **Epic 3, stories 3.5 to 3.8** | Shared `values.yaml`; story 3.6 may change `retrieval.defaultMode`; story 3.8 extends `tests/smoke` | Tests read the default from `values.yaml`; `tests/mcp` does not touch `tests/smoke` |
| **Epic 5 EKS** | Serves `/mcp` on the live hostname from `values-eks.yaml` | The chart rows: hostnames and `allowed_hosts` come only from environment values |
| **Epic 6 OAuth** | Adds `/.well-known/oauth-protected-resource` to `mcp`'s route and auth on/off per environment | The R-001 row's list of routes on the tunnel host |
| **Epic 7 dashboard** | Reads `gen_ai.tool.name` and tool spans | The R-010 row and the span rows |
| **Epic 8 reviewer package** | Uses this epic's trace screenshot and Claude Desktop recording | The span-tree row and row (B) |

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization
- `nfr-criteria.md` - NFR categories and evidence

### Related Documents

- PRD: `_bmad-output/initiative-ticketscope/initiative-ticketscope.md` (R4, R8)
- Epic: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/epic-mcp-server.md`
- Stories: `_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/tickets/tickets.toml`
- Architecture: `_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md`
- Prior test design: `_bmad-output/test-artifacts/test-design/test-design-epic-3.md`

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `bmad-tea-test-design`
**Version**: 4.0 (BMad v6)
