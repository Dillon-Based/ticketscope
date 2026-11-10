---
status: done
---
Expand mode (explicit), story 3.8. Ticket is itself a kind-cluster integrated check, so there was no production code to cover.

- Added `tests/unit/test_hybrid_check_38_expanded.py` with 5 cluster-free tests. All 5 pass.
- Ran the two cluster-free checks in `test_hybrid_check.py` (`-m kind`). Both pass.
- The 2 cluster-dependent tests (chart default served, readiness mismatch) were not run: no kind cluster in this session.
- No heals and no product defects.
