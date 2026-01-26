# Automatically upload frontend files to S3 (if built)

locals {
  # Frontend build directory
  frontend_dist_path = "${path.root}/../project/dist"

  # Check if dist folder exists
  frontend_exists = fileexists("${path.root}/../project/dist/index.html")

  # Get all files in dist folder (only if exists)
  frontend_files = local.frontend_exists ? fileset(local.frontend_dist_path, "**") : []

  # MIME types mapping
  mime_types = {
    "html" = "text/html"
    "css"  = "text/css"
    "js"   = "application/javascript"
    "json" = "application/json"
    "png"  = "image/png"
    "jpg"  = "image/jpeg"
    "jpeg" = "image/jpeg"
    "gif"  = "image/gif"
    "svg"  = "image/svg+xml"
    "ico"  = "image/x-icon"
    "woff" = "font/woff"
    "woff2" = "font/woff2"
    "ttf"  = "font/ttf"
    "eot"  = "application/vnd.ms-fontobject"
  }
}

# Upload each frontend file to S3 (only if frontend is built)
resource "aws_s3_object" "frontend_files" {
  for_each = toset([for f in local.frontend_files : f if !endswith(f, "index.html")])

  bucket = aws_s3_bucket.frontend.id
  key    = each.value
  source = "${local.frontend_dist_path}/${each.value}"

  # Set content type based on file extension
  content_type = lookup(
    local.mime_types,
    reverse(split(".", each.value))[0],
    "application/octet-stream"
  )

  # Use file hash to trigger updates when content changes
  etag = filemd5("${local.frontend_dist_path}/${each.value}")

  # Cache control headers
  cache_control = "public, max-age=31536000"  # 1 year for static assets
}

# Special handling for index.html (no cache) - only if exists
resource "aws_s3_object" "index_html" {
  count = local.frontend_exists ? 1 : 0

  bucket = aws_s3_bucket.frontend.id
  key    = "index.html"
  source = "${local.frontend_dist_path}/index.html"

  content_type  = "text/html"
  etag          = filemd5("${local.frontend_dist_path}/index.html")
  cache_control = "no-cache, no-store, must-revalidate"  # Always check for updates
}
