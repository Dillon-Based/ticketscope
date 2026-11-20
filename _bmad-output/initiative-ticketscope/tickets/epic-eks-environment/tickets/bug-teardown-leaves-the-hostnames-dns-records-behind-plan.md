---
title: "env-down ends red and leaves the hostname's A and AAAA records pointing at a dead ALB"
type: 'bugfix'
ticket: '12'
created: '2026-11-19'
status: done
baseline_revision: '08da3a4304f4a098a61bf3d277b43e653035a822'
route: 'full'
route_source: 'auto'
risk: 'medium'
review: 'quick'
review_source: 'pinned'
lenses_ran: ['quick']
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/epic-eks-environment.md'
  - '{project-root}/_bmad-output/initiative-ticketscope/tickets/epic-eks-environment/tickets/story-env-down-tears-down-in-order-finds-nothing-left-and-expires-plan.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After an ordered teardown the hostname's A and AAAA alias records stay in the bootstrap zone, so `env-down` exits 3 and the next `env-up` fails its DNS stage until a person deletes them by hand (R2, R3, R4). Criteria were approved as written in the bug file (user, 2026-11-19).

**Approach:** `eks-teardown.sh` deletes the hostname's A and AAAA records itself after `terraform destroy`, and the deploy role gains a Route 53 change right limited to that zone, the DELETE action, types A and AAAA and the hostname. A person re-applies bootstrap. Decision (user, 2026-11-19): the cause (external-dns writing no TXT ownership records) stays an open deferred item, not fixed here; this narrows 5.4's "deploy role denied on the hosted zone" to "denied except those two records".

## Boundaries & Constraints

**Always:** Only A and AAAA records named exactly the fixed hostname may be changed; the zone, its NS and SOA records and the certificate validation records are never selected. A zone that cannot be read, or records still present after the step, still fail the job (exit 3 semantics stay). The agent runs no AWS write command outside the workflows; kind behaviour and the teardown order of AD-24 are unchanged.

**Never:** No `terraform destroy` of `bootstrap`, no wildcard record or zone-wide permission, no hand-written `eval/baseline.json` or README table.

</frozen-after-approval>

## Code Map

- `scripts/eks-teardown.sh:230-256, 299-307` -- `dns_check` lists A/AAAA for `$DNS_NAME` in `$ZONE_ID`, prints the remedy, `dns-records` stage then exit 3; the place the delete would go.
- `tests/unit/test_eks_teardown.py:279-305` -- stub `aws`, `DNS_STALE`/`DNS_ERROR`; asserts the remedy is printed and no `change-resource-record-sets` runs (changes under A).
- `.github/workflows/env-down.yml:140-200` -- discovers zone and hostname, calls the script, treats exit 3 as destroyed-but-red.
- `infra/bootstrap/policies/deploy-permissions.json.tftpl` -- the deploy role has `route53:Get*`/`List*` only (`ReadOnlyDiscovery`); `tests/unit/test_infra_bootstrap.py` tests the rendered policy.
- `deploy/charts/platform/values-eks.yaml:41-55` -- external-dns `policy: sync`, `registry: txt`, chart 1.23.0 (`Chart.yaml`).
- `infra/env/irsa.tf:21-35` -- external-dns IRSA role scoped to the zone; do not change.
- `docs/runbooks/env-down.md:75-100` -- "Stale DNS records" section to rewrite.
- `deferred-work.md` -- the two external-dns entries to close with a resolution once fixed.
- Do not touch: `scripts/leftover-check.*`, the kind path, `infra/env` outputs.

## Tasks & Acceptance

**Execution:**
- [ ] `tests/unit/test_eks_teardown.py` -- red first: stale records are deleted by a change batch naming only the hostname's A and AAAA records; none selected when only NS, SOA or other names exist; a failed delete, an unreadable zone, or records still present after the delete exit 3; clean zone makes no change call
- [ ] `scripts/eks-teardown.sh` -- delete the records after `terraform destroy`, re-check, keep exit 3 on any failure
- [ ] `infra/bootstrap/policies/deploy-permissions.json.tftpl`, `tests/unit/test_infra_bootstrap.py` -- scoped Route 53 change right with conditions; test that the rendered policy names the zone, DELETE, A/AAAA and the hostname, and nothing broader
- [ ] `docs/runbooks/env-down.md`, `deferred-work.md` -- runbook and the two entries' resolution

**Acceptance Criteria:**
- Given an environment brought up and torn down, when `env-down` finishes, then the zone holds no A or AAAA record for the hostname and the job is green (bug AC 1; live check after merge and bootstrap re-apply).
- Given that teardown, when `env-up` runs again, then its DNS stage passes with no hand step (AC 2; live check).
- Given the filter, when the test suite runs, then the zone, NS, SOA and certificate records are never selected (AC 3).
- Given an unreadable zone, when teardown runs, then it still fails (AC 4).
- Given `scripts/check.sh`, when run, then it passes.

## Implementation Notes

- `eks-teardown.sh` `dns_clean_up` replaces `dns_check`: lists, deletes in one DELETE-only batch, lists again; exit 3 on an unreadable zone, a failed delete or records still present. The new tests fail on the old script (checked) and pass on the new.
- Added beyond the plan: `scripts/bootstrap-drift.sh` and `bootstrap_drift.py` take `--zone-id` and `--hostname`, because the template gained two variables and the drift check renders it.
- Not run live: the IAM condition keys, the deploy role's delete and the next `env-up`. A person re-applies bootstrap first (`scripts/bootstrap-drift.sh`).

## Plan Change Log

## Review Triage Log

- low, patch: `env-down.yml` header and summary still described a read-only DNS check. Fixed.
- low, patch: the runbook did not say the bootstrap re-apply must precede the first `env-down`. Fixed.
- false: "5.4's AC-3 now has no tagged test". Five `e5-s4--AC-3` tests remain in `test_eks_teardown.py`; `e5-s12` follows the key convention.
- low, rejected: the batch comes from a second listing, so records vanishing between the calls give an empty change batch. Unlikely, and a fix adds a guard branch.
- maybe-false, defer (medium if true): AWS may compare `ChangeResourceRecordSetsNormalizedRecordNames` with a trailing dot, which would deny the delete. A live `env-down` after the re-apply settles it. Entry added to `deferred-work.md`.
- low, rejected: the drift check's `ticketscope.*` zone discovery could differ from `var.hostname`. It is the same discovery `env-up` and `env-down` use, and a mismatch exits 2, loudly.

## Verification

**Commands:**
- `scripts/check.sh` -- expected: `check: all passed`
- `uv run pytest tests/unit/test_eks_teardown.py tests/unit/test_infra_bootstrap.py` -- expected: pass

**Manual checks (after merge and a person's bootstrap re-apply; run `scripts/bootstrap-drift.sh` first):**
- The agent dispatches `env-up` (4 h expiry) then `env-down` and reads the run with `scripts/run-summary.sh`: green, `dns-records` stage clean; read the zone under `ticketscope-readonly`: NS, SOA and the certificate CNAME only.
- Dispatch `env-up` again: DNS stage passes with no hand step.

Live record (2026-11-20, after PR #82):

- Run 44647668634 (`env-down`, 2026-11-20) was denied on `ChangeResourceRecordSets` and exited 3. The live deploy role had no `DeleteHostnameAddressRecords` statement: the first "matches the template" drift result ran before the new template reached the checkout. After the bootstrap re-apply, `iam simulate-principal-policy` allowed the delete for the bare hostname and denied the trailing-dot form and any other name.
- Run 44774843987 (`env-down`, no environment up) was green in 5 seconds: the A and AAAA records were deleted, the zone then held only NS, SOA and the certificate CNAME, and the leftover check was clean. Criterion 1 and 3 are met live, and the IAM condition key's trailing-dot question is settled (bare name).
- Criterion 2 (the next `env-up` passes its DNS stage with no hand step) is observed on the next `env-up`, not run separately (user, 2026-11-20).
