# Restore drill (story 5.7, R9)

Result: not yet run.

The drill restores a backup taken on EKS into a new one-instance cluster (`ticketscope-restore`)
through the Barman Cloud Plugin, and compares it with the source: the `corpus_meta` row, the issue
count, an ordered digest of issue numbers, and the pinned Release's issue count. A person runs it
on a live environment with the admin kubeconfig:

```bash
eval "$(scripts/eks-env.sh)"
aws eks update-kubeconfig --name ticketscope-env --kubeconfig /tmp/ticketscope-admin.kubeconfig
scripts/restore-drill.sh --kubeconfig /tmp/ticketscope-admin.kubeconfig --out /tmp/restore-drill
cp /tmp/restore-drill/restore-drill.md docs/drills/restore-drill.md
```

The script writes the log, the result and this record, with account ids and private hostnames
masked (`scripts/restore_drill.py record`). The recovery cluster does not archive and is deleted
when the script ends. This file is replaced by that record after the first live run.
