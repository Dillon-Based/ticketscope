---
id: 1
type: story
title: "Tracer: keyword search answers through the Gateway on kind"
parent: epic-search-baseline
covers: [R3, R5, R7]
after: []
hitl: true
risk: high
---

# Tracer: keyword search answers through the Gateway on kind

## Description

The repo, and the thinnest path through every layer this epic touches: a keyword query goes in through the Gateway on kind and ranked issues come back from Postgres. Later stories build on everything here.

**Person's step (hitl):** a person creates the public GitHub repo, enables Actions, and runs `scripts/kind-up.sh` locally once to confirm local bring-up matches CI.

- **Repo and PR CI.** One uv repo in the spine's layout. `ci.yml` runs ruff, pyright, pytest and import-linter with the AD-1 layer contracts.
- **Code path.**
  - `ticketscope.contract` holds the `/v1` search models.
  - `core` holds the Retriever port, the mode registry with the keyword mode, and the in-memory CorpusStore fake.
  - The Postgres adapter ranks with pg_textsearch BM25 and negates its scores, so a higher score is better.
  - `api` serves `POST /v1/search` and connects as `ticketscope_ro`. `migrate` and `load` connect as the app owner.
- **Database.**
  - The Postgres image is the CNPG standard PG18 image plus pg_textsearch, preloaded through `shared_preload_libraries`. pgvector is included.
  - Migration 0001 creates both extensions, the issue table with kind and outcome columns, the `corpus_meta` table, and the `ticketscope_ro` default grants.
- **Snapshot.**
  - The snapshot JSON Schema v1 carries every AD-6 field.
  - It is committed with a small synthetic fixture snapshot that holds short and log-heavy issues and no real issue text.
  - The fixture ships in the app image under snapshot version `fixture`, pinned in values. Story 5 swaps in a real version by changing the pin.
  - `load` loads the pinned snapshot and writes the `corpus_meta` row, which `api` reads for `corpus_version`.
  - The fixture records each issue's expected kind beside it, outside the snapshot schema, and `load` stores that kind. Story 5 replaces it with the kind computed in core.
  - Outcomes read `unknown` until story 5 loads derived values.
- **Images and kind.**
  - Both images are tagged with the git SHA (AD-16).
  - `_kind-deploy` builds each image for the runner's architecture only. `ci.yml` builds both for `linux/amd64` and `linux/arm64` when a PR changes files under `images/` (AD-16).
  - `scripts/kind-up.sh` is the only kind bring-up, and `_kind-deploy.yml` calls it (AD-17).
- **Releases.**
  - The `platform` release holds the Gateway API CRDs, Envoy Gateway with cloud-provider-kind, and the CNPG operator.
  - The `ticketscope` release holds a two-instance Cluster, the `migrate` and `load` hooks in AD-22 order, `api`, and its HTTPRoute.
  - `values.yaml` holds the defaults; `values-kind.yaml` holds only environment facts (AD-25).

This story also proves the epic's assumption that a GitHub-hosted runner fits kind.

## Requirements

Verify: On a PR, `ci.yml` passes and `_kind-deploy` brings up both releases on kind, with the Cluster reporting two ready instances. Through the Gateway, `POST /v1/search` with mode `keyword` returns:

- the fixture issue written to match the query best at rank 1,
- scores that fall as rank rises,
- `corpus_version` set to `fixture`,
- every field of the `/v1` shape.

A deliberate change that makes `core` import an adapter fails import-linter.

## References

- parent — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md, sections Requirements (R3, R5, R7), Constraints (Snapshot format, Toolchain, Public repo), Notes (tracer decisions, Assumption)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1, AD-2, AD-4, AD-6, AD-7, AD-9, AD-13, AD-14, AD-16, AD-17, AD-19, AD-20, AD-21, AD-22, AD-25; Structural Seed (repo layout)

## Notes

- Decision: The fixture carries each issue's expected kind, and story 1's load stores it until story 5 loads the computed kind. This keeps the tracer free of story 4 (user, 2026-11-06).
- Decision: Multi-arch builds run in `ci.yml` only when image files change; `_kind-deploy` builds for the runner's architecture, so PR deploys stay fast (user, 2026-11-06).
- Check beyond the criteria (high risk): the `_kind-deploy` job summary records the runner's peak memory and free disk, and the wall-clock time from kind-up to `api` Ready. These numbers back the runner-fit assumption and give the later stories their headroom.
