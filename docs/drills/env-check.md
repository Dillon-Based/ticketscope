# Integrated check on EKS (story 5.11, R1, R3, R4, R5)

Result: green on 2026-11-24 (env-up 908 s, apply start to smoke pass; leftover check clean). The R5 billing figure is still to fill.

`.github/workflows/env-check.yml` is the epic's integrated check: it dispatches `env-up`, waits for
its smoke check, dispatches `env-down` (ordered teardown and its leftover check), then runs the
leftover check once more, all on one SHA. It is green only when the three passed, and `env-up`'s
recorded time, apply start to smoke pass, is under 30 minutes.

Dispatch it after the workflow is on `main`, from a ref the `eks` environment admits, with one
environment at a time and in the lighter month (epic Notes):

```
gh workflow run env-check.yml --ref main
scripts/run-summary.sh <run id>
```

Fill the table from the run (`scripts/run-summary.sh` for each of the three runs). Account ids stay
masked; write no person identifier.

## Runs

| step | run | result |
| --- | --- | --- |
| env-check | https://github.com/Dillon-Based/ticketscope/actions/runs/45486216065 | success (up, down, leftover and verdict jobs) |
| env-up (apply start to smoke pass, target under 1800 s) | https://github.com/Dillon-Based/ticketscope/actions/runs/45486237974 | 908 s (terraform apply 648, platform 145, ticketscope 86, smoke 5) |
| env-down (with its leftover check) | https://github.com/Dillon-Based/ticketscope/actions/runs/45490855745 | success; teardown 716 s; leftover check clean |
| leftover check | job `leftover` in https://github.com/Dillon-Based/ticketscope/actions/runs/45486216065 | success: "clean, nothing tagged environment=eks remains" (two stale volume entries confirmed gone) |

## Evidence the epic closes on

- Restore drill: `docs/drills/restore-drill.md`.
- Failure drill: `docs/drills/failure-drill.md` is the "not yet run" skeleton. R10 (a node loss survived, a standby promoted) is unproven, and plugin bug #828 is still an open unknown. The epic closes with this as an accepted exception (user, 2026-11-24); `scripts/failure-drill.sh` runs in a later window.
- Recreate drill: `docs/drills/recreate-drill.md`.
- Billing, for the month that holds these runs, bootstrap layer included, under $10 (R5):
  - raw, AWS only, from Cost Explorer (month-to-date if the month has not closed): _figure_
  - amortised: raw plus the domain's annual fee from the Cloudflare invoice divided by 12: _figure_
