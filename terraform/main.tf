terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Rayansh-Portfolio"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ============================================================================
# CloudFront Secret Generation
# ============================================================================

resource "random_password" "cloudfront_secret" {
  length  = 32
  special = true
}

locals {
  cloudfront_secret = var.cloudfront_secret != "" ? var.cloudfront_secret : random_password.cloudfront_secret.result
}

# ============================================================================
# AWS Parameter Store - Secure Secret Storage
# ============================================================================

resource "aws_ssm_parameter" "redis_secret" {
  name  = "/personal_portfolio/redis_secret"
  type  = "SecureString"
  value = var.redis_secret

  tags = {
    Name = "${var.project_name}-redis-secret"
  }
}

resource "aws_ssm_parameter" "groq_api_key" {
  name  = "/personal_portfolio/groq_api_key"
  type  = "SecureString"
  value = var.groq_api_key

  tags = {
    Name = "${var.project_name}-groq-api-key"
  }
}

resource "aws_ssm_parameter" "google_key" {
  name  = "/personal_portfolio/google_key"
  type  = "SecureString"
  value = var.google_key

  tags = {
    Name = "${var.project_name}-google-key"
  }
}

resource "aws_ssm_parameter" "pinecone_api_key" {
  name  = "/personal_portfolio/pinecone_api_key"
  type  = "SecureString"
  value = var.pinecone_api_key

  tags = {
    Name = "${var.project_name}-pinecone-api-key"
  }
}

resource "aws_ssm_parameter" "mailgun_domain" {
  name  = "/personal_portfolio/mailgun_domain"
  type  = "SecureString"
  value = var.mailgun_domain

  tags = {
    Name = "${var.project_name}-mailgun-domain"
  }
}

resource "aws_ssm_parameter" "mailgun_secret" {
  name  = "/personal_portfolio/mailgun_secret"
  type  = "SecureString"
  value = var.mailgun_secret

  tags = {
    Name = "${var.project_name}-mailgun-secret"
  }
}

resource "aws_ssm_parameter" "cloudfront_secret" {
  name  = "/personal_portfolio/cloudfront_secret"
  type  = "SecureString"
  value = local.cloudfront_secret

  tags = {
    Name = "${var.project_name}-cloudfront-secret"
  }
}

# ============================================================================
# VPC and Networking (Use Default VPC for Free Tier)
# ============================================================================

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ============================================================================
# Security Group for EC2
# ============================================================================

resource "aws_security_group" "backend_sg" {
  name        = "${var.project_name}-backend-sg"
  description = "Security group for portfolio backend API"
  vpc_id      = data.aws_vpc.default.id

  # SSH access (restrict to your IP in production)
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_ips
  }

  # HTTP
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound - allow all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-backend-sg"
  }
}

# ============================================================================
# IAM Role for EC2 (CloudWatch access)
# ============================================================================

module "iam" {
  source       = "./modules/iam"
  project_name = var.project_name
}

# ============================================================================
# EC2 Instance (t3.micro - Free Tier)
# ============================================================================

module "ec2" {
  source = "./modules/ec2"

  project_name        = var.project_name
  instance_type       = var.instance_type
  ami_id              = var.ami_id
  key_name            = var.key_name
  security_group_ids  = [aws_security_group.backend_sg.id]
  subnet_id           = tolist(data.aws_subnets.default.ids)[0]
  iam_instance_profile = module.iam.instance_profile_name

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    environment        = var.environment
    cloudfront_domain  = "" # Empty initially, will update manually
    custom_domain      = var.domain_name
  }))

  depends_on = [
    aws_ssm_parameter.redis_secret,
    aws_ssm_parameter.groq_api_key,
    aws_ssm_parameter.google_key,
    aws_ssm_parameter.pinecone_api_key,
    aws_ssm_parameter.mailgun_domain,
    aws_ssm_parameter.mailgun_secret,
    aws_ssm_parameter.cloudfront_secret
  ]
}

# ============================================================================
# S3 + CloudFront for Frontend (Free Tier)
# ============================================================================

module "s3_cloudfront" {
  source = "./modules/s3-cloudfront"

  project_name      = var.project_name
  domain_name       = var.domain_name
  backend_domain    = module.ec2.public_dns
  cloudfront_secret = local.cloudfront_secret
}

# ============================================================================
# CloudWatch Monitoring
# ============================================================================

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_name = var.project_name
  instance_id  = module.ec2.instance_id
  alert_email  = var.alert_email
}

# ============================================================================
# Outputs
# ============================================================================

output "ec2_public_ip" {
  description = "Public IP of EC2 instance"
  value       = module.ec2.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of EC2 instance"
  value       = module.ec2.public_dns
}

output "s3_bucket_name" {
  description = "S3 bucket for frontend"
  value       = module.s3_cloudfront.bucket_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = module.s3_cloudfront.cloudfront_domain
}

output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh -i ${var.key_name}.pem ubuntu@${module.ec2.public_ip}"
}
