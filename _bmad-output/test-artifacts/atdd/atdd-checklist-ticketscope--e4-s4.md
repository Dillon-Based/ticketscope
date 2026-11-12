---
runScope: 'story'
runKey: 'story-ticketscope--e4-s4'
testMode: 'red'
testEntry: 'bmad-tea-automate'
workflowStatus: 'completed'
storyId: '4.4'
storyKey: 'ticketscope--e4-s4'
ticketRef: '4 @ _bmad-output/initiative-ticketscope/tickets/epic-mcp-server'
lastStep: 'step-05-validate-and-complete'
lastSaved: '2026-11-11'
generatedTestFiles: ['tests/key_oracle.py', 'tests/unit/test_key_oracle_pinned.py']
inputDocuments: ['_bmad-output/initiative-ticketscope/tickets/epic-mcp-server/test-design-epic-4.md', 'snapshot/fixture.jsonl', 'tests/unit/test_eval_oracle_pinned.py']
acceptanceCriteria:
  - { id: 'AC-1', idSource: 'generated', text: 'The hostile keys and url-derived keys behave as the independent oracle says (R2, R3); see ticket verify line' }
---

# ATDD checklist: story 4.4 (red, scoped to the Independent Oracles protocol)

Scope: this session commits only what `test-design-epic-4.md` ("Independent Oracles") and the
plan checkpoint require before 4.4's build: the key oracle table, the hostile-key cases and a
pin test. It does not write the failing acceptance tests; the build writes those against this oracle.

## Files

- `tests/key_oracle.py`: `KEY_PATTERN` (C-4), `URL_TO_KEY` (six rows), `HOSTILE_KEYS` (ten inputs), `DOT_SEGMENT_KEYS`, `FORBIDDEN_NUMBER`.
- `tests/unit/test_key_oracle_pinned.py`: pins the oracle's bytes (length and SHA-256, prefix-growth allowed) and checks it against the snapshot v2 `key` field and the key pattern. 2 tests, passing, no production code needed.

## Handoff to the build

- Import the oracle from `tests.key_oracle`; do not edit it. A change to it in 4.4's diff is a review finding.
- Row (A) scenarios 1, 6, 7, 8 and 10 use `URL_TO_KEY`, `HOSTILE_KEYS`, `DOT_SEGMENT_KEYS` and `FORBIDDEN_NUMBER`. Scenario 2 compares the url-derived key with the snapshot `key` for each `snapshot/fixture.jsonl` issue.
- `..%2F6629` is in `HOSTILE_KEYS` but not `DOT_SEGMENT_KEYS`: percent-encoded once it stays one segment, and a second encoding must not decode back to a dot segment.
- Not covered here: kind client test, Postgres integration, parity-script option.
