# Upload backend/.env to AWS Parameter Store
# PowerShell script for Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Upload .env to AWS Parameter Store" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "Error: backend\.env not found!" -ForegroundColor Red
    Write-Host "Run setup-windows.ps1 first to create it." -ForegroundColor Yellow
    exit 1
}

# Read .env file
Write-Host "Reading backend\.env..." -ForegroundColor Yellow
$EnvContent = Get-Content -Path "backend\.env" -Raw

# Check if content is not empty
if ([string]::IsNullOrWhiteSpace($EnvContent)) {
    Write-Host "Error: backend\.env is empty!" -ForegroundColor Red
    Write-Host "Edit backend\.env and add your API keys first." -ForegroundColor Yellow
    exit 1
}

# Upload to Parameter Store
Write-Host "Uploading to AWS Parameter Store..." -ForegroundColor Yellow
Write-Host "Parameter name: /rayansh_portfolio/env" -ForegroundColor Cyan

try {
    aws ssm put-parameter `
        --name "/rayansh_portfolio/env" `
        --value $EnvContent `
        --type "String" `
        --region us-east-1 `
        --overwrite

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Success! .env uploaded to Parameter Store" -ForegroundColor Green
        Write-Host ""
        Write-Host "Parameter: /rayansh_portfolio/env" -ForegroundColor Cyan
        Write-Host "Region: us-east-1" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "EC2 will automatically pull this on startup." -ForegroundColor Yellow
    } else {
        Write-Host ""
        Write-Host "Error uploading to Parameter Store" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure:" -ForegroundColor Yellow
    Write-Host "1. AWS CLI is configured (run: aws configure)" -ForegroundColor White
    Write-Host "2. You have permissions for SSM Parameter Store" -ForegroundColor White
    exit 1
}

# Verify upload
Write-Host "Verifying upload..." -ForegroundColor Yellow
try {
    $Param = aws ssm get-parameter --name "/rayansh_portfolio/env" --region us-east-1 --query 'Parameter.ARN' --output text
    Write-Host "Verified! Parameter ARN: $Param" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not verify upload" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done! ✅" -ForegroundColor Green
Write-Host ""
