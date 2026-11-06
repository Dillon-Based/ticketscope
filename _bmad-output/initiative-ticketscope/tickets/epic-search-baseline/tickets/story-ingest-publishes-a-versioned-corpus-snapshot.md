---
id: 3
type: story
title: "Ingest publishes a versioned corpus snapshot"
parent: epic-search-baseline
covers: [R1]
after: [1, 2, 4]
hitl: true
risk: high
---

# Ingest publishes a versioned corpus snapshot

## Description

The ingest job turns closed Kubernetes issues into a frozen, versioned corpus snapshot that every environment and the eval load from (AD-6). Story 5 loads it, and epic-eval-gate derives its labelled pairs from it.

**Person's steps (hitl):**

- A person creates a read-only GitHub token and stores it as a repo secret for `snapshot.yml`. The default Actions token allows too few API calls for this corpus.
- A person dispatches the first `snapshot.yml` run and checks its Release.

- **What it fetches.**
  - `jobs.ingest` is the only component that calls the GitHub API.
  - It takes closed `kubernetes/kubernetes` issues, not PRs, closed in about the last three years, most recently closed first, capped at 20,000.
  - Each issue carries every field AD-6 names: labels, comments (`author_association`, `body`, `created_at`), and timeline events. Timeline events include `marked_as_duplicate` and cross-referenced or closing PRs, each with its merged state.
  - It applies any conditions that story 2 sets.
- **What it writes.**
  - Compressed JSONL, one issue per line, that validates against story 1's schema.
  - A SHA-256 checksum published beside it.
- **Report.** It reports the short and log-heavy split, using story 4's kind function at its default threshold. Story 5 sets the final threshold.
- **Publishing.**
  - `snapshot.yml`, on dispatch, publishes the snapshot as a Release asset with version `YYYY.MM.N`. N is the next free number for that month.
  - A published snapshot is never overwritten. A new run makes a new version, so eval baselines stay tied to one corpus (AD-12).
- **Load-time budget.**
  - Before publishing, `snapshot.yml` times a load of the snapshot into the in-repo Postgres image on the runner, through story 1's load path.
  - The window is tuned so this load finishes within 10 minutes. That leaves the rest of the 30-minute spin-up (initiative R10) to Terraform, EKS and Helm.
- **Long runs.** A run that hits a rate limit or the Actions job time limit resumes from where it stopped instead of starting over.
- **Tests.** PR tests run against recorded GitHub API responses, never the live API. The recordings include a rate-limit response and an issue with 100 or more comments. They show that ingest issues only `GET` requests.

## Requirements

Verify: A dispatched `snapshot.yml` run publishes a `YYYY.MM.N` Release asset and its checksum. The asset validates against the committed schema and holds both short and log-heavy issues. The Release notes state:

- the window,
- the issue count,
- the short and log-heavy split,
- a measured load time within 10 minutes.

A second dispatch publishes `YYYY.MM.N+1` and leaves the first asset unchanged.

## References

- parent — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md, sections Requirements (R1), Constraints (Corpus scope, Corpus terms, Public repo, Snapshot format, Outcome terms), Boundaries (touch points: GitHub issues API, GitHub Releases)
- initiative — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R10)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-6, AD-8, AD-12, AD-17, AD-21; Consistency Conventions (Identifiers, Dates & formats, Provenance, Secrets)
- test design — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md, rows owned by story 3

## Notes

- Decision: The corpus load gets 10 minutes of the 30-minute spin-up, timed in `snapshot.yml` on the runner before publishing (user, 2026-11-06).
- Decision: Ingest uses a read-only token stored as a repo secret by a person, and resumes after a rate limit or job timeout (user, 2026-11-06).
- Decision: Published snapshots are never overwritten; each run gets the next `YYYY.MM.N` and a SHA-256 checksum (user, 2026-11-06).
- If story 2 says the text may not be republished, this story stops before publishing and the epic is replanned.
- The outcome rules need these fields from each issue: labels, `state_reason`, closing PRs with merged state, `marked_as_duplicate` events, and comment `author_association` with `created_at` set against the issue's `closed_at`.
- Check beyond the criteria (high risk): on a sample of 20 issues from the snapshot, compare each field against the issue on github.com. Cover at least one duplicate, one closed by a merged PR, and one with 100 or more comments, so paging is proven.
