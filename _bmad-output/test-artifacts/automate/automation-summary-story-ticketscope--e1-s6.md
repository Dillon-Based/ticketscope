---
runScope: 'story'
runKey: 'story-ticketscope--e1-s6'
testMode: 'expand'
testEntry: 'bmad-tea-automate'
storyId: '1.6'
storyKey: 'ticketscope--e1-s6'
ticketRef: '1.6 @ _bmad-output/initiative-ticketscope/tickets/epic-search-baseline'
storyFile: ''
workflowStatus: 'completed'
stepsCompleted: ['step-01-preflight-and-context', 'step-02-identify-targets', 'step-03-generate-tests', 'step-03c-aggregate', 'step-04-validate-and-summarize']
lastStep: 'step-04-validate-and-summarize'
lastSaved: '2026-11-06'
test_mode: 'expand'
test_operation: 'create'
auto_validate: true
auto_heal_failures: true
max_healing_iterations: 3
use_mcp_healing: true
healing_rounds_used: 1
inputDocuments:
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md (entry 6, from tickets.py find)
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-complete-the-v1-contract-plan.md
  - _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md
  - pyproject.toml
  - tests/unit/conftest.py
  - tests/unit/test_app.py
  - tests/unit/test_contract.py
  - tests/unit/test_modes.py
  - tests/unit/test_postgres_store.py
  - knowledge: test-levels-framework.md, test-priorities-matrix.md, data-factories.md, selective-testing.md, ci-burn-in.md, test-quality.md, test-healing-patterns.md, selector-resilience.md, timing-debugging.md
---

# Automation Summary — story 1.6 (Complete the /v1 contract)

## Preflight

- Mode: **expand**, set explicitly by the request. Operation: Create (autonomous). Context: BMad-Integrated.
- Stack: `backend` (Python, `pyproject.toml`, pytest; `-m 'not kind'` by default). No Playwright or Pact applies (no Pact artifacts in the repo).
- Story resolved with `tickets.py find 1.6` to the epic entry `epic-search-baseline` id 6 (not pulled, so no leaf file), state `review` (built). The ticket status was not changed.
- Criteria: the ticket has only a `verify` line, so the plan's acceptance criteria and its I/O matrix were used, plus test-design rows "`/v1` contract completion (R3)" scenarios 1–6 and "Log-heavy input is accepted by BM25 (R3)".
- Execution mode: sequential. Workers were not spawned, because this session only spawns agents when the user asks.
- No ATDD checklist exists for this story.

## Existing coverage (before this run)

Story 1.6's own tests already cover every I/O matrix row through `create_app` with the fake (`test_app.py`), the k bounds at the model and a round-tripped unknown field (`test_contract.py`), exclude of the top hit / an absent number and keyword availability (`test_modes.py`), and `get_issue` row mapping (`test_postgres_store.py`). The kind checks are in `tests/smoke/test_gateway.py` section (1b).

## Coverage plan (gaps targeted)

| Target | Level | Priority | Gap |
|---|---|---|---|
| problem+json handlers | API (TestClient) | P1 | 405 keeps `Allow`; 500 on the search route (only the issue route was tested) with no exception text; failure after the version check; `title` equals the HTTP phrase on every status. |
| validation 422 rendering | API | P1 | Missing `query`; two invalid fields → two `errors` and one `; `-joined `detail`; non-integer `k` (`"ten"`, `1.5`, `null`); a JSON array body; non-integer paths (`1.5`, `12abc`, `%20`). |
| mode resolution | API | P2 | Mode/k validation precedes the 503 corpus check; a server default (`Settings.default_mode`) outside the registry is a 422 problem. |
| additive-only request (AD-20) / no `exclude` on HTTP (AD-4) | API | P1 | Unknown request fields return a byte-identical body; an `exclude` field in the request is ignored. |
| k defaults/edges | API | P2 | Default k is 10; k=50 returns 50 when the corpus has them (the fixture has only 3 hits). |
| issue detail | API | P2 | A missing body is present as `null`; every outcome field mapped; non-ASCII body; any unloaded integer (−1, 0, 2^40) is 404. |
| readiness | API | P2 | The readiness 503 stays a plain `application/json` body (plan: "not an error response of `/v1`"). |
| keyword `exclude` (AD-19) | Unit | P1 | Over-fetch is exactly `k + len(exclude)`; no exclude fetches exactly k; several excluded; all excluded; fewer hits than k; an absent excluded number never yields k+1 results. |
| Retriever port / registry | Unit | P2 | The built retriever satisfies `Retriever` with the default `exclude`; `available` on an empty store; the registry and `Mode` are immutable. |
| `PostgresCorpusStore` | Unit (fake psycopg) | P1 | `keyword_search` lost direct coverage when its mapping moved to `_issue_record`: row mapping, score sign, `k <= 0` never connects, operator characters sent unescaped as a bound parameter, one connection per `get_issue`, both reads share the mapping. |

## Generated files (owned scope)

- `tests/unit/test_v1_contract_expanded.py`: 32 test functions (38 cases with parameters)
- `tests/unit/test_postgres_store_expanded.py`: 5 test functions (6 cases)

No existing test files and no production files were modified.

## Run and heal

- Command: `uv run pytest tests/unit/test_v1_contract_expanded.py tests/unit/test_postgres_store_expanded.py -q`
- Initial execution: 44 executed, 44 passed, 0 failed, 0 skipped.
- Static checks found one test defect, fixed in healing round 1 (class: lint): `test_postgres_store_expanded.py:34` ruff UP037 quoted annotation `"_Conn"`, fixed by `ruff --fix`. No assertion changed.
- Final execution: 44 executed, **44 passed**, 0 failed, 0 skipped.
- Repo gates: `ruff check .`, `ruff format --check .`, `pyright` (0 errors), `lint-imports` (6 kept) all clean. Full unit suite: `uv run pytest -q` gives 527 passed, 14 deselected (`kind`).
- The kind smoke tests (`-m kind`) were not run in this pass: they need the kind cluster and are not part of this run's generated scope.

## Product defects

None found. Every new test passed against the production code as built.

## Notes for the orchestrator

- Acceptance criteria and production source were preserved; the ticket status was not touched.
- Observed, not a defect: a `Settings.default_mode` outside the registry turns every mode-less search into a 422 that blames the caller (`mode: unknown mode: dense`). It is a misconfiguration, not a request error; the test pins current behaviour. Whether startup should reject such a default is a design choice for epic 3.
