# env-down: tear the EKS environment down, prove it is clean, expire forgotten ones

`.github/workflows/env-down.yml` destroys the `env` stack in AD-24 order and then runs a read-only
leftover check (story 5.4, R3, R4). It never touches `infra/bootstrap`. It runs from `main` (the
`eks` environment's branch rule admits `main`) and shares the `eks-environment` concurrency group
with `env-up`, so the two never overlap; a second run waits.

## Triggers

- **Dispatch** (`gh workflow run env-down.yml`): always tears the environment down now.
- **Schedule** (hourly, minute 17): the `find` job reads the `expires_at` tag of the environment
  VPC. An unexpired or untagged (hand-run) environment is skipped with a summary line that says
  when it expires. An expired one gets the full teardown with nobody dispatching. When no
  environment exists, the leftover check runs on its own and a tagged leftover fails the run.
- `env-up` stamps the tag: `expiry_hours` (1 to 24, default 4) or `expiry_minutes` (5 to 240,
  overrides hours). The agent dispatches only environments expiring within 4 hours, one at a time.

## Order (scripts/eks-teardown.sh)

1. `helm uninstall ticketscope`
2. delete the PVCs of the `ticketscope` namespace
3. delete the Gateway and wait until its ALB is gone, with the controller still running (15 min,
   `ALB_WAIT_SECONDS`)
4. `helm uninstall platform`
5. wait until tagged ENIs and volumes are gone (10 min, `ENI_VOLUME_WAIT_SECONDS`)
6. `terraform destroy` of `infra/env`
7. `scripts/leftover-check.sh`

The job summary lists the time of each stage.

## A stuck Gateway

When the ALB is not gone at 15 minutes the script prints the Gateway's finalizers and the remedy,
and the job fails before `platform` is uninstalled. Nothing is force-deleted and no finalizer is
removed: the controller has to stay to finish. Read its log
(`kubectl -n platform logs deploy/aws-load-balancer-controller`) and the Gateway's events, fix the
cause, and dispatch `env-down` again.

## The leftover check

`scripts/leftover-check.sh` makes list and describe calls only. It selects resources tagged
`environment=eks` (and by the controller's `elbv2.k8s.aws/cluster` tag), never `stack=bootstrap`
or another environment's tag, and also lists ENIs through EC2 because the tagging API can omit
them. An `aws` error, an empty answer or a malformed listing fails the check; it never reads as
clean.

- `scripts/leftover-check.sh --list` prints what is found (the positive control while the
  environment is up: the Gateway's ALB, target groups, the security group, the PVC volumes).
- `scripts/leftover-check.sh --dry-run` injects a tagged ALB and must fail naming it.
- Run it by hand as the read-only role: `eval "$(scripts/eks-env.sh)"`, then the script.

## The deploy role

The deploy role gained read actions for the check: `tag:GetResources`,
`elasticloadbalancing:Describe*`, `logs:DescribeLogGroups`, `kms:ListKeys`, `kms:DescribeKey`,
`kms:ListResourceTags`. A destroy that hits another denial lists it in the job summary under
"Denied actions"; add it to `infra/bootstrap/policies/deploy-permissions.json.tftpl`, re-apply
bootstrap by hand, and dispatch again. Confirm with `aws iam simulate-principal-policy` that the
deploy role is denied on bootstrap ARNs, and that `terraform plan -lock=false` of `infra/bootstrap`
shows no change.

## By hand

The manual steps are in `docs/runbooks/env-up.md` ("Tear down by hand, in AD-24 order"); use them
only when the workflow cannot run.
