# Restore drill (story 5.7, R9)

Result: OK

The source cluster's backup was restored into a new cluster (`ticketscope-restore`) through the
Barman Cloud Plugin, and the two were compared. Identifying values are masked.

## Timings

| stage | seconds |
| --- | ---: |
| backup | 13 |
| restore | 75 |
| compare | 3 |

## Comparison

- Pinned Release's issue count: 32153
- Source: {"corpus_meta": {"embedding_model_id": "BAAI/bge-small-en-v1.5", "loaded_at": "2026-11-23T17:06:19.689576+00:00", "preprocessing_version": "pre1.kind2-t3.outcome3.emb1", "singleton": true, "snapshot_version": "2026.11.1"}, "digest": "309070c419ac4f9757b0aad73b385383", "issues": 32153}
- Restored: {"corpus_meta": {"embedding_model_id": "BAAI/bge-small-en-v1.5", "loaded_at": "2026-11-23T17:06:19.689576+00:00", "preprocessing_version": "pre1.kind2-t3.outcome3.emb1", "singleton": true, "snapshot_version": "2026.11.1"}, "digest": "309070c419ac4f9757b0aad73b385383", "issues": 32153}

Differences:

- none

## Commands and output

```text
stage: backup
+ scripts/eks-backup.sh --kubeconfig /tmp/ticketscope-eks.kubeconfig --incarnation inc-45219791550-1 --name-suffix drill-1795454466
backup.postgresql.cnpg.io/ticketscope-db-ondemand-inc-45219791550-1-drill-1795454466 created
backup ticketscope-db-ondemand-inc-45219791550-1-drill-1795454466: completed
pluginMetadata: {"clusterUID":"22c0dc90-f0c8-4bb3-8636-4f5cd642fc78","displayName":"BarmanCloudInstance","name":"barman-cloud.cloudnative-pg.io","pluginName":"barman-cloud.cloudnative-pg.io","timeline":"1","version":"0.16.0"}
beginWal: 000000010000000000000017
endWal: 000000010000000000000018
objects: backups/inc-45219791550-1/
stage: restore
recovering from serverName inc-45219791550-1 through ObjectStore ticketscope-backup
cluster.postgresql.cnpg.io/ticketscope-restore created
cluster.postgresql.cnpg.io/ticketscope-restore condition met
stage: compare
+ kubectl -n ticketscope exec ticketscope-db-1 -c postgres -- psql -d app -tAc select json_build_object('corpus_meta', (select to_jsonb(c) from corpus_meta c), 'issues', (select count(*) from issue), 'digest', (select md5(string_agg(number::text, ',' order by number)) from issue))
+ kubectl -n ticketscope exec ticketscope-restore-1 -c postgres -- psql -d app -tAc select json_build_object('corpus_meta', (select to_jsonb(c) from corpus_meta c), 'issues', (select count(*) from issue), 'digest', (select md5(string_agg(number::text, ',' order by number)) from issue))
the pinned Release publishes 32153 issues
+ uv run python scripts/restore_drill.py compare /tmp/drill/source.json /tmp/drill/restored.json --expected 32153
restore drill: OK
```
