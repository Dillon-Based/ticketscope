# EKS 1.36 on standard support, a managed node group of Graviton nodes, no Auto Mode, no
# Fargate (AD-16). The API endpoint is public and IAM-authenticated. No customer-managed KMS
# key and no control-plane logging (AD-23).
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
