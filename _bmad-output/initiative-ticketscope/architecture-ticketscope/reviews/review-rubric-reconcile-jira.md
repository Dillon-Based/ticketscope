# Review: rubric + reconcile, Jira corpus amendment (2026-11-06)

Scope: the uncommitted amendment of `architecture-ticketscope.md` (AD-6, AD-8, AD-10, AD-12, AD-17, Identifiers, Provenance, Structural Seed, Deferred, Open questions) and the last ~10 memlog entries. I checked it against the initiative, epic-search-baseline (its Constraints and Notes), tickets.toml entries 13, 14 and 5, epic-eval-gate, spike 12's `findings.md`, `terms.md` and `outcome-mapping.md`, and the brownfield files `core/snapshot.py`, `core/derive.py`, `migrations/0001_init.sql`, `contract/search.py`, `.github/workflows/snapshot.yml`, plus `jobs/ingest/main.py`, `jobs/load/main.py`, `snapshot/exclusions.txt` and `README.md` where they bear on the rules.

## Verdict

**Revise before story 14's plan.** The amendment covers the main points: source, person-run ingest, schema v2 field list, no identities, one instance, `/v1` unchanged, the data-source id, Identifiers and Provenance. AD IDs are stable and no AD was renumbered. Four high findings remain, though. Each is a cross-unit contract that stories 14, 13, 5 and epic 2 would settle differently:

- the reporter-comment field disagrees with the tickets
- the duplicate-link shape cannot produce `/v1` `ref` and `summary`
- AD-8's schema-version selector has nothing to carry it
- the person-run publish path loses `snapshot.yml`'s guards, and the rule is unenforceable as written

## Findings

### Critical

None.

### High

**H1. The reporter-comment field contradicts every ticket, and the memlog says no ticket update is needed.**
- **Spine:** AD-6 gives each comment a `from_reporter` flag: per comment, true for the reporter, and raw, not derived.
- **Tickets:** the epic's Snapshot format constraint calls it "a derived non-reporter-comment flag in place of `author_association`". Story 14 says the answered rule is "read from a non-reporter-comment flag". Story 13 says "comments without author ids, and a derived non-reporter-comment flag". Spike finding 3 calls it a derived "non-reporter comment" boolean, which reads as per issue.
- **Mismatch:** the spine and the tickets disagree on polarity (reporter vs non-reporter), on granularity (per comment vs per issue) and on whether the field counts as "derived". Story 14 builds the core model first, from its ticket text. The last memlog line says "Ticket updates for Sofia: none required", which is wrong.
- **Fix:** keep the spine's per-comment shape, because the answered rule's time condition needs it. Name the field exactly once, `comments[].from_reporter: bool`. Replace the memlog's "none required" with a direction to Sofia to amend the epic's Snapshot format constraint and the descriptions of stories 13 and 14 to that name and shape.

**H2. A duplicate link that carries only the target's `number` cannot produce `/v1` `ref` or a readable `summary`, nor resolve targets outside the corpus.**
- **Spine:** AD-6 gives each duplicate link the target's `number` and the link direction.
- **Problem:** the brownfield `_duplicate` sets `ref` to the target's URL and `summary` to "Duplicate of #N". Story 14 must fill "summary, source and ref per the /v1 outcome shape".
  - A Jira `/browse/` URL needs the key (`MCL-123`), not the integer id.
  - An id in a summary means nothing to a reader.
  - Spike 12 counts 2,822 duplicate targets that fall *outside* the subset. Their key cannot be looked up in the snapshot.
- **Fix:** in AD-6, give each duplicate link the target's `number`, `key` and direction. `number` remains the join and `key` is for display (Identifiers). Optionally state in AD-4 or Deferred that a Jira duplicate's `ref` is the target's `url`.

**H3. AD-8's "the snapshot schema version selects the rule set" has no carrier, and v1 handling at load is unstated.**
- **Brownfield:** `SCHEMA_VERSION = 1` is a code constant. It is written only to `report.json`, which is never published, and no record or asset field carries it. `derive_outcome(issue: SnapshotIssue)` dispatches on nothing.
- **Tickets:** story 13 says the fixture moves to v2 and "jobs.load reads v2 from here on". AD-8 says the GitHub rules stay "only for v1-shaped synthetic tests". Whether load still accepts a v1 asset is not said.
- **Effect:** stories 14, 13 and 5 can each pick a different selector (a per-line field, an asset-name suffix, a model type, a load argument), and that divergence is exactly what AD-8 exists to prevent.
- **Fix:** AD-6 should say every snapshot line carries `schema_version`, or that the Pydantic model type is the selector, with a discriminated union in `core`. AD-8 should add: "`load` accepts only v2 assets and refuses any other version; v1 models and GitHub rules are reachable only from unit tests."

**H4. The person-run publish path drops `snapshot.yml`'s guards, "committed ingest" is unenforceable, and the spine contradicts code that still exists.**
- **Brownfield:** `snapshot.yml` enforces several guards today:
  - publish only from `main`, with the Release `--target` set to the SHA
  - one run at a time, through `concurrency`
  - the version re-checked as still free
  - checksum, JSON Schema validation and the timed 600 s load as gates *before* publish
  - `gh release create` without `--clobber`
  - the Release notes carry the attribution and takedown text
- **Spine:** AD-6 now says only "A person runs the committed `ingest` locally. That same run publishes…". Nothing requires a clean tree at a pushed `main` commit, gates publishing on validation and the timed load, or says where the Release notes and attribution text now come from (today they live in workflow YAML).
- **AD-17:** it says "No workflow runs `ingest`", but `snapshot.yml` still does, against the GitHub API. The spine names no owner for removing it; only the memlog does (story 13).
- **Fix:** add to AD-6 Publishing: "The publish command refuses a dirty tree or a commit not on `origin/main`, targets the Release at that SHA, never clobbers, and publishes only after the checksum, schema-v2 validation and the timed load pass. The Release notes, including spike 12's attribution line, are generated by committed code." Add to AD-17: "Story 13 deletes `snapshot.yml`." The memlog already has the reason.

### Medium

**M1. "Ingest derives nothing" conflicts with ingest's report and the kinds sidecar, and leaves two pair derivations.**
- **Brownfield:** `jobs/ingest/main.py` calls `derive_kind` to write `<version>-kinds.json` and the report's kind split. `jobs/load/main.py` reads kind from that sidecar "until story 5".
- **Tickets:** story 13 must report "the in-subset duplicate pairs by kind and the kind split, using story 14's rules".
- **Spine:** the Identifiers convention lists "the kinds sidecar" as a machine join, which makes it look permanent. Pair extraction is deferred to epic 2, so ingest's pair count in the Release notes and `eval/pairs/<snapshot>.jsonl` can come from two different heuristics.
- **Fix:** reword the AD-8 bullet to "Ingest writes no derived value into the snapshot; it may call `core`'s functions only for its report." Drop "kinds sidecar" from Identifiers, or mark it as a test and timed-load artifact that story 5 retires. In AD-12, say pair extraction is one `core` function, used by both the ingest report and epic 2.

**M2. Deduplicating repeated keys and keeping `number` unique are not in the spine.**
- **Inputs:** the dump repeats issue keys (5 in Mojang). Story 13 says "first document wins".
- **Problem:** MongoDB natural order is not a stable "first", so two ingests of the same dump can differ, which breaks reproducible snapshots. Load's primary key on `number` fails on a duplicate.
- **Fix:** AD-6 should say `number` is unique within a snapshot, and that ingest deduplicates repeated keys deterministically, by a named rule such as the lowest Mongo `_id` or the latest `updated`.

**M3. Nothing guards the thin log-heavy margin.**
- **Inputs:** there are 304 log-heavy pairs at threshold 3, against epic 2's floor of about 200, and 295 of them come from MCL. Story 5 sets the final threshold, and epic-eval-gate asks refinement to check it.
- **Spine:** it records the number only under Open questions. The Deferred threshold item carries no constraint, so story 5 can raise the threshold and leave epic 2 below its floor.
- **Fix:** add to that Deferred item: "Story 5's threshold must keep at least about 200 in-subset log-heavy pairs, re-measured in its PR. Otherwise it goes back to the author."

**M4. The v2-to-database column mapping is unspecified under "no migration change".**
- **Brownfield:** `0001_init.sql` has `state_reason` and `closed_at`. v2 has `resolution` and `resolved_at`, and no `state_reason`.
- **Tickets:** the epic's decision rules out any migration change, and story 13 makes load read v2.
- **Spine:** it does not say which v2 field fills `closed_at`, or what goes in `state_reason`, so stories 13 and 5 can each decide. The ER diagram now shows a `DUPLICATE_LINK` entity, which implies a table the epic rules out.
- **Fix:** add one line under AD-7 or AD-6 Loading: "`resolved_at` loads into `closed_at`; `state_reason` stays null for v2; duplicate links are not stored in Postgres." Label the ER diagram as conceptual, or drop `DUPLICATE_LINK` from it.

**M5. Takedown scope and keying are incomplete, and the brownfield takedown artifacts still assume Kubernetes.**
- **Spine:** Provenance says only "takedown via the exclusion list".
- **Gaps:**
  - AD-21's precomputed embeddings are Release assets keyed by snapshot and derived from the removed text. Nothing says they are deleted too.
  - The exclusion list's key is not named. Requests will arrive as `MCL-123`, but Identifiers says machine joins use `number`.
  - `snapshot/exclusions.txt` and the README section "Corpus attribution and takedown" still say `kubernetes/kubernetes` issue numbers.
- **Fix:** Provenance: "Takedown adds the issue's key to the committed exclusion list; the next snapshot leaves it out; a person deletes earlier snapshot *and embedding* Release assets that hold it." Name story 13 as the owner of rewriting `exclusions.txt` and the README section.

**M6. A decided cross-unit rule sits under Deferred.**
- **Spine:** the Jira `/v1` `source` mapping (duplicate → `label`, answered → `closing_comment`, else null) is settled, binds stories 14 and 5 and epic 4's MCP output, and is recorded under Deferred.
- **Also unsaid:** `linked_pr` is never produced for v2.
- **Fix:** move it into AD-4's Outcome bullet, as an additive note that does not change the enum. Keep only "the per-resolution mapping table: story 14, per `outcome-mapping.md`" under Deferred.

### Low

**L1. Stale or history text in the spine.**
- The Open question "Corpus terms… no author logins… No AD changes" is now false, because Provenance and AD-6 changed. Update it to "under spike 12's terms (Provenance)", or remove it.
- "The corpus switch drove AD-6, AD-8, AD-10, AD-17 and the Identifiers and Provenance conventions" and AD-17's "the old `snapshot.yml` leaves this table" are change history. Move both to the memlog.

**L2. The kind-rule wording is narrower than the epic's.** AD-8 says "`{code}` and `{noformat}` blocks". The epic and spike say `{code…}` toggles, which includes `{code:java}` and similar. Use "`{code…}` (any parameters) and `{noformat}`".

**L3. Masking forms.** `terms.md` also names `[~accountid:…]` mentions, and masking of titles as well as bodies and comments. Provenance says "`[~user]` mentions". Write "`[~…]` mentions in titles, bodies and comments".

**L4. Comments with no author.** If a comment's author is missing in the dump, the spine does not say whether `from_reporter` is null or false. State the default, or let story 14 own it under Deferred's "exact v2 field types".

**L5. The checksum pin.** Story 5 pins the checksum beside the version in values, and AD-6 Loading mentions only the version. epic 5's `values-eks.yaml` must carry it too. Consider "the snapshot version and its checksum pinned in values".

## Reconcile checklist (quiet requirements)

| Requirement | In the spine? | Note |
| --- | --- | --- |
| Attribution line plus a per-record link | Yes (Provenance, `url`) | Where the Release notes text comes from once `snapshot.yml` goes is unowned (H4) |
| No identities, masked UUIDs included | Yes (AD-6, Provenance) | |
| Mention, email and secret masking | Partly | `[~accountid:]` and titles (L3) |
| Takedown | Partly | Embedding assets and the exclusion-list key (M5) |
| One instance | Yes (Identifiers) | |
| Person-run ingest | Yes (AD-6, AD-17) | Guards lost; `snapshot.yml` still exists (H4) |
| `/v1` unchanged, key additive later | Yes (Identifiers, Deferred) | |
| Source enum mapping | Under Deferred only | Move into AD-4 (M6) |
| Kind rule extension | Yes (AD-8) | `{code…}` wording (L2) |
| Dedupe of repeated keys | **No** | M2 |
| Thin log-heavy margin | Open question only | No guard (M3) |
| Reporter-comment flag | Contradicts the tickets | H1 |
| Outcome from `resolution`, answered rule | Yes (AD-8, Deferred) | |
| Corpus size and load budget | Yes (Deferred, AD-21) | |

**Remaining GitHub or Kubernetes assumptions in the spine:** none that bind the corpus. `linked_pr` stays in AD-4's frozen enum, which is fine (M6 notes it is unused). The GitHub OIDC and Kubernetes mentions are platform, not corpus. Outside the spine, these brownfield files still assume Kubernetes:
- `snapshot.yml`
- `snapshot/exclusions.txt`
- `README.md` (line 3 and the attribution section)
- `derive.py`'s klog and Go log-line patterns (harmless; they only add score)

The spine should name story 13 as their owner (H4, M5).

## Rubric

- **Rules enforceable and preventing their divergence:** mostly yes. Exceptions:
  - AD-8's version selector (H3)
  - AD-6's "committed ingest" (H4)
  - AD-8's "ingest derives nothing" (M1), which brownfield and story 13 already break as worded
- **Deferred lets no two units diverge:** fails on the dedupe rule (M2), the threshold vs epic 2's floor (M3) and v2 field types between stories 14 and 13 (H1, H3). It passes on the rest.
- **Ratifies the brownfield code:** mostly. These contradict existing code with no named transition:
  - AD-17 against `snapshot.yml` (H4)
  - Identifiers and AD-8 against the kinds sidecar (M1)
  - AD-6 v2 against `0001_init.sql`'s columns (M4)

  `contract/search.py` is unchanged, and the spine correctly keeps `/v1` unchanged.
- **AD IDs stable:** yes. AD-1 to AD-25 are intact, nothing is renumbered, and Binds lines are unchanged.
- **No rationale bloat:** small leaks (L1). The Identifiers convention runs long but stays normative.
