# Deploy Frontend to S3
# This manually deploys the frontend when GitHub Actions doesn't trigger

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Manual Frontend Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get S3 bucket and CloudFront from Terraform
Write-Host "Getting infrastructure info..." -ForegroundColor Yellow
cd terraform
$S3_BUCKET = terraform output -raw frontend_bucket_name
$CF_DOMAIN = terraform output -raw cloudfront_domain_name
$CF_ID = terraform output -raw cloudfront_distribution_id
cd ..

Write-Host "S3 Bucket: $S3_BUCKET" -ForegroundColor Green
Write-Host "CloudFront: $CF_DOMAIN" -ForegroundColor Green
Write-Host ""

# Check if dist exists
if (-not (Test-Path "project/dist")) {
    Write-Host "Building frontend..." -ForegroundColor Yellow
    cd project
    npm install --legacy-peer-deps
    npm run build
    cd ..
    Write-Host "Build complete!" -ForegroundColor Green
} else {
    Write-Host "Using existing build in project/dist" -ForegroundColor Green
}

# Upload to S3
Write-Host ""
Write-Host "Uploading to S3..." -ForegroundColor Yellow

# Upload all files except HTML with cache
aws s3 sync project/dist s3://$S3_BUCKET/ `
  --delete `
  --cache-control "public, max-age=31536000" `
  --exclude "*.html"

# Upload HTML files without cache
aws s3 sync project/dist s3://$S3_BUCKET/ `
  --cache-control "public, max-age=0, must-revalidate" `
  --exclude "*" `
  --include "*.html"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Upload complete!" -ForegroundColor Green
} else {
    Write-Host "Upload failed!" -ForegroundColor Red
    exit 1
}

# Invalidate CloudFront
Write-Host ""
Write-Host "Invalidating CloudFront cache..." -ForegroundColor Yellow
aws cloudfront create-invalidation --distribution-id $CF_ID --paths "/*"

if ($LASTEXITCODE -eq 0) {
    Write-Host "CloudFront invalidated!" -ForegroundColor Green
} else {
    Write-Host "Invalidation failed!" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete! 🎉" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend URL: https://$CF_DOMAIN" -ForegroundColor Cyan
Write-Host ""
Write-Host "Wait 1-2 minutes for CloudFront to update, then visit your site!" -ForegroundColor Yellow
Write-Host ""
