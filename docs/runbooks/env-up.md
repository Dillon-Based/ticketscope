# env-up: dispatch, read and tear down by hand (story 5.3)

`env-up` brings the EKS environment up from the bootstrap layer through GitHub Actions OIDC and
records how long each stage took. There is no `env-down` yet (story 5.4), so a person tears the
environment down by hand. Region is `us-east-1`. The agent never dispatches this workflow or
applies anything against AWS; every step below is yours.

## Once, before the first dispatch

1. **Branch rule.** Add `main` to the `eks` environment's deployment branch rule (repo settings,
   Environments, `eks`). `env-up` has no push trigger and is dispatched from `main`.
2. **Repo settings.** The only AWS-related value is the `eks` environment variable `AWS_ROLE_ARN`
   (an identifier, not a credential). There must be no AWS secret and no other AWS variable.
3. **Widen the deploy role (bootstrap re-apply).** The role from story 1 had IAM, ECR push, EKS
   and Describe only. A full `infra/env` apply also needs EC2 (VPC, subnets, route tables, internet
   gateway, security groups, launch templates, tags), the cluster's OIDC provider, IAM policy
   reads, and `ecr:DescribeImages`. Those are in
   `infra/bootstrap/policies/deploy-permissions.json.tftpl`, scoped to this account and region,
   never to a `bootstrap` state path. Apply it with the admin identity, from a checkout that has
   the template change (the branch, or `main` after the merge) and bootstrap's untracked
   `terraform.tfvars` (copy it in from the checkout where bootstrap was first applied). The state
   backend is committed, so `init` needs the bucket and a checkout without it fails there instead
   of planning from an empty state.

   ```sh
   scripts/aws-login.sh
   eval "$(scripts/eks-env.sh)"
   terraform -chdir=infra/bootstrap init -reconfigure -backend-config="bucket=$TICKETSCOPE_STATE_BUCKET"
   terraform -chdir=infra/bootstrap plan -out=bootstrap.tfplan   # only the deploy role policy changes
   terraform -chdir=infra/bootstrap apply bootstrap.tfplan
   ```

   If the first dispatch still fails with `AccessDenied` (or `UnauthorizedOperation`), the failing
   action is in the apply log. Add exactly that action to the same template, re-apply bootstrap,
   re-dispatch, and record every denied action in the plan's Implementation Notes.

## Dispatch

```sh
gh workflow run env-up.yml --ref main -f sha=<40 hex> -f expiry_hours=4
gh run watch
```

`sha` is the commit whose images and scripts are deployed. `expiry_hours` is 1 to 24 (default 4);
the environment carries `expires_at` (UTC) as a tag. Bad input fails the `plan` job before any AWS
call. The `plan` job also looks in ECR for `ticketscope-app:<sha>` and `ticketscope-postgres:18-<sha>`;
when both exist, `build` and `images` are skipped, so a second dispatch on the same SHA reuses
them. Otherwise the images are built natively on amd64 and arm64 runners, pushed by digest, and
joined into one multi-arch tag each. That is outside the clock.

## Read the result

The `env` job's summary and the `env-up-stages` artifact (`stages.json`, `stages.md`) list every
stage:

- `terraform_apply`, `kubeconfig`, then `deploy.crds`, `deploy.platform`, `deploy.ticketscope`,
  `deploy.api-mcp-ready`, `deploy.dns_visible`, `deploy.dns_public`, `deploy.https-answers`, then
  `smoke`.
- The total runs from the start of `terraform apply` to the smoke check passing. R1 wants it under
  30 minutes (1800 s). At or over it, the summary says so and the stage times show where; record a
  Decision in the epic's Notes. Do not move the target without the owner.
- `dns_visible` waits on the zone's own name servers before `dns_public` asks the public resolver,
  because a resolver asked too early caches the missing record.

The smoke check (`tests/eks`) gets a search result from the page, lists `/mcp` tools and calls
`search_similar_issues`, and compares the load Job's issue count with the `Issues:` line of the
pinned snapshot's Release. A red smoke check fails the run and leaves the environment up for the
expiry sweep; read the job log, fix, and re-dispatch only after tearing down, or by hand against
the same environment.

## Tear down by hand, in AD-24 order

Use the admin profile and a kubeconfig for the cluster:

```sh
scripts/aws-login.sh
eval "$(scripts/eks-env.sh)"
aws eks update-kubeconfig --name ticketscope-env --region us-east-1 --kubeconfig "$KUBECONFIG"
```

The `env` stack gives your admin role cluster-admin through an access entry, so `kubectl` and
`helm` work as soon as the kubeconfig exists. A cluster applied before that change, or by another
identity, has no entry for you and `helm` says "provide credentials"; add one by hand (the
cluster's deletion removes it):

```sh
ADMIN_ARN="$(aws iam get-role --role-name AccountFullAccessRole --query Role.Arn --output text)"
aws eks create-access-entry --cluster-name ticketscope-env --principal-arn "$ADMIN_ARN"
aws eks associate-access-policy --cluster-name ticketscope-env --principal-arn "$ADMIN_ARN" \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster
```

Then the teardown:

```sh
helm uninstall ticketscope -n ticketscope
kubectl -n ticketscope delete pvc --all
kubectl -n platform delete gateway ticketscope
# wait until the ALB is gone, while the controller still runs:
until [ -z "$(aws elbv2 describe-load-balancers --region us-east-1 \
  --query "LoadBalancers[?contains(LoadBalancerName, 'k8s')].LoadBalancerArn" --output text)" ]; do sleep 10; done
# external-dns wrote no TXT ownership records in the tracer run, so check the zone and delete
# stray A, AAAA and TXT records for the hostname by hand while the controllers still run:
aws route53 list-resource-record-sets --hosted-zone-id "$TICKETSCOPE_ZONE_ID" \
  --query "ResourceRecordSets[?Type=='A'||Type=='AAAA'||Type=='TXT'].[Name,Type]" --output text
helm uninstall platform -n platform
# wait until tagged ENIs and volumes are gone, then:
terraform -chdir=infra/env destroy
```

The state is in the bootstrap bucket (`terraform -chdir=infra/env init -backend-config="bucket=$TICKETSCOPE_STATE_BUCKET"`
first, in a fresh checkout). Then run the leftover list in `docs/runbooks/eks-tracer.md` (step 7)
and confirm the tag-scoped list is empty:

```sh
aws resourcegroupstaggingapi get-resources --tag-filters Key=environment,Values=eks --region us-east-1
```
