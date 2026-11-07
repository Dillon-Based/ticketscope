---
title: 'Complete the /v1 contract'
type: 'feature'
ticket: '6'
created: '2026-11-06'
status: done
baseline_revision: '32049eef3d093ba1591d1cca259780359044f7cb'
route: 'full'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md'
warnings: [oversized]
deferred:
  - summary: >-
      The kind smoke test (3) test_load_log_has_the_report fails when the suite runs right after an in-place kind-up.sh upgrade of an already-loaded cluster.
    evidence: |-
      The same-pin load is a no-op, so the newest Succeeded load pod logs no "load report:" line; only (5)'s forced reload restores it, so a rerun passes. Reproduced twice in this build, after each in-place upgrade. It predates this change: test (3) and the no-op load come from story 1.5. Also, kind-up.sh reuses the HEAD-SHA tag, so an in-place re-run with uncommitted code does not roll the api pod; `kubectl rollout restart` was needed.
    location: >-
      tests/smoke/test_gateway.py (section 3); scripts/kind-up.sh
    severity: low
---

<intent-contract>

## Intent

**Problem:** `/v1` serves only `POST /v1/search`, with no `k` bounds, FastAPI's default JSON error bodies, and a Retriever port without `exclude` or `available(store)`. Epic-mcp-server needs `GET /v1/issues/{number}`, and epic-eval-gate needs `exclude` and `available` (AD-4, AD-19).

**Approach:** Add the issue-detail models and the `k` bounds (1..50) to `ticketscope.contract`, a `get_issue` read to the `CorpusStore` port and both stores, `exclude` and `available` to the keyword mode, and a `GET /v1/issues/{number}` route. Render every `api` error as RFC 9457 `application/problem+json`.

## Boundaries & Constraints

**Always:**
- Contract models keep `extra="allow"` and pass unknown fields through (AD-20). Changes within `/v1` are additive only: existing fields and the `POST /v1/search` 200 shape stay byte-for-byte the same.
- Signature `Retriever.search(query: str, k: int, exclude: frozenset[int] = frozenset()) -> list[Scored]` (AD-19). Keyword fetches `k + len(exclude)` from the store, drops excluded numbers, and truncates to `k`, so an excluded issue never costs a slot.
- `available(store) -> bool` lives on `Mode` in `core.modes.REGISTRY`. Keyword is always available.
- Problem bodies carry `type` (`about:blank`), `title` (the HTTP reason phrase), `status` and `detail`. A validation 422 also carries an `errors` list of `{loc, msg}`. The response header is `Content-Type: application/problem+json`.
- `core` still imports only stdlib and pydantic, and `http.app` stays the only composition root (AD-1). The `lint-imports` and AST allow-list tests stay green.

**Never:**
- No `exclude` on the HTTP surface: AD-4's request has no such field. Eval reaches it through `core`.
- No readable Jira `key` on `/v1` (epic Note: deferred to epic-mcp-server). No new modes, no migration, and no chart change.
- Do not escape or rewrite query text before BM25. pg_textsearch's `to_bm25query` takes operator characters as plain text (checked on kind: `crash & launcher | (java:!) !! "x` ranks).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Issue detail | `GET /v1/issues/{n}`, n loaded | 200 `{issue: {number,title,url,kind,state,body}, outcome: {status,summary,source,ref}}` | — |
| Unknown issue | n not loaded | 404 problem+json | `detail` names the number |
| Non-integer number | `GET /v1/issues/abc` | 422 problem+json | validation `errors` |
| Corpus not loaded | either route | 503 problem+json | `detail: corpus not loaded` |
| k bounds | `k=0`, `k=51`, `k=-1` | 422 problem+json | validation `errors` |
| k edges | `k=1`, `k=50` | 200, at most k results | — |
| Unknown mode | `mode: "nope"` (not in the Literal) and `"dense"` (in it but not in REGISTRY) | 422 problem+json | — |
| Operator characters | query with `& \| ! : ( )` | 200, ranked results | — |
| Pasted log | query of 4 KB or more | 200, ranked results | — |
| Exclude | `search(q, k, exclude={top hit})` | top hit absent; still k results when the corpus has them | — |

</intent-contract>

## Code Map

- `src/ticketscope/contract/search.py` -- `_Wire` has `extra="allow"`. Add `Field(default=10, ge=1, le=50)` to `SearchRequest.k`. Add `IssueDetail(Issue)` with `body: str | None` and `IssueResponse(_Wire)` with `issue: IssueDetail` and `outcome: Outcome`. A `Problem` model is optional, for tests; it needs no field beyond the four plus optional `errors`.
- `src/ticketscope/core/model.py` -- add a frozen `IssueDetail` dataclass (`issue: IssueRecord`, `body: str | None`). Leave `IssueRecord` alone, because keyword hits must not haul multi-KB bodies.
- `src/ticketscope/core/ports.py` -- `CorpusStore.get_issue(number: int) -> IssueDetail | None`; `Retriever.search` gains `exclude`.
- `src/ticketscope/core/modes.py` -- `KeywordRetriever.search(query, k, exclude=frozenset())`; `Mode.available: Callable[[CorpusStore], bool]`, `lambda _store: True` for keyword.
- `src/ticketscope/core/fakes.py` -- `InMemoryCorpusStore` gains an optional `bodies: Mapping[int, str | None]` keyword arg and `get_issue`, which reads the issue from the documents and the body from `bodies` (None when absent).
- `src/ticketscope/adapters/postgres.py` -- `PostgresCorpusStore.get_issue`: one `SELECT` of the `_KEYWORD_SQL` columns plus `body` from `issue` by `number`. Reuse a row-to-`IssueRecord` helper shared with `keyword_search`.
- `src/ticketscope/http/app.py` -- add exception handlers for `StarletteHTTPException` and `RequestValidationError` that return `JSONResponse(..., media_type="application/problem+json")`. Add `GET /v1/issues/{number}` (`number: int`); it raises 503 when `corpus_version()` is None and 404 when `get_issue` is None. Build `Outcome` once, from a helper shared by both routes. Keep `/healthz` and `/readyz` bodies as they are: the readiness 503 is not an error response of `/v1`.
- `tests/unit/conftest.py` -- `fixture_store` passes `bodies={r.number: r.body for r in rows}`.
- `tests/unit/test_app.py` -- `_BrokenStore` needs `get_issue`, which raises.
- `tests/smoke/test_gateway.py` -- the kind smoke file, run in file order against snapshot 2026.11.1. `_search` and `_gateway` are reusable. Add the new checks after section (1), so they run before the upgrade tests.
- Do not change: `migrations/`, `deploy/`, `jobs/`, `snapshot/`, `.importlinter`.

## Tasks & Acceptance

**Execution:**
- [x] `src/ticketscope/contract/search.py` -- k bounds; `IssueDetail`, `IssueResponse` -- AD-4, AD-20
- [x] `src/ticketscope/core/{model,ports,modes,fakes}.py` -- `IssueDetail`, `get_issue`, `exclude`, `available` -- AD-19
- [x] `src/ticketscope/adapters/postgres.py` -- `get_issue` -- AD-4
- [x] `src/ticketscope/http/app.py` -- problem+json handlers, the issue route -- AD-4
- [x] `tests/unit/test_contract.py` -- k 0/1/50/51 at the model; `IssueResponse` round-trips an unknown field
- [x] `tests/unit/test_modes.py` -- exclude drops the top hit and still fills k; `exclude` on an absent number changes nothing; `REGISTRY["keyword"].available(store)` is True
- [x] `tests/unit/test_app.py`, `tests/unit/conftest.py` -- every I/O matrix row through `create_app` with the fake: status, `content-type` starting `application/problem+json` on each error, the problem fields, and the issue body equal to the fixture's
- [x] `tests/unit/test_postgres_store.py` (new) -- `get_issue` against a fake psycopg connection in the style of `test_postgres_corpus_meta.py` (monkeypatch `postgres.psycopg.connect`): a row maps to `IssueDetail` with its body, no row returns None, and the number is sent as a parameter
- [x] `tests/smoke/test_gateway.py` -- through the Gateway: `GET /v1/issues/{n}` for the top hit of `RESULTS_QUERY` returns its number with a non-empty body and the same outcome as the search row; an unknown number is 404 problem+json; `k=0`, `k=51`, `mode=nope` are 422 problem+json; an operator-character query and a 4 KB or larger pasted Java-style stack trace each return 200 with results

**Acceptance Criteria:**
- Given the kind cluster with this branch's image, when `uv run pytest -m kind tests/smoke` runs, then every smoke test passes, the new `/v1` checks included.
- Given `src/ticketscope/core/modes.py` imports `ticketscope.adapters.postgres`, when `uv run lint-imports` runs, then it fails (the layering is unchanged).
- Given a `POST /v1/search` response saved before this change, when the same request runs after it, then the body is identical.

## Implementation Notes

- Added a third handler, for `Exception`, so an unhandled store failure is a 500 problem+json with a generic `detail` (no exception text leaks). It follows "every `api` error" in the Approach; the Code Map named only two handlers.
- The `StarletteHTTPException` handler also covers unknown routes (404) and 405s, and keeps the exception's headers (for example `Allow`).
- `contract.search` exports `K_MIN`/`K_MAX`, and `Problem` has a typed `errors: list[ProblemError] | None`.
- `fixture_store` materialises `build_rows` into a list, because it is an iterator and is now read twice (documents and bodies).
- The fixture has only 3 hits for `TARGET_QUERY`, so the fixture exclude test uses k=2. The fill-k behaviour is also shown on a synthetic 5-issue store.
- Kind run: `FORCE_BUILD=1 scripts/kind-up.sh` with uncommitted changes (tag = HEAD SHA 32049ee). The first smoke run failed only (3) `test_load_log_has_the_report`, because the in-place upgrade's load was a no-op on the already-loaded corpus. After (5)'s reload, the rerun passed 14/14.

## Plan Change Log

## Review Triage Log

### 2026-11-06 — Review pass
- verdicts: 3 findings — high 0, medium 0, low 2, false 0, maybe-false 0 (third graded low, pre-existing)
- findings:
  - `[low]` `[patch]` A registry-miss mode (`dense`) gave a 422 problem without `errors`, unlike a Literal miss (`nope`): two shapes for one error — the route now raises `RequestValidationError`, so the body is `detail: "mode: unknown mode: dense"` with `errors: [{loc: [body, mode]}]`. The test was extended, and the fix was confirmed through the Gateway on kind.
  - `[low]` `[patch]` For malformed JSON, `detail` named a character offset as the field (`23: JSON decode error`) — `json_invalid` now renders as `body: JSON decode error`. A unit test was added, and the fix was confirmed on kind.
  - `[low]` `[defer]` AC1 was shown only by an order-dependent rerun: smoke (3) fails after an in-place upgrade — the failure predates this change (story 1.5's no-op load leaves no report line). Final run here: 14/14 passed. Deferred to frontmatter.

## Design Notes

- **Why filter `exclude` in core, not SQL.** The store port stays one method for every mode, and hybrid (AD-19) already has to over-fetch by `|exclude|`. The cost is `|exclude|` extra rows, which is one for eval.
- **Why problem+json for 422 from validation.** FastAPI's default body is `{"detail": [...]}` as `application/json`. AD-4 and the Errors convention require RFC 9457 for every `api` error, and MCP puts the problem `detail` into `is_error`. So `detail` must be a string, for example `k: Input should be greater than or equal to 1`, and the structured list goes under `errors`.

```python
def _problem(status: int, detail: str, **extra: object) -> JSONResponse:
    body = {"type": "about:blank", "title": HTTPStatus(status).phrase,
            "status": status, "detail": detail, **extra}
    return JSONResponse(body, status_code=status, media_type="application/problem+json")
```

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `FORCE_BUILD=1 scripts/kind-up.sh` (rebuilds the app image for the new HEAD tag and upgrades in place), then with the printed `TICKETSCOPE_GATEWAY_URL` and `TICKETSCOPE_GATEWAY_HOST` exported: `uv run pytest -m kind tests/smoke` -- expected: all pass
- Before and after the change, save the `POST /v1/search` body for `{"query": "zephyrcache eviction stalls node drain", "mode": "keyword"}` from the fake-backed app, then `diff` the two -- expected: no output

## Auto Run Result

Status: built

**Summary.** `/v1` now matches AD-4 and AD-19:
- `GET /v1/issues/{number}` returns the issue with its body, plus its outcome.
- `k` must be between 1 and 50.
- Every `api` error is RFC 9457 `application/problem+json`. A validation 422 carries a string `detail` and an `errors` list.
- `Retriever.search` takes `exclude`: keyword over-fetches by the number excluded, so an excluded issue never costs a slot.
- `Mode.available(store)` exists, and keyword always returns True.
- Contract models still allow unknown fields, and the `POST /v1/search` 200 body is byte-identical.

**Files changed:**
- `src/ticketscope/contract/search.py` -- `k` bounds; `IssueDetail`, `IssueResponse`, `Problem`
- `src/ticketscope/core/model.py` -- `IssueDetail` dataclass
- `src/ticketscope/core/ports.py` -- `CorpusStore.get_issue`; `exclude` on `Retriever.search`
- `src/ticketscope/core/modes.py` -- keyword `exclude`; `Mode.available`
- `src/ticketscope/core/fakes.py` -- `bodies=` and `get_issue` on the in-memory store
- `src/ticketscope/adapters/postgres.py` -- `get_issue`; a shared row-to-issue helper
- `src/ticketscope/http/app.py` -- problem+json handlers (HTTP, validation, 500); the issue route; a shared `_outcome`
- `tests/unit/{conftest,test_app,test_contract,test_modes}.py`, `tests/unit/test_postgres_store.py` -- the I/O matrix, k edges, exclude, the store mapping
- `tests/smoke/test_gateway.py` -- section (1b): issue detail, 404/422 problems, operator characters, a 4 KB stack trace

**Review.** Quick lens, 3 findings:
- Patched: 2 (both low): the registry-miss 422 shape, and the malformed-JSON detail.
- Deferred: 1 (low, pre-existing): smoke (3) ordering after an in-place upgrade.
- Rejected: none.

**Follow-up review recommended:** false. No high and no medium findings were patched (patched by verdict: high 0, medium 0, low 2).

**Verification:**
- ruff, ruff format, pyright, lint-imports (6 kept) and pytest (483 passed) all pass.
- Adding `import ticketscope.adapters.postgres` to `core/modes.py` makes lint-imports fail (checked by the implementer, then reverted).
- The search body diff before and after the change is empty.
- On kind (snapshot 2026.11.1): ran `FORCE_BUILD=1 scripts/kind-up.sh` and `kubectl rollout restart deploy/ticketscope-api`, then `uv run pytest -m kind tests/smoke`: 14 passed.

**Residual risks:**
- Smoke (3) fails after an in-place upgrade until a reload (deferred).
- The kind image is tagged with HEAD's SHA but was built from uncommitted code. CI rebuilds it on the commit.
- Unknown routes and 405s are problem+json now too: the handler covers every Starlette HTTP error.

