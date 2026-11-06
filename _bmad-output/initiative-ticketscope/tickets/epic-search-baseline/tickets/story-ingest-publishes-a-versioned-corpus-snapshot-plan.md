---
title: 'Ingest publishes a versioned corpus snapshot'
type: 'feature'
ticket: '3'
created: '2026-11-06'
status: 'built'
baseline_revision: '3791664a4eb2f6f9996b9860b294bb862c1c1f2a'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: [quick]
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Every environment and the eval need a frozen, versioned corpus of real closed `kubernetes/kubernetes` issues (AD-6), but only story 1's synthetic fixture exists, and nothing calls GitHub or publishes a snapshot under the corpus terms settled by spike 2.

**Approach:** Add `jobs.ingest` over a read-only GitHub REST adapter. It lists closed issues in the window, fetches each issue's timeline (comments and events), applies the corpus terms, and writes gzipped JSONL plus a SHA-256 and a report, checkpointing so it resumes. `snapshot.yml` runs ingest, times a load through story 1's `migrate`/`load` into the in-repo Postgres image, then publishes the next free `YYYY.MM.N` Release with attribution notes.

## Boundaries & Constraints

**Always:**
- `jobs.ingest` is the only GitHub API caller, and it sends `GET` only, with `INGEST_GITHUB_TOKEN`. The client lives in `ticketscope.adapters.github` (AD-1); `httpx2` becomes a runtime dependency at the Stack pin.
- Scope: closed issues, not PRs, `closed_at` within the window (default 1095 days back from the run), most recently closed first, capped at 20,000 (both are workflow inputs).
- Every written line validates against `snapshot/schema-v1.json` and parses as `SnapshotIssue`. `url` is the github.com issue URL. No user object or login field is mapped.
- Before writing, the title, the body and each comment body have email addresses replaced with `[email masked]` and token- or key-shaped secrets (GitHub `gh?_`/`github_pat_` tokens, AWS `AKIA`/`ASIA` keys, Slack `xox?-`, Google `AIza` keys, PEM private-key blocks) replaced with `[secret masked]`.
- Decision (user, 2026-11-06): every `@handle` mention in the title, the body and comment bodies is replaced with `@[user]`; `@org/team` mentions are kept. Masking runs before the record is checkpointed or written.
- Issues listed in `snapshot/exclusions.txt` are never fetched or written.
- The report holds the window, the issue count, and the short / log-heavy split from `derive_kind` at `DEFAULT_KIND_THRESHOLD`.
- A rate-limit response waits for the reset and retries the same request. A pass that hits its deadline saves a checkpoint and exits with code 3; the next pass continues from it without refetching finished issues.
- Version = next free `YYYY.MM.N` for the run month among existing `snapshot-*` tags. Release creation never uses `--clobber` and fails if the tag exists.
- The publish is refused when the timed load exceeds 600 s or the asset fails schema validation.
- PR tests use recorded responses only.

**Never:**
- No live GitHub calls in PR tests, no GraphQL, no `POST`/`PATCH`/`DELETE` to the GitHub API from ingest.
- No change to `load`, the schema, migrations, `derive`, or the values pin (story 5 swaps the pin and the sidecar).
- The kinds sidecar written for the timed load is not published.
- No deletion of Releases by the workflow; takedown deletion stays a person's step.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Normal issue | listed closed issue, timeline with comments, a merged cross-referenced PR, `marked_as_duplicate` | one schema-valid record; comments keep `author_association`/`body`/`created_at`; event `source_*` filled from `source.issue` | No error expected |
| PR in listing | item with `pull_request` key | skipped | No error expected |
| Outside window | `closed_at` before window start | skipped | No error expected |
| 100+ comments | timeline split over pages via `Link: rel="next"` | every comment present | No error expected |
| Rate limit | 403/429 with `x-ratelimit-remaining: 0` or `retry-after` | sleeps until reset, retries the same URL, output identical to an unlimited run | 5xx: bounded retries, then fail |
| Deadline mid-run | pass deadline reached | checkpoint saved, exit 3; next pass refetches nothing finished | Corrupt trailing checkpoint line dropped |
| Planted secrets | email, `ghp_…`, `AKIA…`, PEM block in body/comment | masked markers; originals absent from output | No error expected |
| Excluded issue | number in `exclusions.txt` | absent; no request for its timeline | No error expected |
| Version taken | tags `snapshot-2026.11.1`, `.2` exist | `2026.11.3`; first of a month → `.1` | No error expected |

</frozen-after-approval>

## Code Map

- `src/ticketscope/core/snapshot.py` -- `SnapshotIssue`, `Comment`, `TimelineEvent` (`extra="forbid"`). Reuse; do not change.
- `src/ticketscope/core/derive.py` -- `derive_kind`, `DEFAULT_KIND_THRESHOLD` (3) for the report. Do not change.
- `src/ticketscope/jobs/load/main.py` -- reads `<dir>/<version>.jsonl.gz` and `<version>-kinds.json`; ingest writes both into its output dir so the timed load runs unmodified.
- `src/ticketscope/adapters/postgres.py` -- `apply_migrations`, `replace_corpus`; reached only through `ticketscope-migrate` / `ticketscope-load`.
- `src/ticketscope/adapters/github.py` -- NEW: `GitHubClient(token, transport=None, sleep=time.sleep, clock=time.time)`; `get_pages(path, params)` follows `Link` next; rate-limit wait; raises `DeadlineReached`.
- `src/ticketscope/jobs/ingest/{__init__,main,mask,select,version}.py` -- NEW: orchestration and checkpoint (`main`), masking (`mask`), listing filter and record mapping (`select`), `next_version` (`version`). Entry point `ticketscope-ingest`.
- `snapshot/exclusions.txt` -- NEW: one issue number per line, `#` comments.
- `scripts/time-load.sh` -- NEW: run the Postgres image with `initdb` + `postgres -c shared_preload_libraries=pg_textsearch`, create extensions, the `ticketscope_ro` role, then `ticketscope-migrate` and timed `ticketscope-load`; print seconds.
- `.github/workflows/snapshot.yml` -- NEW: see Design Notes.
- `README.md` -- NEW: short project line plus "Corpus attribution and takedown".
- `pyproject.toml`, `uv.lock` -- `httpx2` to runtime deps; `ticketscope-ingest` script.
- `tests/unit/ingest/recordings/*.json` + `tests/unit/test_ingest*.py` -- NEW.
- `.importlinter` -- no change: `adapters` may import `httpx2`; `jobs` may import adapters.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `uv.lock` -- runtime `httpx2~=2.16.0`, script entry -- the ingest runs from the app image (AD-2)
- [x] `src/ticketscope/adapters/github.py` -- GET-only client, paging, rate-limit wait, deadline -- AD-1, AD-6
- [x] `src/ticketscope/jobs/ingest/*` -- listing, mapping, masking, exclusions, checkpoint/resume, output, report, `next_version` -- AD-6, corpus terms
- [x] `snapshot/exclusions.txt`, `README.md` -- takedown list and attribution/takedown text -- corpus terms 1, 4
- [x] `scripts/time-load.sh` -- timed load through story 1's path -- initiative R10
- [x] `.github/workflows/snapshot.yml` -- dispatch → ingest passes → validate + time → publish -- AD-17, AD-12
- [x] `tests/unit/ingest/recordings/` and tests -- every matrix row, plus "only GET" over the recorded run and a check that no recorded user login appears in the output

**Acceptance Criteria:**
- Given the recordings, when ingest runs to completion, then the output validates against the schema, each record's `url` is its github.com issue URL, and no recorded `user.login` value appears anywhere in the gzipped output.
- Given a completed run, when the outputs are listed, then `<version>.jsonl.gz`, `<version>.jsonl.gz.sha256` (matching `sha256sum -c`), `<version>-kinds.json` and `report.json` exist.
- Given `snapshot.yml` is dispatched on main (person's step), when it finishes, then a `snapshot-YYYY.MM.N` Release holds the asset and checksum, and its notes state window, count, kind split, load seconds ≤ 600, attribution and the takedown path; a second dispatch publishes `N+1` and leaves the first unchanged.

## Design Notes

- **Listing.** `GET /repos/kubernetes/kubernetes/issues?state=closed&sort=updated&direction=desc&since=<window start>&per_page=100`. `since` filters `updated_at`, which is ≥ `closed_at`, so it is a superset. Filter PRs and `closed_at`, sort by `closed_at` desc, then number desc, cap. The selected list is checkpointed before enrichment.
- **Enrichment.** One `GET /repos/…/issues/{n}/timeline?per_page=100` per issue, paged. `commented` items become comments. `marked_as_duplicate`, `unmarked_as_duplicate`, `closed`, `connected` and `cross-referenced` items become events. For a cross-reference, `source_*` comes from `source.issue` (`number`, `html_url`, `pull_request` present, `pull_request.merged_at` not null). Other event types are dropped. ~20k requests at 5,000/h ≈ 4–5 h.
- **Passes.** `snapshot.yml` runs four sequential ingest jobs (`timeout-minutes: 350`, ingest `--deadline-minutes 330`). Each restores the work dir from the previous job's artifact, and later jobs are skipped once a pass reports complete.
- **Checkpoint.** `work/selected.json` and `work/fetched.jsonl` (append + flush per issue, already masked). On resume, a trailing partial line is dropped.
- **Publish job** (`contents: write`, `concurrency: snapshot`): `gh release list` → `next_version` → `gh release create snapshot-<v> <asset> <sha256> --notes-file`. Release creation is the only write, and it uses `GITHUB_TOKEN`, never the ingest token.
- **@mentions.** Pattern: `(?<![\w/.@])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))(?![\w/-])` → `@[user]`. It skips emails (masked first) and `@org/team`. The recordings plant an author's login as an @mention in a body and in a bot-style `@login:` comment.

## Implementation Notes

- `concurrency: snapshot` sits on the whole workflow (never cancelled) instead of only the publish job, so two runs cannot plan the same version; publish re-checks the version is free.
- The REST timeline gives no target on `marked_as_duplicate`, `closed` or `connected` events, so their `source_*` stays null; only `cross-referenced` carries the PR and its merged state. Check this in the 20-issue manual sample.
- Login masking covers `@handle` mentions only (the decision); a bare login in prose ("cc dims") is not masked.
- Timeline items missing `created_at` or failing to parse are dropped with a warning rather than failing a multi-hour run.
- Verified locally (colima): `scripts/time-load.sh` loaded the fixture (8 issues, 0.3 s) and an ingest output built from the recordings (4 issues, 0.2 s); that output's checksum verified, and it held no planted login, token or key.
- The ingest job runs on the runner via `uv run`, not in the app image; the image can run it too (exclusions copied in, after review).

## Plan Change Log

## Review Triage Log

### 2026-11-06 — Review pass (quick)
- verdicts: 6 findings — high 1, medium 0, low 5, false 0, maybe-false 0
- findings:
  - `[high]` `[patch]` A selected issue deleted (410), hidden (404) or transferred (301) before its timeline fetch fails the pass, and since `selected.json` keeps it, every later pass fails too — confirmed in `GitHubClient._get` (any non-200/429/403-limit/5xx raises) and `run` (no per-issue handling). Fix: a `GitHubGone` error for 301/404/410, the issue is skipped and recorded in `work/gone.txt`, and a `gone` count in the report.
  - `[low]` `[patch]` `ticketscope-ingest` in the app image fails because the default `snapshot/exclusions.txt` is not in the image — confirmed against `images/app.Dockerfile`. Fix: copy the file in.
  - `[low]` `[patch]` In `snapshot.yml` validate, `time-load.sh | tail -n1` runs without pipefail, so a failed load is reported as over budget with an empty time. Fix: `pipefail` and an explicit failure message.
  - `[low]` `[patch]` `excluded` in the report is frozen at selection time, so exclusions added between passes are dropped from the output but not counted. Fix: also count selected issues now in the list.
  - `[low]` `[reject]` No checkpoint when the deadline hits during listing — listing is ~1k requests against a 330-minute deadline, so it is unlikely, and the fix needs listing checkpoints.
  - `[low]` `[reject]` Rate-limit retries never stop when no deadline is set — `snapshot.yml` always passes `--deadline-minutes`, and GitHub does not return `retry-after: 0` indefinitely; the fix adds a retry counter for a path not used.

## Verification

**Commands:**
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run lint-imports && uv run pytest` -- expected: all pass
- `uv run pytest tests/unit -k ingest -v` -- expected: one passing case per matrix row
- `actionlint .github/workflows/snapshot.yml` (if installed) -- expected: no errors
- `scripts/time-load.sh` against a locally built Postgres image and the fixture -- expected: prints a load time and exits 0 (needs docker)

**Manual checks (person's step, after merge):**
- Dispatch `snapshot.yml` twice and check both Releases, the notes, and that the first asset's checksum is unchanged.
- High-risk check: compare 20 sampled issues against github.com, including a duplicate, an issue fixed by a merged PR, and one with 100 or more comments.
