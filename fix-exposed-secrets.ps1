# Fix Exposed Secrets in Git History
Write-Host "========================================" -ForegroundColor Red
Write-Host "SECURITY FIX: Remove Exposed Secrets" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

Write-Host "WARNING: This will rewrite Git history!" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to cancel, or Enter to continue..." -ForegroundColor Yellow
Read-Host

# Step 1: Remove terraform.tfvars from Git history
Write-Host ""
Write-Host "Step 1: Removing terraform.tfvars from Git history..." -ForegroundColor Cyan
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch terraform/terraform.tfvars" --prune-empty --tag-name-filter cat -- --all

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to remove file from history" -ForegroundColor Red
    exit 1
}

Write-Host "✅ File removed from Git history" -ForegroundColor Green

# Step 2: Generate NEW CloudFront secret
Write-Host ""
Write-Host "Step 2: Generating NEW CloudFront secret..." -ForegroundColor Cyan
$NewCloudFrontSecret = -join ((1..32) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 256) })
Write-Host "New secret generated: $NewCloudFrontSecret" -ForegroundColor Green

# Step 3: Update terraform.tfvars with new secret
Write-Host ""
Write-Host "Step 3: Updating terraform.tfvars with new secret..." -ForegroundColor Cyan

$AWS_ACCOUNT_ID = aws sts get-caller-identity --query Account --output text

$TfvarsContent = @"
# Terraform Variables
# This file contains sensitive data and should NEVER be committed to Git
# It is already in .gitignore

project_name = "rayansh_portfolio"
aws_region = "us-east-1"
environment = "production"

# EC2
instance_type = "t3.micro"
key_pair_name = "demo"

# Docker
docker_image = "$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rayansh_portfolio:latest"

# CloudFront Security - NEW SECRET (old one was exposed)
cloudfront_secret = "$NewCloudFrontSecret"

# Backend
backend_port = 8080
"@

Set-Location terraform
$TfvarsContent | Out-File -FilePath terraform.tfvars -Encoding UTF8
Write-Host "✅ terraform.tfvars updated" -ForegroundColor Green

# Step 4: Apply Terraform to update CloudFront secret
Write-Host ""
Write-Host "Step 4: Updating CloudFront with new secret..." -ForegroundColor Cyan
Write-Host "This will update the CloudFront distribution with the new secret header." -ForegroundColor Yellow
Write-Host ""

terraform plan -out=tfplan

Write-Host ""
Write-Host "Review the plan above. Press Enter to apply, or Ctrl+C to cancel..." -ForegroundColor Yellow
Read-Host

terraform apply tfplan

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Terraform applied successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Terraform apply failed" -ForegroundColor Red
    exit 1
}

Remove-Item tfplan

Set-Location ..

# Step 5: Force push to GitHub
Write-Host ""
Write-Host "Step 5: Force pushing to GitHub..." -ForegroundColor Cyan
Write-Host "WARNING: This will overwrite remote history!" -ForegroundColor Red
Write-Host "Press Enter to continue, or Ctrl+C to cancel..." -ForegroundColor Yellow
Read-Host

git push origin master --force

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Pushed to GitHub successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Push failed" -ForegroundColor Red
    exit 1
}

# Step 6: Redeploy backend with new secret
Write-Host ""
Write-Host "Step 6: Redeploying backend..." -ForegroundColor Cyan
Write-Host "Backend needs to restart to use the new CloudFront secret." -ForegroundColor Yellow

powershell.exe -ExecutionPolicy Bypass -File redeploy-backend-fixed.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ SECURITY FIX COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "- Removed terraform.tfvars from Git history" -ForegroundColor White
Write-Host "- Generated new CloudFront secret" -ForegroundColor White
Write-Host "- Updated CloudFront distribution" -ForegroundColor White
Write-Host "- Force pushed to GitHub (cleaned history)" -ForegroundColor White
Write-Host "- Redeployed backend with new secret" -ForegroundColor White
Write-Host ""
Write-Host "⚠️ Important: If anyone cloned your repo before, they may still have the old secret in their local history." -ForegroundColor Yellow
Write-Host "The old secret is now useless since CloudFront uses the new one." -ForegroundColor Yellow
