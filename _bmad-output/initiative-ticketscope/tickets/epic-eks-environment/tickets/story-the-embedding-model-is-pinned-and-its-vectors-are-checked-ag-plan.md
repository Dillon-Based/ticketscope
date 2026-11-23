---
title: 'The embedding model is pinned and its vectors are checked against references'
type: 'feature'
ticket: '13'
created: '2026-11-19'
status: done
baseline_revision: '92ccda2be9a048b25118223bb6c60d8f8ddfd33f'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `images/app.Dockerfile` downloads the model unpinned, so a changed upstream file changes retrieval under the same `model_id` (DW-6). The embedder has no committed reference vectors, and nothing checks the arm64 image the EKS nodes run (DW-3, retro A6, R-004).

**Approach:** The build fetches `Qdrant/bge-small-en-v1.5-onnx-Q` at a pinned commit and fails unless the ONNX file's SHA-256 matches. Reference vectors, produced once outside fastembed, are committed, and a test compares the image's embedder to them on amd64 and arm64.

## Boundaries & Constraints

**Always:** Pins are build ARGs in `app.Dockerfile`: `EMBEDDING_MODEL_REVISION` (the HF commit, `aa8f8b060edb00e03bfdd08813a2949946c8ba55` as of 2026-11-19) and `EMBEDDING_MODEL_SHA256` of `model_optimized.onnx` (`51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431`). The build downloads that revision, points `refs/main` at it, then loads through fastembed with `HF_HUB_OFFLINE=1`. The oracle is made with `onnxruntime` and `tokenizers` directly, never fastembed, and is committed with its revision, sha and tolerance. Tolerance: cosine to the reference at least 0.9999 per text, and each component within 2e-3 (widened from 1e-3 by the user, "take your picks", 2026-11-20, after the arm64 image showed 1.05e-3 on the text `crash`). Reference vector files are pinned by byte length and SHA-256 as `test_dense_oracle_pinned.py` does. Tests carry `@pytest.mark.criterion`.

**Never:** Change the model, `modelId`, the chart pin, preprocessing, `kind`/`outcome` or the eval baseline. Hand-write `eval/baseline.json`. Compute the oracle with the code under test. Read Hugging Face outside the `model` build stage. Fix DW-7. Edit an existing oracle file.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Pinned build | Revision and sha match upstream | `model` stage passes; offline embed works | No error expected |
| Changed file | `EMBEDDING_MODEL_SHA256` differs from the downloaded file | Build fails naming expected and actual sha | Exit non-zero, nothing copied to `/models` |
| Bad revision | Revision does not exist | Build fails | Download error propagates |
| Vectors match | Image embedder vs reference, both arches | Within tolerance | No error expected |
| Drift | A component moves past tolerance | Test names the text and the largest difference | Fails; the tolerance is not widened to pass |

</frozen-after-approval>

## Code Map

- `images/app.Dockerfile:24-30` -- the unpinned `model` stage; replace its `RUN` with a call to the new script.
- `images/fetch_model.py` -- new: downloads at the revision, verifies the sha (`hashlib`, 1 MiB chunks), writes `refs/main`, then loads once offline. Takes revision and sha as args.
- `src/ticketscope/adapters/embedder.py:93` -- `model_file_sha256` finds the same file; reuse it in the image test to assert the pin. Do not change it.
- `tests/unit/test_chart_embeddings.py:101` -- pattern for Dockerfile-vs-values checks; extend with the two new ARGs' shape (40 and 64 hex).
- `tests/dense_oracle.py`, `tests/unit/test_dense_oracle_pinned.py` -- the pinning pattern to copy.
- `tests/image/test_app_image.py` -- the image test runs `docker run --network none`; add the reference comparison beside it.
- `.github/workflows/ci.yml:182` (`images`, both arches natively) and `:212` (`containers`, amd64) -- the `images` job only builds; add uv setup, then `pytest tests/image` on each arch with the require flag.
- `scripts/reference_vectors.py` -- new: the oracle generator, run by a person; prints JSON.
- `tests/fixtures/embedder_reference.json` -- new: texts, vectors (384 floats each), revision, sha, tolerance.

## Tasks & Acceptance

**Execution:**
- [ ] `images/fetch_model.py`, `images/app.Dockerfile` -- pinned fetch, sha check, offline load -- DW-6
- [ ] `tests/unit/test_model_pin.py` -- script fails on a wrong sha and on a missing file (tiny local fixture, no network); Dockerfile ARGs are hex of the right length and the script is the only HF reader -- DW-6 shown by a test
- [ ] `scripts/reference_vectors.py` -- independent oracle; run once, output committed -- DW-3
- [ ] `tests/fixtures/embedder_reference.json`, `tests/unit/test_embedder_reference_pinned.py` -- reference data and its byte pin -- DW-3
- [ ] `tests/image/test_app_image.py` -- compare the image's `FastEmbedEmbedder` to the reference within tolerance; assert `model_file_sha256` equals the Dockerfile pin -- DW-3
- [ ] `.github/workflows/ci.yml` -- run `tests/image` in each `images` matrix leg, so arm64 is checked -- R-004
- [ ] `_bmad-output/initiative-ticketscope/deferred-work.md` -- set DW-3 and DW-6 `status: resolved` with this story as the closing entry (the file the build appends to)

**Acceptance Criteria:**
- Given the Dockerfile download, when `EMBEDDING_MODEL_SHA256` does not match the fetched file, then the build fails with both digests, shown by a unit test.
- Given the Dockerfile, then it names a revision and a sha, and `fetch_model.py` is the only place that reads Hugging Face.
- Given the amd64 and arm64 app images, when each embeds the reference texts, then every vector is within the stated tolerance of the committed reference.
- Given the eval run on the unchanged model, when CI scores it, then `eval/baseline.json` needs no change.

## Implementation Notes

- Built 2026-11-20: `images/fetch_model.py`, pinned ARGs, `scripts/reference_vectors.py`, `tests/fixtures/embedder_reference.json` (94,712 bytes, sha256 `5c65fce1…9f64`), unit and image tests, `ci.yml` `images` job runs `tests/image` per arch, DW-3 and DW-6 resolved. `.dockerignore` gains `!images/fetch_model.py`; `test_chart_embeddings.py` now keys on `fetch_model.py`.
- Verified on arm64 (colima): image builds; a wrong sha fails the `model` stage naming both digests; `scripts/check.sh` passes; unit suite 1515 passed.
- **Resolved (user, "take your picks", 2026-11-20): component limit widened to 2e-3; cosine unchanged.** Was: `test_the_image_embedder_matches_the_reference_vectors` fails on the arm64 image: text `crash` (3 tokens) has cosine 0.999989 (passes 0.9999) but largest component difference 1.050e-3 (limit 1e-3). Deterministic over repeated runs, same with one text per call, same with the pre-review loader. Host fastembed vs reference was 4.3e-4. Tolerance is frozen, so it was not changed. The amd64 leg has not run.

## Plan Change Log

## Review Triage Log

Quick lens, 6 findings:
- medium, patched: `HF_HUB_OFFLINE` set after `huggingface_hub` was imported, so fastembed's load could resolve `main` online and read an unverified revision. The load now runs in a fresh process with the variable set and requires the cache to hold only the pinned snapshot.
- low, patched: the only-reader test did not catch an unpinned `TextEmbedding(` in the Dockerfile. It does now.
- low, patched: the 384-dimension test lacked a criterion marker.
- medium, patched: the `images` job's path filter now includes `embedder.py`, `tests/image/**`, the fixture and `uv.lock`, so the arm64 check runs when what it tests changes.
- low, rejected: image tests run after both builds in one job; the fix adds steps for little gain.
- false: the long reference text is 1,654 tokens, so truncation is exercised.

## Design Notes

fastembed 0.9.1 resolves this model to the quantized Qdrant export (`model_optimized.onnx`, 66,465,124 bytes), not BAAI's own file, and its download takes no revision. `snapshot_download(revision=...)` followed by writing `refs/main` makes its offline load read the pinned snapshot; this was run on 2026-11-19 and embedded a 384-dim vector. The reference vectors fix the manifest's `model_sha256` too, since `model_file_sha256` hashes the same file.

Which texts to embed: a short list of real Mojang-style issue titles plus one empty-ish and one long (over 512 tokens, to pin truncation). The set is committed with the vectors.

## Verification

**Commands:**
- `uv run pytest tests/unit/test_model_pin.py tests/unit/test_embedder_reference_pinned.py` -- expected: pass
- `scripts/check.sh` -- expected: all static jobs pass
- `docker build -f images/app.Dockerfile -t ticketscope-app:t .` then `TICKETSCOPE_TEST_APP_IMAGE=ticketscope-app:t TICKETSCOPE_REQUIRE_CONTAINER_TESTS=1 uv run pytest tests/image` -- expected: pass on this machine's arm64 image
- `docker build --build-arg EMBEDDING_MODEL_SHA256=$(printf 0%.0s {1..64}) -f images/app.Dockerfile .` -- expected: fails in the `model` stage with the digest mismatch

**Manual checks (if no CLI):**
- The `images` job's arm64 and amd64 legs both run `tests/image` and pass in CI; the amd64 leg cannot be run locally.
