<!-- bmad:context -->
<!-- Verified 2026-11-11 against 197de6b. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## ticketscope

Similar-issue search (keyword, dense, hybrid) over Mojang bug-tracker issues from The Public Jira Dataset v7. Python 3.14, uv, FastAPI, Postgres 18, MCP server, Helm on kind/EKS. Architecture spine: `_bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md` (AD-n ids); tickets: `_bmad-output/initiative-ticketscope/tickets/`.

## Policy

- Never write person identifiers (masked ids included); keep masking of mentions, emails and secrets in every committed or published artifact. Never commit raw dump documents.
- Never overwrite a published snapshot Release; each publish is the next `snapshot-YYYY.MM.N`. Takedown steps are in `README.md`.
- Never hand-write `eval/baseline.json` or the README results table; the baseline is CI output only (`docs/decisions/adr-eval-baseline-is-ci-output-only.md`), the table comes from `python3 scripts/render_readme_table.py --write`.
- Call it "a personal project, deployed and operated on Kubernetes", never "production". Nothing from youscope.

## Where things are

- Wiring lives in three composition roots: `ticketscope.http.app`, `ticketscope.mcp.main`, `ticketscope.jobs.<job>.main`.
- Decisions: `docs/decisions/`. Deferred items: `_bmad-output/deferred-work.md`.

## Running and verifying

- Python 3.14 only (`requires-python`); use `uv run`, never bare `pytest`/`ruff`.
- CI also runs `uv run lint-imports` and `python3 scripts/render_readme_table.py --check`; `pytest` alone covers neither.
- `tests/postgres` and `tests/image` skip silently without `TICKETSCOPE_TEST_PG_IMAGE` (built from `images/postgres.Dockerfile`); set `TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1` to make a skip fail.
- `-m kind` tests (`tests/integrated`, `tests/smoke`) need a cluster from `scripts/kind-up.sh`; default runs exclude them.
- Tag tests with `@pytest.mark.criterion("<story key>--AC-<n>")`; `scripts/live_results.py` reads it.

## Conventions that differ from defaults

- Join issues on `number` (integer Jira id), never on `key` (`MCL-123`, display only).
- `load` is the only writer of corpus tables; `api` and `eval` use the read-only role. Schema changes are plain SQL in `migrations/`, applied only by the `migrate` Job.
- `kind` and `outcome` are computed once in `core` at load; never recompute them in api, page or eval. Changing them, or the duplicate-cluster rule, requires a reload and a new baseline.
- Config is `TICKETSCOPE_*` env vars read by one settings module per process; no config files in images.

<!-- /bmad:context -->
