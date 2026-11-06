# Verification review: Jira corpus amendment (2026-11-06)

**Lens:** was each committed decision in the amended parts (AD-6, AD-8, AD-10, AD-12, AD-17, Identifiers, Provenance, Deferred, Open questions) checked against reality (web, dataset, live tracker, brownfield code), or just asserted?
**Scope:** `git diff` of `architecture-ticketscope.md` plus the last 10 `.memlog.md` entries; spike 12 evidence (`findings.md`, `terms.md`, `convert.py`); brownfield `src/ticketscope/core/snapshot.py`, `core/derive.py`, `migrations/0001_init.sql`, `src/ticketscope/contract/search.py`, `.github/workflows/snapshot.yml`.

**Verdict: PASS WITH FIXES.** The dataset identity, licence, citation and corpus numbers are verified. The `/v1` and migration claims hold against the code. Nothing blocks the amendment. Two medium items should be fixed before stories 13 and 14 start: the person-run publish has lost the gates that `snapshot.yml` enforced, and the attribution misses a CC BY 4.0 requirement. The rest is low: wording, unconfirmed live-tracker behaviour, and a semconv drift.

## What was verified

| Claim (where) | How checked | Result |
| --- | --- | --- |
| The Public Jira Dataset v7 is Zenodo 15719919, CC BY 4.0 (AD-6, Provenance) | Fetched zenodo.org/records/15719919 | **Confirmed.** "The Public Jira Dataset", version v7, CC BY 4.0, published 2025-06-23, creators Montgomery, Lüders, Maalej (Univ. Hamburg), one file of 5.8 GB. |
| The MSR 2022 paper (Provenance, terms.md attribution line) | Same Zenodo record | **Confirmed.** "An Alternative Issue Tracking Dataset of Public Jira Repositories", MSR 2022, IEEE, pp. 73–77. Matches terms.md's draft line. |
| Mojang moved to Jira Cloud in February 2025 (terms.md, findings) | minecraft.net "Changes to Minecraft bug reporting system" (via search; the page itself timed out) | **Confirmed.** Migration in the first week of February 2025, with an opt-in consent deadline of 2025-02-07. |
| `https://bugs.mojang.com/browse/<key>` is the right link form today (Identifiers, Provenance) | curl plus a read of the live SPA bundle (`/assets/index-*.js`) | **Partly confirmed, see F3.** The server returns 200 for any path (also `/browse/NOPE-99999999` and `/asdf/qwerty`), so terms.md's "old links still answer 200" is not evidence. The bundle's router does handle `/browse/<KEY>`: it maps `MCL-123` to project `MCL` and redirects client-side to the canonical `/browse/<PROJECT>/issues/<KEY>`. MCL, REALMS and MCD (Dungeons) are all registered projects in the portal. Whether the 2022 issues exist in the Cloud tenant was **not checked**: a live API probe was blocked in this session. |
| `number` = Jira issue `id`, an integer unique within an instance (Identifiers) | convert.py, spike timed load, Atlassian sources | **Confirmed for the dump.** convert.py uses `int(issue["id"])`. The spike's two Mojang snapshots validated with every number unique and loaded into `issue.number integer`, so the ids fit int4. Caveat in F5: Atlassian's MIG-2740 asks JCMA to preserve internal issue ids, which implies a Server-to-Cloud migration does not. The id is the 2022 Server id, not the live Cloud id. |
| `gen_ai.data_source.id` is a current GenAI semconv attribute (AD-10) | `open-telemetry/semantic-conventions-genai` `model/gen-ai/registry.yaml` and `spans.yaml` (main, last changed 2026-11-06) | **Current, with drift, see F4.** It is defined (stability development). The GenAI conventions now live in their own repo, and opentelemetry.io's core registry marks the attribute as moved there. The current INTERNAL `gen_ai.retrieval` span does not list `gen_ai.data_source.id`; only the now-deprecated `gen_ai.retrieval.client` span and the agent spans do. |
| "60 GB restored" (AD-6 Prevents) | Epic memlog / epic decision | **User-stated, not measured.** The 5.8 GB zip is verified. The restored size comes from the user (epic decision, 2026-11-06). The conclusion holds either way, since a standard GitHub-hosted runner has far less free disk. |
| Corpus size ~32k, cap ~50k (Deferred) | findings.md | **Confirmed.** 32,154 issues, a 3.9 s load. |
| 10,466 pairs, 304 log-heavy (Open questions) | findings.md subset table | **Confirmed.** |
| `/v1` outcome `source` mapping needs no contract or migration change (memlog, Deferred) | `contract/search.py` `OutcomeSource`, `0001_init.sql` CHECK | **Confirmed.** `label` and `closing_comment` are already allowed in both, and `outcome_status` already allows all six values. |
| v2 drops `state_reason`, `labels`, `timeline`, `author_association` with no migration change | `0001_init.sql` | **Holds.** `issue.state_reason` is nullable, so load writes null or derives a value. There is no label or timeline table. |
| GitHub rules only reachable from v1 synthetic tests (AD-8) | grep for `fixture.jsonl` / `schema-v1` consumers | **Holds.** The v1 fixture is used only in `tests/` and `snapshot.yml`. Today `derive.py` is wholly GitHub-shaped (labels, `author_association`, `linked_pr`), and `SnapshotIssue` is a single v1 model with `extra="forbid"`. Both are story 14's work, as the spine says. |

## Findings

### F1 — MEDIUM — Person-run publish lost the gates `snapshot.yml` enforced (AD-6, AD-17)

`snapshot.yml` guarantees six things before a Release exists:

- publish only from `main`
- a next-free `YYYY.MM.N` version, re-checked before publish
- `sha256sum -c`
- validation against both the JSON Schema and `SnapshotIssue`
- a timed load inside the 600 s budget
- `gh release create --target $GITHUB_SHA` with no `--clobber`

The amended AD-6 keeps only "publishes a versioned snapshot and its SHA-256 checksum" and "never overwritten". The epic decision (epic-search-baseline.md:115) also names the **timed load** on the person's machine, and the spine drops it. Nothing ties the asset to the commit of `ingest` that produced it. So "from committed code" is unverifiable, and AD-12 baseline lineage loses its anchor.

**Fix:** add to AD-6 Publishing: "The run publishes only from a clean checkout of `main`. Before publishing it validates against `snapshot/schema-v2.json` and core's model, runs the timed load (AD-21), and takes the next free version. The Release targets that commit's SHA, and the notes record the commit, row count and load time. One script (e.g. `scripts/publish-snapshot.sh`) does all of this, so the checks don't depend on the person remembering them."

### F2 — MEDIUM — The attribution does not meet CC BY 4.0 §3(a)(1)(B)/(C) (Provenance)

CC BY 4.0 requires stating whether the material was modified and giving a URI or hyperlink to the licence. The snapshot masks emails, secrets and `[~user]` mentions, drops fields, and rewrites nothing else, but it is modified. The draft line in terms.md says "CC BY 4.0" with no link and no modification notice. The Provenance row only points at that line.

**Fix:** extend the Provenance convention: the attribution line links `https://creativecommons.org/licenses/by/4.0/` and says the text was modified (emails, secrets and user mentions masked; user ids removed; the subset selected). Story 13 carries the exact wording.

### F3 — LOW — The live-link form is plausible but unconfirmed, and terms.md's evidence is invalid (Identifiers, Provenance)

- `bugs.mojang.com` answers 200 to every path, so a 200 proves nothing.
- The live SPA does redirect `/browse/<KEY>` to `/browse/<PROJECT>/issues/<KEY>` for MCL, REALMS and MCD. The spine's form is valid, but it relies on a client-side redirect.
- Mojang's migration was consent-gated. Per the announcement, bugs carry over with personal data stripped, but this was not confirmed against the live tenant. Some 2022 issues may not resolve.

**Fix:** keep `/browse/<key>`, or store the canonical `/browse/<project>/issues/<key>`, since both work today. Add a Deferred line: "Story 13 checks a sample of record links in a rendering browser and records the hit rate. If links fail, url falls back to the dataset DOI plus the key." Correct terms.md's "old links still answer 200" claim, or drop it.

### F4 — LOW — The GenAI semconv drifted under AD-10 (only the rename is amended; the drift predates this change)

`gen_ai.data_source.id` is still a registry attribute, but the conventions moved to `open-telemetry/semantic-conventions-genai` (the core site marks them as moved). The INTERNAL `gen_ai.retrieval` span that matches ticketscope's retrieval span:

- does not list `gen_ai.data_source.id`
- defines `gen_ai.retrieval.top_k`, where the spine uses `ticketscope.retrieval.k`
- sets the span name to `{gen_ai.operation.name}`

The spine diagram names the span `retrieval {mode}`. All GenAI attributes remain at development stability.

**Fix:** no change needed for the amendment, since setting a registry attribute is allowed. Add a version-check line to AD-10's next update: "semconv source = semantic-conventions-genai @ <commit>; consider `gen_ai.retrieval.top_k` over `ticketscope.retrieval.k`." Owner: epic 7 or whoever next touches telemetry.

### F5 — LOW — Identifiers should say which id (Identifiers)

"Its integer Jira issue id" reads as the live tracker id. It is the Jira Server id as of the January 2022 dump. Mojang's 2025 JCMA move very likely reassigned internal ids (Atlassian MIG-2740 asks for them to be preserved), while keys survive. That matters if epic 4's `get_issue` or a future refresh ever cross-references the live tracker.

**Fix:** reword it to "the Jira issue id as recorded in The Public Jira Dataset v7 (not the live Cloud id; only `key` is stable across the 2025 migration)".

### F6 — LOW — `snapshot.yml` still exists and still publishes a Kubernetes snapshot (AD-17 vs brownfield)

The spine says no workflow publishes a snapshot. On `main` today, `snapshot.yml` is dispatchable, calls the GitHub-API ingest with `INGEST_GITHUB_TOKEN`, and writes Kubernetes attribution into Release notes. The spine hands removal to story 13, which is fine. Until then the spine and the repo disagree, and a stray dispatch would publish a Release under the new rules' version namespace.

**Fix:** make removal (or disabling) of `snapshot.yml` an explicit story 13 AC, and also retire `INGEST_GITHUB_TOKEN`. Optionally note "until story 13 lands" in AD-17.

### F7 — LOW — Minor spine wording and consistency

- **AD-6 vs Deferred / AD-2.** AD-2 ships every component, ingest included, in one app image. Deferred says ingest's dump reader runs "never in the image's runtime path". Say the Mongo client is an optional dependency group excluded from the image build, or that ingest's source adapter is not in the image.
- **AD-6 duplicate links.** It doesn't say whether links to targets outside the snapshot are kept. convert.py kept them with `source_number: null`. A Jira link carries the target id, so `number` is always available. State that pairs (AD-12) use only targets present in the snapshot.
- **AD-6 "never overwritten, except by a takedown".** The takedown process (snapshot.yml notes, Provenance) *deletes* earlier assets and publishes a new version. It never overwrites. Say "never overwritten; a takedown deletes affected assets and publishes a new version".
- **ER diagram.** `DUPLICATE_LINK` has no table in `0001_init.sql`, and none is planned. Pairs are derived from the snapshot (AD-12). Either mark it "snapshot only" or drop it. The old `LABEL` entity had the same issue.
- **Deferred outcome `source`.** It maps a Jira duplicate *resolution* to `source: label`. The user decided this and `/v1` allows it. A one-line note that `label` here means "the tracker's own disposition field" would stop epic 4 reading it literally.

## Not checked

- **Live existence of 2022 MCL, REALMS and MCD issues in the Mojira Cloud tenant.** The API probe was blocked in this session.
- **Restored dump size.** User-stated as about 60 GB.
- **Mojang ids fitting int4 beyond the spike subset.** This holds for the 32,154-issue subset, verified by the timed load.

## Sources

- [Zenodo record 15719919](https://zenodo.org/records/15719919)
- [minecraft.net: Changes to Minecraft bug reporting system](https://www.minecraft.net/en-us/article/changes-to-minecraft-bug-reporting-system)
- [OpenTelemetry semconv registry: gen-ai](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)
- [open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai) (`model/gen-ai/registry.yaml`, `spans.yaml`)
- [Atlassian MIG-2740: preserve internal issue IDs in JCMA](https://jira.atlassian.com/browse/MIG-2740)
- [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode)
- Live `https://bugs.mojang.com` SPA bundle, read 2026-11-06
