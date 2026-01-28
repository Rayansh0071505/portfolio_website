# S3 Bucket for Frontend
resource "aws_s3_bucket" "frontend" {
  bucket_prefix = "${var.bucket_prefix}-frontend-"

  tags = {
    Name = "${var.project_name}-frontend"
  }
}

# Block all public access (CloudFront will serve through OAI)
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable versioning for frontend bucket
resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# Enable encryption for frontend bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket for Logs
resource "aws_s3_bucket" "logs" {
  bucket_prefix = "${var.bucket_prefix}-logs-"

  tags = {
    Name = "${var.project_name}-logs"
  }
}

# Enable ACL for logs bucket (required by CloudFront)
resource "aws_s3_bucket_ownership_controls" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "logs" {
  bucket = aws_s3_bucket.logs.id
  acl    = "log-delivery-write"

  depends_on = [aws_s3_bucket_ownership_controls.logs]
}

# Block public access to logs bucket
resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = false
  block_public_policy     = true
  ignore_public_acls      = false
  restrict_public_buckets = true
}

# Enable versioning for logs bucket
resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

# CloudFront Origin Access Identity
resource "aws_cloudfront_origin_access_identity" "frontend" {
  comment = "OAI for ${var.project_name} frontend"
}

# S3 Bucket Policy - Allow CloudFront OAI to read
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudFrontAccess"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.frontend.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
      },
      {
        Sid    = "CloudFrontListBucket"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.frontend.iam_arn
        }
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.frontend.arn
      }
    ]
  })
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend" {
  count   = var.cloudfront_enabled ? 1 : 0
  enabled = true

  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = "S3Frontend"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.frontend.cloudfront_access_identity_path
    }
  }

  # Backend API Origin
  # Note: CloudFront requires a DNS name, not an IP address
  origin {
    domain_name = aws_instance.backend.public_dns
    origin_id   = "BackendAPI"
    origin_path = ""

    custom_origin_config {
      http_port              = var.backend_port
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    custom_header {
      name  = "X-CloudFront-Secret"
      value = var.cloudfront_secret
    }
  }

  # Frontend S3 Cache Behavior
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3Frontend"

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  # API Cache Behavior
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "BackendAPI"

    forwarded_values {
      query_string = true
      headers      = [
        "Content-Type",
        "Authorization",
        "Origin"
      ]

      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "https-only"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
    compress               = false
  }

  # Restrict locations to free tier regions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # HTTPS viewer protocol
  viewer_certificate {
    cloudfront_default_certificate = var.custom_domain == "" ? true : false
    acm_certificate_arn            = var.custom_domain != "" ? aws_acm_certificate.frontend[0].arn : null
    ssl_support_method             = var.custom_domain != "" ? "sni-only" : null
    minimum_protocol_version       = "TLSv1.2_2021"
  }

  # Custom domain alias
  aliases = var.custom_domain != "" ? [var.custom_domain] : []

  # Logging
  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.logs.bucket_regional_domain_name
    prefix          = "cloudfront-logs"
  }

  # Comment is used by GitHub Actions to identify this distribution
  comment = "${var.project_name}-cdn"

  tags = {
    Name = "${var.project_name}-cdn"
  }

  depends_on = [aws_eip.backend]
}

# ACM Certificate for custom domain (if provided)
resource "aws_acm_certificate" "frontend" {
  count             = var.custom_domain != "" ? 1 : 0
  domain_name       = var.custom_domain
  validation_method = "DNS"

  tags = {
    Name = "${var.project_name}-cert"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# S3 Bucket for static assets caching
resource "aws_s3_bucket" "assets" {
  bucket_prefix = "${var.bucket_prefix}-assets-"

  tags = {
    Name = "${var.project_name}-assets"
  }
}

resource "aws_s3_bucket_versioning" "assets" {
  bucket = aws_s3_bucket.assets.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket = aws_s3_bucket.assets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy to delete old versions
resource "aws_s3_bucket_lifecycle_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
