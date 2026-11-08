---
runScope: 'story'
runKey: 'story-ticketscope--eval-gate-s2'
testMode: 'expand'
testEntry: 'bmad-tea-automate'
workflowStatus: 'completed'
lastStep: 'step-04-validate-and-summarize'
ticketRef: '2 @ _bmad-output/initiative-ticketscope/tickets/epic-eval-gate'
---

# Automation summary: ticket 2.2 (cluster scoring, split by ticket kind)

Mode: expand (explicit). Added `tests/unit/test_eval_score_expanded.py` (15 tests): cutoff boundaries
(ranks 1, 2, 5, 6, 10, 11) for Recall@1/5/10 and MRR@10, averaging across queries and the kind split,
any-member hit with the query excluded, skipped modes sorted, p95 ceiling boundaries, derived `relevant`
ordering, cluster ordering, pairs-file round trip.

Run: 2 test defects (invalid `direction` enum value; wrong p95 expectation) healed in one iteration.
Full suite: 837 passed, 39 kind-marked deselected. ruff and pyright clean on the new file.
Product defects: none. Production code and ticket status untouched.
