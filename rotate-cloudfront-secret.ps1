# Rotate CloudFront Secret (Simple Fix)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rotate CloudFront Secret" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Generate new CloudFront secret
Write-Host "Step 1: Generating new CloudFront secret..." -ForegroundColor Yellow
$NewCloudFrontSecret = -join ((1..32) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 256) })
Write-Host "New secret: $NewCloudFrontSecret" -ForegroundColor Green
Write-Host ""

# Step 2: Update terraform.tfvars
Write-Host "Step 2: Updating terraform.tfvars..." -ForegroundColor Yellow
Set-Location terraform

# Read current tfvars
$TfvarsContent = Get-Content terraform.tfvars -Raw

# Replace cloudfront_secret line
$TfvarsContent = $TfvarsContent -replace 'cloudfront_secret\s*=\s*"[^"]*"', "cloudfront_secret = `"$NewCloudFrontSecret`""

# Write back
$TfvarsContent | Out-File -FilePath terraform.tfvars -Encoding UTF8 -NoNewline
Write-Host "✅ terraform.tfvars updated" -ForegroundColor Green
Write-Host ""

# Step 3: Apply Terraform
Write-Host "Step 3: Applying Terraform to update CloudFront..." -ForegroundColor Yellow
terraform apply -auto-approve

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ CloudFront updated with new secret" -ForegroundColor Green
} else {
    Write-Host "❌ Terraform apply failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Set-Location ..
Write-Host ""

# Step 4: Update backend .env in Parameter Store
Write-Host "Step 4: Updating backend .env in Parameter Store..." -ForegroundColor Yellow

# Get current .env
$CurrentEnv = aws ssm get-parameter --name "/rayansh_portfolio/env" --region us-east-1 --query 'Parameter.Value' --output text

# Replace CLOUDFRONT_SECRET line
$NewEnv = $CurrentEnv -replace 'CLOUDFRONT_SECRET=.*', "CLOUDFRONT_SECRET=$NewCloudFrontSecret"

# Save to temp file
$NewEnv | Out-File -FilePath .env.temp -Encoding UTF8 -NoNewline

# Upload to Parameter Store
aws ssm put-parameter --name "/rayansh_portfolio/env" --value (Get-Content .env.temp -Raw) --type SecureString --overwrite --region us-east-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Parameter Store updated" -ForegroundColor Green
} else {
    Write-Host "❌ Parameter Store update failed" -ForegroundColor Red
}

Remove-Item .env.temp
Write-Host ""

# Step 5: Redeploy backend
Write-Host "Step 5: Redeploying backend with new secret..." -ForegroundColor Yellow
powershell.exe -ExecutionPolicy Bypass -File redeploy-backend-fixed.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ CloudFront Secret Rotated!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "- New CloudFront secret: $NewCloudFrontSecret" -ForegroundColor White
Write-Host "- Updated terraform.tfvars (local only - NOT committed)" -ForegroundColor White
Write-Host "- Updated CloudFront distribution" -ForegroundColor White
Write-Host "- Updated backend .env in Parameter Store" -ForegroundColor White
Write-Host "- Backend redeployed" -ForegroundColor White
Write-Host ""
Write-Host "⚠️ Note: Old secret is still in GitHub history, but it won't work anymore." -ForegroundColor Yellow
Write-Host "CloudFront will only accept requests with the new secret." -ForegroundColor Yellow
Write-Host ""
Write-Host "Test your app:" -ForegroundColor Cyan
$CF_DOMAIN = terraform output -raw cloudfront_domain_name -Path terraform
Write-Host "https://$CF_DOMAIN" -ForegroundColor White
