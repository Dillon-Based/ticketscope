---
title: 'Search page shows ranked issues with how each ended'
type: 'feature'
ticket: '7'
created: '2026-11-06'
status: done
baseline_revision: 'd29ed1efd99c932c64d21c7f926dc8d7951c1839'
route: 'full'
route_source: 'auto'
risk: 'low'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md'
warnings: [oversized]
deferred: []
---

<intent-contract>

## Intent

**Problem:** `api` serves only `/v1`, so a triage engineer has no page to paste a ticket into (epic R4). AD-14's route table sends `/` to `api`, but the chart routes only `/v1`.

**Approach:** Serve one server-rendered HTML page at `/` from `api`, with no JS. It takes ticket text, runs core keyword retrieval, and lists the ranked issues with title, link, kind, and outcome status and summary. It also has an empty state and an error state. Then route `/` through the Gateway.

## Boundaries & Constraints

**Always:**
- The page uses core keyword retrieval (`REGISTRY["keyword"]`, k=10) and builds its rows from the same `SearchResult` contract models that `POST /v1/search` returns, through one shared builder. That keeps one result shape (AD-4).
- Every echoed value (query text, titles, summaries, URLs, kind, status) is escaped with `html.escape(..., quote=True)`. An issue link goes in an `href` only when it starts with `https://` or `http://`.
- Error states show a fixed, generic message and never show exception text or a traceback. The handler logs the exception server-side.
- The form posts `application/x-www-form-urlencoded` to `/`, and the body is parsed with `urllib.parse.parse_qs`. Do not add `python-multipart`, Jinja or any other dependency. A long pasted log must not have to fit in a URL.
- `http.page` imports only stdlib, `ticketscope.contract` and `ticketscope.core`. lint-imports and the AST allow-list tests stay green.
- Each result row is marked up so a test can read it with stdlib `html.parser`: `<li class="result" data-rank="N" data-outcome="<status>">` holds the title link, `class="kind"` and `class="outcome"` elements, and a `class="summary"` element when the summary is not null.

**Never:**
- No JavaScript, no external assets, and no new `/v1` field or behaviour. The `POST /v1/search` 200 body and the problem+json handlers for `/v1` stay unchanged.
- No tracing: story 9 instruments the page. No mode picker: dense and hybrid modes belong to epic-hybrid-retrieval.
- Do not touch `migrations/`, `jobs/`, `snapshot/` or `eval/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Open page | `GET /` | 200 `text/html; charset=utf-8`, a form (a `textarea name="q"`, method post, action `/`) and no results | — |
| Results | `POST /` with `q=<matching text>` | 200, the query echoed in the textarea, an `<ol>` of rows, ranks 1..n in order, each with a title link, kind and outcome | — |
| Link form | `GET /?q=<text>` | the same results as the POST | — |
| Blank query | `q=""` or whitespace only | 200, the form with a prompt to enter ticket text, and no search run | — |
| No match | `q=xylophone quokka` | 200, an empty-state message ("No matching issues"), no rows | — |
| Corpus not loaded | `corpus_version()` is None | 503, an HTML error state saying the corpus is not loaded | no stack trace |
| Store failure | the store raises | 500, an HTML error state with a generic message | no exception text, no `Traceback`; logged |
| Escaping | `q=<script>alert(1)</script>`, or an issue titled `<script>x</script>` | the text appears escaped (`&lt;script&gt;`), and no raw `<script` appears in the body | — |
| Pasted log | `q` of 4 KB or more, posted | 200, ranked rows | — |

</intent-contract>

## Code Map

- `src/ticketscope/http/app.py` -- `create_app` is the only composition root (AD-1). Move the `SearchResult` list comprehension in `search()` into a module-level `_results(hits: list[Scored]) -> list[SearchResult]`, used by both `/v1/search` and the page. `_outcome` already exists. Add `GET /` and `POST /` handlers that return `HTMLResponse`: read `q` (GET from the query param, POST from `parse_qs(await request.body())` decoded as UTF-8), strip it to decide whether it is blank, and pass the unstripped text to retrieval. Check `corpus.corpus_version()` first (None → 503 state), then call `REGISTRY["keyword"].build(corpus).search(q, 10)`. Wrap both calls in `try/except Exception` → `log.exception`, then the 500 state. This keeps the global `_server_problem` (JSON) from answering a page request. `/healthz`, `/readyz` and `/v1` stay as they are.
- `src/ticketscope/http/page.py` (new) -- pure functions that return `str`. For example, `render(query: str, results: list[SearchResult] | None, message: str | None) -> str`, with small helpers for a row and an `_esc`. Inline `<style>` is fine. The page `<title>` is "ticketscope". Show the kind as `short` / `log-heavy` and the outcome status as its enum value, plus the summary when present and the `ref` as a link when present. The footer carries the attribution line from the README, for corpus terms condition 1. Check the README for the exact wording; at minimum, cite The Public Jira Dataset v7 (CC BY 4.0) and say that the text belongs to its authors.
- `deploy/charts/ticketscope/templates/api.yaml` -- in the `ticketscope-api` HTTPRoute, add a second `matches` entry `path: {type: Exact, value: /}` to the existing rule. The match is Exact so that `/healthz` and future `/mcp` paths do not ride the page route (AD-14).
- `tests/unit/test_app.py` -- has the `client` fixture (fixture store + `Settings(default_mode="keyword")`) and `_BrokenStore`; reuse them or import them from there. `tests/target.py` has `TARGET_QUERY`, `TARGET_NUMBER` and `NO_MATCH_QUERY`. `InMemoryCorpusStore(((IssueRecord, search_text), ...), corpus_version=..., bodies=...)` builds a one-off store for the escaping case.
- `tests/smoke/test_gateway.py` -- runs in file order. `_gateway()` returns `(url, host)`, and `OUTCOMES` lists the statuses. Add section (1c) after (1b), before (2), and update the module docstring's list of sections.
- `eval/golden-queries.json` -- read only. `queries[*].query` holds the vague and the log-heavy example queries (the log-heavy one is about 1.5 KB with newlines and tabs).

## Tasks & Acceptance

**Execution:**
- [x] `src/ticketscope/http/page.py` -- the HTML renderer: form, rows, empty, blank and error states, escaping -- R4
- [x] `src/ticketscope/http/app.py` -- the shared `_results` builder; the `GET /` and `POST /` page routes -- R4, AD-4
- [x] `deploy/charts/ticketscope/templates/api.yaml` -- the Exact `/` match on the api HTTPRoute -- AD-14
- [x] `tests/unit/test_page.py` (new) -- every I/O matrix row through `create_app` on the fake. Parse rows with `html.parser` and assert rank order, the title link `href` equal to the issue url, the kind, and `data-outcome` in the outcome enum. Assert that the top row for `TARGET_QUERY` is `TARGET_NUMBER` with outcome `fixed`, matching `/v1/search`, and that `GET /?q=` gives the same rows as POST. For error states, assert the status, that `content-type` starts with `text/html`, and that the body has neither `database down` nor `Traceback`. For escaping, test both the query and a stored title. Also check that `POST /v1/search` still returns JSON for the same query.
- [x] `tests/smoke/test_gateway.py` -- (1c) through the Gateway: `GET /` is 200 HTML with the form. For each golden query, a POST to `/` (form-encoded, `Host` header) renders at least one row, with ranks 1..n and every row's `data-outcome` in `OUTCOMES` with a non-empty outcome element. A `<script>` query comes back escaped.

**Acceptance Criteria:**
- Given the kind cluster running this branch's image, when the vague and the log-heavy query from `eval/golden-queries.json` are each submitted to the page through the Gateway, then each response renders a ranked list where every row shows a title link, a kind and an outcome. (R4)
- Given `uv run pytest -m kind tests/smoke` on that cluster, when it runs, then every smoke test passes, including section (1c). (R4, R7)
- Given a `POST /v1/search` body saved before this change, when the same request runs after it, then the body is identical. (R3)

## Implementation Notes

- `POST /` reads the body in an async handler, then runs the blocking store call through `run_in_threadpool`, so a slow store never blocks the event loop.
- The page shows the blank-query prompt on a bare `GET /` as well as on a blank submit. The `q` textarea is always present.
- An outcome `ref` is shown as a link only when it is http(s). Otherwise it is shown as escaped text.
- `tests/unit/test_page.py` also checks that `http/page.py` imports only stdlib, contract and core. The existing AST allow-list test covers only core and contract.

- Parent fix after hand-back: HTML drops one newline right after `<textarea>`, so a query that started with a newline did not echo exactly. `page.render` now emits a newline after the open tag. The unit test parser mirrors the browser rule, and `test_leading_newline_in_the_query_is_echoed` covers it.
- Kind run (parent): `FORCE_BUILD=1 scripts/kind-up.sh`, then a rollout restart. The first smoke run failed only (3) `test_load_log_has_the_report`, the known deferred ordering issue; the rerun passed 18/18.

## Plan Change Log

## Review Triage Log

### 2026-11-06 — Review pass
- verdicts: 4 findings — high 0, medium 0, low 4, false 0, maybe-false 0
- findings:
  - `[low]` `[patch]` `render_page` built `_results(hits)` and the page outside its `try`, so a failure there (e.g. a stored row whose `outcome_status` is outside the enum) gave the browser a problem+json 500 instead of the HTML error state — the no-match and results paths moved inside the guarded block; `test_invalid_stored_row_is_a_500_page` added.
  - `[low]` `[patch]` The footer attribution left out README.md:7's MSR 2022 paper clause, against the plan's "exact wording" — `_ATTRIBUTION` is now the README line verbatim, and the footer test reads it from the README.
  - `[low]` `[patch]` For a repeated `q`, POST took the first value and GET the last — POST now takes the last; `test_repeated_q_takes_the_last_value_on_get_and_post` added.
  - `[low]` `[reject]` Smoke (1c) never checks the `summary` element — no defect: the same `page.render` is checked field by field (summary included) against `/v1/search` in `test_results_match_v1_search`, and the AC asks only for a title link, kind and outcome; a smoke check would add no new path.

## Design Notes

- **Why POST with a hand-parsed body.** FastAPI's `Form` needs `python-multipart`, which is a new dependency for one field. A GET-only form puts a pasted stack trace into the URL, and uvicorn's h11 limits a request head to 16 KB. `parse_qs` on the raw body is the standard library and is enough. `GET /?q=` stays for shareable links to short queries.
- **Why the page catches its own errors.** The global `Exception` handler answers with problem+json, which is right for `/v1` and wrong for a browser. The page renders its own HTML error state and logs the exception.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `FORCE_BUILD=1 scripts/kind-up.sh`, then `kubectl -n ticketscope rollout restart deploy/ticketscope-api && kubectl -n ticketscope rollout status deploy/ticketscope-api` (the image tag is HEAD's SHA, so an in-place re-run with uncommitted code does not roll the pod). Then, with the printed `TICKETSCOPE_GATEWAY_URL` and `TICKETSCOPE_GATEWAY_HOST` exported, run `uv run pytest -m kind tests/smoke` -- expected: all pass. If (3) `test_load_log_has_the_report` fails right after an in-place upgrade, that is the known deferred story 1.5 ordering issue: rerun the suite once.
- Save the `POST /v1/search` body for `{"query": "zephyrcache eviction stalls node drain", "mode": "keyword"}` from the fake-backed app before and after the change, then `diff` the two -- expected: no output

## Auto Run Result

Status: built

**Summary.** `api` serves the search page at `/`. It is server-rendered HTML with no JS and no external assets. It takes ticket text from a posted form (or `GET /?q=` for links) and runs core keyword retrieval (k=10). It lists the ranked issues with their title link, kind, and outcome status, summary and ref. Its rows come from the same `SearchResult` builder as `POST /v1/search`. Blank, empty, not-loaded (503) and failure (500) states render as HTML, with no exception text. Everything echoed is escaped, and only http(s) URLs become links. The api HTTPRoute now also matches Exact `/` (AD-14).

**Files changed:**
- `src/ticketscope/http/page.py` (new) -- the HTML renderer: form, rows, states, escaping, attribution footer
- `src/ticketscope/http/app.py` -- the shared `_results` builder; the `GET /` and `POST /` page routes, with their own HTML error handling
- `deploy/charts/ticketscope/templates/api.yaml` -- the Exact `/` match on the api route
- `tests/unit/test_page.py` (new) -- every I/O matrix row on the fake, plus the review-patch tests
- `tests/smoke/test_gateway.py` -- section (1c): the form, each golden query's ranked rows with outcomes, and `<script>` escaping through the Gateway

**Review.** Quick lens, 4 findings:
- Patched: 3, all low: the HTML error state now covers rendering, the attribution is verbatim, and POST takes the last `q`.
- Deferred: none.
- Rejected: 1 (low). The smoke summary check duplicates the unit coverage of the same renderer.

**Follow-up review recommended:** false. Patched by verdict: high 0, medium 0, low 3.

**Verification:**
- ruff, ruff format, pyright, lint-imports (6 kept) and pytest (548 passed) all pass.
- The `POST /v1/search` body is byte-identical to the baseline (diffed against a worktree at the baseline revision).
- On kind: `FORCE_BUILD=1 scripts/kind-up.sh`, then a rollout restart, then `uv run pytest -m kind tests/smoke`. The first run failed only (3) `test_load_log_has_the_report`, the known deferred story 1.5 ordering issue, and the rerun passed 18/18. Both golden queries rendered ranked rows, each with an outcome, through the Gateway.

**Residual risks:**
- Smoke (3) still fails after an in-place upgrade until a reload. This is deferred from story 1.6.
- The kind image was tagged with HEAD's SHA but built from uncommitted code; CI rebuilds it on the commit.
- The page is not traced yet (story 9).
