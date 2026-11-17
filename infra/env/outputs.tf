output "cluster_name" {
  value = module.eks.cluster_name
}

output "region" {
  value = local.region
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "lb_controller_role_arn" {
  value = module.lb_controller_irsa.arn
}

output "external_dns_role_arn" {
  value = module.external_dns_irsa.arn
}

output "environment" {
  value = var.environment
}
