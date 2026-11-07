---
title: 'Load the pinned snapshot with kind and outcome'
type: 'feature'
ticket: '5'
created: '2026-11-06'
status: done
baseline_revision: 'b525b53e51c3c095a05c249b6eae3834a46b5324'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
followup_review_recommended: false
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md'
warnings: ['oversized']
deferred: []
---

<intent-contract>

## Intent

**Problem:** `load` still reads the kinds sidecar of a snapshot baked into the image (`fixture`), writes every outcome as `unknown`, reloads on every upgrade, and records no preprocessing version. So no environment serves the real Mojang corpus, and nothing records kind or outcome (R2, AD-8, AD-21, AD-22, AD-25).

**Approach:** Pin the published snapshot `2026.11.1` and its SHA-256 in `values.yaml`. `load` checks `corpus_meta` first and does nothing when the snapshot, model and preprocessing version all match. Otherwise it downloads the Release asset and verifies its checksum. It derives kind and outcome with core's functions, swaps the corpus in one transaction and logs a report. Also commit the golden-query file, and move the kind smoke checks to the real snapshot.

## Boundaries & Constraints

**Always:**
- Kind and outcome come only from `core.derive.derive_kind` / `derive_outcome` (default threshold), with `outcome_summary/source/ref` from the `Outcome`. The sidecar is never read by `load`.
- Kind threshold stays **3** (re-measured on 2026.11.1: t=2 → 342 log-heavy pairs, t=3 → 309, t=4 → 279, t=5 → 262; floor ≈ 200). Only the "provisional" comment on `DEFAULT_KIND_THRESHOLD` changes. The derivation version stays `kind2-t3.outcome3`.
- `core` exposes `preprocessing_version()` = `f"{PREPROCESSING_RULE_VERSION}.{derivation_version()}"` with `PREPROCESSING_RULE_VERSION = "pre1"` (search-text construction), so a derivation change changes it. `search_text` moves into core beside it.
- Checksum is mandatory. An empty pin, a mismatch, or a download failure means exit 1 before any DB write. A local `<snapshot_dir>/<v>.jsonl.gz` is used if present, and is checked against the same pin.
- The no-op check runs before any download. It compares `(snapshot_version, embedding_model_id=None, preprocessing_version())` with the `corpus_meta` row, and logs a line containing `no-op`. Any difference logs `reloading` with the reason.
- The reload is one transaction (`replace_corpus`: TRUNCATE + COPY + `corpus_meta` with `preprocessing_version` and `embedding_model_id` NULL), so `api` sees the old corpus or the new one.
- The report is one log line, `load report:`, with the issue count, % per kind, % per outcome (all six statuses, zeros included), `load_seconds` and `budget_seconds=600`. It also carries `within_budget=true|false`, logged at WARNING when false.
- `values.yaml` holds `snapshot.version`, `snapshot.sha256` and `snapshot.baseUrl`; environment files never override them (AD-25). Unit tests keep the fixture; the image no longer ships it.
- Golden-query file `eval/golden-queries.json`: `snapshot_version`, `mode: keyword`, `k: 10`, and per entry: `id`, `kind`, `query`, `chosen_by`, `source_issue {number,key}`, `expected_issue {number,key}`, `known_keyword_miss`. No OS user-name paths or other person identifiers in committed text.

**Never:**
- No change to derive rules, `KIND_RULE_VERSION`/`OUTCOME_RULE_VERSION`, migrations, the `/v1` contract, ingest's outputs or the published Release.
- No golden-query gate in the kind check (story 11 owns it). No embedding work.
- No `pytest -m kind` test that leaves `corpus_meta` stale at the end.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| First load | empty DB, or row from story 1 (`fixture`, NULL preprocessing) | download, verify, load 32,153 issues, row = pin + `pre1.kind2-t3.outcome3` | No error expected |
| Same pin | row matches | logs `no-op`, no download, no write, exit 0 | No error expected |
| Derivation changed | row's preprocessing differs | logs `reloading` (preprocessing), full reload | No error expected |
| Wrong checksum | asset bytes ≠ pinned SHA-256 | exit 1, `replace_corpus` never called, old corpus kept | error logged with both digests |
| Empty pin | `TICKETSCOPE_SNAPSHOT_SHA256` unset | exit 1 before download | error names the setting |
| Download fails | HTTP error / timeout | exit 1, partial file removed, old corpus kept | error logged |
| Non-v2 line | v1 line | exit 1 (existing behavior) | error with line number |
| Fixture kinds | each fixture issue | computed kind == `fixture-kinds.json` | — |

</intent-contract>

## Code Map

- `src/ticketscope/core/derive.py` -- add `PREPROCESSING_RULE_VERSION`, `preprocessing_version()`, `search_text(issue)` (moved from load, same text). Comment on line 21 only otherwise.
- `src/ticketscope/adapters/release.py` -- NEW: `fetch_snapshot(base_url, version, dest_dir, sha256, *, timeout)`. Use a local file if present, else stream `{base_url}/snapshot-{v}/{v}.jsonl.gz` with `httpx2` (already a runtime dependency; follow redirects) into a temp file. Hash while streaming, rename on match, delete on mismatch, raise `ChecksumMismatch`.
- `src/ticketscope/adapters/postgres.py` -- `CorpusMeta(snapshot_version, embedding_model_id, preprocessing_version)` dataclass; `read_corpus_meta(conninfo) -> CorpusMeta | None`; `replace_corpus(conninfo, meta, rows)` writes all three meta columns. Keep the single transaction.
- `src/ticketscope/jobs/load/main.py` -- rewrite flow: settings → wait → meta compare (no-op) → fetch → `build_rows(issues)` derives kind/outcome, counting into a `Counter` → `replace_corpus` → report. Drop `read_kinds` from `load` (conftest and the kind unit test read `fixture-kinds.json` directly).
- `src/ticketscope/settings.py` -- `snapshot_sha256: str = ""`, `snapshot_base_url: str = "https://github.com/Dillon-Based/ticketscope/releases/download"`, `snapshot_download_timeout_seconds: int = 300`.
- `deploy/charts/ticketscope/values.yaml` -- `snapshot.version: "2026.11.1"`, `sha256: "e7940ba12db44b9ac909e2634d537e30406448f45a9d780fd96fa7e6ec211b2f"`, `baseUrl`. Remove the "Story 5 swaps" comment.
- `deploy/charts/ticketscope/templates/jobs.yaml` -- load Job env for SHA256 (`required`), base URL, and `TICKETSCOPE_SNAPSHOT_DIR=/snapshots`, with an `emptyDir` volume there (the image user 10001 cannot write `/app`).
- `images/app.Dockerfile` -- drop the fixture copy and `/app/snapshots`.
- `scripts/time-load.sh` -- stop requiring `<v>-kinds.json`; export `TICKETSCOPE_SNAPSHOT_SHA256` computed from the local asset (`shasum -a 256` / `sha256sum`). `publish-snapshot.sh` keeps calling it unchanged; ingest still writes the sidecar (unused, left alone).
- `tests/unit/conftest.py` -- `snapshot_dir` drops the sidecar; `fixture_store` uses the new `build_rows`; add `fixture_sha256` and set the env var in load tests.
- `tests/unit/test_load_main.py` -- matrix rows with fakes: monkeypatch `read_corpus_meta`, `replace_corpus`, `fetch_snapshot`/HTTP (an `httpx2.MockTransport` or a local file). Also a report-line assertion, and the computed fixture kind against `fixture-kinds.json`.
- `tests/unit/test_release.py` -- NEW: the adapter's checksum mismatch, local-file path and partial-file cleanup.
- `tests/unit/test_golden_queries.py` -- NEW. The file's `snapshot_version` equals the values pin, and each expected issue differs from its source. Each source and expected issue exists in the pinned asset, which the test downloads once per session through `fetch_snapshot` (network, checksum-verified) and checks by number and key.
- `eval/golden-queries.json` -- NEW, the entries in Design Notes.
- `tests/smoke/test_gateway.py` -- rewrite for the real snapshot. Read the pin from `values.yaml` (`yaml` is not a dependency: a regex on the `snapshot:` block is enough). Checks: `corpus_version` == pin, ranked results with outcomes, and `NO_MATCH_QUERY` still returns empty (`xylophone quokka`, verify on the real corpus; replace if it matches). Add the load checks in Tasks; drop the `>= 900000` and `TARGET_NUMBER` asserts (those stay in `test_app.py`/`test_modes.py`).
- `README.md` -- in the takedown steps, the PR also bumps `snapshot.version`/`sha256` in `values.yaml`.
- Evidence: `_bmad-output/.../tickets/story-load-the-pinned-snapshot-with-kind-and-outcome-kind-samples.md` -- NEW, see Tasks.

## Tasks & Acceptance

**Execution:**
- [x] `src/ticketscope/core/derive.py` -- `preprocessing_version`, `search_text`, comment -- AD-8, AD-21
- [x] `src/ticketscope/adapters/release.py`, `adapters/postgres.py`, `settings.py` -- download and verify, meta read and write -- AD-6, AD-21
- [x] `src/ticketscope/jobs/load/main.py` -- no-op, derive, report -- AD-7, AD-8, AD-22
- [x] chart `values.yaml`, `templates/jobs.yaml`, `images/app.Dockerfile`, `scripts/time-load.sh`, `README.md` -- pin, emptyDir, no fixture in the image -- AD-25
- [x] `eval/golden-queries.json` + `tests/unit/test_golden_queries.py` -- R-004 file and its file check
- [x] `tests/unit/conftest.py`, `test_load_main.py`, `test_release.py` -- every matrix row
- [x] `tests/smoke/test_gateway.py` -- in order, in one module: (1) `corpus_version` == pin and keyword results carry outcomes. (2) SQL through `kubectl exec` on the CNPG primary (`-l cnpg.io/cluster=ticketscope-db,cnpg.io/instanceRole=primary`, container `postgres`, `psql -d app -tAc`): issue count == 32153, zero rows with an empty kind or outcome, more than one distinct `outcome_status`, and `corpus_meta` == pin + current preprocessing. (3) `kubectl logs job/ticketscope-load` has the `load report:` line with both kind and six outcome shares and `within_budget=true`. (4) `helm upgrade --reuse-values` → the load log contains `no-op`. (5) `UPDATE corpus_meta SET preprocessing_version='pre0.stale'`, upgrade → log has `reloading`, and the meta row is current again. (6) Two instances ready (keep).
- [x] Evidence file -- 20 short issues with score 2 and 20 log-heavy issues with score 3–4 from 2026.11.1 (seeded random), each with the key linked to bugs.mojang.com, the score and the title. Exclude issues whose text has an OS user-name path. Linked from the PR body.

**Acceptance Criteria:**
- Given the kind CI run, when `uv run pytest -m kind tests/smoke` runs after `kind-up.sh`, then checks (1)–(6) pass on snapshot 2026.11.1.
- Given an asset whose checksum differs from the pin, when `load` runs against a DB already holding a corpus, then it exits 1 and the corpus and `corpus_meta` are unchanged (unit test with fakes, plus the adapter test).
- Given the fixture, when the unit suite runs, then every fixture issue's computed kind equals `fixture-kinds.json`, and `test_app`/`test_modes` still find `TARGET_NUMBER` at rank 1.
- Given `eval/golden-queries.json`, when `test_golden_queries.py` runs, then each source and expected issue exists in the pinned asset, and each expected issue differs from its source.
- Given `scripts/time-load.sh <dir> 2026.11.1` with only the asset in `<dir>`, when it runs, then it exits 0 and prints a time under 600.

## Implementation Notes

- Golden query `log-heavy`: the MCL-866 body names an in-game player (`Going to play offline as '<name>'`). That conflicts with "no person identifiers in committed text", so the committed query replaces that one name with `[user]` (1,223 chars). Re-measured on 2026.11.1 in the in-repo Postgres image: MCL-602 still ranks 9, and MCD-6745 → MCD-6467 still ranks 5. `chosen_by` says so.
- `read_corpus_meta` decodes `bytes`: `time-load.sh`'s throwaway cluster is `SQL_ASCII`, where psycopg returns text columns as bytes. Without the decode, the no-op never matched there. CNPG databases are UTF-8 and unaffected. `PostgresCorpusStore.corpus_version` has the same latent issue (pre-existing, not touched).
- `load` sets the `httpx2` logger to WARNING, because the Release redirect URL carries a signed query that would otherwise be logged.
- `load_seconds` covers fetch, derive and write, measured after the no-op decision.
- `read_kinds` moved to `tests/target.py` (with `fixture_kinds()` and `snapshot_pin()`), for the conftest, `test_snapshot.py` and `test_ingest_jira.py`. The two sidecar-only load tests (`unknown kind`, `no kind`) were removed. `test_app`'s outcome assertion now expects the target's derived `fixed`.
- `.dockerignore` no longer admits `snapshot/`, because the image copies nothing from it.
- `fetch_snapshot` takes an optional `transport` (for `httpx2.MockTransport` in tests).

## Plan Change Log

## Review Triage Log

### 2026-11-06 — Review pass
- verdicts: 1 findings — high 0, medium 0, low 1, false 0, maybe-false 0
- findings:
  - `[low]` `[patch]` `tests/smoke/test_gateway.py` `_load_log()` read `kubectl logs job/ticketscope-load`, which prints one pod only; with the load Job's `backoffLimit: 2` a retried attempt could make checks (3)–(5) read a failed pod's log — patched: `_load_log()` now lists Succeeded pods by `job-name=ticketscope-load`, sorted by creation time, and reads the newest; kind smoke re-run 7/7.

## Design Notes

**Golden queries — for the person's approval at this plan review.** Measured on 2026.11.1 loaded locally with pg_textsearch BM25, k=10, keyword mode; reruns gave the same rank. Method: draw 150 duplicate pairs per kind (`random.Random(5)` over the sorted `(source, duplicate_target)` pairs whose target is in the snapshot). Keep those whose twin ranks in the top 10. Pick the one whose source and twin titles share the fewest words (Jaccard over lowercase words > 2 chars), skipping any with OS user-name paths. Hit rate: log-heavy 27/150, vague 20/150, the expected keyword baseline.

| id | kind | query | source → expected | twin rank |
|---|---|---|---|---|
| `vague` | short | source title verbatim: `Item Level Drops` | MCD-6745 (477621) → MCD-6467 (462385, open, outcome unknown) | 5 |
| `log-heavy` | log_heavy | source title + `\n\n` + body as pasted (1,227 chars, an `InvalidCredentialsException` stack trace) | MCL-866 (40574) → MCL-602 (38127, Fixed, "Login error when switched to another profile") | 9 |

Both twins rank in the top 10, so `known_keyword_miss: false` for both. Alternate vague entry: MCL-9284 → MCL-9282 at rank 5. The log-heavy runner-up, MCL-189 → MCL-50 at rank 4, was rejected because its body holds a Windows user-folder name. `chosen_by` records the method above in one sentence.

**Provenance finding (not fixed here).** 1,188 of the 32,153 issues in the published 2026.11.1 hold an OS user-folder path (`C:\Users\<name>\…`), often a real name. Some bodies also name Mojang staff in `{panel:title=…}`. Ingest's masking does not cover these, so the Provenance convention ("no person identifiers anywhere") is not met by the published asset. Record this as a residual risk for an ingest follow-up. This story only keeps such text out of the files it commits.

**No-op before download** keeps upgrades fast and lets the kind check prove idempotence from the log alone. Tampering with `corpus_meta` in step (5) is how CI shows "a changed derivation version reloads" without a code change. The unit test covers the real path by monkeypatching `derivation_version`.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass (the golden-query test needs network access to github.com)
- `uv run pytest tests/unit/test_load_main.py tests/unit/test_release.py tests/unit/test_golden_queries.py -v` -- expected: one passing case per matrix row and AC
- `helm lint deploy/charts/ticketscope -f deploy/charts/ticketscope/values-kind.yaml --set-string image.app.tag=lint --set-string image.postgres.tag=18-lint` -- expected: passes
- `gh release download snapshot-2026.11.1 -p '2026.11.1.jsonl.gz' -D <tmp> && scripts/time-load.sh <tmp> 2026.11.1` -- expected: exit 0, seconds < 600
- `scripts/kind-up.sh && uv run pytest -m kind tests/smoke` (or the PR's `kind-deploy` job) -- expected: all pass

**Manual checks:**
- The person approves the two golden queries above, and reads the kind-samples evidence to see that the split reads right.

## Auto Run Result

Status: built

**Summary.** `load` now serves the published Mojang snapshot `2026.11.1`, pinned with its SHA-256 in `values.yaml`. It does nothing when `corpus_meta` already matches the pin, the embedding model (none) and `preprocessing_version()` (`pre1.kind2-t3.outcome3`), and logs `no-op`. Otherwise it logs `reloading` with the reason, downloads the Release asset and verifies it, derives kind and outcome with core, swaps the corpus in one transaction, and logs one `load report:` line. The kinds sidecar is no longer read, and the image no longer ships the fixture. The golden-query file is committed, and the kind smoke checks run on the real snapshot.

**Files changed**
- `src/ticketscope/core/derive.py`: adds `PREPROCESSING_RULE_VERSION`, `preprocessing_version()` and `search_text()` (moved from load). The threshold comment records the measurement.
- `src/ticketscope/adapters/release.py` (new): `fetch_snapshot` downloads with a streamed hash, uses a local file when present, and checks it against the same pin. It removes partial files and raises `ChecksumMismatch`.
- `src/ticketscope/adapters/postgres.py`: adds `CorpusMeta` and `read_corpus_meta` (which decodes bytes from a SQL_ASCII database). `replace_corpus` writes all three meta columns.
- `src/ticketscope/jobs/load/main.py`: the flow is pin, then no-op check, then fetch, derive, swap and report. The over-budget report logs at WARNING. httpx2 INFO logging is silenced, because the redirect URL is signed.
- `src/ticketscope/settings.py`: adds the sha256, base URL and download timeout settings.
- `deploy/charts/ticketscope/values.yaml` and `templates/jobs.yaml`: the pin. The load Job env has a required sha256, and the `/snapshots` emptyDir is added.
- `images/app.Dockerfile` and `.dockerignore`: no snapshot is shipped in the image.
- `scripts/time-load.sh`: needs only the asset, and sets the checksum from it.
- `README.md`: the takedown steps now include the PR that bumps the pin.
- `eval/golden-queries.json` (new): the vague MCD-6745 → MCD-6467 and log-heavy MCL-866 → MCL-602 entries. One player name in the log-heavy query is replaced with `[user]`.
- Tests:
  - New: `tests/unit/test_release.py` and `tests/unit/test_golden_queries.py`.
  - Rewritten: `tests/unit/test_load_main.py` and `tests/smoke/test_gateway.py`.
  - Updated: `tests/target.py`, `tests/unit/conftest.py`, `test_app.py`, `test_snapshot.py` and `test_ingest_jira.py`.
- Evidence (new): [story-load-the-pinned-snapshot-with-kind-and-outcome-kind-samples.md](story-load-the-pinned-snapshot-with-kind-and-outcome-kind-samples.md).

**Review (quick lens).** The review raised 1 finding and 1 patch was applied: `low`, the smoke log helper now reads the Succeeded load pod. Nothing was deferred or rejected.

**Follow-up review recommended:** false. The pass patched 0 high, 0 medium and 1 low.

**Verification**
- ruff, the format check, pyright and lint-imports are clean. `pytest` gives 418 passed; the golden-query test downloads the pinned asset from github.com.
- The matrix and AC tests pass: 32 in `test_load_main.py`, `test_release.py` and `test_golden_queries.py`. Every I/O matrix row has a covering test.
- `helm lint` passes.
- `scripts/time-load.sh <dir> 2026.11.1`, with only the downloaded asset in `<dir>`, exits 0 in 2.8 s and loads 32,153 issues. The outcome shares match the plan.
- `scripts/kind-up.sh` on a fresh cluster built from the working tree, then `pytest -m kind tests/smoke`, passes 7 of 7, before and after the patch.

**Residual risks**
- 1,188 issues in the published snapshot hold OS user-folder paths that often contain real names, which goes against the Provenance convention. This belongs to an ingest follow-up.
- The manual check is still owed: the person approves the two golden queries, including the `[user]` masking of one player name in MCL-866's body, and reads the kind-samples evidence.
- CI needs network access to github.com for `test_golden_queries.py` and for the load Job.
- `PostgresCorpusStore.corpus_version` has the same SQL_ASCII bytes issue that this change fixed in `read_corpus_meta`. It predates this story, and CNPG (UTF-8) is not affected.
- Locally: deleting a kind cluster leaves the `ticketscope-cloud-provider-kind` container trusting the old CA, so the Gateway never becomes Programmed until that container is removed.
- No operator actions outside the repo are owed.
