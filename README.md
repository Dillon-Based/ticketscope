# ticketscope

Similar-issue search over resolved Mojang bug-tracker issues: a personal project, deployed and operated on Kubernetes.

## Corpus attribution and takedown

Issue text from the Mojang bug tracker (bugs.mojang.com), as collected in The Public Jira Dataset v7 by Lloyd Montgomery, Clara Lüders and Walid Maalej (Zenodo, doi:10.5281/zenodo.15719919, CC BY 4.0), described in "An Alternative Issue Tracking Dataset of Public Jira Repositories", MSR 2022, pp. 73–77. The text belongs to its authors; each record links to its source issue. Data collected in January 2022; changes to source issues after that date are not reflected.

The corpus snapshots published as `snapshot-YYYY.MM.N` Releases of this repository hold the resolved issues of the Mojang projects MCL, REALMS and MCD, plus the unresolved issues their duplicates point to. Every record links to its issue at `https://bugs.mojang.com/browse/<key>`.

Before a snapshot is written, the ingest job changes the data as follows:

- It stores no reporter, assignee, creator or comment-author id, not even the dataset's masked ones. A comment keeps only whether the reporter wrote it.
- It replaces each `[~user]` or `[~accountid:…]` mention with `[~user]`, and each `@handle` mention with `@[user]`.
- It replaces email addresses with `[email masked]`.
- It replaces token- and key-shaped secrets, such as GitHub tokens, cloud access keys and private-key blocks, with `[secret masked]`.

A published snapshot is never overwritten: each run publishes the next version. A person publishes it with `scripts/publish-snapshot.sh` from a clean, up-to-date checkout of `main`, against the dump restored into a local MongoDB; no workflow runs ingest or publishes.

**Takedown.** To have an issue removed, open an issue in this repository with the issue key, such as `MCL-123`. A maintainer then:

1. adds the key to [`snapshot/exclusions.txt`](snapshot/exclusions.txt), so ingest never writes it again;
2. runs `scripts/publish-snapshot.sh`, which publishes a new version without the issue;
3. deletes the assets of the earlier Releases that hold the issue. This is the one exception to "never overwritten", and a person does it by hand.
