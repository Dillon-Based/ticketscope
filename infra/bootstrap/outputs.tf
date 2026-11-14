output "state_bucket" {
  value = aws_s3_bucket.state.bucket
}

output "certificate_arn" {
  value = aws_acm_certificate_validation.main.certificate_arn
}

output "zone_id" {
  value = data.aws_route53_zone.main.zone_id
}

output "name_servers" {
  value = data.aws_route53_zone.main.name_servers
}

output "deploy_role_arn" {
  value = aws_iam_role.deploy.arn
}

output "readonly_role_arn" {
  value = aws_iam_role.readonly.arn
}

output "ecr_repository_urls" {
  value = { for k, r in aws_ecr_repository.image : k => r.repository_url }
}
