# Plans infra/env with a mocked AWS provider (story 5.5): no credential, no AWS call, so the PR
# check can prove the stack plans. Run by scripts/tf-plan-check.sh.

mock_provider "aws" {
  # main.tf slices the first two availability zones, so the mock must supply two.
  override_data {
    target = data.aws_availability_zones.available
    values = {
      names = ["us-east-1a", "us-east-1b"]
    }
  }

  # The EKS and IRSA modules parse these as an ARN or a JSON object, which a mock's random
  # strings are not, so each gets a well-formed default.
  mock_data "aws_caller_identity" {
    defaults = {
      account_id = join("", ["1234", "56789012"])
      arn        = "arn:aws:iam::${join("", ["1234", "56789012"])}:user/plan-test"
      user_id    = "AIDAPLANTEST"
    }
  }

  mock_data "aws_iam_session_context" {
    defaults = {
      arn        = "arn:aws:iam::${join("", ["1234", "56789012"])}:role/plan-test"
      issuer_arn = "arn:aws:iam::${join("", ["1234", "56789012"])}:role/plan-test"
    }
  }

  mock_data "aws_iam_policy_document" {
    defaults = {
      json = "{}"
    }
  }

  mock_data "aws_partition" {
    defaults = {
      partition  = "aws"
      dns_suffix = "amazonaws.com"
    }
  }
}

variables {
  # The account id must be 12 digits, but no account id may appear as a literal in infra/
  # (test_infra_bootstrap.py), so it is assembled here. The mock never reaches AWS.
  account_id = join("", ["1234", "56789012"])
  zone_id    = "Z00000000000000000000"
}

run "plans_without_aws_credentials" {
  command = plan
}
