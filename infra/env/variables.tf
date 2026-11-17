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

variable "node_count" {
  type    = number
  default = 2
}
