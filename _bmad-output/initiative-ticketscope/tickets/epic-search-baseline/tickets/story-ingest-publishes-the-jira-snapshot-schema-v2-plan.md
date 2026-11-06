---
title: 'Ingest publishes the Jira snapshot (schema v2)'
type: 'feature'
ticket: '13'
created: '2026-11-06'
status: 'built'
baseline_revision: 'f4de1fb5c40119747da0cbbfa50a21388ad5dd3e'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The corpus moved to the Mojang subset of The Public Jira Dataset v7 (spike 12), but `jobs.ingest` still calls the GitHub API, the committed schema, fixture and `load` are v1, and `snapshot.yml` publishes from a runner that cannot hold the 60 GB dump (AD-6).

**Approach:** Replace the GitHub ingest with one that reads a locally restored dump through pymongo, builds `SnapshotIssueV2` records (masked, identity-free, Duplicate links only) and reports counts with core's rules. Generate `snapshot/schema-v2.json` from the core model, move the fixture and `load` to v2, and replace `snapshot.yml` with a committed person-run `scripts/publish-snapshot.sh` that keeps story 3's guards.

## Boundaries & Constraints

**Always:**
- Scope: instance `Mojang`, projects MCL, REALMS, MCD; every resolved issue plus each unresolved in-scope issue that a resolved duplicate's `core.duplicate_target` points to (AD-26). Repeated keys: the first document by `_id` wins, so a re-run is byte-identical.
- Each record is a `SnapshotIssueV2`: `number` = Jira `id`, `key`, `url` = `https://bugs.mojang.com/browse/<key>`, `issue_type`, `resolution` (raw name), `resolved_at`, comments with `from_reporter` (author masked id == reporter masked id), and `duplicate_links` holding only links whose type maps to Duplicate in the spike's `jira_issue_linktype_mapping.json` (settles story 14's deferral). No reporter, assignee, creator or author id, masked UUIDs included.
- Title, body and comment bodies go through story 3's `mask`, then `[~user]`/`[~accountid:…]` mentions become `[~user]`.
- `snapshot/exclusions.txt` holds Jira keys; an excluded issue is never written, nor added as an open target.
- The report holds the subset, issue count, open targets added, repeated keys dropped, excluded, resolved issues without a resolution date, the kind split and in-subset duplicate pairs by kind (one per duplicate issue whose target is in the snapshot, under that issue's kind).
- `schema-v2.json` is generated from `SnapshotIssueV2`; a test fails when the committed file drifts. `load` parses only v2 and refuses any other line.
- The publish script runs only from a clean checkout of `main` equal to `origin/main`, takes the next free `YYYY.MM.N`, checks the checksum, validates every line against schema v2 and the model, requires the timed load ≤ 600 s, and creates `snapshot-<v>` targeting that commit without `--clobber`. Release notes come from a tested renderer and carry the commit, counts, load time and spike 12's attribution line; the README carries it too.
- pymongo lives in a uv `ingest` dependency group; the app image does not include it.

**Never:**
- No raw dump document committed; the recorded slice is synthetic, dump-shaped and already identity-free in its text.
- No kind or outcome written into the snapshot; no change to core's derive rules, migrations, `/v1` contract or the values pin (story 5).
- No workflow runs ingest or publishes (AD-17); no Release deletion by the script.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Resolved in scope | MCL issue, resolution `Fixed` | one valid v2 record | No error expected |
| Out of scope | resolved `MC-1`; unresolved MCL no duplicate points to | absent | No error expected |
| Open target | resolved `Duplicate` → unresolved REALMS-9 | REALMS-9 written, `state` open | No error expected |
| Repeated key | two documents MCL-5 | first by `_id` kept once | No error expected |
| Non-Duplicate link | `Relates` link | not in `duplicate_links` | No error expected |
| Comment flags | reporter / other before / other after resolution | `from_reporter` true / false / false; answered rule sees only the before | No error expected |
| Identities | ids in reporter, assignee, creator, comment authors | none appear in the gz output | No error expected |
| Masking | email, `ghp_…`, `[~alice]`, `[~accountid:5b1…]` | markers; originals absent | No error expected |
| Excluded | key in `exclusions.txt` | absent, counted | Malformed line → `ValueError` with line |
| Bad time | unparseable `created` | — | issue skipped and counted, run continues |
| Not main / dirty | publish script elsewhere | refuses before ingest | exit non-zero |
| Over budget | timed load > 600 s or schema-invalid line | no Release | exit non-zero |

</frozen-after-approval>

## Code Map

- `src/ticketscope/core/snapshot.py`, `core/derive.py` -- `SnapshotIssueV2`, `duplicate_target`, `derive_kind`, `derive_outcome`, `DEFAULT_KIND_THRESHOLD`. Reuse; do not change.
- `src/ticketscope/jobs/ingest/mask.py` -- reuse `mask`; add `mask_jira` (mentions after `mask`).
- `src/ticketscope/jobs/ingest/version.py` -- keep `next_version`.
- `src/ticketscope/jobs/ingest/main.py` -- REWRITE: CLI `--version --out-dir --mongo-uri --database --exclusions`; writes `<v>.jsonl.gz` (sorted by `number`, gzip mtime 0), `.sha256`, `<v>-kinds.json`, `report.json`. Keep `_write_atomic`, output naming and exit codes.
- `src/ticketscope/jobs/ingest/jira.py` -- NEW, pure: dump document → `SnapshotIssueV2`, `select` (dedupe, scope, open targets), `report`.
- `src/ticketscope/adapters/jira_dump.py` -- NEW: pymongo reader, `find({"fields.project.key": {"$in": …}}).sort("_id", 1)` with a projection like the spike's `measure.PROJECTION` plus link side `id`s. Only module importing pymongo.
- `src/ticketscope/jobs/ingest/notes.py` -- NEW: `render_notes(report, load_seconds, commit)` + `python -m` CLI; `ATTRIBUTION` constant from `terms.md`.
- `src/ticketscope/jobs/ingest/schema.py` -- NEW: `schema_v2()` from `SnapshotIssueV2.model_json_schema()` with `$schema` 2020-12 and `$id`; `python -m … --write` regenerates; `check(path)` validates a gz asset against schema and model.
- `src/ticketscope/jobs/ingest/linktypes.json` -- NEW: copy of the spike's `jira_issue_linktype_mapping.json` (package data).
- `src/ticketscope/adapters/github.py`, `jobs/ingest/select.py`, `tests/unit/ingest/`, `tests/unit/test_ingest_github.py`, `.github/workflows/snapshot.yml`, `snapshot/schema-v1.json` -- DELETE. Keep `httpx2` (smoke tests use it).
- `src/ticketscope/jobs/load/main.py` -- parse `SnapshotIssueV2`; row `state_reason=None`, `closed_at=resolved_at`; rest unchanged (story 5 derives).
- `snapshot/fixture.jsonl` -- rewrite as 8 synthetic v2 issues, same numbers and expected kinds (`{code}`/`{noformat}` in log-heavy ones); `fixture-kinds.json` unchanged. `tests/target.py`, smoke test keep working.
- `snapshot/exclusions.txt`, `README.md` -- keys; Mojang attribution and takedown via the publish script.
- `scripts/publish-snapshot.sh` -- NEW; reuses `scripts/time-load.sh` unchanged.
- `images/app.Dockerfile` -- drop the `exclusions.txt` copy (ingest no longer runs from the image, AD-2).
- `pyproject.toml`, `uv.lock` -- `[dependency-groups] ingest = ["pymongo~=4.…"]`; description to Mojang. `.importlinter` unchanged (adapters may import pymongo).
- Spike reference (read-only): `spike-choose-the-jira-corpus-findings/measure.py` (`parse_time`, `_user`, `comments_of`, `is_duplicate_linktype`), `convert.py`, `terms.md`.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock` -- ingest group with pymongo; description -- AD-2
- [x] `src/ticketscope/adapters/jira_dump.py` -- Mongo reader -- AD-1, AD-6
- [x] `src/ticketscope/jobs/ingest/{jira,main,mask,schema,notes}.py`, `linktypes.json` -- mapping, selection, masking, outputs, report, schema, notes
- [x] delete the GitHub ingest, `snapshot.yml`, `schema-v1.json`; generate `snapshot/schema-v2.json` -- AD-6, AD-17
- [x] `src/ticketscope/jobs/load/main.py`, `snapshot/fixture.jsonl`, `images/app.Dockerfile` -- v2 load and fixture
- [x] `scripts/publish-snapshot.sh`, `README.md`, `snapshot/exclusions.txt` -- person-run publish, attribution, takedown
- [x] `tests/unit/ingest/slice.json` + `tests/unit/test_ingest_jira.py`, `test_ingest_notes.py`, `test_snapshot.py`, `test_load_main.py` -- every matrix row and test-design rows for story 13 (P2 "valid Jira snapshot" 1–8, "no identities" 1–5, "fixture and load move to v2" 1–2, "Release notes report" 1–2)

**Acceptance Criteria:**
- Given the recorded slice, when ingest runs through `jira.select` and `main.write_outputs`, then every line validates against `schema-v2.json` and parses as `SnapshotIssueV2`, and `sha256sum -c` passes.
- Given `SnapshotIssueV2` changes, when tests run, then the schema drift test fails until `python -m ticketscope.jobs.ingest.schema --write` is rerun.
- Given the v2 fixture, when `scripts/time-load.sh` runs on it, then it prints a load time and exits 0.
- Given a restored dump on the person's machine after merge, when `scripts/publish-snapshot.sh` runs, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, with notes stating subset, count, pairs by kind, kind split, load seconds ≤ 600 and the attribution line.

## Implementation Notes

- `jsonschema` moved from `dev` into the `ingest` group (the publish script's `schema --check` needs it); `dev` includes `ingest` via `include-group`, so `uv sync --locked` in CI installs pymongo for pyright/tests while the image's `--no-dev` sync leaves both out (checked with `docker build` + `find_spec`).
- `tests/unit/test_ingest.py` (the GitHub ingest's tests) was deleted along with `test_ingest_github.py`; `Settings.ingest_github_token` was removed with the GitHub ingest. `mask_optional` was dropped (no caller left).
- `main` imports `adapters.jira_dump` lazily, so `write_outputs`/`select` need no pymongo. `main` refuses a `--version` that is not `YYYY.MM.N` and an empty selection.
- Over-budget guard is enforced twice: the script checks `<= 600`, and `notes.render_notes` refuses a load time over 600 s (no notes, no Release).
- Extra test `tests/unit/test_publish_script.py`: the script's guards in a throwaway git clone with stubbed `uv`/`gh`/`docker` (off main, dirty, HEAD != origin/main refuse before any tool runs).
- Verified also against a real MongoDB (`mongo:7` with the slice inserted): `ticketscope-ingest`, `shasum -c`, `schema --check`, `notes`, and `scripts/time-load.sh` on the output (exit 0).

## Plan Change Log

## Review Triage Log

### 2026-11-06 — Review pass (quick)
- verdicts: 5 findings — high 0, medium 0, low 3, false 2, maybe-false 0
- findings:
  - `[low]` `[reject]` `jira.to_issue` gives `from_reporter=False` to a comment without an author id, and to every comment of an issue without a reporter, so core's answered rule could count them (the spike required a known author). Real, but the subset has 0.0% Question/Support issues (findings.md, candidate subsets), so the answered rule cannot fire here. The suggested fix (`True` for an unknown author) would contradict AD-6's meaning of `from_reporter`. Revisit if the corpus gains Question/Support issues.
  - `[false]` `[reject]` `select` aborts on a document without a usable `id` or on two keys sharing an `id`. This is a deliberate loud failure: `number` is the primary key, so a shared id would break the load. Only an unparseable time is specified as skip-and-count.
  - `[low]` `[patch]` `mask_jira` turns `[~jane@example.com]` into `[~user]]`, because emails are masked before mentions. Fix: replace mentions before `mask`; a test case was added.
  - `[low]` `[patch]` The `core/snapshot.py` docstring still points at the deleted `snapshot/schema-v1.json`. Fix: a docstring-only rewording.
  - `[false]` `[reject]` No test runs `sha256sum -c`. The `.sha256` line is `<digest>  <name>`, exactly the format `sha256sum -c` reads; the publish script runs it, and it passed in the manual run against a real MongoDB.

## Design Notes

- **Link direction.** For a Duplicate-mapped link, the side present gives the text: `outwardIssue` → `type.outward`, `inwardIssue` → `type.inward`; `"duplicates"` → `duplicates`, anything else → `duplicated_by`. `target_number` is the side's `id`; if absent, the dump's id for that key within scope; else the link is dropped and counted. Self-links are dropped.
- **Times.** Jira `2021-12-28T20:34:52.000+0200` → aware UTC (spike `parse_time`). A comment without a parseable time is dropped.
- **Person-run sequence.** `docker run mongo` + `mongorestore` of the dump → `scripts/publish-snapshot.sh` (needs `gh auth` with write access and Docker). Since the script requires `main`, the first publish happens after this PR merges; the person then deletes the `INGEST_GITHUB_TOKEN` repo secret.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `uv run pytest tests/unit -k "ingest or snapshot or load" -v` -- expected: one passing case per matrix row and test-design case
- `scripts/time-load.sh` on the gzipped v2 fixture -- expected: exit 0 and a time (needs Docker)
- `docker build -f images/app.Dockerfile .` -- expected: builds without pymongo

**Manual checks:**
- Person-run publish after merge (Approach); compare 20 sampled records against bugs.mojang.com, including a duplicate pair and a Question/Support issue.
