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
  description = "Registered domain with a Route53 hosted zone; also the fixed hostname."
}

variable "admin_principal_arn" {
  type        = string
  description = "IAM principal of the person's admin identity; trusted to assume the read-only role."
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
