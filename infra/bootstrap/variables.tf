# No defaults: the values come from an untracked terraform.tfvars (see README.md).

variable "account_id" {
  type        = string
  description = "AWS account id the stack is applied to."

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "account_id must be 12 digits."
  }
}

variable "alert_email" {
  type        = string
  description = "Address the budget alarm notifies."
}

variable "domain" {
  type        = string
  description = "Registered domain the stack hosts a Route53 zone for."
}

variable "hostname" {
  type        = string
  description = "The fixed hostname the certificate covers: the domain or a subdomain of it."

  validation {
    condition     = var.hostname == var.domain || endswith(var.hostname, ".${var.domain}")
    error_message = "hostname must be the domain or a subdomain of it."
  }
}

variable "admin_principal_arn" {
  type        = string
  description = <<-EOT
    Exact ARN of the person's admin identity, trusted to assume the read-only role: the
    Identity Center role (with its path, e.g. role/managed/<name>), from
    `aws iam get-role --role-name <name> --query Role.Arn`.
  EOT

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:(role|user)/[^*?]+$", var.admin_principal_arn))
    error_message = "admin_principal_arn must be one exact IAM role or user ARN, with no wildcard."
  }
}

variable "repo" {
  type        = string
  description = <<-EOT
    The repository exactly as it appears in the OIDC `sub` claim, between `repo:` and
    `:environment:eks`. A repo with immutable subjects uses `owner@<owner id>/name@<repo id>`;
    otherwise `owner/name`. Read it from the diagnostic step in aws-oidc-check.yml.
  EOT

  validation {
    condition     = !can(regex("[*?]", var.repo))
    error_message = "repo must be the exact subject text, with no wildcard."
  }
}
