# Security Group for EC2 Backend
resource "aws_security_group" "backend" {
  name_prefix = "${var.project_name}-backend-"
  description = "Security group for backend API server"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-backend-sg"
  }
}

# Allow SSH from anywhere (restrict this in production)
resource "aws_vpc_security_group_ingress_rule" "backend_ssh" {
  security_group_id = aws_security_group.backend.id
  description       = "SSH from anywhere - RESTRICT THIS"

  from_port   = 22
  to_port     = 22
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"

  tags = {
    Name = "allow-ssh"
  }
}

# Allow HTTP traffic (for Let's Encrypt certificate validation if needed)
resource "aws_vpc_security_group_ingress_rule" "backend_http" {
  security_group_id = aws_security_group.backend.id
  description       = "HTTP from CloudFront"

  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"

  tags = {
    Name = "allow-http-cloudfront"
  }
}

# Allow Backend API Port - CloudFront Only
resource "aws_vpc_security_group_ingress_rule" "backend_api_cloudfront" {
  security_group_id = aws_security_group.backend.id
  description       = "Backend API port from CloudFront"

  from_port   = var.backend_port
  to_port     = var.backend_port
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"  # CloudFront uses dynamic IPs, backend uses custom header verification

  tags = {
    Name = "allow-backend-port"
  }
}

# Allow outbound traffic (internet access)
resource "aws_vpc_security_group_egress_rule" "backend_outbound" {
  security_group_id = aws_security_group.backend.id
  description       = "Allow all outbound traffic"

  ip_protocol = "-1"
  cidr_ipv4   = "0.0.0.0/0"

  tags = {
    Name = "allow-outbound"
  }
}

# Security Group for Redis (if using ElastiCache)
resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-"
  description = "Security group for Redis"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-redis-sg"
  }
}

# Allow Redis from Backend
resource "aws_vpc_security_group_ingress_rule" "redis_from_backend" {
  security_group_id = aws_security_group.redis.id
  description       = "Redis port from backend"

  from_port                    = 6379
  to_port                      = 6379
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.backend.id

  tags = {
    Name = "allow-redis-backend"
  }
}

# Allow outbound from Redis
resource "aws_vpc_security_group_egress_rule" "redis_outbound" {
  security_group_id = aws_security_group.redis.id
  description       = "Allow outbound from Redis"

  ip_protocol = "-1"
  cidr_ipv4   = "0.0.0.0/0"

  tags = {
    Name = "redis-outbound"
  }
}
