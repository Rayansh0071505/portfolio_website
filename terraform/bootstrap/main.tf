# Bootstrap Terraform - Creates S3 bucket for Terraform state
# Run this ONCE before main infrastructure

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
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "rayansh_portfolio"
}

# Random ID for unique bucket name
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 Bucket for Terraform State
# Note: S3 bucket names cannot contain underscores, only hyphens
resource "aws_s3_bucket" "terraform_state" {
  bucket = "rayansh-portfolio-tf-state-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "rayansh-portfolio-terraform-state"
    Environment = "production"
    ManagedBy   = "Terraform Bootstrap"
  }
}

# Enable versioning
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Output bucket name
output "terraform_state_bucket" {
  description = "S3 bucket name for Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "bucket_arn" {
  description = "ARN of the Terraform state bucket"
  value       = aws_s3_bucket.terraform_state.arn
}

output "next_steps" {
  description = "Next steps"
  value       = <<-EOT

  ✅ Terraform state bucket created: ${aws_s3_bucket.terraform_state.bucket}

  Next steps:
  1. Add this to GitHub Secret: TERRAFORM_STATE_BUCKET = ${aws_s3_bucket.terraform_state.bucket}
  2. Create file: terraform/backend.tf with this content:

     terraform {
       backend "s3" {
         bucket  = "${aws_s3_bucket.terraform_state.bucket}"
         key     = "infrastructure.tfstate"
         region  = "${var.aws_region}"
         encrypt = true
       }
     }

  3. Run main Terraform:
     cd ../
     terraform init
     terraform plan -out=tfplan
     terraform apply tfplan

  EOT
}
