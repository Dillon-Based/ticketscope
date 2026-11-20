locals {
  region = "us-east-1"
  azs    = slice(data.aws_availability_zones.available.names, 0, 2)
  # The bootstrap bucket (infra/bootstrap local.bucket); CNPG backups go under backups/.
  backup_bucket = "ticketscope-${var.account_id}"
}

data "aws_availability_zones" "available" {
  state = "available"
}
