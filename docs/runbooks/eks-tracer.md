# EKS tracer: hand steps (story 5.2)

The tracer proves the Gateway, ACM certificate and external-dns chain on an applied
environment, once, by hand. The agent wrote and statically checked everything here; every step
below is yours because it writes to AWS. Use the admin profile (`scripts/aws-login.sh`, profile
`ticketscope-sso`). Region is `us-east-1`. Time each stage and keep the numbers for the plan's
Implementation Notes.

Placeholders: `<account>` is the 12-digit account id, `<host>` the fixed hostname (bootstrap's
`hostname`), `<sha>` the git SHA of the commit you deploy. Nothing below is committed with a real
value.

## 1. Push the images (multi-arch)

Nodes are Graviton, so the arm64 image has to be there. The Postgres tag leads with the major
(`18-<sha>`, as `kind-up.sh` does).

```sh
REG=<account>.dkr.ecr.us-east-1.amazonaws.com
aws ecr get-login-password --region us-east-1 --profile ticketscope-sso \
  | docker login --username AWS --password-stdin "$REG"
docker buildx build --platform linux/amd64,linux/arm64 -f images/app.Dockerfile \
  -t "$REG/ticketscope-app:<sha>" --push .
docker buildx build --platform linux/amd64,linux/arm64 -f images/postgres.Dockerfile \
  -t "$REG/ticketscope-postgres:18-<sha>" --push .
```

## 2. Apply `infra/env`

Needs an untracked `infra/env/terraform.tfvars` with `account_id` and `zone_id`
(`terraform -chdir=infra/bootstrap output zone_id`).

```sh
terraform -chdir=infra/env init -backend-config="bucket=ticketscope-<account>"
time terraform -chdir=infra/env apply
aws eks update-kubeconfig --name ticketscope-env --region us-east-1 \
  --profile ticketscope-sso --kubeconfig /tmp/ticketscope-eks.kubeconfig
```

Record the apply time.

## 3. Deploy

```sh
export CERT=$(terraform -chdir=infra/bootstrap output -raw certificate_arn)
scripts/eks-deploy.sh --kubeconfig /tmp/ticketscope-eks.kubeconfig --tag <sha> \
  --hostname <host> --certificate-arn "$CERT" --ecr-registry "$REG"
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
curl -sS https://<host>/ | head          # the search page
dig <host> +short                          # the ALB, through external-dns's record
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
helm uninstall platform -n platform
# wait until tagged ENIs and volumes are gone, then:
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

## What the agent could not verify

These are the points the tracer settles: the Gateway API CRD version the controller accepts
(`GATEWAY_API_VERSION`, default v1.6.0), whether the HTTPS listener's `tls.mode: Terminate`
without `certificateRefs` is accepted by the controller, whether the controller's IAM policy
covers the ALB Gateway path, and whether external-dns reads the ALB address from the Gateway
status (AD-14).
