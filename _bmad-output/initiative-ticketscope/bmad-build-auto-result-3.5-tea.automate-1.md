---
status: done
---

Expand mode, autonomous (mode was explicit). Added `tests/unit/test_eval_embedder_expanded.py`: 7 pass, 1 strict xfail pinning a product defect. Full unit suite passes (1065 passed, 1 xfailed). Summary: `_bmad-output/test-artifacts/automate/automation-summary-story-ticketscope--e3-s5.md`.

Product defect, unfixed: in `scripts/kind-up.sh`, `EMBEDDINGS_COMPUTE=1` resets the Helm timeout to 50m after eval set 60m, when `EVAL_ENABLED=1` is also set.

Ticket status not changed.
