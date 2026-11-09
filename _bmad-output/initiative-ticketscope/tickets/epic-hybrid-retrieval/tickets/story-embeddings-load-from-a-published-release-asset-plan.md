---
title: 'Embeddings load from a published Release asset'
type: 'feature'
ticket: '4'
created: '2026-11-09'
status: 'built'
baseline_revision: '9e6b6e73ad1dc2c37fc1a478202be0cdbcb6f7ee'
route: 'full'
route_source: 'auto'
risk: 'high'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/test-design-epic-3.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-hybrid-retrieval/tickets/spike-choose-the-embedding-model-findings.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `load` can only compute embeddings itself (story 1, kind only, off by default), so CI and `env-up` have no dense data and the 1,146 s embedding cost cannot fit spin-up.

**Approach:** The publish script computes embeddings from the published snapshot on a person's machine and attaches them as a checksummed Release asset. `values.yaml` pins it. `load` downloads, verifies and bulk-loads it in the existing single transaction.

## Boundaries & Constraints

**Always:** Keep the publish guards (clean `main`, never overwrite, timed load under 600 s, generated notes with attribution). Embed from the checksum-verified snapshot only, which is masked at ingest. The asset holds only issue number, model id and vector, plus a manifest (snapshot, model id, model file SHA-256, preprocessing version, runtime versions, counts). Write issues, embeddings and `corpus_meta` in one transaction. A wrong checksum, missing or extra issue, or wrong dimension fails the load and keeps the previous corpus. A second load is a no-op. No environment file overrides the pin (AD-25). Model id and preprocessing version come from one source.

**Decisions (user, 2026-11-09):** (1) The asset is its own Release, tagged `embeddings-<ver>-<model>-<preproc>`; no published Release is touched and the snapshot pin is unchanged. (2) A pinned asset always wins; `embeddings.computeOnKind` applies only when the pin is empty, and `kind-up.sh` `EMBEDDINGS_COMPUTE=1` stays as the no-pin path. (3) The 600 s timed load includes the asset download and bulk-load, and is reported in the notes.

**Never:** Compute embeddings in `load` when the asset is pinned. Overwrite or `--clobber` an asset. Add a takedown step (C-6, out of scope). Change the `/v1` or span contract.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Pinned load | Pin and checksum set, empty DB | `issue_embedding` has one row per issue, `corpus_meta` has model id, no `Embedder` call | No error expected |
| Repeat load | Same snapshot, model, preprocessing | No-op (`reload_reason` is None) | No error expected |
| Bad checksum | Asset bytes differ from pin | Load fails with reason, DB unchanged | Non-zero exit, old corpus kept |
| Bad coverage | Asset lacks or adds an issue, or wrong dimension | Load fails, DB unchanged | Non-zero exit, old corpus kept |
| Empty pin checksum | `embeddings` pin present, sha256 empty | Pin test fails | Load returns 1 |
| Publish re-run | Asset name already published | Script refuses | Non-zero exit, nothing uploaded |

</frozen-after-approval>

## Code Map

- `scripts/publish-snapshot.sh` -- guards at lines 37-47, `taken_tags` 49-52, timed load 82-88, `gh release create` 106-110. Extend with an embed-and-attach phase.
- `scripts/time-load.sh` -- sets the snapshot checksum only. Needs the embedding pin env.
- `src/ticketscope/jobs/ingest/notes.py` -- `render_notes`, `ATTRIBUTION`. Add embedding notes.
- `src/ticketscope/jobs/load/main.py` -- `run` 222, `pinned_meta` 157, `reload_reason` 167, `embedding_rows`. Add the asset path.
- `src/ticketscope/adapters/release.py` -- `fetch_snapshot`, `asset_name`, `asset_url`, `sha256_file`, `ChecksumMismatch`, `read_snapshot_pin` (regex parser, snapshot-only). Generalise or add an embeddings pin reader.
- `src/ticketscope/adapters/postgres.py` -- `EmbeddingRow` 235, `replace_corpus` 280 (one transaction). Reuse it.
- `src/ticketscope/core/derive.py` -- `embedding_text`, `EMBEDDING_RULE_VERSION`, `preprocessing_version`. The single source for the key.
- `src/ticketscope/settings.py` -- add the asset pin settings.
- `deploy/charts/ticketscope/values.yaml` -- `embeddings:` block at lines 38-46. Add `assetVersion` and `sha256`.
- `deploy/charts/ticketscope/templates/jobs.yaml` -- env mapping around lines 72-90, deadline at line 56.
- `scripts/kind-up.sh` -- `EMBEDDINGS_COMPUTE` at about lines 17 and 127-132.
- `.github/workflows/ci.yml` -- `integrated-check` at lines 120-131.
- `tests/integrated/test_dense_kind.py` -- count assertion at about lines 116-118.
- Tests to extend: `tests/unit/test_publish_script.py`, `test_load_main.py`, `test_release.py`, `test_chart_embeddings.py`, `test_chart_pin.py`. Do not change `.importlinter` layering.

## Tasks & Acceptance

**Execution:**
- [ ] `src/ticketscope/adapters/release.py` -- pin reader and fetch for the embedding asset -- reuse checksum verification
- [ ] `src/ticketscope/jobs/load/main.py` -- load from the asset when pinned, with coverage and dimension checks -- no compute path
- [ ] `src/ticketscope/jobs/ingest/notes.py` and `scripts/publish-snapshot.sh` -- embed from the verified snapshot, write the manifest, attach with the guards
- [ ] `scripts/time-load.sh` -- time the asset load
- [ ] `values.yaml`, `jobs.yaml`, `settings.py` -- pin keys and env -- AD-25
- [ ] `ci.yml`, `kind-up.sh`, `test_dense_kind.py` -- integrated-check loads the asset
- [ ] Unit and Postgres tests for each I/O row, the pin and the publish guards

**Acceptance Criteria:**
- Given the pin, when `load` runs on kind, then `issue_embedding` has one row per issue and no embedding is computed.
- Given a loaded corpus, when `load` runs again, then it is a no-op.
- Given a wrong checksum, when `load` runs, then it fails with its reason and the corpus is unchanged.
- Given the timed load, when it runs, then it stays under 600 s.
- Given a person runs the publish script, then the Release shows the asset, its checksum and notes with attribution, and a person merges the pin (hitl).

## Implementation Notes

## Plan Change Log

## Review Triage Log

Pass 1 (quick): 0 high, 1 medium, 3 low, 6 false.

| Finding | Verdict | Route | Evidence |
|---|---|---|---|
| Wrong-dimension check is self-referential | low | rejected | Needs a checksummed asset built consistently wrong, pinned by a person, with the model id matching. Fixing it adds a new setting. |
| AC 1 and 4 not exercised in CI | false | - | The pin is empty by design; the person merges it (hitl). Tests skip until then. |
| Dense test flag contradicts the pin | low | patch | `_dense_enabled()` now returns True whenever pinned. |
| `model_file_sha256` can hash another model's file | medium | patch | `rglob(...)[0]` could match a sibling model; now restricted to the model's `models--<hf repo>` directory. |
| Half-finished publish (snapshot published, embeddings fail) | false | - | By design: the embeddings Release is separate and `--embeddings-only` recovers it. |
| Snapshot and embedding pins must move together | false | - | The load fails loudly with a reason. The plan prefers that to a silent fallback. |
| `time-load.sh` symlink may dangle | false | - | `SNAPSHOT_DIR` is made absolute with `cd && pwd` at line 29. |
| Timed load excludes the real download | low | rejected | Loopback is the practical test; the real download is a manual check for the person. |
| Notes CLI traceback on a bad manifest | low | rejected | The manifest is our own build output; the fix adds a guard. |
| Planned test extensions not in the diff | false | - | The same coverage sits in new test files and all matrix rows are covered. |

## Design Notes

The asset key is `(snapshot, model, preprocessing)`. The preprocessing string comes from `preprocessing_version(embeddings=True)`, so the name, the pin and `corpus_meta` cannot drift apart.

## Verification

**Commands:**
- `uv run pytest tests/unit tests/postgres` -- expected: pass
- `uv run lint-imports` -- expected: layers kept
- `helm template deploy/charts/ticketscope` -- expected: renders with the embeddings pin

**Manual checks (if no CLI):**
- A person runs `scripts/publish-snapshot.sh`, confirms the Release asset and notes, then merges the pin.
- `ci.yml` `integrated-check` passes loading the asset.
