---
status: done
---

expand mode (explicit), story 5.11. Added `tests/unit/test_dispatch_and_watch_script.py` (6 tests): runs
`scripts/dispatch-and-watch.sh` against stub gh/date/sleep, covering GH_REPO refusal, run-id output and
$GITHUB_OUTPUT hand-off, no-run-found failure, and the WATCH_JOB wait (success while the run continues,
failure, run ended without the job). All 16 tests in the two 5.11 files pass; ruff and pyright clean.
No test defects to heal, no product defects found. No production code or ticket status changed.
Note: the script uses GNU `date -d`, so it only works on Linux runners (stubbed in tests); fine for CI.
