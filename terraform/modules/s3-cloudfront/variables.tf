variable "project_name" {
  description = "Project name"
  type        = string
}

variable "domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for custom domain (must be in us-east-1)"
  type        = string
  default     = ""
}

variable "backend_domain" {
  description = "Backend API domain or IP"
  type        = string
  default     = ""
}

variable "cloudfront_secret" {
  description = "Secret for CloudFront custom header (origin verification)"
  type        = string
  sensitive   = true
}
