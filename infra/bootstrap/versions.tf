terraform {
  required_version = "~> 1.17"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Committed, so a checkout that was never configured fails at `init` instead of planning from
  # an empty local state. The bucket name carries the account id, so it comes at init:
  #   terraform init -backend-config="bucket=$TICKETSCOPE_STATE_BUCKET"   (eks-env.sh exports it)
  # The very first apply, before the bucket exists, runs `terraform init -backend=false`.
  backend "s3" {
    key          = "bootstrap/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}

provider "aws" {
  region              = "us-east-1"
  allowed_account_ids = [var.account_id]

  default_tags {
    tags = {
      project = "ticketscope"
      stack   = "bootstrap"
    }
  }
}
