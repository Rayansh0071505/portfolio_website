variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "rayansh-ai-portfolio"
}

# EC2 Configuration
variable "instance_type" {
  description = "EC2 instance type (free tier: t3.micro, t3.small, m7i-flex.large)"
  type        = string
  default     = "m7i-flex.large"  # 8 GiB RAM for embeddings model
}

variable "key_pair_name" {
  description = "EC2 Key Pair name for SSH access"
  type        = string
}

variable "instance_root_volume_size" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 30
}

# VPC Configuration
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "Private subnet CIDR"
  type        = string
  default     = "10.0.2.0/24"
}

# S3 Configuration
variable "bucket_prefix" {
  description = "Prefix for S3 bucket name"
  type        = string
  default     = "rayansh-ai"
}

variable "enable_versioning" {
  description = "Enable S3 versioning"
  type        = bool
  default     = true
}

# CloudFront Configuration
variable "cloudfront_enabled" {
  description = "Enable CloudFront distribution"
  type        = bool
  default     = true
}

variable "custom_domain" {
  description = "Custom domain for CloudFront (optional)"
  type        = string
  default     = ""
}

# Backend Configuration
variable "backend_port" {
  description = "Backend API port"
  type        = number
  default     = 8080
}

variable "docker_registry" {
  description = "Docker registry URL"
  type        = string
  default     = ""
}

variable "docker_image" {
  description = "Docker image name and tag"
  type        = string
  default     = "rayansh-ai:latest"
}

# CORS Configuration
variable "allowed_origins" {
  description = "Allowed CORS origins for backend"
  type        = list(string)
  default     = []
}

variable "cloudfront_secret" {
  description = "Secret header for CloudFront to backend verification"
  type        = string
  sensitive   = true
}

# ElastiCache Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type (free tier: cache.t3.micro, cache.t4g.micro)"
  type        = string
  default     = "cache.t4g.micro"  # 0.5 GiB RAM, ARM-based (cheaper), good for caching
}

variable "redis_enabled" {
  description = "Enable ElastiCache Redis for semantic caching"
  type        = bool
  default     = true
}
