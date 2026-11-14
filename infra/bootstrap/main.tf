locals {
  region = "us-east-1"
  bucket = "ticketscope-${var.account_id}"
  oidc   = "token.actions.githubusercontent.com"
}

# DNS and certificate: the hosted zone is created by registering the domain in Route53.
data "aws_route53_zone" "main" {
  name         = var.domain
  private_zone = false
}

resource "aws_acm_certificate" "main" {
  domain_name       = var.domain
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for o in aws_acm_certificate.main.domain_validation_options : o.domain_name => o
  }

  zone_id         = data.aws_route53_zone.main.zone_id
  name            = each.value.resource_record_name
  type            = each.value.resource_record_type
  records         = [each.value.resource_record_value]
  ttl             = 60
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

# State and CNPG backups. Bootstrap's own state lives under bootstrap/, which the deploy
# role's policy never reaches.
resource "aws_s3_bucket" "state" {
  bucket = local.bucket

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    id     = "expire-old-versions-and-partial-uploads"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.state]
}

# Image registry: the two images, last 10 kept.
resource "aws_ecr_repository" "image" {
  for_each = toset(["ticketscope-app", "ticketscope-postgres"])

  name                 = each.key
  image_tag_mutability = "MUTABLE"
  force_delete         = false

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "image" {
  for_each   = aws_ecr_repository.image
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# Cost alarm.
resource "aws_budgets_budget" "monthly" {
  name         = "ticketscope-monthly"
  budget_type  = "COST"
  limit_amount = "8"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}

# Keyless CI: GitHub's OIDC provider and the one role the `eks` environment may assume.
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://${local.oidc}"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_role" "deploy" {
  name = "ticketscope-deploy"

  assume_role_policy = templatefile("${path.module}/policies/deploy-trust.json.tftpl", {
    oidc_provider_arn = aws_iam_openid_connect_provider.github.arn
    repo              = var.repo
  })
}

resource "aws_iam_role_policy" "deploy" {
  name = "ticketscope-deploy"
  role = aws_iam_role.deploy.id

  policy = templatefile("${path.module}/policies/deploy-permissions.json.tftpl", {
    account_id = var.account_id
    region     = local.region
    bucket     = aws_s3_bucket.state.bucket
  })
}

# Read-only role for the agent, assumed from the admin identity.
resource "aws_iam_role" "readonly" {
  name = "ticketscope-readonly"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = var.admin_principal_arn }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "readonly" {
  role       = aws_iam_role.readonly.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_role_policy" "readonly_extras" {
  name   = "ticketscope-readonly-extras"
  role   = aws_iam_role.readonly.id
  policy = file("${path.module}/policies/readonly-extras.json.tftpl")
}
