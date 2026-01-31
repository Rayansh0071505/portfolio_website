# Backend EC2 outputs
output "backend_public_ip" {
  description = "Public IP of the backend EC2 instance"
  value       = aws_eip.backend.public_ip
}

output "backend_instance_id" {
  description = "Instance ID of the backend"
  value       = aws_instance.backend.id
}

output "backend_private_ip" {
  description = "Private IP of the backend EC2 instance"
  value       = aws_instance.backend.private_ip
}

output "backend_public_dns" {
  description = "Public DNS hostname of the backend EC2 instance"
  value       = aws_instance.backend.public_dns
}

output "backend_security_group_id" {
  description = "Security group ID for backend"
  value       = aws_security_group.backend.id
}

# S3 outputs
output "frontend_bucket_name" {
  description = "Name of the frontend S3 bucket"
  value       = aws_s3_bucket.frontend.bucket
}

output "frontend_bucket_region" {
  description = "Region of the frontend bucket"
  value       = aws_s3_bucket.frontend.region
}

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = aws_s3_bucket.logs.bucket
}

output "assets_bucket_name" {
  description = "Name of the assets S3 bucket"
  value       = aws_s3_bucket.assets.bucket
}

# CloudFront outputs
output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = var.cloudfront_enabled ? aws_cloudfront_distribution.frontend[0].domain_name : null
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = var.cloudfront_enabled ? aws_cloudfront_distribution.frontend[0].id : null
}

output "cloudfront_etag" {
  description = "CloudFront distribution etag"
  value       = var.cloudfront_enabled ? aws_cloudfront_distribution.frontend[0].etag : null
}

# Backend configuration
output "backend_api_endpoint" {
  description = "Backend API endpoint"
  value       = "http://${aws_eip.backend.public_ip}:${var.backend_port}"
}

output "backend_health_check_url" {
  description = "Health check URL for backend"
  value       = "http://${aws_eip.backend.public_ip}:${var.backend_port}/"
}

# VPC outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Public subnet ID"
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "Private subnet ID"
  value       = aws_subnet.private.id
}

# Redis security group
output "redis_security_group_id" {
  description = "Security group ID for Redis"
  value       = aws_security_group.redis.id
}

# Logs group
output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.backend.name
}

# Custom domain info
output "custom_domain_certificate_arn" {
  description = "ACM certificate ARN for custom domain"
  value       = var.custom_domain != "" ? aws_acm_certificate.frontend[0].arn : null
}

# SSH connection info
output "ssh_command" {
  description = "SSH command to connect to backend"
  value       = "ssh -i demo.pem ec2-user@${aws_eip.backend.public_ip}"
}

# Important configuration for environment variables
output "parameter_store_path" {
  description = "Path for environment variables in Parameter Store"
  value       = "/${var.project_name}/env"
}

# ElastiCache Redis outputs
output "redis_endpoint" {
  description = "ElastiCache Redis endpoint for semantic caching"
  value       = var.redis_enabled ? aws_elasticache_cluster.semantic_cache[0].cache_nodes[0].address : null
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = var.redis_enabled ? aws_elasticache_cluster.semantic_cache[0].cache_nodes[0].port : null
}

output "redis_connection_string" {
  description = "Full Redis connection string for LangChain"
  value       = var.redis_enabled ? "redis://${aws_elasticache_cluster.semantic_cache[0].cache_nodes[0].address}:${aws_elasticache_cluster.semantic_cache[0].cache_nodes[0].port}" : null
  sensitive   = false
}
