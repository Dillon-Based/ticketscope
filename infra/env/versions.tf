terraform {
  required_version = "~> 1.17"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # The bootstrap bucket holds this state under env/ (the deploy role reaches only env/*).
  # The bucket name carries the account id, so it comes at init:
  #   terraform init -backend-config="bucket=ticketscope-<account id>"
  backend "s3" {
    key          = "env/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}

provider "aws" {
  region              = local.region
  allowed_account_ids = [var.account_id]

  # Every env resource carries `environment`, so the tag-scoped list and the leftover check
  # (story 5.4) find it. Resources the controllers create get it from their own settings.
  default_tags {
    tags = {
      project     = "ticketscope"
      stack       = "env"
      environment = var.environment
    }
  }
}
