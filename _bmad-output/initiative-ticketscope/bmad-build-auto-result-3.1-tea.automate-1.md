---
status: blocked
---

Expand mode, ticket `3.1` ("Tracer: dense search answers through /v1 on kind").

Ticket 3.1 resolves, but nothing has been built for it. Its plan is `ready-for-dev` and was halted after planning. The only working-tree change is that untracked plan file.

On branch `story-3-1`:
- `git diff main` is empty.
- There is no `Embedder` port, no `DenseRetriever`, no `migrations/0002_issue_embedding.sql` and no `src/ticketscope/adapters/embedder.py`.
- `grep` for "dense" and "Embedder" in `src/` finds only the existing `ModeName` literal in `contract/search.py`.

I wrote no tests, because tests for the planned behaviour would fail against code that does not exist, and I am not allowed to change production code. I changed nothing and did not touch the ticket's status.

Next step: run the build for 3.1, then re-run `bmad-tea-automate` in expand mode.
