---
type: epic
title: "Keyword search over Mojang issues, deployed on kind"
parent: initiative-ticketscope
covers: [R1, R2, R3, R5, R8, R11]
sources: []
companions: [_bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md]
after: []
refined: true
risk: high
status: done
---

# Keyword search over Mojang issues, deployed on kind

## Description

The platform baseline and the first working search, built to the spine's contracts.

- **Repo and CI.** One workflow per concern, plus a reusable kind-deploy step that epics 2 and 4 build on.
- **Releases on kind.** Two Helm releases, which epic 5 later deploys to EKS:
  - The platform release holds the operators, the Gateway, the OTel Collector, Tempo and Grafana.
  - The app release holds a two-instance CloudNativePG Postgres 18 with pgvector and pg_textsearch, backing up to SeaweedFS.
- **Corpus.** An ingest job publishes a versioned corpus snapshot of Mojang bug-tracker issues, taken from The Public Jira Dataset v7, as a GitHub Release asset. A load job, the only writer, loads it with each issue's kind and outcome. Epic 2 derives its labelled pairs from that snapshot, and epic 3 adds its embedding table.
- **Search.** A keyword (BM25) retrieval API serves the one search page under the /v1 contract and retriever registry, which epic 3 extends and epic 4 calls.
- **Tracing.** Retrieval and database spans follow the span contract, which epics 3, 4 and 7 build on.

## Outcome

A triage engineer pastes a vague or log-heavy ticket into the page on the kind-deployed chart and sees ranked Mojang issues with how each ended (initiative R1, R2, R5).

## Requirements

- R1 (parent R1): An ingest job publishes a versioned corpus snapshot of the Mojang subset of The Public Jira Dataset v7 (see Corpus scope). The snapshot carries every field the spine's snapshot contract names. It is met when a published snapshot validates against the committed JSON Schema and holds both short and log-heavy issues.
- R2 (parent R1): A load job, the only writer, loads the pinned snapshot and stores each issue's kind and outcome, each computed once in core. It is met when every loaded issue has a kind and an outcome, and the load reports the share of each kind and each outcome.
- R3 (parent R2): Keyword (BM25) retrieval through `/v1/search` returns ranked issues with how each ended. It is met when a vague query and a log-heavy query each return ranked issues with outcomes.
- R4 (parent R5): One search page takes ticket text and shows the ranked issues with how each ended. It is met when the page renders results for both example queries.
- R5 (parent R3): CloudNativePG Postgres runs on the cluster with pgvector, pg_textsearch, two instances, persistent volumes and backups to SeaweedFS. It is met when CI deploys it on kind on every PR and a backup completes.
- R6 (parent R8): One search request yields one trace whose retrieval and database spans follow the span contract, viewable in Grafana through Tempo. It is met when CI on kind shows that trace.
- R7 (parent R11): Helm deploys the platform and app releases, and CI runs them on kind on every PR through the reusable kind-deploy step. It is met when the integrated check passes on a PR.

## Constraints

- **Outcome precedence:**
  1. duplicate: a `marked_as_duplicate` event or the `triage/duplicate` label
  2. fixed: closed by a merged linked PR
  3. not_planned: from `state_reason`
  4. stale: a `lifecycle/rotten` or `lifecycle/stale` label
  5. answered: a support issue closed after a maintainer comment
  6. unknown

  This GitHub precedence stays in core, covered by story 4's unit tests on synthetic issues; no snapshot feeds it once the fixture moves to v2, and the refactor sweep may retire it. Changing it requires a reload and a baseline update (spine AD-8, AD-12).
- **Jira outcome:** for the Mojang corpus, the outcome comes from the issue's Jira `resolution`, mapped per spike 12's `outcome-mapping.md`: duplicate, fixed, not_planned, stale, answered, else unknown. A Question or Support type issue resolved after a comment by someone other than the reporter is answered. Its `/v1` source by branch: duplicate → `label`; answered → `closing_comment`; fixed, not_planned, stale and unknown → `null`. Changing the mapping requires a reload and a baseline update (spine AD-8, AD-12).
- **Outcome terms:**
  - A support issue carries the `kind/support` label.
  - A maintainer comment has an `author_association` of OWNER, MEMBER or COLLABORATOR.
  - The `/v1` outcome `source` by branch: duplicate → `label`; fixed → `linked_pr`; answered → `closing_comment`; not_planned, stale and unknown → `null`.
  - These terms are GitHub's. Jira issues have no labels of this kind and no `author_association`; the Jira outcome above replaces them for the Mojang corpus.
- **Example queries:** one vague and one log-heavy query, picked by the load story from the real snapshot and committed in a golden-query file with the issue each should return; the page, sweep and integrated-check stories read that file.
- **Derivation version:** core exposes a derivation version that changes with the kind threshold or the outcome rule; it is part of the preprocessing version in `corpus_meta`, so a change reloads (spine AD-8, AD-21).
- **Corpus scope:** the resolved issues of Mojang's MCL, REALMS and MCD projects in The Public Jira Dataset v7 (collected January 2022), plus the unresolved issues their duplicates point to: about 32,000 issues, capped at about 50,000. One Jira instance only, because Jira issue ids are unique only within an instance. The load finishes within 10 minutes, its share of the 30-minute spin-up (initiative R10). Published snapshots are never overwritten, except that a takedown deletes the Release assets holding the removed issue (see Corpus terms).
- **Corpus terms:** spike 2 settled them for GitHub text, and spike 12 for the Mojang corpus, whose terms the author accepted: the issue text may be stored and republished as a public Release asset and demo index, on four conditions.
  1. Attribution: every record links to its bugs.mojang.com issue, and the Release notes and README carry spike 12's attribution line (`terms.md`): the dataset and the MSR 2022 paper are cited, and the text belongs to its authors.
  2. No identities: no reporter, assignee or author id appears anywhere in a snapshot, masked UUIDs included, and `[~user]` mentions are masked.
  3. Masking: ingest masks email addresses and token- or key-shaped secrets in issue and comment bodies before publishing.
  4. Takedown: on request, the issue goes on a committed exclusion list, the next snapshot version leaves it out, and a person deletes the earlier Release assets that hold it.
- **Public repo:** the repo is public on GitHub, so Release assets are public.
- **Kind rule:** a deterministic core function over the issue body that counts fenced blocks and log-like lines; Jira `{code…}` and `{noformat}` toggles count as fenced blocks (spike 12). The load story sets the threshold and reports the split. Changing it requires a reload and a baseline update (spine AD-8).
- **Snapshot format:** compressed JSONL, one issue per line, with its JSON Schema committed in the repo as epic-eval-gate's contract (spine AD-6). The Jira corpus needs schema v2, carrying the Jira `resolution`, the readable issue key and a derived non-reporter-comment flag in place of `author_association`.
- **Toolchain:** ruff for lint and format, pyright and pytest. Test-framework depth goes to `bmad-tea-framework`.

## Done when

- CI deploys the platform and app releases to kind on every PR. CloudNativePG Postgres runs with pgvector, pg_textsearch, two instances, persistent volumes, and backups to SeaweedFS, and a backup completes (R5, R7).
- Spikes 2 and 12 have settled the corpus and its terms. A published Mojang corpus snapshot then validates against the committed JSON Schema and holds short and log-heavy issues with their resolution, comments and duplicate links (R1).
- The load job stores every issue with its kind and an outcome, and reports the share of each (R2).
- A vague query and a log-heavy query to the keyword mode of `/v1/search` return ranked issues with outcomes, and the page shows them (R3, R4).
- A search request yields one trace with retrieval and database spans in Tempo, viewable in Grafana (R6).
- import-linter enforces the spine's layer rules in CI. The code follows the spine's /v1, span, Helm and CI contracts.
- Delivered on the cluster, with an integrated check passing in CI.

## Boundaries

- Dense and hybrid modes and the embedding table belong to epic-hybrid-retrieval; extracting labelled pairs and scoring belong to epic-eval-gate.
- The MCP server belongs to epic-mcp-server. EKS, S3 backups and the recorded drills belong to epic-eks-environment.
- Touch point: The Public Jira Dataset v7 on Zenodo — the source of the corpus, read only; owner: epic-search-baseline
- Touch point: GitHub Releases — hosts the versioned corpus snapshot and precomputed embeddings; owner: epic-search-baseline

## References

- parent — _bmad-output/initiative-ticketscope/initiative-ticketscope.md, section Requirements (R1, R2, R3, R5, R8, R11)
- architecture spine — _bmad-output/initiative-ticketscope/architecture-ticketscope/architecture-ticketscope.md, AD-1–AD-4, AD-6–AD-11, AD-13, AD-14, AD-16–AD-22
- test design — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/test-design-epic-1.md, Test Coverage Plan (the Owner column names the story that writes each test), Mitigation Plans (R-004)

## Notes

- Decision: Adopted the architecture spine. The snapshot/load split, the platform release with Tempo and Grafana, pg_textsearch for BM25, and SeaweedFS backups on kind replace this epic's earlier wording (user, 2026-11-05).
- Decision: Refined. The outcome precedence rule and the corpus scope are settled now; corpus terms go to a human-in-the-loop spike before ingest publishes; the repo is public (user, 2026-11-06).
- Decision: The kind-rule shape, the snapshot format and the toolchain are settled at refinement as Sofia's picks, unopposed. The page is left to its story: one server-rendered page from `api`, with no JS framework (user, 2026-11-06).
- Assumption: A GitHub-hosted runner fits kind with the platform release, two Postgres instances and SeaweedFS. The tracer story proves it first.
- Decision: Stories planned (11 entries). The tracer bullet is story 1, "Tracer: keyword search answers through the Gateway on kind", kept whole with the repo and CI setup inside it rather than split out, because it proves the riskiest path (user, 2026-11-06).
- Decision: Sequencing. The corpus-terms spike (2) comes second as the least certain part. Three lanes run after the tracer: data 2 → 4 → 3 → 5, API 6 → 7, platform 8; they meet at the trace story (9). Stories sharing code wait on each other through `after` (user, 2026-11-06).
- Decision: The tracer uses a synthetic fixture snapshot with no real issue text until the corpus terms are settled (user, 2026-11-06).
- Decision: The outcome terms and the example-query owner are settled as Sofia's picks (see Constraints) (user, 2026-11-06).
- Decision: The refactor sweep (10) and a closing integrated check on kind (11) are kept (user, 2026-11-06).
- Decision: Story 1.5 reviewed. The derivation version joins the reload check, a reload swaps the corpus in one transaction, and the example queries move from these Notes to a committed golden-query file (user, 2026-11-06).
- Decision: The redone test design is adopted as a companion. Each story writes the tests the design assigns it, and its one open risk, R-004 (keyword ranking can pass on irrelevant results), is mitigated by story 5's golden-query file and story 11's expected-issue checks. If no vague query's expected issue ranks in the top-k under keyword, story 5 records it as a known keyword miss, and story 11 reports that check without gating it until epic-hybrid-retrieval (user, 2026-11-06).
- Decision: The epic builds unattended through the loop; stories 1, 3 and 5 carry `plan_checkpoint`, and no story carries `done_checkpoint` (user, 2026-11-06).
- Decision: Corpus terms settled (spike 2): yes, with attribution, no author logins, masking of emails and secrets, and a takedown path that may delete earlier Release assets. Story 3 carries the conditions; this amends "published snapshots are never overwritten" for takedowns only (user, 2026-11-06).
- Decision: Added spike 12, "Choose the Jira corpus". The first Kubernetes snapshot (5,907 issues) has 21 duplicates and none with a target, too little ground truth for epic-eval-gate. The spike tests The Public Jira Dataset v7 as the corpus. Story 5 waits on it, and so does epic-eval-gate's pair extraction. It switches if a subset has usable terms, at least about 1,000 in-subset duplicate pairs with at least about 200 of each kind, under 20% unknown outcomes, and fits the load budget. A switch replans stories 1–5, the schema, and epic-eval-gate (user, 2026-11-06).
- Decision: Spike 12 decided: switch the corpus to The Public Jira Dataset v7 (Zenodo 15719919, CC BY 4.0), subset Mojang MCL + REALMS + MCD: resolved issues to January 2022 plus the unresolved targets of their duplicates. That is 32,154 issues with 10,466 in-subset duplicate pairs (10,162 short, 304 log-heavy at threshold 3), 0.7% unknown, loaded in 3.9 s. Outcomes come from `resolution` per spike 12's `outcome-mapping.md`. "Answered" means a Question/Support-type issue resolved after a comment by someone other than the reporter. The kind rule maps Jira `{code}`/`{noformat}` blocks onto fences, which needs a reload and a baseline update. Attribution is the line in spike 12's `terms.md`, plus a link to each source issue. If Mojang's terms are judged insufficient, fall back to Apache SPARK. The data lane (stories 1–5 and the snapshot schema) and epic-eval-gate are to be replanned (user, 2026-11-06).
- Decision: Mojang's terms are accepted, so the SPARK fallback is not taken. Corpus scope, Corpus terms, the Jira outcome, the Kind rule, the Snapshot format and the source touch point are amended above, and the epic is renamed to "Keyword search over Mojang issues, deployed on kind" (user, 2026-11-06).
- Decision: Replanned for spike 12. Story 3 closes as done for the pipeline it built: masking, the exclusion list, versioning, the checksum, Release publishing and the timed load. New story 14, "Derive Jira outcome and kind in core", then new story 13, "Ingest publishes the Jira snapshot (schema v2)", come before story 5. Story 5 now waits on 12, 13 and 14, and story 10 also waits on 13 and 14. Spike 12 closes as done. Stories 1, 2 and 4 stay done and are not rewritten (user, 2026-11-06).
- Decision: The Jira outcome's `/v1` source is `label` for duplicate, `closing_comment` for answered and `null` otherwise, so story 14 changes neither the `/v1` contract nor the migration (user, 2026-11-06).
- Decision: Story 4's GitHub outcome rules stay in core, covered by its own unit tests; the refactor sweep may retire them (user, 2026-11-06).
- Decision: Story 13's ingest runs locally and is person-run: a person restores the dataset dump and runs the committed ingest, and the checksum, timed load and Release publish run from that machine. The 5.8 GB dump (about 60 GB restored) does not fit a GitHub-hosted runner, and the data is frozen at January 2022 (user, 2026-11-06).
- Decision: `/v1` does not carry the readable Jira key for now; each issue's `url` already shows it. Revisit when epic-mcp-server is refined (user, 2026-11-06).
- Note: The Jira switch invalidates part of the architecture spine: AD-6's snapshot fields (`state_reason`, `author_association`, timeline events) the Identifiers convention (a GitHub issue number in `kubernetes/kubernetes`), AD-10's `gen_ai.data_source.id=ticketscope-k8s-issues`, and the Provenance convention ("Public GitHub issues only"). `bmad-architecture` amends them before story 13's plan, as entry 13 records; the spine is not edited here.
- Decision: Epic closed as done. The closure check verified every Done when line against implementation evidence: trace at `6400e5a` has R1–R7 FULL, and the integrated check passed in CI (run 42414691589, PR #20). The retrospective verdict is accepted-with-open-items. Six superseded GitHub-era criteria (stories 3, 4 and 14) are waived under W-001 (`_bmad-output/test-artifacts/gate-waivers.md`), with their remediation and the search latency threshold carried to epic-eval-gate (user, 2026-11-08).
