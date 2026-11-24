# Recreate drill (story 5.9, R11, R2)

Result: OK

An environment was brought up, backed up on its way down (`backup_first`), destroyed, and a second
environment was brought up with `restore_from` naming the first one's backup folder. The second
archives under its own `serverName`; the two were compared. Identifying values are masked.

## Runs

| step | run | result |
| --- | --- | --- |
| env-up (first incarnation inc-45260100245-1, expiry_hours=2) | 45260100245 | env job success: smoke passed, on-demand backup completed |
| env-down with backup_first (pre-down backup, then teardown) | 45266017998 | backup and destroy succeeded (55 resources); leftover check failed on a deleted subnet (see Notes) |
| env-up with restore_from=inc-45260100245-1 (second incarnation inc-45268386170-1, expiry_hours=2) | 45268386170 | incarnation-check OK; env job success: smoke passed, on-demand backup completed |
| env-down (second incarnation) | 45272176321 | destroy succeeded; leftover check failed on deleted subnets (see Notes) |

## Corpus facts

- first: {"certificate": "A6:AC:3E:12:37:CB:9B:CC:3C:6E:45:F4:CB:B1:C1:37:0D:89:ED:E4:04:6A:A6:9E:2D:67:FA:A6:71:E4:C2:7C", "corpus_meta": {"embedding_model_id": "BAAI/bge-small-en-v1.5", "loaded_at": "2026-11-23T20:48:47.339714+00:00", "preprocessing_version": "pre1.kind2-t3.outcome3.emb1", "singleton": true, "snapshot_version": "2026.11.1"}, "digest": "309070c419ac4f9757b0aad73b385383", "hostname": "ticketscope.heffernan.dev", "issues": 32153}
- second: {"certificate": "A6:AC:3E:12:37:CB:9B:CC:3C:6E:45:F4:CB:B1:C1:37:0D:89:ED:E4:04:6A:A6:9E:2D:67:FA:A6:71:E4:C2:7C", "corpus_meta": {"embedding_model_id": "BAAI/bge-small-en-v1.5", "loaded_at": "2026-11-23T20:48:47.339714+00:00", "preprocessing_version": "pre1.kind2-t3.outcome3.emb1", "singleton": true, "snapshot_version": "2026.11.1"}, "digest": "309070c419ac4f9757b0aad73b385383", "hostname": "ticketscope.heffernan.dev", "issues": 32153}

Differences (equal `loaded_at` means the second did not load again):

- none

## The first incarnation's folder, listed before and after the second environment

Differences in key, size and ETag:

- none

## Notes

- R2: both environments served ticketscope.heffernan.dev under the same bootstrap certificate (equal SHA-256 fingerprints, read over HTTPS in each run).
- R11: the second environment archived under its own folder backups/inc-45268386170-1/ (11 objects: one base backup, WAL on timeline 2, continuing after the first's last segment). Its on-demand backup completed. No 'Expected empty archive' failure occurred and skipEmptyWalArchiveCheck was never set.
- Equal loaded_at in both facts: the second environment restored the corpus from the first's backup and did not load it again. No load Job is rendered when restore_from is set.
- The first incarnation's folder backups/inc-45260100245-1/ held 29 objects (two base backups) after its teardown and the same 29 (key, size, ETag) after the second environment ran and was backed up.
- The control run without the serverName change (plugin issue 767) was not run: it needs a third environment, and November's 25 environment-hour budget already holds about 10 dispatches plus these two (about 1.5 hours each with the builds outside the clock). Whether the same-name recreate fails on current plugin versions is therefore unknown.
- Both env-down runs ended in a failed leftover check although the destroy completed. The check listed deleted EC2 subnets as 'unconfirmed' (volumes are confirmed gone through describe-volumes; subnets have no confirmation path), 40 minutes after the first subnet was destroyed. A read-only describe-subnets then returned InvalidSubnetID.NotFound for it, and no VPC, cluster or tagged volume remained. Deferred to deferred-work.md.
- The step summary cannot be read back through the API, so the corpus facts are also printed to the run log as 'corpus-facts:' lines (env-up's facts step, and env-down's backup_first step for the first incarnation, taken before teardown).

## Commands and output

```text
+ gh workflow run env-up.yml --ref worktree-story-5-9 -f sha=9bcd79e059c32890c258ea03e78fd79032c29e94 -f expiry_hours=2
  run 45260100245: plan, build, images, env success
+ gh workflow run env-down.yml --ref worktree-story-5-9 -f backup_first=true
  run 45266017998: last backup taken, teardown complete (Destroy complete! Resources: 55 destroyed.), leftover check failed on subnet tagging lag
corpus-facts (incarnation inc-45260100245-1, printed before its teardown):
{"certificate":"A6:AC:3E:12:37:CB:9B:CC:3C:6E:45:F4:CB:B1:C1:37:0D:89:ED:E4:04:6A:A6:9E:2D:67:FA:A6:71:E4:C2:7C","corpus_meta":{"embedding_model_id":"BAAI/bge-small-en-v1.5","loaded_at":"2026-11-23T20:48:47.339714+00:00","preprocessing_version":"pre1.kind2-t3.outcome3.emb1","singleton":true,"snapshot_version":"2026.11.1"},"digest":"309070c419ac4f9757b0aad73b385383","hostname":"ticketscope.heffernan.dev","incarnation":"inc-45260100245-1","issues":32153}
+ aws s3api list-objects-v2 --prefix backups/inc-45260100245-1/   (read-only profile; 29 objects, saved as BEFORE)
+ gh workflow run env-up.yml --ref worktree-story-5-9 -f sha=3df0d0e306e1e151ffdffef4e4b4109f436013f3 -f expiry_hours=2 -f restore_from=inc-45260100245-1
  run 45268386170: plan, build, images, env success
incarnation-check: OK, inc-45268386170-1 restores from inc-45260100245-1
backup ticketscope-db-ondemand-inc-45268386170-1: completed
corpus-facts (incarnation inc-45268386170-1):
{"certificate":"A6:AC:3E:12:37:CB:9B:CC:3C:6E:45:F4:CB:B1:C1:37:0D:89:ED:E4:04:6A:A6:9E:2D:67:FA:A6:71:E4:C2:7C","corpus_meta":{"embedding_model_id":"BAAI/bge-small-en-v1.5","loaded_at":"2026-11-23T20:48:47.339714+00:00","preprocessing_version":"pre1.kind2-t3.outcome3.emb1","singleton":true,"snapshot_version":"2026.11.1"},"digest":"309070c419ac4f9757b0aad73b385383","hostname":"ticketscope.heffernan.dev","issues":32153}
+ aws s3api list-objects-v2 --prefix backups/inc-45268386170-1/   (11 objects: base/<stamp>/backup.info, data.tar, wals/ timeline 2)
+ aws s3api list-objects-v2 --prefix backups/inc-45260100245-1/   (read-only profile; 29 objects, saved as AFTER)
+ gh workflow run env-down.yml --ref worktree-story-5-9
  run 45272176321: teardown complete, leftover check failed on subnet tagging lag
+ python3 scripts/recreate_drill.py compare first.facts.json second.facts.json
recreate drill: compare OK
+ python3 scripts/recreate_drill.py archive-diff first-before.json first-after.json
recreate drill: archive-diff OK
```
