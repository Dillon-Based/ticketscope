# Integrated check on EKS (story 5.11, R1, R3, R4, R5)

Result: not run yet

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
| env-check | _run URL_ | _conclusion_ |
| env-up (apply start to smoke pass, target under 1800 s) | _run URL_ | _seconds_ |
| env-down (with its leftover check) | _run URL_ | _conclusion_ |
| leftover check | _job in the env-check run_ | _conclusion_ |

## Evidence the epic closes on

- Restore drill: `docs/drills/restore-drill.md`.
- Failure drill: `docs/drills/failure-drill.md` (a person runs `scripts/failure-drill.sh` in the December window).
- Recreate drill: `docs/drills/recreate-drill.md`.
- Billing, for the month that holds these runs, bootstrap layer included, under $10 (R5):
  - raw, AWS only, from Cost Explorer (month-to-date if the month has not closed): _figure_
  - amortised: raw plus the domain's annual fee from the Cloudflare invoice divided by 12: _figure_
