---
title: 'One MCP tool call yields one trace in Tempo'
type: 'feature'
ticket: 5
created: '2026-11-11'
status: done
baseline_revision: 'd0aff5bf236cfa3317be92eccf2ad30196926ae9'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/test-design-epic-4.md'
warnings: []
deferred: []
---

<intent-contract>

## Intent

**Problem:** `ticketscope-mcp` exports no traces, and its HTTP calls to `api` carry no trace context, so an MCP tool call is not one trace from the tool call through `api`, retrieval and the database (R5).

**Approach:** `mcp`'s `main` sets up OTLP telemetry as `ticketscope-mcp`; the `mcp` SDK already emits the SERVER `tools/call {tool}` span (and continues `_meta.traceparent`), so the story pins its attribute keys in one constants list, adds the query-text opt-in, and makes `apiclient` open the CLIENT span and inject `traceparent` itself. A kind check finds the trace in Tempo.

## Boundaries & Constraints

**Always:** `service.name` is `ticketscope-mcp`; OTLP export to `settings.otlp_endpoint` only (empty creates no exporter); semconv opt-in set (`telemetry.set_semconv_opt_in`). The tool span is the SDK's `OpenTelemetryMiddleware` span (SERVER, `tools/call {tool}`, `mcp.method.name`, `gen_ai.operation.name=execute_tool`, `gen_ai.tool.name`, status ERROR on `is_error`); do not open a second tool span. `apiclient` opens a CLIENT span named by the HTTP method (`POST`/`GET`) with HTTP semconv attributes (`http.request.method`, `url.full` without query, `server.address`, `server.port`, `http.response.status_code`; status ERROR and `error.type` on a transport failure or a 5xx), and injects `traceparent` from the current context in an `httpx2` request event hook (C-1: the httpx instrumentor was tried on an `httpx2` client and yields no span and no header, so it is not added). `mcp` continues `_meta.traceparent` only; an HTTP `traceparent` header on `/mcp` is ignored (C-3; no ASGI instrumentation on `mcp`). Query text goes on the tool span (`ticketscope.query.text`) only when `settings.trace_query_text` is true. One constants list names the tool span's attribute keys and cites the semconv version in use (R-010); a test equals the emitted keys to it. `mcp` still creates no psycopg instrumentation and no DB connection. Import-linter passes: `mcp`/`apiclient` import only `contract`, `apiclient`, `settings`, `telemetry`.

**Never:** Touch `tests/smoke/` (the Tempo helper lives in `tests/mcp/`), the captured Claude Desktop requests or their pin test, `eval/baseline.json`, the tool names or outputs, or chart readiness probes. No query text on any span by default. Do not add `opentelemetry-instrumentation-httpx`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Plain call | `search_similar_issues` over `/mcp`, no `_meta` trace | SERVER `tools/call search_similar_issues` is the root; CLIENT `POST` is its child; the fake `/v1` sees `traceparent` with the tool span's trace id and the CLIENT span's id | No error |
| `_meta` context | `_meta.traceparent` set | tool span has that trace id and parent span id | malformed `_meta.traceparent` starts a new trace, no error |
| Header and `_meta` | HTTP `traceparent` X and `_meta.traceparent` Y differ | tool span is in trace Y | none |
| Tool error | unknown mode (API 422) or unknown key | tool span status ERROR, `gen_ai.tool.name` present | tool error as before |
| API unreachable | transport error | CLIENT span status ERROR with `error.type`; tool error as before | tool error as before |
| get_issue | `get_issue` call | own trace: tool span, CLIENT `GET`; `api` has `GET /v1/issues/by-key/{key}` | none |
| Query text | `trace_query_text` false (default) / true | no span carries the query / tool span has `ticketscope.query.text` | none |
| No endpoint | `otlp_endpoint` empty | no exporter is created | none |

</intent-contract>

## Code Map

- `src/ticketscope/mcp/main.py` -- composition root; currently calls only `telemetry.configure_logging()` and its docstring says tracing is this story. Call telemetry setup with `SERVICE_MCP` and `settings.otlp_endpoint`, and pass `settings.trace_query_text` to the server.
- `src/ticketscope/telemetry.py` -- `setup()` also instruments psycopg; add a way to set up without it (e.g. `instrument_db: bool = True`). Has `SERVICE_MCP`, `tracer_provider`, `get_tracer`, `set_semconv_opt_in`. Must not import any other `ticketscope` layer (import-linter).
- `src/ticketscope/mcp/server.py` -- `build_server(client)`/`build_app(settings, client)`; the tool functions; add the query-text opt-in on `trace.get_current_span()` (the SDK's tool span is current inside the tool). The SDK middleware is `mcp/server/_otel.py` in the installed package (`OpenTelemetryMiddleware`, on by default; tracer name `mcp-python-sdk`, global provider).
- `src/ticketscope/mcp/spans.py` (new) -- the constants list of the tool span's attribute keys (`mcp.method.name`, `mcp.protocol.version`, `jsonrpc.request.id`, `gen_ai.operation.name`, `gen_ai.tool.name`, plus `error.type` on errors and `ticketscope.query.text` when opted in), citing the semconv version/spec date; record whether the AD-10 open question (GenAI semconv drift) was revisited, in Implementation Notes.
- `src/ticketscope/apiclient/__init__.py` -- `ApiClient._send` wraps every call; open the CLIENT span there, and give the `httpx2.AsyncClient` an `event_hooks={"request": [...]}` that injects `traceparent` with `opentelemetry.propagate.inject`. Error mapping stays unchanged.
- `tests/mcp/test_search_tool.py` -- kind client test pattern (`_client`, `_gateway`, `eventually`). `tests/smoke/test_gateway.py:616-745` -- the Tempo pattern to copy (`_attributes`, `_spans`, `_kind`, `_tempo` via `kubectl get --raw .../services/tempo:3200/proxy`); copy, do not import or edit.
- `tests/unit/test_mcp_server.py`, `tests/unit/test_apiclient.py`, `tests/unit/test_telemetry.py` -- in-process patterns (`httpx2.MockTransport`, `ASGITransport`, `InMemorySpanExporter`).
- `deploy/charts/ticketscope/templates/mcp.yaml` -- already sets the OTLP endpoint and `TICKETSCOPE_TRACE_QUERY_TEXT`; check it needs no change.
- `.github/workflows/mcp-e2e.yml` -- already runs `pytest -m kind tests/mcp`; the new kind test file is picked up.

## Tasks & Acceptance

**Execution:**
- [x] `src/ticketscope/telemetry.py`, `src/ticketscope/mcp/main.py` -- set up telemetry as `ticketscope-mcp` without psycopg; update the docstring -- R5 export
- [x] `src/ticketscope/apiclient/__init__.py` -- CLIENT span and `traceparent` injection via request event hook -- C-1
- [x] `src/ticketscope/mcp/spans.py`, `src/ticketscope/mcp/server.py` -- constants list citing the semconv version; `ticketscope.query.text` only when opted in -- R-010, AD-10
- [x] `tests/unit/` -- in-memory exporter tests per the matrix: tool span shape and key equality to the list, `traceparent` captured on `apiclient`'s outgoing request equal to the tool span's trace id and the CLIENT span's id, `_meta` continuation, malformed `_meta`, header vs `_meta`, ERROR on tool error and on unreachable API, query text off/on, empty endpoint creates no exporter, `get_issue` trace -- R5
- [x] `tests/mcp/tempo.py` (helper) with a unit test on recorded Tempo bodies (base64 and hex span ids, string `intValue`) -- R-008; `tests/mcp/test_trace.py` (kind) -- one at a time: `search_similar_issues` mode=hybrid, TraceQL `{resource.service.name="ticketscope-mcp" && name="tools/call search_similar_issues"}` within the call's start/end (C-2), assert the root is that span and beneath it CLIENT `POST`, api `POST /v1/search`, `retrieval hybrid`, `embeddings {model}` and a db CLIENT span, parent ids chained; a `_meta.traceparent` call lands in that trace id; header plus `_meta` with different ids lands in `_meta`'s; unknown mode gives ERROR; `get_issue` (key from a search result) gives its own trace with CLIENT `GET` and api `GET /v1/issues/by-key/{key}`; no span carries the query; tool span keys equal the constants list -- R5

**Acceptance Criteria:**
- Given a `search_similar_issues` call with no caller context, when the trace is read from Tempo on kind, then one trace has the `ticketscope-mcp` tool span as its root with the CLIENT `POST`, `api`'s `POST /v1/search`, `retrieval hybrid`, `embeddings {model}` and the db query beneath it.
- Given `_meta.traceparent` (alone, or with a different HTTP `traceparent`), when a tool is called, then the tool span's trace id is the `_meta` one.
- Given a tool error, when the span is read, then its status is ERROR; and `get_issue` yields its own trace the same way.
- Given default settings, when any tool is called, then no span carries query text, and the tool span's attribute keys equal the constants list.
- Given `apiclient` in a unit test, when it sends a request inside a tool span, then the outgoing `traceparent` carries the tool span's trace id.
- Given the existing suite, when run (`pytest`, `lint-imports`, ruff, pyright), then it passes, including the Claude Desktop replay and captured-pin tests.

## Implementation Notes

- AD-10 open question (GenAI semconv drift) revisited: `mcp/spans.py` pins the tool-span keys as emitted by `mcp` 2.3.0 (semconv schema 1.44.0 in `opentelemetry-semantic-conventions` 0.66b2). The retrieval span's `ticketscope.retrieval.k` versus `gen_ai.retrieval.top_k` drift is unchanged and stays open for epic 7.
- `mcp/main.py` calls `telemetry.setup(SERVICE_MCP, otlp_endpoint, instrument_db=False)`; the chart already sets the OTLP endpoint and `TICKETSCOPE_TRACE_QUERY_TEXT`, so it needed no change.
- The kind tests in `tests/mcp/test_trace.py` were run by the orchestrator on the local kind cluster after `FORCE_BUILD=1 scripts/kind-up.sh`: first runs exposed three test-side faults (other tests' traces inside the second-granular window, Tempo's search `limit` of 20 crowding out the new trace, and Tempo v2 answering 200 with an empty trace for an unknown id). Fixed in `tests/mcp/tempo.py` (nanosecond `since_ns` filter, limit 200) and `tests/mcp/test_trace.py`; two consecutive full `tests/mcp` runs then passed (26 passed).
- `story-4-5` was behind `main` (story 4.4 was not on it); the branch had no unique commits, so it was fast-forwarded to `main` before planning.

## Plan Change Log

## Review Triage Log

### 2026-11-11 — Review pass
- verdicts: 5 findings — high 0, medium 1, low 3, false 0, maybe-false 0 (one finding is plan bookkeeping, rejected)
- findings:
  - `[medium]` `[patch]` kind trace tests' second-granular window can include other calls' traces — confirmed on the cluster (20 matches); fixed with a nanosecond `since_ns` filter in `tests/mcp/tempo.py`, and a search limit of 200
  - `[low]` `[patch]` unknown-key tool error has no unit test — added `test_an_api_404_for_an_unknown_key_sets_error_status_on_the_tool_span`
  - `[low]` `[patch]` new tests lack `criterion` markers — added module-level markers (`ticketscope--e4-s5--AC-1..5`)
  - `[low]` `[reject]` kind tests do not assert error-path attribute keys — the unit test `test_an_api_422_sets_error_status_on_the_tool_span` asserts them; a second check adds nothing
  - `[low]` `[reject]` plan status and checkboxes — plan bookkeeping, updated at finalize, not a code defect

### 2026-11-11 — Follow-up review pass
- verdicts: 0 findings — high 0, medium 0, low 0, false 0, maybe-false 0
- findings: none from the Quick lens, including the expanded trace tests.
- Verification correction: Pyright rejected `type[Exception]` for the test factory's `request` keyword. Narrowed it to `type[httpx2.RequestError]`; all four expanded tests and Pyright pass.

## Design Notes

C-1 result (checked 2026-11-11 with `opentelemetry-instrumentation-httpx==0.66b2` against an `httpx2.AsyncClient` over `MockTransport`): zero spans and no `traceparent`, so the fallback applies. The SDK's own span already satisfies the tool-span rows, which is why this story adds a constants list and tests rather than a span wrapper. A probe in process confirmed a `_meta.traceparent` wins over a different HTTP `traceparent` header.

## Verification

**Commands:**
- `uv run pytest` -- expected: pass (kind tests excluded by default)
- `uv run pytest -m kind tests/mcp --collect-only -q` -- expected: collects, no import errors (also run for real: see Implementation Notes)
- `uv run lint-imports` -- expected: all contracts kept
- `uv run ruff check . && uv run ruff format --check . && uv run pyright` -- expected: clean
- `python3 scripts/render_readme_table.py --check` -- expected: pass

## Auto Run Result

**Status:** built; ticket and plan status remain owned by the orchestrator. No `tickets.py mark` was run.

**Summary:** Follow-up Quick review of the existing MCP telemetry implementation and expanded trace tests found no defects. The implementation exports `ticketscope-mcp` tool spans, propagates context through the apiclient CLIENT span, continues MCP `_meta.traceparent`, and records query text only with the existing opt-in. Corrected the expanded test exception-factory annotation so Pyright accepts the `request` keyword.

**Files changed in this pass:**
- `tests/unit/test_mcp_trace_expanded.py` — retained four automation tests for main telemetry setup, invalid settings, timeout and transport-error spans; narrowed the exception-factory type to `httpx2.RequestError`.
- `_bmad-output/test-artifacts/automate/automation-summary-story-ticketscope--e4-s5.md` — retained automation coverage and outcome report; aligned application wording with repository instructions.
- `_bmad-output/initiative-ticketscope/bmad-build-auto-result-4.5-tea.automate-1.md` — retained the preceding automation run's result artifact.
- This plan — recorded follow-up triage and verification, preserving its built status.

**Review:** Quick lens: zero findings, zero patches from review, zero deferrals, zero rejected findings. Verification found and corrected one test annotation error. Existing deferred-work ledger entries were untouched.

**Follow-up review recommended:** false; patched review counts: high 0, medium 0, low 0.

**Verification:** `uv run pytest`: 1341 passed, 36 skipped, 81 deselected. Container tests skipped because no test image was configured. `uv run lint-imports`: 10 contracts kept. Ruff check and formatting check passed; Pyright passed after the annotation correction, as did all four expanded tests. `python3 scripts/render_readme_table.py --check` passed. Kind collection found 26 MCP tests. The first kind invocation failed because Gateway environment variables were missing; after setting `TICKETSCOPE_GATEWAY_URL=http://127.0.0.1:18080` and `TICKETSCOPE_GATEWAY_HOST=ticketscope.kind.internal` for the existing local Gateway, all 26 tests passed in 108.11 seconds, including the Claude Desktop replay and all five Tempo checks. CI itself was not dispatched.

**Residual risks:** Tempo checks depend on ingestion latency; the SDK attribute-key contract is pinned and tested. Container-specific checks were not executed in this pass. No human decision is needed for this hand-back.
