---
title: 'One search request yields one trace in Tempo'
type: 'feature'
ticket: '9'
created: '2026-11-07'
status: done
baseline_revision: 'ffe83d9750ca56c5a632071ed0fc7f6d8a69416a'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md'
warnings: [oversized]
deferred: []
operator_actions:
  - "Port-forward Grafana (kubectl -n platform port-forward svc/grafana 3000:80), sign in with the admin credentials from the platform/grafana Secret, open Explore on the Tempo datasource, look up the trace id from smoke test (8) (or any recent POST /v1/search trace), and confirm it shows the ticketscope-api SERVER span, then retrieval keyword, then the psycopg db query span."
---

<intent-contract>

## Intent

**Problem:** Nothing emits or collects traces, so R6 ("one search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo") is unmet. AD-10 fixes the span tree, names and attributes; AD-11 puts the OTel Collector, Tempo and Grafana in the `platform` release.

**Approach:** Add `ticketscope.telemetry` (service names, the semconv opt-in, OTLP/HTTP export, JSON logs with `trace_id`/`span_id`). `api` instruments FastAPI (SERVER span) and psycopg (CLIENT span) and wraps every retrieval call, for `/v1/search` and the page, in an INTERNAL `retrieval {mode}` span. `migrate` and `load` export as `ticketscope-jobs`. The platform chart gains the collector, Tempo and Grafana with a Tempo datasource. A new `kind` smoke test sends one `POST /v1/search` with a known `traceparent` and asserts the AD-10 tree through the Tempo API and through Grafana's Tempo datasource.

## Boundaries & Constraints

**Always:**
- `service.name` is exactly `ticketscope-api` or `ticketscope-jobs`. Every process sets `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental,database,http` (in `os.environ`, before any instrumentor is created), from one constant in `telemetry`.
- Retrieval span: name `retrieval {mode}` (e.g. `retrieval keyword`), kind INTERNAL, child of the SERVER span, parent of the psycopg search span. Attributes: `gen_ai.operation.name=retrieval`, `gen_ai.data_source.id=ticketscope-mojang-jira` (spine AD-10; the test design's older `ticketscope-k8s-issues` is superseded), `ticketscope.retrieval.mode`, `ticketscope.retrieval.k`, `ticketscope.corpus.version`, `ticketscope.result.count`. An exception sets status ERROR.
- Query text never appears on a span unless `TICKETSCOPE_TRACE_QUERY_TEXT=true`; then the retrieval span carries `ticketscope.query.text`. This includes the SERVER span's `url.query` on `GET /?q=…` (redact it via the FastAPI `server_request_hook` when not opted in). psycopg spans must not capture parameters.
- Custom attributes live only under `ticketscope.*`. Export is OTLP to the in-cluster collector only; with an empty `TICKETSCOPE_OTLP_ENDPOINT`, no exporter is created (local runs, unit tests, person-run ingest).
- Logs from `api`, `migrate` and `load` are JSON lines with `ts`, `level`, `logger`, `message`, `trace_id`, `span_id` (32/16 hex, or null outside a span), and `exception` when present. Existing message text is unchanged, so `load report:`, `no-op` and `reloading` still appear verbatim.
- `/healthz` and `/readyz` are not traced. ASGI `receive`/`send` sub-spans are excluded.
- `telemetry` imports no `ticketscope` layer; `core` and `contract` never import `opentelemetry` (import-linter + the existing AST allow-list).
- Platform chart values: defaults in `values.yaml`; `values-kind.yaml` only gains environment facts if any are needed (AD-25). Grafana, Tempo and the collector get no HTTPRoute, Ingress or LoadBalancer (AD-14). Grafana's admin password is chart-generated, never in values or git.
- Small resource requests and limits on all three, sized for the GitHub-hosted runner.

**Never:**
- No metrics pipeline, Prometheus, `spanmetrics` connector or dashboard (epic 7). No OTel logs pipeline (AD-11: traces only). No MCP spans (epic 4). No embeddings span (epic 3).
- No change to `core` retrieval logic, the `/v1` contract or bodies, the page HTML, migrations, or `jobs/ingest`.
- No `OTEL_*` variable read by our code other than the opt-in we set (config convention: `TICKETSCOPE_*`).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Search traced | `POST /v1/search` keyword on the fake, in-memory exporter | SERVER `POST /v1/search` → INTERNAL `retrieval keyword` with all six AD-10 attributes, `ticketscope.result.count` = len(results); resource `service.name=ticketscope-api` | — |
| Page traced | `POST /` with `q` | a `retrieval keyword` span under the SERVER span, k=10 | — |
| No query text | default settings, `POST /v1/search` and `GET /?q=secretword` | no span attribute value contains `secretword`; `url.query` absent or redacted | — |
| Opt-in | `trace_query_text=True` | retrieval span has `ticketscope.query.text` = the query | — |
| Store raises | `_BrokenStore` | retrieval span status ERROR; response unchanged (problem+json 500 / HTML 500) | exception recorded on span |
| Probes | `GET /healthz`, `/readyz` | no span exported | — |
| Log in span | a log line emitted inside a span | JSON with that span's `trace_id`/`span_id` | — |
| No endpoint | `otlp_endpoint=""` | no exporter, no network attempt, app works | — |
| Tempo E2E | one `POST /v1/search` through the Gateway with `traceparent: 00-<tid>-<sid>-01` | Tempo `GET /api/v2/traces/<tid>` returns ticketscope-api SERVER → `retrieval keyword` → psycopg CLIENT (`db.system.name=postgresql`) | poll ≤ 60 s, fail with the last response |

</intent-contract>

## Code Map

- `pyproject.toml` / `uv.lock` -- add runtime deps `opentelemetry-sdk~=1.45.2`, `opentelemetry-exporter-otlp-proto-http~=1.45.2`, `opentelemetry-instrumentation-fastapi~=0.66b2`, `opentelemetry-instrumentation-psycopg~=0.66b2` (Stack: sdk 1.45, instrumentation ≥ 0.66b2). HTTP exporter, not gRPC (lighter image). `uv lock`.
- `src/ticketscope/telemetry.py` -- NEW, cross-cutting like `settings.py`. Suggested surface: `SEMCONV_OPT_IN`, `DATA_SOURCE_ID`, `SERVICE_API`, `SERVICE_JOBS`; `setup(service_name, otlp_endpoint) -> TracerProvider` (sets the opt-in env, builds the provider with `Resource({"service.name": …})`, adds `BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces"))` only when the endpoint is non-empty, sets it global, instruments psycopg once, installs JSON logging); `configure_logging()` (JSON handler on root only when root has no handlers — same rule as `basicConfig`, so pytest's caplog keeps working); `JsonFormatter`; `instrument_app(app, tracer_provider, record_query_text)` (FastAPIInstrumentor.instrument_app with `excluded_urls="healthz,readyz"`, `exclude_spans=["receive","send"]`, and a `server_request_hook` that removes/redacts `url.query` unless opted in); `retrieval_span(tracer, mode, k, corpus_version, query, record_query_text)` context manager yielding something to set `ticketscope.result.count`.
- `src/ticketscope/settings.py` -- add `otlp_endpoint: str = ""` and `trace_query_text: bool = False`.
- `src/ticketscope/http/app.py` -- `create_app(store, settings, tracer_provider=None)`: instrument the app, get a tracer, and wrap the retrieval call in `search()` and in `render_page()` with `retrieval_span` (after `corpus_version()`, so the version is an attribute; the version query's own db span sits under SERVER, which is fine). `main()`: `telemetry.setup(SERVICE_API, settings.otlp_endpoint)` before `uvicorn.run(..., log_config=None)` so uvicorn logs go through the JSON root handler. Keep all existing behaviour and error handling.
- `src/ticketscope/jobs/load/main.py`, `jobs/migrate/main.py` -- replace `logging.basicConfig(...)` with `telemetry.setup(SERVICE_JOBS, settings.otlp_endpoint)`; wrap the job body in one INTERNAL span (`load` / `migrate`) and `provider.shutdown()` in `finally` to flush. Return codes and messages unchanged. Note load creates `Settings()` after basicConfig today; reorder as needed.
- `.importlinter` -- add `opentelemetry` to the `core` and `contract` forbidden lists; add a `telemetry` contract forbidding `ticketscope.contract/core/adapters/http/jobs/settings`.
- `deploy/charts/platform/Chart.yaml` + `Chart.lock` -- dependencies: `opentelemetry-collector` 0.178.2 (`https://open-telemetry.github.io/opentelemetry-helm-charts`, alias `otel-collector`), `tempo` 3.2.1 (`https://grafana-community.github.io/helm-charts`, app 3.1.1), `grafana` 14.4.0 (same repo, app 13.3.0) — the grafana-community repo is where Tempo 3.1 / Grafana 13.3 (Stack) are published. Each with `condition: <name>.enabled`. Update the description.
- `deploy/charts/platform/values.yaml` -- collector: `mode: deployment`, `image.repository: otel/opentelemetry-collector-contrib`, `image.tag: "0.164.0"` (Stack pin; chart appVersion is 0.163.2), `fullnameOverride: otel-collector`, ports: only `otlp` and `otlp-http` enabled (disable jaeger*, zipkin), `alternateConfig` (subchart null-removal bug): receivers otlp grpc+http on `${env:MY_POD_IP}`, processors `memory_limiter` + `batch`, exporter OTLP gRPC to `tempo.platform.svc:4317` insecure (check the exporter's component name in 0.164 — `otlp` vs `otlp_grpc` — from the collector's startup log), `health_check` extension, one `traces` pipeline. Tempo: `fullnameOverride: tempo`, `tempo.reportingEnabled: false`, `retention` short (e.g. 24h), no persistence. Grafana: `fullnameOverride: grafana`, no persistence, `datasources` provisioning one `type: tempo` datasource, `uid: tempo`, `url: http://tempo.platform.svc:3200`, default; admin password left to the chart's generated Secret.
- `scripts/kind-up.sh`, `.github/workflows/ci.yml` (`charts` job) -- `helm repo add open-telemetry …` and `helm repo add grafana-community …` before `dependency build`.
- `deploy/charts/ticketscope/values.yaml` -- `telemetry: {otlpEndpoint: "http://otel-collector.platform.svc:4318", recordQueryText: false}` (same in every environment: the platform release is identical, AD-13). `templates/api.yaml` and `templates/jobs.yaml` -- env `TICKETSCOPE_OTLP_ENDPOINT` on api, migrate and load; `TICKETSCOPE_TRACE_QUERY_TEXT` on api.
- `.github/workflows/_kind-deploy.yml` -- nothing required (platform pods are already logged in Diagnostics).
- `tests/smoke/test_gateway.py` -- add section (8) at the end and update the docstring. Reuse `_gateway()`, `_kubectl` style, `PLATFORM_NAMESPACE`. Tempo via the API-server service proxy: `kubectl get --raw /api/v1/namespaces/platform/services/tempo:3200/proxy/api/v2/traces/<tid>`. Grafana via a `kubectl port-forward svc/grafana` subprocess, admin creds from the `grafana` Secret, `GET /api/datasources/proxy/uid/tempo/api/v2/traces/<tid>`. Tempo JSON span ids may be base64 or hex: compare ids as returned within one response.
- `tests/unit/test_app.py` -- has the `client` fixture and `_BrokenStore`; reuse. `tests/unit/test_layer_imports.py` -- core/contract allow-list already blocks opentelemetry; keep green.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock` -- OTel runtime deps -- AD-10, Stack
- [x] `src/ticketscope/telemetry.py`, `src/ticketscope/settings.py`, `.importlinter` -- setup, JSON logs, retrieval span, app instrumentation, layer rule -- AD-10, Logging convention
- [x] `src/ticketscope/http/app.py` -- instrumented app, retrieval spans for `/v1/search` and the page, JSON logging in `main` -- AD-10
- [x] `src/ticketscope/jobs/load/main.py`, `src/ticketscope/jobs/migrate/main.py` -- `ticketscope-jobs` tracing and JSON logs -- AD-10
- [x] `deploy/charts/platform/{Chart.yaml,Chart.lock,values.yaml}`, `scripts/kind-up.sh`, `.github/workflows/ci.yml` -- collector, Tempo, Grafana with Tempo datasource -- AD-11, AD-13, AD-14
- [x] `deploy/charts/ticketscope/{values.yaml,templates/api.yaml,templates/jobs.yaml}` -- OTLP endpoint and opt-in env -- AD-25
- [x] `tests/unit/test_telemetry.py` (new) -- every unit-level I/O matrix row with an `InMemorySpanExporter` + `SimpleSpanProcessor` provider passed to `create_app`; JSON log line inside a span; `setup` sets the opt-in env and creates no exporter without an endpoint; jobs `main` emits a `ticketscope-jobs` span (monkeypatched DB calls, as `test_load_main.py` does)
- [x] `tests/unit/test_chart_telemetry.py` (new, `helm template`, skip when helm or the platform `charts/*.tgz` are absent, like `test_chart_backup.py`) -- platform renders the collector (contrib 0.164.0, OTLP exporter to Tempo), Tempo, Grafana with a `tempo` datasource, and no HTTPRoute/Ingress/LoadBalancer for them; ticketscope renders `TICKETSCOPE_OTLP_ENDPOINT` on api, migrate and load. Add it to the `charts` job's pytest line in `ci.yml`.
- [x] `tests/smoke/test_gateway.py` -- (8) `test_one_search_yields_one_trace_in_tempo`: POST `/v1/search` (keyword, a golden query) with a fresh `traceparent`; poll Tempo for that trace id (≤ 60 s); assert a `ticketscope-api` SERVER span named `POST /v1/search`, an INTERNAL `retrieval keyword` child of it with the AD-10 attributes (`ticketscope.corpus.version` == pin, `ticketscope.result.count` ≥ 1) and no attribute containing the query, and a CLIENT span with `db.system.name=postgresql` whose parent is the retrieval span. (8b) the same trace id is returned through Grafana's Tempo datasource proxy.

**Acceptance Criteria:**
- Given the kind cluster from `scripts/kind-up.sh` on this branch, when `uv run pytest -m kind tests/smoke` runs, then every test passes, including (8) and (8b).
- Given the repo, when `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` runs, then all pass, including `test_telemetry.py`.
- Given the api pod on kind, when `kubectl -n ticketscope logs deploy/ticketscope-api` is read after a search, then each line is a JSON object, and the lines logged during the request carry the trace's `trace_id`.
- Given Grafana port-forwarded (`kubectl -n platform port-forward svc/grafana 3000:80`), when the trace id from (8) is opened in Explore on the Tempo datasource, then the same span tree is shown (manual, human-visual).

## Implementation Notes

- Store-raises row: `_BrokenStore` fails `corpus_version()` before any retrieval span opens, so `test_telemetry.py` uses `_SearchBrokenStore` (version ok, search raises) for both `/v1/search` (problem+json 500) and the page (HTML 500).
- Collector exporter is `otlp_grpc` (0.164's component list; `otlp` still validates as an alias). Config validated with `otelcol-contrib validate`.
- Tempo keeps the chart's default jaeger receivers/ports (ClusterIP only): setting `tempo.tempo.receivers.jaeger: null` breaks the subchart's `_ports.tpl`.
- `.importlinter`: jobs contract ignores `ticketscope.telemetry -> fastapi` (a `TYPE_CHECKING`-only import for `instrument_app`'s annotation); `FastAPIInstrumentor` and the OTLP exporter are imported lazily so jobs never load fastapi.
- Probe exclusion is `/healthz$,/readyz$` (matched on scheme://host/path), so a search for "healthz" is still traced.
- Kind run: (3) failed once after the in-place `kind-up` upgrade (no-op load, the known deferred ordering issue); after a forced reload it passes with JSON log lines. (8) and (8b) pass.

## Plan Change Log

## Review Triage Log

### 2026-11-07 — Review pass
- verdicts: 4 findings — high 0, medium 1, low 3, false 0, maybe-false 0
- findings:
  - `[medium]` `[patch]` `/readyz` still exported spans. The probe's `corpus_version()` psycopg query made a parentless `SELECT` CLIENT trace every 5 s; Tempo search on kind confirmed root `SELECT` traces from `ticketscope-api`, against the "Probes → no span exported" matrix row. Fixed: `telemetry.untraced()` (wrapping `suppress_instrumentation`) around the readyz `corpus_version()` call, plus `test_readyz_db_work_is_untraced`. Re-checked on kind after a rebuild: no `ticketscope-api` traces in a 40 s window of probes.
  - `[low]` `[patch]` On its deadline branch, `_grafana` read stderr from a live `kubectl port-forward`, so (8b) would hang instead of failing. Fixed: terminate first, then `communicate(timeout=10)`.
  - `[low]` `[patch]` In `_poll_trace`, `json.loads` sat outside the `try`, so a 200 that was not JSON stopped polling at once. Fixed: moved inside the `try`.
  - `[low]` `[reject]` Existing `load.main()` unit tests run the real `telemetry.setup` (psycopg instrumented for the session, the global provider set, an exporter if `TICKETSCOPE_OTLP_ENDPOINT` is set in the shell). Rejected: the suite stays green, the network case needs a deliberately set env var (the same exposure every `Settings()` env var already has), and the fix adds a new session-wide fixture rather than correcting a line.

## Design Notes

- **Why the retrieval span lives in `http`, not `core`.** AD-1 keeps `core` to stdlib + pydantic, and eval (epic 2) calls `core` directly without spans. `telemetry.retrieval_span` wraps `mode.build(corpus).search(...)` at the two call sites in `app.py`; epic 4/3 reuse the same helper.
- **Why a caller-chosen `traceparent` in the smoke test.** It makes the trace id known, so the test fetches exactly one trace by id instead of searching a time window shared with probes and other tests. Envoy Gateway without tracing configured forwards the header unchanged. The SERVER span then has a remote parent that is not in Tempo, which is also the shape of the full AD-10 demo (the parent is the mcp CLIENT span).
- **Why OTLP/HTTP on 4318.** One fewer native dependency (no grpcio) in the app image; the collector receives both.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts --force-update && helm repo add grafana-community https://grafana-community.github.io/helm-charts --force-update && helm dependency build deploy/charts/platform && helm lint deploy/charts/platform -f deploy/charts/platform/values-kind.yaml && uv run pytest tests/unit/test_chart_backup.py tests/unit/test_chart_telemetry.py` -- expected: no lint errors, tests pass (not skipped)
- `FORCE_BUILD=1 scripts/kind-up.sh`, then `kubectl -n ticketscope rollout restart deploy/ticketscope-api && kubectl -n ticketscope rollout status deploy/ticketscope-api`, then with the printed `TICKETSCOPE_GATEWAY_URL`/`TICKETSCOPE_GATEWAY_HOST` exported, `uv run pytest -m kind tests/smoke` -- expected: all pass, including (8) and (8b). If (3) fails right after an in-place upgrade, it is the known deferred ordering issue: rerun once.

**Manual checks (if no CLI):**
- Grafana Explore via port-forward shows the trace from (8) with the SERVER → retrieval → db tree (operator).

## Auto Run Result

Status: awaiting-operator

**Summary.** One search request now yields one AD-10 trace in Tempo. New `ticketscope.telemetry` sets the semconv opt-in, the service names (`ticketscope-api`, `ticketscope-jobs`), OTLP/HTTP export to the in-cluster collector (none when no endpoint is set) and JSON logs with `trace_id`/`span_id`. api instruments FastAPI (SERVER; probes and ASGI sub-spans excluded, `url.query` redacted unless opted in) and psycopg (CLIENT, no parameters). It wraps the retrieval in both `/v1/search` and the page in an INTERNAL `retrieval {mode}` span with the six AD-10 attributes; query text is recorded only with `TICKETSCOPE_TRACE_QUERY_TEXT=true`. migrate and load each emit one `ticketscope-jobs` span. The platform release adds the OTel Collector (contrib 0.164.0, traces only), Tempo 3.1 and Grafana 13.3 with a provisioned Tempo datasource. None of the three is exposed, and Grafana's admin password is chart-generated.

**Files changed:**
- `pyproject.toml`, `uv.lock`: OTel SDK 1.45.2, the OTLP/HTTP exporter, and the FastAPI and psycopg instrumentations 0.66b2.
- `src/ticketscope/telemetry.py` (new): setup, JSON formatter, app instrumentation, retrieval, job and untraced helpers.
- `src/ticketscope/settings.py`: `otlp_endpoint`, `trace_query_text`.
- `src/ticketscope/http/app.py`: instrumented app, retrieval spans, untraced readiness check, JSON logging in `main`.
- `src/ticketscope/jobs/load/main.py`, `jobs/migrate/main.py`: jobs telemetry and one span each; behaviour unchanged.
- `.importlinter`: opentelemetry is forbidden in core and contract; new telemetry contract.
- `deploy/charts/platform/{Chart.yaml,Chart.lock,values.yaml}`: collector, Tempo and Grafana.
- `deploy/charts/ticketscope/{values.yaml,templates/_helpers.tpl,api.yaml,jobs.yaml}`: OTLP endpoint and query-text opt-in env.
- `scripts/kind-up.sh`, `.github/workflows/ci.yml`: the two new Helm repos; the chart telemetry tests run in the `charts` job.
- `tests/unit/test_telemetry.py`, `tests/unit/test_chart_telemetry.py` (new); `tests/smoke/test_gateway.py`: (8) the Tempo trace tree, (8b) the same trace through Grafana's Tempo datasource.

**Review findings (quick lens, one pass).** 3 patches applied (medium: readiness probe traces; low: the `_grafana` hang, `_poll_trace` JSON). Nothing deferred. 1 low finding rejected: unit tests run the real telemetry setup (suite green, the network case needs a deliberately set env var, the fix adds a session-wide fixture).

**Follow-up review recommended:** false. Patched by verdict: high 0, medium 1, low 2.

**Verification:**
- ruff, ruff format, pyright, lint-imports (7 contracts kept) and pytest: 646 passed, 1 xfailed.
- `helm lint` on the platform chart with `values-kind.yaml` is clean; chart render tests: 15 passed, none skipped.
- Local kind (colima): `FORCE_BUILD=1 scripts/kind-up.sh` and the full smoke suite gave 21/22. The one failure was (3), the known deferred no-op-after-upgrade ordering issue, which passed after a forced reload. After the review patches, the api image was rebuilt and reloaded: (8) and (8b) pass, and Tempo held no probe traces.
- api logs on kind are JSON lines; the request's access log line carries its trace's `trace_id`.
- Not run: `_kind-deploy` on a PR. The orchestrator owns the PR.

**Operator actions owed:** the Grafana Explore check (AC 4) is a human visual check; see `operator_actions` in the frontmatter.

**Residual risks:**
- The GitHub-hosted runner's fit with three more pods (about 320 Mi requested, about 1.1 Gi in limits) is unmeasured until the first `_kind-deploy`; its runner-fit summary records peak memory.
- Smoke (3) still fails after an in-place upgrade; (6b)'s upgrade also leaves a no-op load (deferred from earlier stories).
- Tempo keeps the chart's default jaeger receiver ports (cluster-internal), and traces do not survive a Tempo restart (no persistence, by design).
- In (8) the SERVER span's parent is the test's synthetic `traceparent`, so Grafana shows the trace with a missing root parent.

## Operator Confirmation

Confirmed 2026-11-07: the external actions this story owed were carried out.

- Port-forward Grafana (kubectl -n platform port-forward svc/grafana 3000:80), sign in with the admin credentials from the platform/grafana Secret, open Explore on the Tempo datasource, look up the trace id from smoke test (8) (or any recent POST /v1/search trace), and confirm it shows the ticketscope-api SERVER span, then retrieval keyword, then the psycopg db query span.

_Appended by the bmad-loop orchestrator (`bmad-loop confirm`, #335): a human confirmed these external actions out of band, and the story was advanced from `awaiting-operator` to `done`._
