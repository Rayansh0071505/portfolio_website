variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"  # Free tier available in all regions
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "personal-portfolio"
}

variable "instance_type" {
  description = "EC2 instance type (FREE TIER: t3.micro or t2.micro)"
  type        = string
  default     = "t3.micro"
}

variable "ami_id" {
  description = "AMI ID for EC2 instance (Ubuntu 22.04 LTS)"
  type        = string
  # Default: Ubuntu 22.04 LTS for us-east-1
  # Find latest AMI: aws ec2 describe-images --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" --query 'Images[*].[ImageId,CreationDate]' --output table
  default = "ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS (update for your region)
}

variable "key_name" {
  description = "SSH key pair name (create this in AWS EC2 console first)"
  type        = string
}

variable "ssh_allowed_ips" {
  description = "List of IP addresses allowed for SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # WARNING: Restrict to your IP in production!
}

variable "domain_name" {
  description = "Custom domain name (optional)"
  type        = string
  default     = ""
}

variable "alert_email" {
  description = "Email for CloudWatch alerts"
  type        = string
}

# ============================================================================
# Application Secrets (Store in terraform.tfvars - NOT in git!)
# ============================================================================

variable "redis_secret" {
  description = "Redis connection string"
  type        = string
  sensitive   = true
}

variable "groq_api_key" {
  description = "Groq API key"
  type        = string
  sensitive   = true
}

variable "google_key" {
  description = "Google Cloud key (base64)"
  type        = string
  sensitive   = true
}

variable "pinecone_api_key" {
  description = "Pinecone API key"
  type        = string
  sensitive   = true
}

variable "mailgun_domain" {
  description = "Mailgun domain"
  type        = string
  sensitive   = true
}

variable "mailgun_secret" {
  description = "Mailgun API key"
  type        = string
  sensitive   = true
}

variable "cloudfront_secret" {
  description = "CloudFront custom header secret for origin verification"
  type        = string
  sensitive   = true
  default     = ""  # Auto-generated if not provided
}
