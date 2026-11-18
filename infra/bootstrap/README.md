# infra/bootstrap

The persistent AWS layer (AD-15): the hostname certificate, the GitHub OIDC provider and
deploy role, the state and backup bucket, two ECR repositories (last 10 images kept), a
$8/month budget alarm, and a read-only role for the agent. It is applied once, by hand, from
your machine. The ephemeral `env` stack (story 5.2 onward) is not here. Nothing in this stack
destroys the bucket or the hosted zone (`prevent_destroy` on both).

Region is `us-east-1`. No AWS credential, account id or email is stored in the repo.

## What the agent wrote, and what you do

The Terraform and the policy templates in `policies/` are checked by
`uv run pytest tests/unit/test_infra_bootstrap.py` with no AWS access. Everything below is
yours: it needs your account.

## 1. Account

1. Create the AWS account (or use a fresh one). Record the plan and credit terms here once
   known: _not yet recorded_. This does not gate the apply.
2. Enable MFA on the root user, then stop using root.
3. The admin identity is your Identity Center role. Its exact ARN, path included, is
   `admin_principal_arn`: `aws iam get-role --role-name AccountFullAccessRole --query Role.Arn`.
   The CLI profile for it is `ticketscope-sso` (see "Signing in as the admin").

## 2. Domain

Route53 registration was declined for a new account, so the domain is registered at Cloudflare
Registrar. Cloudflare Registrar keeps its own name servers on the domain (custom name servers
need a transfer out, which ICANN blocks for 60 days after registration), so Route53 hosts only
a delegated subdomain. `domain` and `hostname` are both that subdomain, e.g.
`ticketscope.<your domain>`; Cloudflare keeps the apex.

1. Check the parent has no CAA record that excludes Amazon: `dig CAA <parent domain>`.
2. Create only the zone first, then read its name servers:
   `terraform -chdir=infra/bootstrap apply -target=aws_route53_zone.main`, then
   `terraform -chdir=infra/bootstrap output name_servers`.
3. In Cloudflare DNS for the parent, add four `NS` records named after the subdomain label
   (e.g. `ticketscope`), one per name server. Delegation works on every Cloudflare plan.
   DNSSEC on the parent can stay as it is: the child is an unsigned delegation.
4. Check: `dig NS <subdomain> @<a Cloudflare name server>` returns the four, and
   `dig SOA <subdomain> @1.1.1.1` returns the Route53 SOA.
5. Then the full apply (step 4). The certificate waits for validation through the zone.

A zone whose name changes is replaced, and `prevent_destroy` blocks that: `terraform state rm
aws_route53_zone.main`, delete the old zone with `aws route53 delete-hosted-zone`, and create
the new one. Its name servers are new, so update the NS records.

## 3. tfvars

Create `infra/bootstrap/terraform.tfvars` (untracked, ignored by `*.tfvars`):

```hcl
account_id          = "<12-digit account id>"
alert_email         = "<your address>"
domain              = "<your domain>"
hostname            = "<the fixed hostname, e.g. ticketscope.<your domain>>"
admin_principal_arn = "<admin identity ARN>"
repo                = "<owner>/<repo>"   # or owner@<id>/repo@<id>, see below
```

`repo` must match the OIDC `sub` claim exactly. Repositories that use GitHub's immutable
subjects present `repo:<owner>@<owner id>/<repo>@<repo id>:environment:eks`, and the plain
`owner/repo` then never matches (`Not authorized to perform sts:AssumeRoleWithWebIdentity`).
Run `.github/workflows/aws-oidc-check.yml`: its first step prints the `sub`. The ids are
account details, so they stay in the untracked tfvars.

## 4. Apply (local state)

```sh
export AWS_PROFILE=ticketscope-sso
terraform -chdir=infra/bootstrap init -backend=false   # local state, before the bucket exists
terraform -chdir=infra/bootstrap plan -out=bootstrap.tfplan
terraform -chdir=infra/bootstrap apply bootstrap.tfplan
```

Certificate validation waits on DNS and can take several minutes. Confirm the budget
subscription email AWS sends. Commit `infra/bootstrap/.terraform.lock.hcl` if it changed.

## 5. Migrate state into the bucket

State starts local (step 4 runs `init -backend=false`). Once the bucket exists, move it under
`bootstrap/`. The S3 backend block is committed in `versions.tf` without its bucket, which names
the account id and so comes at init. An old untracked `backend.tf` from an earlier version of
these steps must be deleted: two backend blocks fail the init.

```sh
terraform -chdir=infra/bootstrap init -migrate-state -backend-config="bucket=ticketscope-<account id>"
```

Every later `init` passes the same flag (`eval "$(scripts/eks-env.sh)"` exports the bucket as
`$TICKETSCOPE_STATE_BUCKET`):
`terraform -chdir=infra/bootstrap init -reconfigure -backend-config="bucket=$TICKETSCOPE_STATE_BUCKET"`.
A checkout that skips it fails at `init`, so a plan can never start from an empty local state.

Answer yes, then delete the local `terraform.tfstate*` files.

## 6. GitHub environment `eks`

In the repository settings create the environment `eks`. Its deployment branch rule must
admit story branches. The deploy role trusts exactly one subject,
`repo:<repo>:environment:eks`, so only jobs in that environment can assume it. Do not store
any AWS secret or variable; the workflow gets the role ARN from the `deploy_role_arn` output
(put it in the workflow file when story 5.2 adds one, it is not a secret).

## 7. Read-only profile

In `~/.aws/config` (not the repo):

```ini
[profile ticketscope-readonly]
role_arn       = <readonly_role_arn output>
source_profile = ticketscope-sso
region         = us-east-1
```

## Signing in as the admin

One identity: the Identity Center role (`AccountFullAccessRole`), through the `ticketscope-sso`
profile. Only changes to `infra/bootstrap` need it; deploys use OIDC and checks use the
read-only profile, which assumes its role from this one. `aws login` reuses the browser's
console session, so the console must be signed in to the ticketscope account (not another
account the same login can reach).

1. Sign in to the AWS console through Identity Center, in the ticketscope account.
2. Run `scripts/aws-login.sh`. It clears stray `AWS_*` variables, runs `aws login`, and fails
   unless the identity is `assumed-role/AccountFullAccessRole/...`.
3. `export AWS_PROFILE=ticketscope-sso`. Sessions expire; when Terraform says the login session
   has expired, run the script again.

## Verify

```sh
terraform -chdir=infra/bootstrap plan                      # no changes (a second plan is empty)
dig NS <domain>                                            # the zone's name servers
aws acm describe-certificate --region us-east-1 --certificate-arn <certificate_arn output>   # ISSUED
aws budgets describe-budgets --account-id <account id>     # ticketscope-monthly, 8 USD
aws ecr get-lifecycle-policy --repository-name ticketscope-app
aws ecr get-lifecycle-policy --repository-name ticketscope-postgres
aws s3api get-public-access-block --bucket <state_bucket output>   # all four true
aws s3api get-bucket-versioning --bucket <state_bucket output>     # Status Enabled
aws s3api get-bucket-lifecycle-configuration --bucket <state_bucket output>   # the expiry rule, Enabled
```

Run `terraform -chdir=infra/bootstrap plan` again after the state migration (step 5): it must
also show no changes, now against the bucket-backed state.

Read-only profile (`AWS_PROFILE=ticketscope-readonly`):

```sh
aws sts get-caller-identity                                # works
aws s3 mb s3://ticketscope-denied-check                    # AccessDenied
aws iam simulate-principal-policy --policy-source-arn <deploy_role_arn output> --action-names s3:GetObject
aws ce get-cost-and-usage --time-period Start=<yyyy-mm-01>,End=<yyyy-mm-dd> --granularity MONTHLY --metrics UnblendedCost
```

OIDC: dispatch a workflow in environment `eks` that assumes the deploy role and runs
`aws sts get-caller-identity`; it must print the role's identity with no AWS secret or
variable in the repo. Record any denial you see.
