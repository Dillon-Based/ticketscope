# EKS 1.36 on standard support, a managed node group of Graviton nodes, no Auto Mode, no
# Fargate (AD-16). The API endpoint is public and IAM-authenticated. No customer-managed KMS
# key and no control-plane logging (AD-23).
data "aws_caller_identity" "current" {}

# The role the person signs in with. env-up's deploy role creates the cluster and so is its only
# admin; without this entry the hand teardown is refused until an entry is made by hand. Skipped
# when the admin applies the stack itself, because the creator-admin entry then already names it
# (two entries for one principal fail), and when the role does not exist.
data "aws_iam_roles" "admin" {
  name_regex  = "^${var.admin_role_name}$"
  path_prefix = var.admin_role_path
}

locals {
  admin_applies = strcontains(data.aws_caller_identity.current.arn, ":assumed-role/${var.admin_role_name}/")
  admin_access_entry = (length(data.aws_iam_roles.admin.arns) == 1 && !local.admin_applies) ? {
    admin = {
      principal_arn = one(data.aws_iam_roles.admin.arns)
      policy_associations = {
        admin = {
          policy_arn   = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = { type = "cluster" }
        }
      }
    }
  } : {}
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.cluster_name
  kubernetes_version = var.kubernetes_version

  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.public[*].id

  endpoint_public_access  = true
  endpoint_private_access = false

  enable_irsa                              = true
  enable_cluster_creator_admin_permissions = true

  # Read-only cluster access for the unattended agent: the bootstrap read-only role, with EKS's
  # view policy (get, list and watch on most resources; no secrets, no writes). The agent runs
  # `kubectl get` and `logs` through it and still cannot change anything. Whether the view policy
  # reaches pod logs is unverified; the next live run settles it.
  access_entries = merge({
    readonly = {
      principal_arn = "arn:aws:iam::${var.account_id}:role/ticketscope-readonly"
      policy_associations = {
        view = {
          policy_arn   = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy"
          access_scope = { type = "cluster" }
        }
      }
    }
  }, local.admin_access_entry)

  create_kms_key              = false
  encryption_config           = null
  enabled_log_types           = []
  create_cloudwatch_log_group = false

  iam_role_name            = "ticketscope-env-cluster"
  iam_role_use_name_prefix = false

  addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni = {
      before_compute = true
    }
    aws-ebs-csi-driver = {
      service_account_role_arn = module.ebs_csi_irsa.arn
      # Volumes the driver creates carry the environment tag, for the leftover check.
      configuration_values = jsonencode({
        controller = {
          extraVolumeTags = {
            environment = var.environment
          }
        }
      })
    }
  }

  eks_managed_node_groups = {
    main = {
      ami_type       = "AL2023_ARM_64_STANDARD"
      instance_types = [var.node_instance_type]
      capacity_type  = "ON_DEMAND"

      min_size     = var.node_count
      max_size     = var.node_count
      desired_size = var.node_count

      iam_role_name            = "ticketscope-env-node"
      iam_role_use_name_prefix = false
    }
  }
}
