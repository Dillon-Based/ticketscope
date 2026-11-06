---
title: 'Tracer: keyword search answers through the Gateway on kind'
type: 'feature'
ticket: '1'
created: '2026-11-06'
status: 'built'
baseline_revision: '4ca22e31f1371030a3c5a788ee0c51e106c6f61d'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/tickets/story-tracer-keyword-search-answers-through-the-gateway-on-kind.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The repo has no code. Every later story needs the repo, CI, both images, both Helm releases on kind, and one working request path from the Gateway to Postgres. The epic's assumption that a GitHub-hosted runner can hold all of this is also unproven.

**Approach:** Build the thinnest slice through every layer to the spine's contracts. A synthetic fixture snapshot is loaded into a two-instance CNPG Postgres with pg_textsearch. `POST /v1/search` with mode `keyword` answers through the Envoy Gateway. A PR runs `ci.yml`, which calls `_kind-deploy`, which runs `scripts/kind-up.sh` and then a smoke check against the Gateway.

## Boundaries & Constraints

**Always:**
- The spine's layer table (AD-1) is enforced by import-linter. `core` imports only stdlib and pydantic, and `contract` imports only pydantic.
- There is one app image (AD-2). Images are tagged with the git SHA (AD-16).
- Config comes only from `TICKETSCOPE_*` env vars through `ticketscope.settings`. Secrets come only from CNPG or the chart.
- `api` connects as `ticketscope_ro`. `migrate` and `load` connect as the app owner (AD-7).
- `migrate` runs as a post-install/pre-upgrade hook and `load` as a post-install/post-upgrade hook, in that order (AD-22).
- The fixture has no real issue text. Its issue numbers are ≥ 900000, so they cannot collide with real issues.
- `values-kind.yaml` holds only environment facts (AD-25).

**Never:**
- No `GET /v1/issues`, no k bounds, no problem+json and no `exclude`/`available` (story 6). No page (story 7). No SeaweedFS or backups (story 8). No telemetry (story 9).
- No checksum download (story 5). No kind or outcome functions in core (story 4).
- No `Ingress`, no `ts_rank`, no `pg_search` or `vchord_bm25`.
- No live GitHub API calls.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Best match | `{"query": <fixture target query>, "mode": "keyword"}` | 200. Rank 1 is the target fixture issue, ranks run 1..n, scores do not increase as rank rises, `score_kind` is `bm25`, `corpus_version` is `fixture`, and every result has `issue` and `outcome.status` set to `unknown` | No error expected |
| Mode omitted | `{"query": "..."}` | The server default mode from settings (`keyword`) applies | No error expected |
| Unknown mode | `{"query": "...", "mode": "nope"}` | 422 from contract validation; the body shape is left to story 6 | Not an unhandled 500 |
| No match | A query with no fixture terms | 200 with `results: []` | No error expected |
| Corpus not loaded | `corpus_meta` is empty | `/readyz` returns 503, so `api` is not Ready | Readiness fails; the process stays up |
| Load re-run | Helm upgrade with the same pin | The issue rows and the single `corpus_meta` row are replaced in one transaction, with no duplicates | Roll back on error and exit non-zero |

</frozen-after-approval>

## Code Map

Greenfield: no code exists. Follow the spine's Structural Seed layout.

- `pyproject.toml`, `uv.lock` -- Python 3.14 and the Stack table pins. Holds the ruff, pyright and pytest config; the pytest marker `kind` is deselected by default.
- `.importlinter` -- layer and forbidden contracts from the AD-1 table. The one allowed exception is `ticketscope.http.app` → `ticketscope.adapters.postgres`, the composition root.
- `src/ticketscope/contract/search.py` -- the `/v1` `SearchRequest`/`SearchResponse` models, exactly as AD-4 gives them. `mode` is optional with no hard-coded default.
- `src/ticketscope/core/` -- `snapshot.py` (the pydantic `SnapshotIssue` with AD-6 fields), `model.py` (`IssueRecord`, `Scored`), `ports.py` (`CorpusStore`, `Retriever` Protocols), `modes.py` (`REGISTRY`, the keyword mode), `fakes.py` (an in-memory `CorpusStore` with naive term-overlap scoring).
- `src/ticketscope/adapters/postgres.py` -- psycopg 3. Keyword search orders by pg_textsearch BM25 and returns `-score`. Also reads `corpus_version`.
- `src/ticketscope/http/app.py` -- `create_app()` is the factory and composition root. It serves `POST /v1/search`, `/healthz` and `/readyz`.
- `src/ticketscope/jobs/{migrate,load}/main.py` -- `migrate` waits for the database and for the `ticketscope_ro` role, then applies `migrations/*.sql` in order, tracked in `schema_migrations` under an advisory lock. `load` reads the pinned snapshot `.jsonl.gz` and the expected-kinds sidecar, then replaces the issues and `corpus_meta` in one transaction.
- `src/ticketscope/settings.py` -- pydantic-settings for the `TICKETSCOPE_*` vars.
- `migrations/0001_init.sql` -- creates the extensions, then `ALTER DEFAULT PRIVILEGES … TO ticketscope_ro` before any table. Then the `issue` table (number PK, title, body, url, state, state_reason, created/closed_at, kind CHECK, outcome_status/summary/source/ref, and a search text column with a bm25 index) and the `corpus_meta` table.
- `snapshot/schema-v1.json`, `snapshot/fixture.jsonl`, `snapshot/fixture-kinds.json` -- JSON Schema draft 2020-12 with every AD-6 field. The fixture holds about 8 synthetic issues, both short and log-heavy, one of them written as the best match for `tests/smoke`'s query. The kinds sidecar sits outside the schema.
- `images/app.Dockerfile`, `images/postgres.Dockerfile` -- the app image uses uv, Python 3.14 and the fixture gzipped to `/app/snapshots/fixture.jsonl.gz`. The postgres image is the CNPG `standard` PG18 image plus the PGDG pg_textsearch package.
- `deploy/charts/platform/` -- dependencies on Envoy Gateway (which brings the Gateway API CRDs) and the CNPG operator. Templates for the GatewayClass and the one Gateway. Commit `Chart.lock` and ignore `charts/*.tgz`.
- `deploy/charts/ticketscope/` -- the Cluster (2 instances, `shared_preload_libraries: [pg_textsearch]`, managed role `ticketscope_ro`), the `ticketscope-db-ro` Secret (generated once via `lookup`), the migrate and load hook Jobs, the api Deployment and Service, and the HTTPRoute for `/v1`. `values.yaml` sets `retrieval.defaultMode: keyword` and `snapshot.version: fixture`.
- `deploy/charts/*/values-kind.yaml` -- hostname, gateway class and storage class only.
- `scripts/kind-up.sh` -- builds images for the native arch if missing, creates kind (node image pinned to 1.36), starts cloud-provider-kind, `kind load`s the images, installs `platform --wait` and then `ticketscope`, and waits for api to be Ready. It prints timestamps and the Gateway address.
- `.github/workflows/ci.yml`, `.github/workflows/_kind-deploy.yml` -- see Design Notes.
- `tests/unit/`, `tests/smoke/test_gateway.py` -- see Tasks.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `.importlinter`, `.gitignore`, `src/ticketscope/**` -- the packages above -- AD-1, AD-4, AD-9, AD-19, AD-20
- [x] `migrations/0001_init.sql` -- the schema and grants -- AD-7, AD-21
- [x] `snapshot/*` -- the schema, fixture and kinds sidecar -- AD-6
- [ ] `images/*.Dockerfile` -- both images -- AD-2, AD-9, AD-16
- [ ] `deploy/charts/{platform,ticketscope}/**` -- both releases -- AD-13, AD-14, AD-22, AD-25
- [ ] `scripts/kind-up.sh` -- the only kind bring-up -- AD-17
- [ ] `.github/workflows/{ci,_kind-deploy}.yml` -- PR CI and the reusable deploy -- AD-16, AD-17
- [x] `tests/unit/` -- contract shape; the keyword retriever and REGISTRY over the fake; the I/O matrix through `create_app` with the fake injected; the fixture validates against the schema and parses as `SnapshotIssue`; the sidecar covers every fixture issue with both kinds present
- [ ] `tests/smoke/test_gateway.py` (marker `kind`) -- reads `TICKETSCOPE_GATEWAY_URL` and `TICKETSCOPE_GATEWAY_HOST`, posts the target query, asserts the Best-match row and that the response parses as `SearchResponse`, and checks the Cluster through `kubectl`: `readyInstances == 2`

**Acceptance Criteria:**
- Given a PR, when `ci.yml` runs, then ruff, pyright, pytest and lint-imports pass, and `_kind-deploy` brings up both releases and passes the smoke test.
- Given a PR that changes `images/`, when `ci.yml` runs, then both images build for `linux/amd64` and `linux/arm64`.
- Given a one-line change that makes a `core` module import `ticketscope.adapters.postgres`, when `lint-imports` runs, then it fails.
- Given a `_kind-deploy` run, when it finishes, then its job summary shows peak memory, free disk, and the wall-clock time from kind-up to api Ready.

## Implementation Notes

- **Extensions are not trusted.** The PGDG control files for `pg_textsearch` 1.5.1 and `vector` 0.8.7 carry no `trusted = true`, so the Cluster's `postInitApplicationSQL` creates both as superuser and 0001 keeps `CREATE EXTENSION IF NOT EXISTS` (the Design Notes fallback).
- **pg_textsearch packaging.** PGDG ships `postgresql-18-pg-textsearch` 1.5.1 for trixie, and the CNPG `18-standard-trixie` image already has the PGDG apt source, so no source build was needed.
- **Keyword SQL.** The query names the index (`to_bm25query(q, 'issue_search_bm25_idx')`) because psycopg binds parameters out of line, and pg_textsearch needs the name for parameterized queries. A subquery keeps the BM25 `ORDER BY … LIMIT` and then drops rows whose score is not negative, so a query with no fixture terms returns `[]`.
- **Load re-run.** `load` uses `TRUNCATE issue` plus `COPY`, then replaces the single `corpus_meta` row, all in one transaction. `corpus_meta` has a boolean singleton primary key, so a second row is impossible.
- **Mode validation.** The contract types `mode` as `"keyword"|"dense"|"hybrid"`, so `nope` gets FastAPI's default 422. A contract-valid mode missing from `REGISTRY` (`dense` today) also returns 422, from the route. Story 6 owns the body shape.
- **Gateway address.** `kind-up.sh` reads the Gateway's `status.addresses[0]` on Linux. On macOS kind nodes are not reachable from the host, so it port-forwards the Envoy Service to `127.0.0.1:18080` instead. cloud-provider-kind runs with `--gateway-channel=disabled --enable-default-ingress=false`, so Envoy Gateway is the only Gateway API implementation and no Ingress exists.
- **Gateway CRD ordering.** Envoy Gateway's chart keeps the Gateway API CRDs in its `crds` subchart's `crds/` directory, which Helm installs before templates. No separate CRD step was added. This is unverified until the first `_kind-deploy` run.
- **Chart.lock not committed yet.** `helm` could not be installed in the build session, so `deploy/charts/platform/Chart.lock` was not generated. `kind-up.sh` and the `charts` CI job fall back to `helm dependency update` when the lock is missing (CI warns). Run `helm dependency update deploy/charts/platform` once and commit the lock.
- **Pyright** runs strict on `src` and standard on `tests`, because the TestClient types are only partly known.
- **ruff** excludes the vendored `_bmad`, `.agents`, `.claude` and `.codex` trees.
- **httpx2.** The smoke test uses `httpx2`, the spine's client, and Starlette's TestClient uses it too.

## Plan Change Log

## Review Triage Log

**Pass 1 (quick lens).** Verdicts: high 1, medium 2, low 2, false 1, rejected 1 (maybe-false 0).

| # | Finding | Verdict | Route | Evidence / action |
|---|---------|---------|-------|-------------------|
| 1 | `tests/smoke/test_gateway.py` load re-run test uses `kubectl create job --from=job/…` | high | patch | kubectl's `--from` accepts only `cronjob/`, so with `check=True` the smoke step fails every PR. Replace it with `helm upgrade --reuse-values`. |
| 2 | The same test skips the matrix's "Helm upgrade with the same pin" path and its hooks | medium | patch | It re-ran only the load container. The fix in #1 runs the pre-upgrade migrate and post-upgrade load hooks, and an appending load would fail the upgrade on the issue PK and the corpus_meta singleton. |
| 3 | `.importlinter` core and contract contracts are deny-lists | medium | patch | `core` importing `httpx2` or `jsonschema` passes lint-imports, which erodes the "stdlib and pydantic only" rule. Add an AST allow-list unit test. |
| 4 | `kind-up.sh` macOS branch: empty `ENVOY_SVC` lookup | low | patch | `pkill -f "port-forward.*"` then kills every user port-forward and the script exits 0 with a dead URL. Fail fast when the lookup is empty. |
| 5 | `deploy/charts/platform/Chart.lock` not committed | low | defer | Real, but both dependencies are pinned to exact versions, so the only loss is helm's digest check. Generating the lock needs helm, which is unavailable in this build. Logged in deferred-work.md. |
| 6 | Plan tasks unchecked while `in-review`; AC1, AC2 and AC4 unproven | rejected | — | The fix would edit this build's plan. The CI proof comes from the draft PR in step 5. |
| 7 | `controllerName` in platform `values-kind.yaml` is not an environment fact | false | — | The controller is part of the gateway class: Envoy on kind, the AWS LB controller on EKS. AD-25 lists "gateway class" as an environment fact. |

## Design Notes

- **Who runs the check.** A reusable workflow's cluster dies with its job, so `_kind-deploy.yml` takes a `check` input (a shell command) and runs it after `kind-up.sh`. `ci.yml` calls it with `uv run pytest -m kind tests/smoke`. `eval.yml` will reuse it the same way.
- **cloud-provider-kind runs on the host**, as a container on the `kind` docker network started by `kind-up.sh`, because it needs the docker socket. The platform chart holds Envoy Gateway; cloud-provider-kind gives the Envoy Service its LoadBalancer IP. The smoke test hits that IP with the `Host` header.
- **No `--wait` on the ticketscope install.** Helm's wait would block hooks on api readiness, and api readiness needs `load`. So `migrate` polls until it can connect and the role exists, and `kind-up.sh` runs `kubectl rollout status` on api afterwards.
- **Extensions.** If `vector` or `pg_textsearch` is not `trusted` in its control file, the app owner cannot create it. In that case the Cluster's `postInitApplicationSQL` creates it as superuser, and 0001 keeps `CREATE EXTENSION IF NOT EXISTS`.
- **pg_textsearch packaging.** If no PGDG package exists for PG18 on the CNPG base, build it from the tagged source release in a builder stage.
- **Multi-arch** builds run on native `ubuntu-24.04` and `ubuntu-24.04-arm` runners (free for public repos), path-gated on `images/**`. This avoids QEMU.
- **Gateway CRD ordering.** If the Gateway or GatewayClass fails to map on a fresh install because the CRDs are subchart templates, install the CRDs first in `kind-up.sh` with the chart's `crds` output, and record that here.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `helm lint deploy/charts/platform deploy/charts/ticketscope -f <each values-kind.yaml>` -- expected: no errors (helm runs in CI if it is not installed locally)
- Temporarily add `import ticketscope.adapters.postgres` to `src/ticketscope/core/modes.py`, run `uv run lint-imports`, and confirm it fails; then revert.
- Push the branch and open a draft PR -- expected: `ci.yml` is green, including the `_kind-deploy` smoke job and the multi-arch image builds.

**Manual checks (if no CLI):**
- The `_kind-deploy` job summary shows the three runner-fit numbers.
- Person's step (hitl): run `scripts/kind-up.sh` on a local machine and confirm the same smoke test passes.
