# IRSA roles for the controllers and the EBS driver (AD-23). Names start with ticketscope-env-,
# the prefix the deploy role may manage. The CNPG backup role is story 5.6's.
module "lb_controller_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"
  version = "~> 6.0"

  name            = "ticketscope-env-lb-controller"
  policy_name     = "ticketscope-env-lb-controller"
  use_name_prefix = false

  attach_load_balancer_controller_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["platform:aws-load-balancer-controller"]
    }
  }
}

module "external_dns_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"
  version = "~> 6.0"

  name            = "ticketscope-env-external-dns"
  policy_name     = "ticketscope-env-external-dns"
  use_name_prefix = false

  attach_external_dns_policy    = true
  external_dns_hosted_zone_arns = ["arn:aws:route53:::hostedzone/${var.zone_id}"]

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["platform:external-dns"]
    }
  }
}

module "ebs_csi_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"
  version = "~> 6.0"

  name            = "ticketscope-env-ebs-csi"
  policy_name     = "ticketscope-env-ebs-csi"
  use_name_prefix = false

  attach_ebs_csi_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
}

# CNPG backups (story 5.6, AD-18): the Cluster's service account writes WAL and base backups
# under backups/ in the bootstrap bucket, and nothing else. The candidate set is inferred from
# the S3 multipart docs and Barman; the plan's Implementation Notes record what live runs needed.
data "aws_iam_policy_document" "cnpg_backup" {
  statement {
    sid       = "BackupObjects"
    actions   = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:AbortMultipartUpload", "s3:ListMultipartUploadParts"]
    resources = ["arn:aws:s3:::${local.backup_bucket}/backups/*"]
  }

  statement {
    sid       = "BackupPrefixListing"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${local.backup_bucket}"]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["backups/*"]
    }
  }

  statement {
    sid       = "BackupMultipartListing"
    actions   = ["s3:ListBucketMultipartUploads"]
    resources = ["arn:aws:s3:::${local.backup_bucket}"]
  }
}

resource "aws_iam_policy" "cnpg_backup" {
  name   = "ticketscope-env-cnpg-backup"
  policy = data.aws_iam_policy_document.cnpg_backup.json
}

module "cnpg_backup_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts"
  version = "~> 6.0"

  name            = "ticketscope-env-cnpg-backup"
  use_name_prefix = false

  policies = {
    backup = aws_iam_policy.cnpg_backup.arn
  }

  # The Cluster's service account is named after the Cluster (ticketscope-db);
  # spec.serviceAccountName stays unset.
  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["ticketscope:ticketscope-db"]
    }
  }
}
