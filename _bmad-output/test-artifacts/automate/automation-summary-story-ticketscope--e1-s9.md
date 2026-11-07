---
runScope: 'story'
runKey: 'story-ticketscope--e1-s9'
testMode: 'expand'
testEntry: 'bmad-tea-automate'
storyId: '1.9'
storyKey: 'ticketscope--e1-s9'
ticketRef: '1.9 @ _bmad-output/initiative-ticketscope/tickets/epic-search-baseline'
storyFile: ''
workflowStatus: 'completed'
stepsCompleted: ['step-01-preflight-and-context', 'step-02-identify-targets', 'step-03-generate-tests', 'step-03c-aggregate', 'step-04-validate-and-summarize']
lastStep: 'step-04-validate-and-summarize'
lastSaved: '2026-11-07'
test_mode: 'expand'
test_operation: 'create'
auto_validate: true
auto_heal_failures: true
max_healing_iterations: 3
use_mcp_healing: true
healing_rounds_used: 1
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md (entry 9, from tickets.py find; R6)
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-one-search-request-yields-one-trace-in-tempo-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
  - src/ticketscope/{telemetry.py,settings.py,http/app.py,jobs/load/main.py,jobs/migrate/main.py}
  - deploy/charts/ticketscope/{values.yaml,values-kind.yaml,templates/_helpers.tpl,templates/api.yaml,templates/jobs.yaml}
  - tests/unit/test_telemetry.py, tests/unit/test_chart_telemetry.py, tests/unit/test_chart_backup.py, tests/unit/conftest.py, tests/smoke/test_gateway.py
  - knowledge: test-levels-framework.md, test-priorities-matrix.md, data-factories.md, selective-testing.md, ci-burn-in.md, test-quality.md, test-healing-patterns.md, selector-resilience.md, timing-debugging.md
---

# Automation Summary: story 1.9 (One search request yields one trace in Tempo)

## Preflight

- Mode: **expand**, set explicitly by the request. Operation: Create (autonomous). Context: BMad-Integrated.
- Stack: `backend` (Python, pytest, with Helm charts rendered offline by `helm template`). Playwright and Pact do not apply.
- Story: `tickets.py find 1.9` resolved it to `epic-search-baseline` entry 9. The entry is not pulled. Its state is `in-progress`, and its plan status is `awaiting-operator`. **This run did not change the ticket status or the plan status.**
- Criteria: the ticket has only a `verify` line, so this run used the plan's acceptance criteria, its I/O matrix and its Boundaries. It also used these test-design rows:
  - "Span attributes follow AD-10" (P1, API);
  - "Logs carry trace context" (P1, Unit);
  - "One search request yields one trace in Tempo" (E2E, already covered by smoke tests (8) and (8b)).
- The test-design row still names `ticketscope-k8s-issues`, which the plan supersedes with `ticketscope-mojang-jira` (spine AD-10). The tests follow the plan.
- Execution: sequential, with no subagents.

## Existing coverage (before this run)

- `tests/unit/test_telemetry.py` (17 cases) covers every unit-level row of the I/O matrix:
  - the search tree;
  - the page trace with k=10;
  - no query text by default, and the opt-in;
  - store failure on `/v1/search` and on the page;
  - probes, including untraced readyz database work;
  - JSON logs inside and outside a span;
  - `configure_logging`;
  - `setup` with no endpoint, and with an endpoint;
  - the `load` jobs span, and the error status of a failed `migrate`.
- `tests/unit/test_chart_telemetry.py` covers the platform renders and the endpoint on all three ticketscope workloads.
- `tests/smoke/test_gateway.py` (8) and (8b) cover the Tempo and Grafana E2E path. Both are marked `kind`.

## Coverage plan (gaps targeted)

| Target | Level | Priority | Gap |
|---|---|---|---|
| Trace-context propagation | API | P1 | Nothing checked that the SERVER span continues an incoming `traceparent`, which smoke test (8) depends on. Also unchecked: each request without one starts its own trace. |
| Retrieval span edges | API/Unit | P1 | `result.count` = 0 on no match. No retrieval span when the corpus is not loaded, for a blank page query, on a 422, or on issue detail. `retrieval_span` sets ERROR, records the exception, propagates it and sets no count. Only `ticketscope.*` or `gen_ai.*` keys. Opt-in query text on the page path. |
| SERVER `url.query` | API | P1 | Kept verbatim when opted in. Absent when there is no query string. Redacted on `/v1/search?…`. Stable HTTP semconv names, with no `http/dup` duplicates. |
| Probes | API/Unit | P2 | Probes with a query string are untraced. A not-ready `/readyz` is untraced. `untraced()` restores instrumentation after a normal exit and after an exception. |
| JSON logs | Unit/API | P1 | A log line during a request carries the SERVER span's ids and the exception, but not the query. `%`-args are formatted and non-ASCII text is preserved. The `exc_text` path. Multi-line messages and tracebacks still give one line. A job's log line inside its span carries the span's ids. |
| Provider / instrumentation | Unit | P2 | Blank or `/`-only endpoints create no exporter. The endpoint is stripped before `/v1/traces` is appended. psycopg is instrumented once, with `capture_parameters=False` and `enable_commenter=False`. `create_app` sets the semconv opt-in. `api.main` calls `setup(ticketscope-api, endpoint)` before `uvicorn.run(log_config=None, factory=True)`. Settings parse the env. |
| Jobs | Unit | P1 | A failed `load` sets ERROR and still flushes. A crashing `load` records the exception and still flushes. A successful `migrate` emits an OK span. |
| Layer rule | Unit (static) | P2 | `telemetry` imports no `ticketscope` module, and imports fastapi only under TYPE_CHECKING. `core` and `contract` have no `opentelemetry` import. Importing telemetry and the jobs loads neither fastapi nor the OTLP exporter. |
| Chart plumbing | Unit (helm) | P2 | `recordQueryText=true` renders `"true"` on api only. An empty endpoint renders `""` everywhere. Each env var appears exactly once. `values-kind.yaml` does not override telemetry (AD-13/AD-25). No `OTEL_*` env var is rendered. |

## Generated files

- `tests/unit/test_telemetry_expanded.py`: 36 cases, with parameters.
- `tests/unit/test_chart_telemetry_expanded.py`: 6 cases. They skip without helm and do not need the platform dependencies.

No existing test file and no production file was modified.

## Run and heal

- Command: `uv run pytest tests/unit/test_telemetry_expanded.py tests/unit/test_chart_telemetry_expanded.py -q`
- Initial run: 42 cases, 41 passed and 1 failed.
  - `test_job_logs_inside_the_job_span_carry_its_ids` was a setup defect (Syntax/import/setup class): pytest leaves the root logger at WARNING, so the job's INFO line never reached the handler.
  - Fix: `caplog.set_level(logging.INFO)` in that test. The assertion is unchanged.
- Lint fix: the fake instrumentor's `calls` became a `ClassVar` (RUF012). `ruff format` reflowed both files.
- Final run: **42 passed**, stable across 3 repeated runs. Healing rounds used: 1 of 3.
- Repo gates are all clean:
  - `ruff check .` and `ruff format --check .`;
  - `pyright`: 0 errors;
  - `lint-imports`: 7 contracts kept;
  - full suite `uv run pytest -q`: 688 passed, 1 xfailed (the known 1.7 defect), 22 deselected (`kind`).
- The kind smoke tests were not run. This run added no smoke tests, and (8) and (8b) were verified in the build.

## Product defects

None found. Still standing from the story review, and not re-raised:
- The rejected low finding: existing `load.main()` unit tests run the real `telemetry.setup`, which sets the global provider and instruments psycopg for the session.
- The new tests that call `load.main()` and `migrate.main()` share that behaviour. They log a harmless "Overriding of current TracerProvider is not allowed" warning.

## Notes and recommendations

- The `charts` CI job runs `test_chart_telemetry.py`. The new `test_chart_telemetry_expanded.py` renders only the ticketscope chart, which needs no dependency build, so it runs in `checks` wherever helm is installed. It needs no workflow change.
- `test_server_span_uses_stable_http_semconv` pins today's opt-in (`http`, not `http/dup`). If the opt-in constant changes, that test must change with it.
- Next workflow: `bmad-tea-trace` for story 1.9. The only uncovered criterion is the manual Grafana Explore check (AC 4, operator).

## Playwright Utils deviations

None. Playwright does not apply: the backend stack has no browser tests.
