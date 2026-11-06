---
review: adversarial (spine attack), Jira-corpus amendment
target: architecture-ticketscope.md as amended 2026-11-06 (AD-6, AD-8, AD-10, AD-12, AD-17, the Identifiers and Provenance conventions)
units: epic-search-baseline stories 13 (ingest v2), 14 (Jira derive), 5 (load); epic 2 (eval pairs); epic 3 (embeddings); epic 4 (MCP)
brownfield: src/ticketscope/core/snapshot.py, core/derive.py, jobs/load/main.py, migrations/0001_init.sql, contract/search.py; spike 12 convert.py and measure.py
date: 2026-11-06
verdict: NOT YET SAFE TO BUILD STORY 13. The amendment makes the right switch, but the duplicate link, which is the corpus's ground truth, is under-specified. Ingest, outcome derivation, the story 13 report and epic 2's pairs can each pick a different duplicate target while each obeys every AD. Three high holes (H1 to H3) sit on the story 13, 14 and 5 seam and should close before story 13's plan checkpoint. H4 can wait for epic 4's refinement, but it needs a guard rule now.
---

# Adversarial review: the Jira amendment

Method: for each hole, two units one level down each make a build choice that obeys every AD as written, and the two builds still conflict. Each hole ends with the rule text that closes it. Holes are ordered by severity.

---

## H1. HIGH: The duplicate rule has no single owner. Ingest scope, outcome, the story 13 report and epic 2's pairs can disagree

**Units:** story 13 (ingest) × story 14 (derive_outcome) × epic 2 (pair extraction); story 13's Release-notes pair count is a fourth copy.

**ADs obeyed:** AD-6 (the snapshot carries "duplicate links, each with the target's number and the link direction"), AD-8 ("ingest derives nothing", and the outcome comes from `resolution`), AD-12 ("Epic 2 derives labelled duplicate pairs deterministically from the snapshot's duplicate links").

**Why the spine cannot hold as written:**
- The corpus scope is "resolved issues plus the unresolved issues their duplicates point to". To select that scope, ingest must decide (a) which issues are duplicates, which means mapping `resolution` onto `duplicate` (an outcome derivation), and (b) which link is "the" duplicate target. Spike 12 does (b) with a heuristic: prefer the `duplicates` direction, else fall back to any Duplicate-mapped link in either direction (`measure.duplicate_target`), with link types classified through `jira_issue_linktype_mapping.json`. AD-8 forbids ingest to derive anything, so story 13 cannot follow AD-8 to the letter and still select the scope. It must either break AD-8 or carry its own copy of the rule.
- AD-6 asks for "duplicate links" in general. It does not say whether that means every Duplicate-mapped link, only the chosen target, or both directions.

**Divergent lawful builds:**
- **Story 13** emits every Duplicate-mapped link, in both directions (`duplicates` and `is duplicated by`). It selects its scope and counts the Release-notes "in-subset pairs by kind" with a private copy of spike 12's heuristic. A private copy is allowed, because ingest may import `core` but AD-8 says it derives nothing, so the author does not reach for core.
- **Story 14** chooses the target for `outcome.ref` and the summary ("Duplicate of …") from the first `duplicates` link only, with no fallback. For the 58 reversed-direction Mojang pairs, `ref` is null.
- **Epic 2** builds a pair from every link, so a target with 5 duplicates yields 5 pairs counted from both ends. It counts each pair under the kind of whichever side was the query, and it includes links whose source issue was not resolved Duplicate.
- **Result:** the pair count in the Release notes (10,466), the epic 2 pairs file and the duplicate outcomes on `/v1` all differ. The per-kind split, which is the gating input that spike 12 measured as only just meeting the bar (304 log-heavy), moves without any AD being broken.

**Fix (new AD, or tighten AD-8 and AD-12):**

> **AD-8a — One duplicate rule, in `core`.** `core` owns `duplicate_target(issue) -> DuplicateLink | None`: the rule that says whether an issue is a duplicate (its `resolution` maps to `duplicate`) and which of its links is the target (the first `duplicates`-direction link, else the first Duplicate-mapped link in either direction). `derive_outcome` (its `ref` and summary), ingest's scope selection and its Release-notes counts, and epic 2's pair extraction all call this one function, and nothing else picks a target. Ingest may *call* `core`'s pure functions to select and report; it never *persists* a derived value into the snapshot. A pair is `(duplicate.number, target.number)`, at most one per duplicate issue, emitted only when the target is in the snapshot, and counted under the duplicate issue's persisted kind. Changing the rule changes `derivation_version` (AD-8) and needs a baseline update (AD-12).

And change the AD-8 bullet "Ingest derives nothing" to: "Ingest writes no derived field. It may call `core` functions to select its scope and to report."

---

## H2. HIGH: The duplicate-link shape cannot produce `outcome.ref`, and out-of-subset targets have no defined shape

**Units:** story 13 (emits links) × story 14 (`derive_outcome` per issue) × story 5 (load) × epic 2.

**ADs obeyed:** AD-6 (a link carries the target's `number` and the direction), AD-8 (`derive_outcome` is one entry-point function over the issue), the Identifiers convention (`key` is for display, and `url` is `https://bugs.mojang.com/browse/<key>`), AD-4 (`ref: url|null`).

**Divergent lawful builds:**
- **Story 13** emits `{target_number, direction}`, exactly as AD-6 lists. For a target outside the subset it either (a) resolves the target's id from the full dump, (b) emits `target_number: null`, as spike 12's `convert.py` does, or (c) drops the link. All three obey AD-6.
- **Story 14's** `derive_outcome(issue)` is a pure function of a single issue (AD-8 and brownfield `derive.py`). To build `ref` and "Duplicate of MCL-123" it needs the target's *key*, which it cannot reach from a number without the whole corpus. It therefore emits `ref: null` and a number-only summary such as "Duplicate of #456789", which shows the internal Jira id that users never see. It could instead build `https://bugs.mojang.com/browse/456789`, a broken link, and nothing in the spine forbids that.
- **Epic 2** reads the pairs. Under (a) it gets pairs whose target is not in the database, so Recall@k is silently capped below 1. Under (b) the field is unexpectedly nullable, and pydantic rejects it or epic 2 skips it.

**Fix (tighten AD-6's link bullet):**

> each duplicate link carries `target_number` (int, always set, resolved from the dump even when the target is outside the subset), `target_key` (e.g. `MCL-123`), `direction` (`duplicates` | `is_duplicated_by`), and `link_type` (the raw Jira name). Ingest emits every Duplicate-mapped link of the issue, unfiltered. Whether the target is in the corpus is decided at load and in pair extraction by membership in the snapshot, never by a flag that ingest writes. `outcome.ref` for a duplicate is `https://bugs.mojang.com/browse/<target_key>`. A URL is never built from a `number`.

---

## H3. HIGH: Schema-version dispatch and the Release asset layout are unspecified, so story 13 and story 5 can disagree on how to read the same file

**Units:** story 13 (publishes the asset) × story 14 (the core model and the version-selected rule set) × story 5 (downloads, verifies and loads) × epic 2 (reads the snapshot to extract pairs).

**ADs obeyed:** AD-6 ("the snapshot schema is versioned", "`YYYY.MM.N` and its SHA-256 checksum as a GitHub Release asset"), AD-8 ("the snapshot schema version selects the rule set inside that function").

**Why it is open:** brownfield `SnapshotIssue` carries no version field (`SCHEMA_VERSION = 1` is a module constant), and `load` reads `<snapshot_dir>/<version>.jsonl.gz`. AD-8's selector therefore has no defined place to read the version from, and AD-6 does not name the Release tag, the asset file names or the checksum format.

**Divergent lawful builds:**
- **Story 14** makes `derive_outcome(issue: SnapshotIssueV1 | SnapshotIssueV2)` dispatch on the Python type, and adds `schema_version: Literal[2]` to each line as the pydantic discriminator.
- **Story 13** writes no per-line version. It records `schema: 2` in the Release notes and names the asset `mojang-2026.11.1.jsonl.gz`, with a `SHA256SUMS` file.
- **Story 5** downloads `<version>.jsonl.gz` and `<version>.sha256` (bare hex), so the asset is not found. Once that is fixed, every line fails the discriminated union because it has no `schema_version`.
- **Story 13** also keeps v1 loadable in `load` "for the fixture". AD-8 says the GitHub rules remain "only for v1-shaped synthetic tests", which does not clearly forbid `load` from reaching them, so a v1 snapshot pinned by mistake loads through the GitHub rules with everything `unknown`.

**Fix (tighten AD-6 and AD-8):**

> **Asset layout.** The Release tag is `snapshot-YYYY.MM.N`. Its assets are `corpus-YYYY.MM.N.jsonl.gz` and `corpus-YYYY.MM.N.jsonl.gz.sha256` (`sha256sum` format). Values pin the version and the hex digest. **Version carriage.** Every line carries `schema_version` as a literal discriminator, and one file holds one version. `core` exposes `parse_issue(line)`, the only parser, which `load`, ingest's self-check and epic 2 all use. **Dispatch.** `load` accepts only the current schema version (2) and refuses any other with a non-zero exit, so the previous corpus stays. The v1 model and the GitHub rules are reachable only from unit tests.

---

## H4. HIGH (guard needed now, built in epic 4): `number` is an internal Jira id that collides with the numbers users and LLMs see

**Units:** epic 4 (MCP `get_issue(number)`) × epic 1 (`/v1`, the page) × the Identifiers convention.

**ADs obeyed:** AD-5 (`get_issue(number)` mirrors `GET /v1/issues/{number}`), Identifiers (`number` is the Jira issue id, and `key` joins `/v1` "only additively", deferred to epic 4).

**The clash:** an LLM client sees `url: https://bugs.mojang.com/browse/MCL-6629` and calls `get_issue(6629)`. Jira ids and project-key sequence numbers are both small integers, so 6629 may be a *different* in-corpus issue. The call then returns a confidently wrong result instead of 404. Epic 4 can follow AD-5 to the letter (an argument named `number`, of type int) and ship this. Epic 1 has no reason to add `key` to `/v1`, because the decision was deferred. And because `key` has no column in `0001_init.sql`, adding it later needs a migration plus a reload, which H6 shows may silently not happen.

**Fix (Identifiers convention, plus AD-4 and AD-5):**

> Every `/v1` issue object carries `key` (additive, from story 5 on, stored by `load`). No surface where a person or an LLM types an identifier accepts a bare integer as a Jira id without naming it as such. MCP `get_issue` takes `key: str` (e.g. `MCL-123`) and maps to `GET /v1/issues/by-key/{key}`. `GET /v1/issues/{number}` stays for machine joins. The MCP tool descriptions say that `number` is not the number in the key.

(If the author prefers to defer, the minimum is this guard: "epic 4 may not expose an integer issue argument to MCP clients".)

---

## H5. HIGH: Committed real-corpus text (test slices, golden queries, pairs) is outside the Provenance and takedown rules

**Units:** story 13 (tests "on a recorded slice of the dataset") × story 5 (commits a golden-query file "from the real snapshot") × epic 2 (`eval/pairs/<snapshot>.jsonl`) × epic 3 (embedding Release assets) × the takedown path.

**ADs obeyed:** Provenance ("no person identifiers anywhere, masked UUIDs included", "takedown via the exclusion list"), AD-6 (masking happens "before publishing", meaning the Release asset).

**Divergent lawful builds:**
- **Story 13** commits a recorded slice of *raw* dump documents as a test fixture, because masking is the thing under test and it needs unmasked input. Raw Jira documents carry `reporter`, `assignee` and `author` objects with masked UUID `key`/`name` fields. Provenance forbids those "anywhere", but AD-6 scopes masking to "before publishing", and the author reads a test fixture as not publishing.
- **Story 5** commits the golden queries as verbatim issue text, together with the expected issue.
- **A takedown** follows the epic's path exactly: it adds the issue to the exclusion list, publishes the next snapshot and deletes the old Release assets. The issue's text stays in the public git history, in the golden-query file and in the test slice. Its vectors stay in the embedding assets, which AD-21 keys by snapshot but which the takedown rule does not name. Its `number` stays in the old pairs file. The values pin may still point at the deleted asset, so every PR's `_kind-deploy` fails until someone bumps it.

**Fix (Provenance convention):**

> Every committed or published artifact derived from the corpus (snapshot assets, embedding assets, pairs files, golden queries, test fixtures, README examples) passes the same masking and identity scrub as the snapshot. Test fixtures replace every person field with synthetic tokens before commit. Raw dump documents are never committed. A takedown covers all of them: the exclusion list is checked in CI against the committed fixtures, golden queries and the current pairs file; the embedding assets of affected snapshots are deleted along with the snapshot assets; and the takedown PR bumps the values pin, the pairs file and `baseline.json` in one diff.

---

## H6. MEDIUM: Two owners of the v2 shape, and a flag whose shape and polarity already disagree between the spine and the tickets

**Units:** story 14 (runs first, "adds the schema-v2 fields its rules read" to core's model) × story 13 (commits JSON Schema v2, "carries … the duplicate link … comments without author ids").

**ADs obeyed:** AD-6 ("`core` owns the snapshot model; the JSON Schema committed in `snapshot/` mirrors it").

**Divergent lawful builds:**
- **Story 14** defines `SnapshotIssueV2` with only the fields its rules read: `resolution`, `issue_type`, a flag and `key`. It keeps the brownfield `extra="forbid"`. Following its ticket ("a non-reporter-comment flag"), it adds an *issue-level* `has_non_reporter_comment: bool`.
- **Story 13** follows AD-6 and writes `comments[].from_reporter`, `duplicate_links` and `resolved_at`, then hand-writes `schema-v2.json` to match. Every line fails `extra="forbid"` validation in core. Story 13 then edits core's model, which makes it the second owner, while the schema file and the model each "mirror" the other.
- **The flag itself:** the spine says per-comment `from_reporter` (true means the reporter wrote it). The epic and story 14 say "non-reporter-comment flag" (the opposite polarity, and possibly issue-level). A comment whose author was deleted or is missing in the dump forces ingest to choose true or false, which is a hidden decision on "answered" made outside core.

**Fix (tighten AD-6):**

> The v2 model in `core` is introduced complete, with every AD-6 field, by the first story that touches it (story 14). `snapshot/schema-v2.json` is *generated* from that model by a committed script, and `ci.yml` fails if the generated file differs from the committed one. The flag is `comments[].from_reporter: bool | null`: null when the dump cannot tell, and treated as "not a non-reporter comment" by `core`. Ticket wording that says "non-reporter-comment flag" refers to this field.

(Sofia: align story 14's and the epic's wording with this field name.)

---

## H7. MEDIUM: The database columns stay v1-shaped, and load's no-op check ignores schema changes

**Units:** story 13 (makes `load` read v2) × story 5 (persists kind and outcome) × epic 4 (adds `key`, see H4) × epic 3 (adds `issue_embedding`).

**ADs obeyed:** AD-7 (one migration track; `load` is the only writer), AD-22 step 4 (load does nothing when the snapshot, model and preprocessing versions are unchanged), story 14 ("the migration does not change").

**Divergent lawful builds:**
- **Story 13** maps v2 into the existing `issue` row: `resolved_at` goes to `closed_at`, and `state_reason` is filled from `resolution` the way `convert.py` does it (`duplicate`, `not_planned`, `completed`). That is a second outcome derivation, written to a column that `api` could expose.
- **Story 5** leaves `state_reason` null.
- **Later, epic 4** adds `issue.key` through migration `0002`. On an existing kind cluster, `helm upgrade` runs migrate, then load sees the same snapshot, model and preprocessing versions and skips. `key` stays NULL, the API returns null keys, and nothing fails.

**Fix (AD-7 and AD-22):**

> The `issue` table holds only fields of the current snapshot schema plus the derived fields. Migration `0002` (owned by story 13) renames `closed_at` to `resolved_at`, drops `state_reason` and adds `key`. `load` writes no raw field that it has reinterpreted. The no-op key in `corpus_meta` adds `schema_head`, the last applied migration. `load` reloads whenever `schema_head`, `snapshot_version`, `embedding_model_id` or `preprocessing_version` differs.

---

## H8. MEDIUM: Who publishes precomputed embeddings now that no workflow publishes snapshot assets

**Units:** epic 3 (embeddings) × AD-17 (no workflow "runs ingest or publishes a snapshot") × AD-21 (embeddings are Release assets keyed by snapshot, model and preprocessing).

**Divergent lawful builds:**
- **Epic 3** adds `embeddings.yml`, which downloads the snapshot, embeds it and attaches the result to the person-created `snapshot-…` Release. It reads AD-17 as forbidding only snapshot publishing.
- **Another reading** treats attaching to that Release as "publishing a snapshot". Epic 3 then publishes from a person's machine under a different tag scheme, and `load` (story 5 or epic 3) looks in the wrong Release.
- **AD-17's table** has no row for either option.

**Fix (AD-17 and AD-21):**

> Precomputed embeddings are published by `embeddings.yml` (dispatch). It reads only a published snapshot asset, never the dataset, and attaches `embeddings-<snapshot>-<model>-<preprocessing>.*` plus a `.sha256` to that snapshot's Release. It never touches the `corpus-*` assets.

---

## H9. MEDIUM: The snapshot pin can drift per environment

**Units:** story 5 (pin and checksum "in values") × epic 5 (`values-eks.yaml`) × epic 2 (`baseline.json` records the snapshot).

**ADs obeyed:** AD-6 ("the snapshot version pinned in values"), AD-25 (environment files hold environment facts; they are not prevented from setting other keys).

**The clash:** brownfield `values.yaml` holds `snapshot:`. Nothing stops `values-eks.yaml` from pinning another version, for example when an operator holds EKS back after a takedown. Then EKS serves a different corpus from the one CI gated, and `baseline.json`'s snapshot no longer matches what is live.

**Fix (AD-25):**

> `snapshot.version` and `snapshot.sha256` live only in `values.yaml`. Environment files must not set them, and a chart test fails if they do. `ci.yml` fails when `baseline.json`'s snapshot version differs from the pin, or when `eval/pairs/<pin>.jsonl` is missing.

---

## H10. LOW: Person-run ingest and the runtime and telemetry rules

**Units:** story 13 × AD-2 (one app image) × AD-10 ("export is OTLP to the in-cluster collector, and nowhere else") × the Deferred note (the dump client is "never in the image's runtime path").

**Divergent lawful builds:**
- **Story 13** adds `pymongo` to the main dependencies, so it ships in the image (AD-2: one repo, one image).
- **Story 13** wires `ticketscope.telemetry` into ingest like every other job (`service.name=ticketscope-jobs`). On a laptop there is no collector, so the exporter retries and the timed load measurement includes the export timeouts.

**Fix:**

> Ingest's dataset reader lives in `ticketscope.adapters.jira_dump`, behind a uv dependency group, `ingest`, that the image does not install. An import-linter contract forbids any other package from importing it. Person-run ingest sets up no OTLP exporter.

---

## Not holes (checked)

- **Jira ids fit `integer`** in `0001_init.sql`. Mojang ids are far below 2^31.
- **AD-10's rename** of `gen_ai.data_source.id` is not a spanmetrics dimension (AD-11), so the dashboard is unaffected.
- **The kind split** is computed at load from the published (masked) body. Eval reads the persisted kind (AD-8), so masking cannot cause the kind used by eval and the kind reported by the API to diverge, provided story 13's report also runs `derive_kind` on the masked body. It should state that it does.
