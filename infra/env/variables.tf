variable "account_id" {
  type        = string
  description = "AWS account id the stack is applied to."

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "account_id must be 12 digits."
  }
}

variable "zone_id" {
  type        = string
  description = "Bootstrap Route53 zone id (bootstrap output zone_id); external-dns may write only there."
}

variable "environment" {
  type        = string
  default     = "eks"
  description = "Value of the `environment` tag on every resource, and the leftover check's filter."
}

variable "cluster_name" {
  type    = string
  default = "ticketscope-env"
}

variable "kubernetes_version" {
  type        = string
  default     = "1.36"
  description = "EKS and the kind node image are both 1.36, on standard support (AD-16)."
}

variable "node_instance_type" {
  type        = string
  default     = "t4g.medium"
  description = "Graviton, so the arm64 images run. t4g.large is the fallback if the pods do not fit."
}

variable "admin_role_name" {
  type        = string
  default     = "AccountFullAccessRole"
  description = "The admin identity's IAM role (Identity Center). It gets cluster-admin access, so the hand teardown needs no manual access entry."
}

variable "admin_role_path" {
  type    = string
  default = "/managed/"
}

variable "node_count" {
  type    = number
  default = 2
}

variable "expires_at" {
  type        = string
  default     = ""
  description = "UTC time (YYYY-MM-DDTHH:MM:SSZ) after which the scheduled env-down sweep may destroy this environment (R4). Empty for a hand-run environment, which then carries no expires_at tag."

  validation {
    condition     = var.expires_at == "" || can(regex("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", var.expires_at))
    error_message = "expires_at must be empty or a UTC time like 2026-11-18T18:00:00Z."
  }
}
