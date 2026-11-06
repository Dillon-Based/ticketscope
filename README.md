# ticketscope

Similar-issue search over closed Kubernetes issues: a personal project, deployed and operated on Kubernetes.

## Corpus attribution and takedown

The corpus snapshots published as `snapshot-YYYY.MM.N` Releases of this repository hold the text of closed issues from [`kubernetes/kubernetes`](https://github.com/kubernetes/kubernetes). That text belongs to its authors. Every record links to its issue on github.com.

Before a snapshot is written, the ingest job changes the text as follows:

- It stores no author login. Comments keep only the author's association with the repository, such as `MEMBER`.
- It replaces each `@handle` mention with `@[user]`. Team mentions such as `@kubernetes/sig-node-bugs` stay.
- It replaces email addresses with `[email masked]`.
- It replaces token- and key-shaped secrets, such as GitHub tokens, cloud access keys and private-key blocks, with `[secret masked]`.

A published snapshot is never overwritten: each run publishes the next version.

**Takedown.** To have an issue removed, open an issue in this repository with the `kubernetes/kubernetes` issue number. A maintainer then:

1. adds the number to [`snapshot/exclusions.txt`](snapshot/exclusions.txt), so ingest never fetches or writes it again;
2. dispatches `snapshot.yml`, which publishes a new version without the issue;
3. deletes the assets of the earlier Releases that hold the issue. This is the one exception to "never overwritten", and a person does it by hand.
