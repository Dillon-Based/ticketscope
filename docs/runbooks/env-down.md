# env-down: tear the EKS environment down, prove it is clean, expire forgotten ones

`.github/workflows/env-down.yml` destroys the `env` stack in AD-24 order and then runs a read-only
leftover check (story 5.4, R3, R4). It never touches `infra/bootstrap`. It runs from `main` (the
`eks` environment's branch rule admits `main`) and shares the `eks-environment` concurrency group
with `env-up`'s `env` job, so a destroy and an apply never overlap; a second run waits.

## Triggers

- **Dispatch** (`gh workflow run env-down.yml`): always tears the environment down now.
- **Dispatch with `only_if_expired=true`**: the same decision as the schedule (below). `env-up`'s
  `expire` job sends this one, so a late dispatch from an old `env-up` run skips a newer
  environment that has not expired.
- **Schedule** (hourly, minute 17): the `find` job reads the `expires_at` tag of the environment
  VPC. An unexpired or untagged (hand-run) environment is skipped with a summary line that says
  when it expires. An expired one gets the full teardown with nobody dispatching. When no
  environment exists, the leftover check runs on its own and a tagged leftover fails the run.
- `env-up` stamps the tag: `expiry_hours` (1 to 5, default 4) or `expiry_minutes` (5 to 240,
  overrides hours). The agent dispatches only environments expiring within 4 hours, one at a time.

## Expiry: the expire job, with the schedule as a backstop

The schedule cannot be the guarantee. In the story 5.4 live runs GitHub created runs for about 2
of 19 hourly slots and none for the rest; nothing in the repo can make it fire.

So `env-up` has an `expire` job. It runs once `terraform apply` has started, whether the `env` job
passed or failed (a failed smoke check leaves the environment up), and never with `plan_only`. It
has no AWS credentials and no environment, only `actions: write`: it sleeps until `expires_at`,
then dispatches `env-down` with `only_if_expired=true` through the run's `GITHUB_TOKEN`. It is not
in the concurrency group, so a manual `env-down` never waits for it. A hosted job stops at 6
hours, which is why the expiry is at most 5 hours.

If the `expire` job did not run or failed (the run was cancelled, the dispatch was refused), the
hourly schedule may still catch it; otherwise dispatch `env-down` by hand. Check the next morning
that no environment is left: `aws ec2 describe-vpcs --filters Name=tag:environment,Values=eks`
under the read-only profile.

## Order (scripts/eks-teardown.sh)

1. `helm uninstall ticketscope`
2. delete the PVCs of the `ticketscope` namespace
3. delete the Gateway and wait until its ALB and the Gateway object are gone, with the controller
   still running (15 min, `ALB_WAIT_SECONDS`)
4. delete the controller's configuration objects, each waited on with the controller still
   running (5 min each, `CONFIG_WAIT_SECONDS`): the TargetGroupConfigurations (`ticketscope`
   namespace), the LoadBalancerConfigurations (`platform` namespace), then the GatewayClass
   (`GATEWAY_CLASS`, default `alb`)
5. `helm uninstall platform`
6. wait until tagged ENIs and volumes are gone (10 min, `ENI_VOLUME_WAIT_SECONDS`)
7. `terraform destroy` of `infra/env`
8. the DNS check (read-only): no A or AAAA record for the hostname is left in the zone
9. `scripts/leftover-check.sh`

The job summary lists the time of each stage.

## A stuck Gateway or configuration object

The `platform` release holds both the load balancer controller and the objects that carry its
finalizers: the GatewayClass, the LoadBalancerConfiguration and the TargetGroupConfigurations.
`helm uninstall platform` deletes them all at once; in the first live run the controller went
first and they stayed Terminating until helm gave up after 10 minutes. Step 4 deletes them while
the controller still runs.

When the ALB is not gone at 15 minutes, or a configuration object at 5, the script prints the
object's finalizers and the remedy, and the job fails before `platform` is uninstalled. Nothing is
force-deleted and no finalizer is removed: the controller has to stay to finish. Read its log
(`kubectl -n platform logs deploy/aws-load-balancer-controller`) and the object's events, fix the
cause, and dispatch `env-down` again.

A new kind in `deploy/charts/platform/templates` that the controller puts finalizers on
(Gateway, GatewayClass, LoadBalancerConfiguration, TargetGroupConfiguration, IngressClassParams,
TargetGroupBinding) fails `tests/unit/test_eks_teardown.py` until the script deletes it before
`helm uninstall platform`.

## Stale DNS records

external-dns (policy `sync`, registry `txt`) has never written its TXT ownership records here, so
it never deletes the hostname's A and AAAA records. Left behind, they point at a load balancer
that no longer exists and break the next `env-up`'s DNS stage. The cause is open (see
`deferred-work.md`).

After `terraform destroy`, so the environment is gone and billing stops either way, the script
lists the zone's A and AAAA records for the hostname. When any exist, or the zone cannot be read,
it prints them and exits 3: the leftover check still runs and the job fails. The job log has the
exact commands, with the zone id and hostname filled in. Run them with an identity that may change
the zone (the admin profile; the deploy role and the read-only role may only read it):

```sh
aws route53 list-resource-record-sets --hosted-zone-id "$TICKETSCOPE_ZONE_ID" \
  --query "ResourceRecordSets[?Name=='${TICKETSCOPE_HOSTNAME}.' && (Type=='A' || Type=='AAAA')]" --output json \
  | jq '{Changes: [.[] | {Action: "DELETE", ResourceRecordSet: .}]}' > stale-records.json
aws route53 change-resource-record-sets --hosted-zone-id "$TICKETSCOPE_ZONE_ID" \
  --change-batch file://stale-records.json
```

Check the listing before you delete. The hostname and zone id come from the hosted zone whose name
starts with `ticketscope.`, the same discovery `env-up` uses; by hand, `eval "$(scripts/eks-env.sh)"`
exports both.

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
`kms:ListResourceTags`. The DNS check needs only the Route 53 `Get*`/`List*` it already has. A
destroy that hits another denial lists it in the job summary under "Denied actions"; add it to
`infra/bootstrap/policies/deploy-permissions.json.tftpl`, re-apply bootstrap by hand, and dispatch
again. Confirm with `aws iam simulate-principal-policy` that the deploy role is denied on bootstrap
ARNs, and that `terraform plan -lock=false` of `infra/bootstrap` shows no change.

## By hand

The manual steps are in `docs/runbooks/env-up.md` ("Tear down by hand, in AD-24 order"); use them
only when the workflow cannot run.
