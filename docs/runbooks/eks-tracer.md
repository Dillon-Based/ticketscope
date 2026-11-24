# EKS tracer: hand steps (story 5.2)

The tracer proves the Gateway, ACM certificate and external-dns chain on an applied
environment, once, by hand. The agent wrote and statically checked everything here; every step
below is yours because it writes to AWS. Use the admin profile (`scripts/aws-login.sh`, profile
`ticketscope-sso`). Region is `us-east-1`. Time each stage and keep the numbers for the plan's
Implementation Notes.

## Before you start (every terminal)

Sign in once, then run this in **each** terminal you use. It exports `AWS_PROFILE`, `KUBECONFIG`,
`REG`, `CERT`, `TICKETSCOPE_ZONE_ID`, `TICKETSCOPE_STATE_BUCKET` and `TICKETSCOPE_HOSTNAME`, puts
Docker Desktop's credential helper on `PATH`, writes the untracked `infra/env/terraform.tfvars`,
and `cd`s to the repo root, so no step below depends on what another terminal exported:

```sh
scripts/aws-login.sh
eval "$(scripts/eks-env.sh)"
SHA=$(git rev-parse HEAD)
```

`<sha>` below is `$SHA`. The agent never runs the steps below; it reads AWS and the cluster
through `AWS_PROFILE=ticketscope-readonly` and the kubeconfig. Nothing below is committed with a
real value.

## 1. Push the images

Nodes are Graviton, so the arm64 image has to be there. AD-16 wants both arches; the tracer needs
only arm64, which a Mac builds natively (add `linux/amd64` only for the multi-arch check). The
Postgres tag leads with the major (`18-<sha>`, as `kind-up.sh` does).

```sh
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$REG"
docker buildx build --platform linux/arm64 -f images/app.Dockerfile \
  -t "$REG/ticketscope-app:$SHA" --push .
docker buildx build --platform linux/arm64 -f images/postgres.Dockerfile \
  -t "$REG/ticketscope-postgres:18-$SHA" --push .
```

## 2. Apply `infra/env`

`eks-env.sh` wrote the untracked `infra/env/terraform.tfvars` (`account_id`, `zone_id`). Read the
plan before applying: it must create no NAT gateway, KMS key or log group, and nothing outside
`infra/env`.

```sh
terraform -chdir=infra/env init -backend-config="bucket=$TICKETSCOPE_STATE_BUCKET"
terraform -chdir=infra/env plan -out=env.tfplan
time terraform -chdir=infra/env apply env.tfplan
aws eks update-kubeconfig --name ticketscope-env --region us-east-1 --kubeconfig "$KUBECONFIG"
```

Record the apply time.

## 3. Deploy

```sh
time scripts/eks-deploy.sh --kubeconfig "$KUBECONFIG" --tag "$SHA" \
  --hostname "$TICKETSCOPE_HOSTNAME" --certificate-arn "$CERT" --ecr-registry "$REG"
```

It prints the time of each stage (crds, platform, ticketscope, api-mcp-ready, https-answers) and
a total. The kubeconfig user runs `aws eks get-token`, so keep the profile logged in.

external-dns runs `policy: sync`, which deletes records it owns. To dry-run it first, install
`platform` once with `--set-json 'external-dns.extraArgs=["--dry-run"]'` added to the script's
`helm upgrade` line, read its log, then deploy again without it.

### If the record is not written

Read the Gateway's address and external-dns's log:

```sh
kubectl -n platform get gateway ticketscope -o jsonpath='{.status.addresses}'
kubectl -n platform logs deploy/external-dns
```

If `.status.addresses` is empty or external-dns ignores it, set the fallback and redeploy:

```sh
TARGET_ANNOTATION=$(kubectl -n platform get gateway ticketscope \
  -o jsonpath='{.status.addresses[0].value}') scripts/eks-deploy.sh ...
```

(The ALB's DNS name is in the AWS console under Load Balancers if the status stays empty.) Record
which of the two worked. If neither does, stop and replan.

## 4. Smoke

```sh
curl -sS "https://$TICKETSCOPE_HOSTNAME/" | head   # the search page
dig "$TICKETSCOPE_HOSTNAME" +short                  # the ALB, through external-dns's record
```

Then search from the page, and call `/mcp` with an MCP client: list the tools, then call
`search_similar_issues` (for example with the Inspector:
`npx @modelcontextprotocol/inspector` against `https://<host>/mcp`, streamable HTTP). Record the
requests, the certificate mode used (explicit ARN) and node memory headroom
(`kubectl top nodes`, `kubectl describe nodes | grep -A8 "Allocated resources"`).

## 5. Capture the aws output while the environment is up

The tag-scoped list, with ids masked before it is committed (account id, ARNs, resource ids; no
person identifiers) into `tests/fixtures/aws/`, for example `up.json`:

```sh
aws resourcegroupstaggingapi get-resources --tag-filters Key=environment,Values=eks \
  --region us-east-1 --profile ticketscope-sso
```

It should show the ALB, a target group, the security group and the EBS volumes. Controller-made
resources carry the tag through `--default-tags`, and volumes through the EBS driver's
`extraVolumeTags`.

## 6. Hand teardown, in this order

```sh
export KUBECONFIG=/tmp/ticketscope-eks.kubeconfig
helm uninstall ticketscope -n ticketscope
kubectl -n ticketscope delete pvc --all
kubectl -n platform delete gateway ticketscope
# wait until the ALB is gone, while the controller still runs:
until [ -z "$(aws elbv2 describe-load-balancers --region us-east-1 --profile ticketscope-sso \
  --query "LoadBalancers[?contains(LoadBalancerName, 'k8s')].LoadBalancerArn" --output text)" ]; do sleep 10; done
# external-dns did not delete its records in the tracer run (no TXT ownership records were
# written), so check the zone while the controllers still run, and delete by hand if needed:
aws route53 list-resource-record-sets --hosted-zone-id "$TICKETSCOPE_ZONE_ID" \
  --query "ResourceRecordSets[?Type=='A'||Type=='AAAA'||Type=='TXT'].[Name,Type]" --output text
helm uninstall platform -n platform
# wait until tagged ENIs and volumes are gone, then (AWS_PROFILE must be exported):
terraform -chdir=infra/env destroy
```

Then capture the same tag-scoped list again as `down.json` (masked); it should be empty.

## 7. Leftover list

Check by hand, with the tag filter and by name, after destroy. Anything found is a teardown bug
to record:

- load balancers and target groups (`aws elbv2 describe-load-balancers`, `describe-target-groups`)
- security groups named `k8s-*` and `ticketscope-env*`
- network interfaces and EBS volumes (`aws ec2 describe-network-interfaces`, `describe-volumes`)
- Route53 records in the bootstrap zone for `<host>` and its `txt` records (external-dns removes
  them under `policy: sync`; delete by hand if it did not)
- IAM roles and policies named `ticketscope-env-*`
- CloudWatch log groups named `/aws/eks/ticketscope-env/*` (logging is off, so none expected)

## What the tracer settled (2026-11-17)

- The controller (chart 3.6.3) needs the Gateway API v1.6.0 standard bundle; against v1.3.0 it
  logged `Disabling ALBGatewayAPI: missing required CRDs [ReferenceGrant]`. Restart the controller
  after the CRDs change, because it decides at startup.
- The listener's `tls.mode: Terminate` with an `options` entry and no `certificateRefs` is
  accepted by the API server (the v1.3.0 CRD rejects it with neither) and by the controller, which
  took the certificate from the `LoadBalancerConfiguration`'s explicit ARN.
- The module's controller IAM policy covers the ALB Gateway path: no `AccessDenied`.
- external-dns read the ALB address from the Gateway status and wrote A and AAAA alias records
  with no target annotation. It wrote no TXT ownership records and so deleted nothing at
  teardown: delete the records by hand (step 6) until story 5.4 handles it.
- The IRSA trust names and the chart's ServiceAccount names must agree; the chart pins them.

Not settled: the Gateway being Programmed before any route exists (routes already existed when
the ALB was first created).

## 8. Backups (story 5.6, R6, R8)

`env-up` passes the incarnation (`inc-<run id>-<attempt>`), the bootstrap bucket and the backup role's ARN to the
release, and runs `scripts/eks-backup.sh` after the smoke check (outside the clock). Backups land under
`backups/<incarnation>/` in the bootstrap bucket. A hand deploy takes `--incarnation <id>` too.

Check with the read-only profile. The read-only kubeconfig's EKS view access does not cover the CNPG
custom resources (`backups`, `clusters`, `scheduledbackups` are Forbidden), so run the first three `kubectl`
lines with the admin kubeconfig from `eks-env.sh`; pod logs (`kubectl logs ticketscope-db-1 -c plugin-barman-cloud`) work read-only.

```bash
kubectl -n ticketscope get backups.postgresql.cnpg.io,scheduledbackups.postgresql.cnpg.io   # one Backup `completed`
kubectl -n ticketscope get cluster ticketscope-db -o jsonpath='{.spec.serviceAccountName}'   # empty
kubectl -n ticketscope get secrets; kubectl -n ticketscope get role,rolebinding -o yaml       # record the names and rules
BUCKET="ticketscope-$(aws sts get-caller-identity --query Account --output text --profile ticketscope-readonly)"
INC=$(kubectl -n ticketscope get cluster ticketscope-db -o jsonpath='{.spec.plugins[0].parameters.serverName}')
aws s3 ls "s3://$BUCKET/backups/$INC/" --recursive --profile ticketscope-readonly | head
# simulate-principal-policy reported explicitDeny for every action in this account (AllowedByOrganizations
# false, no matched statement), so simulate the policy document itself:
PARN=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text --profile ticketscope-readonly):policy/ticketscope-env-cnpg-backup
V=$(aws iam get-policy --policy-arn "$PARN" --query Policy.DefaultVersionId --output text --profile ticketscope-readonly)
aws iam get-policy-version --policy-arn "$PARN" --version-id "$V" --query PolicyVersion.Document --profile ticketscope-readonly > policy.json
aws iam simulate-custom-policy --policy-input-list "$(cat policy.json)" --profile ticketscope-readonly \
  --action-names s3:GetObject --resource-arns "arn:aws:s3:::$BUCKET/env/terraform.tfstate" --query 'EvaluationResults[0].EvalDecision'   # implicitDeny
aws iam simulate-custom-policy --policy-input-list "$(cat policy.json)" --profile ticketscope-readonly \
  --action-names s3:PutObject s3:GetObject s3:DeleteObject --resource-arns "arn:aws:s3:::$BUCKET/backups/x" --query 'EvaluationResults[].EvalDecision'   # allowed
```

Tighten the policy in `infra/env/irsa.tf` against what a backup, a restore read and a retention delete actually needed,
and record that set in the plan's Implementation Notes. Pod Identity is the fallback only if IRSA fails on the first recreate.

The restore drill (story 5.7) is `scripts/restore-drill.sh`; its record is `docs/drills/restore-drill.md`.

The failure drill (story 5.8) is `scripts/failure-drill.sh`, run last in the window with admin AWS credentials and the admin kubeconfig; its record is `docs/drills/failure-drill.md`. It needs the `env-up` that deployed `database.instancePlacement: required`.
