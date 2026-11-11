---
title: 'Story 4.1: tracer, an MCP client calls search_similar_issues through the Gateway on kind'
type: 'feature'
ticket: '1'
created: '2026-11-11'
status: done
baseline_revision: '830cc25a28245a3290069b9e7aa69fcb5903a987'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'thorough'
review_source: 'pinned'
lenses_ran: ['blind-hunter', 'edge-case-hunter', 'verification-gap', 'intent-alignment']
review_loop_iteration: 0
followup_review_recommended: false
context: []
warnings: ['oversized']
deferred: []
---

<intent-contract>

## Intent

**Problem:** Nothing lets an MCP client reach retrieval. Epic 4 needs a stateless MCP server that reaches `api` only over `/v1`, deployed on kind behind the Gateway, with CI proving it end to end (R1).

**Approach:** Thinnest path: `mcp` SDK 2.3.0 dependency; `ticketscope.apiclient` (httpx2 over `ticketscope.contract`); `ticketscope.mcp` (`MCPServer`, stateless Streamable HTTP at `/mcp`, one tool `search_similar_issues(query, mode?, k?)`); chart Deployment, Service, HTTPRoute; `kind-up.sh` wait/restart; import-linter contracts; `mcp-e2e.yml` with a client test in `tests/mcp/`.

## Boundaries & Constraints

**Always:** `mode` is a plain `str | None` on the tool and in `apiclient`; `apiclient` builds the request body as a plain dict and sends `mode` exactly as given, omitting the key when `None` (never via `SearchRequest`, whose Literal would reject it inside `mcp`; R-005). Tool output is the `/v1/search` body unchanged, typed `SearchResponse` so the output schema is generated from the contract (extra fields pass through, AD-20). `mcp` has no default mode and no mode list (AD-25). `mcp` probes check only the process (R-009). `allowed_hosts` and route hostnames come from values. All config via `TICKETSCOPE_*` in `Settings`. `mcp` logs one JSON line per tool call (the two-replica check reads pod logs). The independent review runs thorough (R-004).

**Never:** `mcp` or `apiclient` import `core`, `adapters`, `http`, `jobs`, `psycopg` or `fastembed`; mount a database Secret in `mcp`; call `telemetry.setup` (it instruments psycopg; tracing is story 4.5); a wildcard or empty `allowed_hosts`; `get_issue`, error mapping, tunnel host or Gateway listener changes (stories 4.2–4.4); edit `eval/baseline.json`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| No mode | `{query}` | `/v1` call has no `mode` key; response `mode` is the server default | No error expected |
| Keyword | `{query, mode:"keyword"}` | `structuredContent` equals direct `POST /v1/search` body | No error expected |
| Unknown mode | `mode:"bogus"` | `apiclient` sends `"bogus"` unchanged; API 422 reaches the client | `isError`; detail polish is story 4.3 |
| No initialize | `tools/call` with no prior `initialize` | Succeeds on any replica | No error expected |
| Foreign host | `Host` outside `allowed_hosts` | Refused (in process: SDK 4xx; via Gateway: 4xx) | No stack trace |
| Bad chart values | `*` or empty hosts | `helm template` fails | `fail` message names the value |
| api down | `api` unreachable | `mcp` stays Ready | Tool error only (asserted in story 4.7) |

</intent-contract>

## Code Map

- `pyproject.toml`, `uv.lock` -- add `mcp~=2.3.0` (resolves with httpx2 2.16, pydantic 2.14.3, starlette, uvicorn 0.54 already pinned; verified in a scratch venv) and script `ticketscope-mcp = "ticketscope.mcp.main:main"`; run `uv lock`.
- `src/ticketscope/settings.py` -- the one settings module; add `api_base_url` (empty by default), `api_timeout_seconds` (10), `mcp_allowed_hosts` (comma-separated env, parsed to list). Reuse `http_host`/`http_port`, `otlp_endpoint`, `trace_query_text`.
- `src/ticketscope/contract/search.py` -- `SearchResponse`, `SearchRequest` (do not use for the body), `Problem`. Unchanged.
- `src/ticketscope/http/app.py:295` -- `main()` shape to mirror (uvicorn, `log_config=None`); its `_problem` bodies show what a 422 returns.
- `src/ticketscope/telemetry.py` -- `configure_logging()` gives JSON logs; add `SERVICE_MCP = "ticketscope-mcp"` only.
- SDK (mcp 2.3.0): `mcp.server.mcpserver.MCPServer`; `.streamable_http_app(stateless_http=True, transport_security=TransportSecuritySettings(allowed_hosts=[...]), host=...)`; `.custom_route` for `/healthz`.
- `.importlinter` -- seven contracts today; `tests/unit/test_import_linter_enforcement.py` asserts "Contracts: 7 kept".
- `deploy/charts/ticketscope/templates/api.yaml`, `_helpers.tpl` -- model for Deployment/Service/HTTPRoute, `otlpEnv`, labels. api's route owns `/v1` and Exact `/`; `/mcp` does not overlap.
- `deploy/charts/ticketscope/values.yaml`, `values-kind.yaml` -- `hostname` (kind: `ticketscope.kind.internal`); this epic owns the `mcp` keys.
- `scripts/kind-up.sh:112-140` -- api image-note/restart/`rollout status` block to mirror for `ticketscope-mcp`.
- `.github/workflows/eval.yml`, `_kind-deploy.yml`, `.github/kind-paths.yml`, `ci.yml` `charts` job -- patterns for the new workflow, path filter and chart-test list.
- `tests/smoke/test_gateway.py` (`_gateway()`, `pytestmark = kind`), `tests/waiting.py` (`eventually`; no `time.sleep`), `tests/target.py` (values.yaml readers), `tests/unit/test_chart_telemetry.py` and `test_chart_backup.py` (`_render`, `_docs`, `_flat`), `tests/unit/test_eval_workflow.py` (workflow parse test).

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock` -- add dependency and entrypoint -- one image, two processes
- [x] `src/ticketscope/settings.py` -- add the three mcp fields -- AD-25 single settings module
- [x] `src/ticketscope/apiclient/__init__.py` -- `ApiClient(base_url, timeout)` over `httpx2.AsyncClient`; `async search(query, mode, k) -> SearchResponse` (plain-dict body, `k` only when given); non-2xx raises `ApiError(status, detail)` with the problem `detail` when present -- R-005
- [x] `src/ticketscope/mcp/server.py`, `__init__.py` -- `build_server(client)` registering `search_similar_issues` (returns `SearchResponse`, logs one JSON line per call); `build_app(settings, client)` returning the stateless Starlette app with `TransportSecuritySettings(allowed_hosts=settings.mcp_allowed_hosts)` and `/healthz`; refuse empty or `*` hosts at startup
- [x] `src/ticketscope/mcp/main.py` -- composition root: `Settings()`, fail clearly on empty `api_base_url`, `telemetry.configure_logging()`, `uvicorn.run` -- `ticketscope-mcp`
- [x] `src/ticketscope/telemetry.py` -- add `SERVICE_MCP`
- [x] `.importlinter` -- contracts: `mcp` and `apiclient` forbid `core`, `adapters`, `http`, `jobs`, `psycopg`, `fastembed`; nothing imports `mcp` -- AD-1
- [x] `deploy/charts/ticketscope/templates/mcp.yaml`, `values.yaml`, `values-kind.yaml` -- `mcp.replicas` (1; kind 2), `mcp.hosts` (extra hosts), `mcp.apiTimeoutSeconds`, `mcp.resources`; Deployment (`ticketscope-mcp` command, httpGet `/healthz` probes, env: `TICKETSCOPE_API_BASE_URL=http://ticketscope-api.<ns>.svc`, allowed hosts = `hostname` + `mcp.hosts`, timeout, `otlpEnv`, `TRACE_QUERY_TEXT`; no DB Secret, no `DEFAULT_MODE`), Service, HTTPRoute (`/mcp` PathPrefix on the `platform` Gateway, same host list); `fail` on `*` or an empty list
- [x] `images/app.Dockerfile` -- comment lists `ticketscope-mcp`
- [x] `scripts/kind-up.sh` -- note the deployed mcp image, restart `ticketscope-mcp` on a same-tag rebuild, `rollout status deploy/ticketscope-mcp` before returning; update header comment (R-011)
- [x] `.github/workflows/mcp-e2e.yml`, `.github/kind-paths.yml` -- PR workflow through `_kind-deploy.yml` behind the `kind` filter; `check: uv run pytest -m kind tests/mcp --junitxml=reports/mcp.xml`; add `tests/mcp/**` to the `kind` list
- [x] `.github/workflows/ci.yml` -- list the new chart test file(s) in the `charts` job
- [x] `tests/unit/test_apiclient.py`, `test_mcp_server.py`, `test_mcp_settings.py` -- in-process server against a fake `/v1` (no cluster): tools/list, output schema equals the contract-generated schema, omitted mode sends no key, unknown/empty mode sent unchanged, extra field passes through, call with no `initialize`, foreign Host refused, `/healthz` ok without `/v1`, tool call log line; settings read from `TICKETSCOPE_*`, missing base URL fails
- [x] `tests/unit/test_chart_mcp.py` -- probes target mcp, no Secret/DB env, API URL is the in-cluster Service, hosts from values, `*`/empty refused, kind replicas 2, no mode key; `tests/unit/test_mcp_workflow.py` -- workflow parse, kind-paths, `ci.yml` charts lists the chart tests, kind-up.sh waits for mcp
- [x] `tests/unit/test_import_linter_enforcement.py` -- count becomes 10; planted forbidden imports in `mcp` and `apiclient` break it
- [x] `tests/mcp/__init__.py`, `test_search_tool.py` (`kind`) -- client through the Gateway: list tools; vague query without mode (response `mode` equals `retrieval.defaultMode` read from `values.yaml`) and with `mode=keyword`, `jsonschema` validation against the advertised `outputSchema`; keyword result equals direct `POST /v1/search`; `tools/call` without `initialize`; 20 calls on fresh connections succeed and both `ticketscope-mcp` pods' logs show tool calls (`eventually`); foreign Host refused

**Acceptance Criteria:**
- Given a PR touching kind paths, when `mcp-e2e.yml` runs, then it deploys to kind and `pytest -m kind tests/mcp` passes: tools/list; a no-mode call whose `mode` equals `retrieval.defaultMode`; a `mode=keyword` call equal to direct `POST /v1/search`; each result valid against the advertised `outputSchema`; a call with no `initialize`; 20 fresh-connection calls with tool-call logs on both pods; a foreign Host refused (R1).
- Given the in-process server and a fake `/v1`, when a tool call omits `mode`, then the fake receives no `mode` key; given `mode="bogus"`, then it receives `"bogus"` (R1, R-005).
- Given `helm template` with kind values, when rendered, then the `mcp` Deployment has 2 replicas, probes that never call api, no database Secret, the in-cluster API URL, and hosts from values; given `*` or no hosts, then render fails (R1).
- Given a same-tag image rebuild, when `kind-up.sh` finishes, then `ticketscope-mcp` was restarted and is Ready (R1, R-011).
- Given the changes, when `uv run lint-imports`, ruff, pyright and `pytest` run, then all pass with 10 contracts kept, and `ci.yml`'s `charts` job lists the new chart tests (R1).

## Implementation Notes

Route `full`: about 1,200 added lines (src ~450, chart and scripts ~250, tests ~500). That exceeds the ticket's 800-line mark, so the review runs `thorough` and is named here (R-004). The entry says to split at the checkpoint if the estimate is "well over" 800; at about 1.5x with the tests carrying the surplus, the plan keeps one story. Fallback split if the orchestrator disagrees: packages, settings, import-linter and unit tests first; chart, kind-up, workflow and `tests/mcp` second.

## Plan Change Log

## Review Triage Log

### 2026-11-11 — Review pass
- verdicts: 40 findings — high 0, medium 1, low 17, false 4, maybe-false 2 (rest merged into the rows below; 16 duplicates of a listed row share its verdict and route)
- findings:
  - `[low]` `patch` cancelled tool call logs status=ok (`except Exception` misses CancelledError) — `except BaseException` in `src/ticketscope/mcp/server.py`
  - `[medium]` `patch` failure-path log line (`status=api_422`, `status=error`) never asserted — caplog tests added in `tests/unit/test_mcp_server.py`
  - `[low]` `patch` mcp OTLP endpoint and TRACE_QUERY_TEXT env unchecked; "api only" test misnamed — mcp added to the telemetry workload loops, query-text assertion added, test renamed
  - `[low]` `patch` e2e takes the output schema only from the server's tools/list — also asserts equality with `SearchResponse.model_json_schema()`
  - `[low]` `reject` foreign-host e2e may be answered by Gateway hostname routing, not the mcp guard — the in-process test asserts the 421 guard; the ticket's own wording allows a Gateway 4xx; a fix needs a different probe path
  - `[maybe-false]` `reject` host with a port breaks the HTTPRoute hostnames — no port-bearing host is reachable in this story; tunnel host is story 4.2; would be low
  - `[low]` `reject` wildcard check inspects only the part before `:`, so `host:*` passes in Python — a port wildcard on a fixed host is the SDK's own pattern; the chart refuses every `*`
  - `[low]` `reject` empty or wildcard hosts at startup raise a traceback, not a clean exit — fails loudly with the variable named; not worth added code
  - `[low]` `reject` `ApiClient` never closed; 2xx non-JSON body; non-string problem detail; zero timeout — process exit closes connections, both bodies surface as tool errors, the API's problems carry string detail
  - `[false]` `reject` 20 fresh connections may all hit one pod — probability about 2e-6; the kind run passed with both pods logging
  - `[false]` `reject` kubelet probe path is not exercised by e2e — pods reaching Ready in the e2e deploy is that evidence
  - `[false]` `reject` no securityContext, topology spread or PDB — the api Deployment has none either; not in the intent
  - `[low]` `reject` unmeasured resources, no auth or rate limit on /mcp, new dependency in the shared image, no job timeout, contract name overstates, regex read of values.yaml, test naming, shared test helper hostname — the plan records measuring for the PR; the rest are outside the intent or cosmetic
  - `[low]` `reject` chart now needs `hostname` or `mcp.hosts` to render — required by the plan (refuse empty hosts); recorded as a residual risk
  - `[false]` `reject` api-down keeps mcp Ready is not observed — the intent's matrix assigns that assertion to story 4.7
  - `[maybe-false]` `reject` non-string or comma-bearing `mcp.hosts` entries, missing `mcp` block in an override — would be low

### 2026-11-11 — Follow-up review pass (thorough)
- verdicts: 23 findings — high 0, medium 3, low 14, false 6, maybe-false 0
- lenses: blind-hunter (10), verification-gap (0), edge-case-hunter (7), intent-alignment (6 descriptive divergences).
- findings:
  - `[low]` `reject` B1: production ApiClient is never explicitly closed — carried: the prior pass rejected this same lifecycle claim; one process-owned pool is reclaimed at process exit. No new pool-lifecycle machinery added.
  - `[low]` `reject` B2: invalid arguments bypass the tool's logging finally block — SDK validation precedes invocation, so rejected arguments do lack this application log. Invalid-call accounting adds instrumentation outside the tool and has negligible impact on this tracer; SDK errors remain observable. Reject the low finding under the complexity rule.
  - `[medium]` `patch` B3: historical logs can satisfy the two-replica assertion — snapshot each pod's call count before issuing the twenty calls and require each count to increase. A regression test proves stale logs alone fail and new calls on both pods pass.
  - `[false]` `reject` B4: twenty random calls can miss one replica and polling adds no traffic — carried: same fixed-count sampling claim as the prior pass's rejected row. Retain the ticket's specified twenty calls and that row's verdict/route; no additional request loop introduced.
  - `[low]` `reject` B5: malformed chart hosts can render invalid routes or a divergent comma-parsed allowlist — helper validation covers empty entries and wildcards, not general DNS syntax. Invalid operator-supplied schemes, ports, paths or whitespace can fail Kubernetes validation; the shipped DNS hostname is valid. General hostname guards add complexity for uncommon malformed configuration; prior host/port concerns remain recorded above.
  - `[low]` `reject` B6: zero, negative or non-finite timeout settings are accepted — requires malformed operator configuration; the shipped setting is 10 seconds. Additional configuration guards are not justified for this low finding; other existing timeout settings follow the same simple settings pattern.
  - `[false]` `reject` B7: a legitimate configured Origin is refused — no Origin is configured or promised by this ticket, and its native MCP client sends none. SDK inspection confirms absent Origin is admitted and nonempty unlisted Origins are intentionally refused. Browser/tunnel client compatibility is not evidence of a failing current caller.
  - `[medium]` `patch` B8: existing layers can import the new apiclient without lint failure — a disposable source-copy experiment demonstrated this for contract/search.py (10 contracts kept). Core, settings and telemetry already fail transitively through contract. Add apiclient to contract's forbidden list and a planted-import regression case, retaining ten contracts.
  - `[low]` `patch` B9: API timeout failure has no tool-surface coverage — parameterize the existing transport-failure test with ReadTimeout, proving isError and one status=error log. This establishes timeout propagation, not a total elapsed-time deadline; error detail refinement belongs to story 4.3.
  - `[low]` `reject` B10: resource sizing remains unmeasured — carried: prior resource-measurement finding remains a recorded residual risk. PR runner measurements are not available in this local review; this pass makes no sizing or CI-performance claim.
  - `[low]` `reject` E1: ports, commas and whitespace in chart hosts can diverge or invalidate routes — same root as B5, same evidence and low-severity complexity rejection; valid shipped values do not encounter it.
  - `[false]` `reject` E2: allowed-host requests with a legitimate Origin receive 403 — same root and refutation as B7: no permitted Origin/current Origin-bearing caller exists in this ticket. Keep the SDK's restrictive origin policy.
  - `[low]` `reject` E3: invalid timeout settings start successfully — same malformed-configuration root and low-severity complexity rejection as B6.
  - `[low]` `reject` E4: a continuously trickling upstream body can exceed the read timeout — httpx timeouts bound inactivity, not total response elapsed time. The internal API returns a finite JSON search response, with no demonstrated trickling endpoint. Adding a total-deadline state machine is not justified by this low finding; story 4.3 owns timeout error behavior.
  - `[low]` `patch` E5: supplied HTTP client is left open by the SDK — installed streamable_http_client only enters clients it creates itself. Make the test helper an async context manager owning both the HTTP and MCP clients, closing them before each asyncio loop exits.
  - `[false]` `reject` E6: all twenty connections can choose one replica — carried: same sampling claim/verdict/route as B4 and the prior log. Keep the prescribed fixed request count.
  - `[low]` `reject` E7: rejected arguments have no ticketscope tool-call record — same root as B2; SDK validation rejects before the function. Reject additional invalid-call instrumentation under the low-severity complexity rule.
  - `[low]` `reject` I1: same-tag restart is only checked by source-text tests — the identified test limitation was real. This pass additionally ran FORCE_BUILD=1 scripts/kind-up.sh, observed both restart branches, compared the old/new pod UID sets (disjoint, two new pods), and checked 2/2 updated and Ready. Behavioral execution supplies the missing evidence; no new implementation is needed.
  - `[medium]` `patch` I2: current twenty calls are not isolated from historical pod logs — grouped with B3; before/after counts and the stale-log regression now establish current-run traffic on both pods.
  - `[low]` `reject` I3: foreign-host Gateway refusal can come from route matching — carried: the prior pass recorded exactly this distinction. The unit test directly establishes the MCP 421 guard, and the Gateway test establishes external refusal, as the ticket requests.
  - `[false]` `reject` I4: API-outage independence is structural/in-process rather than a cluster outage test — carried: the prior pass assigned the cluster outage scenario to story 4.7. The ticket requires process-only probes here, which both chart and in-process tests establish.
  - `[low]` `reject` I5: the old 1,200-line checkpoint estimate was not split — this describes the existing plan's historical route decision, not a broken runtime behavior. The proposed correction edits this build's plan, which the review rules explicitly reject; preserve its recorded interpretation and the completed four-lens independent review. No ticket-tree or status rewrite performed.
  - `[false]` `reject` I6: execution evidence mixes earlier kind runs, later unit-only automation and absent PR CI — these are explicitly different runs, not contradictory claims of one run's evidence. This result records its own exact local commands and retains GitHub CI as unexecuted.

## Design Notes

- Probes on `/healthz` need the SDK host check not to apply to custom routes (kubelet sends the pod IP as `Host`). Verify it; if it does apply, use `tcpSocket` probes.
- Unknown until measured, to record in the PR: `mcp-e2e.yml` wall-clock and peak runner memory with two replicas (test design NFR), and `mcp` resource sizing (start 50m/128Mi, memory limit 256Mi).
- Keep `json_response` at the SDK default; Claude Desktop format questions belong to story 4.2.
- Existing chart tests may render with an empty `hostname`; supply one in their renders rather than weakening the refusal.
- If the SDK needs `initialize` for stateless `tools/call`, that is a finding to resolve against the spec, not to test around.

## Verification

**Commands:**
- `uv sync --locked && uv run ruff check . && uv run ruff format --check . && uv run pyright` -- expected: clean
- `uv run lint-imports` -- expected: 10 contracts kept
- `uv run pytest` -- expected: all pass, including the new unit tests and the updated enforcement test
- `uv run pytest tests/unit/test_chart_mcp.py` -- expected: pass with Helm 4.3.1
- `scripts/kind-up.sh && uv run pytest -m kind tests/mcp` -- expected: pass against local kind (Docker required)

**Manual checks (if no CLI):**
- `kubectl -n ticketscope get deploy ticketscope-mcp` shows 2/2 Ready; scaling `ticketscope-api` to 0 leaves mcp Ready.

## Auto Run Result

Status: built (hand-back only; ticket plan frontmatter status preserved for the orchestrator).
Review: thorough follow-up; four independent lenses; 23 findings individually triaged above. Four patch groups: two medium (current-run replica evidence and contract import guard), two low (timeout-error coverage and test HTTP-client cleanup). No high patches, no deferred items, follow-up review recommended: false on this follow-up pass. All 18 rejected rows retain their reasons above.

**Summary.** Hardened the already-built story 4.1 tracer and incorporated the preceding automation pass's expanded tests. Production MCP/API/chart wiring remains as built; tightened the architecture guard and the evidence that the Gateway test supplies.

**Files changed in this pass.**
- `.importlinter`: forbid contract importing apiclient.
- `tests/unit/test_import_linter_enforcement.py`: plant that forbidden import in a disposable copy.
- `tests/mcp/test_search_tool.py`: own HTTP-client cleanup; compare replica call counts before and after this run's twenty calls.
- `tests/unit/test_mcp_replica_check.py`: prove historical logs cannot satisfy the replica check.
- `tests/unit/test_mcp_server.py`: cover ReadTimeout as a tool error with one error log.
- `tests/unit/test_mcp_expanded.py`, the automation summary and `bmad-build-auto-result-4.1-tea.automate-2.md`: preserve/include the preceding automation pass's 25 tests and provenance.
- This plan: append individual review verdicts and this hand-back; preserve status, intent contract and existing review/deferred records.

**Verification.**
- `uv sync --locked`: passed.
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright`: passed (zero type errors).
- `uv run lint-imports`: 10 contracts kept, 0 broken.
- `uv run pytest`: 1,187 passed, 17 skipped, 61 kind tests deselected; includes expanded MCP tests and the new stale-log/import/timeout regressions.
- `uv run pytest tests/unit/test_chart_mcp.py`: 10 passed with Helm v4.3.1.
- `scripts/kind-up.sh`: passed, 95 seconds; MCP 2/2 Ready.
- `FORCE_BUILD=1 scripts/kind-up.sh`: passed, 38 seconds, same image tag; both api and mcp restart branches executed. Both MCP pod UIDs changed and deployment reported 2/2 updated and Ready.
- `TICKETSCOPE_GATEWAY_URL=http://127.0.0.1:18080 TICKETSCOPE_GATEWAY_HOST=ticketscope.kind.internal uv run pytest -m kind tests/mcp`: six passed after review fixes, and six passed again after same-tag rebuild. The post-rebuild attempt initially failed because the tool session had closed the local port-forward; reran with the Gateway port-forward owned by the test command.
- Both existing deferred-work ledgers compared byte-for-byte against HEAD and were unchanged. No tickets.py mark command ran.

**Residual risks.** The local Apple Silicon Docker VM still requires the pre-existing, cluster-only `OPENSSL_armcap=0` override on MCP. Helm retained that override during both deploys. A direct import of jwt in the freshly built app image without it exited 132 (SIGILL); the successful cluster tests therefore do not prove a clean native-arm64 deployment. No image workaround or unrelated dependency change was committed. GitHub Actions/amd64 CI has not run in this session, and PR peak-memory/resource-sizing measurements remain outstanding. The prescribed fixed twenty-request replica sample can still be unlucky; this pass preserves the prior triage decision and now refuses to count historical traffic. The orchestrator owns final verification, ticket status and ledger resolutions.
