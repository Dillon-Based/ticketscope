# infra/bootstrap

The persistent AWS layer (AD-15): the hostname certificate, the GitHub OIDC provider and
deploy role, the state and backup bucket, two ECR repositories (last 10 images kept), a
$8/month budget alarm, and a read-only role for the agent. It is applied once, by hand, from
your machine. The ephemeral `env` stack (story 5.2 onward) is not here. Nothing in this stack
destroys the bucket or the hosted zone (`prevent_destroy` on the bucket).

Region is `us-east-1`. No AWS credential, account id or email is stored in the repo.

## What the agent wrote, and what you do

The Terraform and the policy templates in `policies/` are checked by
`uv run pytest tests/unit/test_infra_bootstrap.py` with no AWS access. Everything below is
yours: it needs your account.

## 1. Account

1. Create the AWS account (or use a fresh one). Record the plan and credit terms here once
   known: _not yet recorded_. This does not gate the apply.
2. Enable MFA on the root user, then stop using root.
3. Create an admin identity (IAM Identity Center user, or an IAM user with MFA) and a CLI
   profile for it, e.g. `ticketscope-admin`. Note its ARN: that is `admin_principal_arn`.

## 2. Domain

Register the domain in Route53 (this creates the hosted zone), or create a hosted zone for a
domain registered elsewhere and point the registrar's name servers at it. The stack reads the
zone by name and validates the certificate through it.

## 3. tfvars

Create `infra/bootstrap/terraform.tfvars` (untracked, ignored by `*.tfvars`):

```hcl
account_id          = "<12-digit account id>"
alert_email         = "<your address>"
domain              = "<your domain>"
admin_principal_arn = "<admin identity ARN>"
repo                = "<owner>/<repo>"
```

## 4. Apply (local state)

```sh
export AWS_PROFILE=ticketscope-admin
terraform -chdir=infra/bootstrap init
terraform -chdir=infra/bootstrap plan -out=bootstrap.tfplan
terraform -chdir=infra/bootstrap apply bootstrap.tfplan
```

Certificate validation waits on DNS and can take several minutes. Confirm the budget
subscription email AWS sends. Commit `infra/bootstrap/.terraform.lock.hcl` if it changed.

## 5. Migrate state into the bucket

State starts local. Once the bucket exists, move it under `bootstrap/`. Create
`infra/bootstrap/backend.tf` (untracked, ignored; it names the bucket and so the account id):

```hcl
terraform {
  backend "s3" {
    bucket       = "ticketscope-<account id>"
    key          = "bootstrap/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}
```

```sh
terraform -chdir=infra/bootstrap init -migrate-state
```

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
source_profile = ticketscope-admin
region         = us-east-1
```

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
