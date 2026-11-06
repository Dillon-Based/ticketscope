---
id: 12
type: spike
title: "Choose the Jira corpus"
parent: epic-search-baseline
covers: [R1]
after: []
assignee: ""
refined: true
hitl: true
risk: high
---

# Choose the Jira corpus

## Description

Can the Public Jira Dataset replace Kubernetes issues as the corpus? If it can, which subset of about 20,000–50,000 issues should we use?

Why this is open:

- **Too little ground truth.** The first real Kubernetes snapshot (`snapshot.yml` run 42261907819: 5,907 closed issues from 2023-11-07 to 2026-11-06) has only 21 duplicates, and none of them names the issue it duplicates. epic-eval-gate derives its labelled pairs from duplicates, so it would have almost nothing to score. That is the brief's open question "Ground truth volume".
- **Weak corpus fit.** Kubernetes issues are developer bug reports, not support requests (the brief's open question "Corpus fit").
- **Not a deciding factor:** the same run recorded no `fixed` outcomes, because the ingest token's API responses left out PR cross-references. Switching corpus makes that moot.

The candidate is The Public Jira Dataset, v7 (Montgomery, Lüders, Maalej, MSR 2022):

- Zenodo record 15719919, DOI 10.5281/zenodo.15719919, licensed CC BY 4.0. Reuse requires crediting the creators and citing the paper.
- One 5.8 GB zip holding a MongoDB dump: 16 public Jira instances, 1,822 projects, 2.7 million issues, 9 million comments, 1 million issue links.
- Reporters, assignees, creators and the authors of comments and changes are replaced with UUID4 masks. Issue and comment text is not anonymised.

Who waits on the answer:

- **Story 5** waits on this spike: it pins the snapshot, sets the kind threshold from real data and writes the golden-query file.
- **epic-eval-gate** waits on the decision, because its pairs come from the corpus.
- **If the decision is to switch**, the data lane is replanned: stories 1, 2, 3 and 4, the snapshot schema, story 5, and epic-eval-gate.

**Person's steps (hitl):** a person downloads the dataset (in progress on 2026-11-06), reads the sampled issues, and decides.

## Approach

1. **Restore.** Restore the dump into a throwaway MongoDB container on the author's machine. Spike scripts stay out of the product code: a spike leaves evidence, not product code.
2. **Measure each instance**, then each project for the best few. One script writes a CSV for each scope:
   1. **Ground truth.** Count issues resolved `Duplicate` that have a "duplicates" link to an issue in the same subset. Split them by kind, with the kind rule extended to Jira `{code}` and `{noformat}` blocks.
   2. **Outcome coverage.** Map `resolution` onto duplicate, fixed, not_planned, stale, answered and unknown, and report the share left `unknown`. Define "answered" without `author_association`. For example: a Question or Support issue resolved after a comment by someone other than the reporter.
   3. **Corpus fit.** Report the issue-type mix (Bug against Question or Support) and who reports the issues. Read 20 sampled issues from each leading candidate, including Mojang if the dump holds it.
   4. **Text hygiene.** Wiki-markup noise; mention syntax (`[~accountid:…]`, `[~user]`); emails, tokens and keys left in the text; NUL characters.
   5. **Size and load.** The proposed subset's issue count, and a timed load through story 3's timed-load script against the 600 s budget. Note that the data ends at its 2022 collection date.
   6. **Terms.** CC BY 4.0 covers the dataset. Check whether any instance's own site terms limit republishing its issue text, and draft the attribution line: the dataset citation plus a link to each source issue.
3. **Decide.** Apply the decision rule below. The author signs off.

**Time box:** about one day once the download finishes.

**Decision rule:** switch if one subset meets all four:

- its licence and terms allow a public Release asset;
- it has at least about 1,000 in-subset duplicate pairs, with at least about 200 of each kind;
- under 20% of its outcomes are `unknown`;
- it fits the 600 s load budget.

A subset closer to support tickets breaks ties between candidates; it is not a requirement (see Notes).

## Acceptance Criteria

1. **The instances and leading projects are compared on the decision rule**
   Verify: a findings note beside this ticket holds a table per instance and per leading project. Each table gives the issue count, in-subset duplicate pairs by kind, the outcome shares under the proposed mapping, the issue-type mix, and the text-hygiene counts. The CSVs it was built from sit with it.
2. **The recommended subset is shown to work**
   Verify: the findings note names the subset and its expected duplicate-pair count by kind. It shows the subset's measured load time through story 3's timed-load script within 600 s, and 20 sampled issues per leading candidate with the author's judgement of each.
3. **The answer and its consequences are recorded where the waiting tickets read them**
   Verify: the epic's Notes holds a dated Decision line: switch, stay, or switch with named conditions. On switch, the line names:

- the subset;
- the `resolution`-to-outcome mapping and the "answered" rule;
- the kind rule extended to Jira `{code}` and `{noformat}` blocks, since a kind-rule change needs a reload and a baseline update (epic Constraints, Kind rule);
- the attribution line.

It also amends the epic's Corpus scope (the 20,000 cap and the source) and Corpus terms for the new source, and says the data lane and epic-eval-gate are to be replanned.
4. **The author accepts it**
   Verify: the Decision line is attributed to the author (user) and dated.

## References

- parent — _bmad-output/initiative-ticketscope/tickets/epic-search-baseline/epic-search-baseline.md, sections Requirements (R1), Constraints (Corpus scope, Corpus terms, Outcome precedence, Outcome terms, Kind rule), Notes
- brief — _bmad-output/initiative-ticketscope/brief-ticketscope/brief-ticketscope.md, open questions (Ground truth volume, Corpus fit)
- dataset — https://zenodo.org/records/15719919, The Public Jira Dataset v7 (CC BY 4.0)
- paper — https://arxiv.org/abs/2201.08368, An Alternative Issue Tracking Dataset of Public Jira Repositories (MSR 2022)
- evidence — https://github.com/Dillon-Based/ticketscope/actions/runs/42261907819, the first Kubernetes snapshot (its `snapshot` artifact and ingest log)

## Notes

- Decision: The thresholds above (about 1,000 pairs, at least about 200 of each kind, under 20% unknown, within the load budget) are the switch rule (user, 2026-11-06).
- Decision: A subset closer to support tickets breaks ties between candidates; it is not a hard requirement (user, 2026-11-06).
- Paths for the builder: the dataset zip is downloading to `~/Downloads`; spike scripts stay out of `src/`; the timed load is `scripts/time-load.sh` from story 3.
- Open question: Which of the 16 instances does the dump hold? The Zenodo page does not name them.
- Check beyond the criteria (high risk): before deciding, sample 10 duplicate pairs from the recommended subset and confirm on the source Jira (or in the dump's change history) that each pair really is a duplicate, so the eval's ground truth is trusted.
