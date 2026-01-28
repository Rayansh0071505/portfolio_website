# Windows PowerShell Setup Script for rayansh_portfolio
# Run this script in PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "rayansh_portfolio Setup - Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create .env file
Write-Host "[Step 1/7] Creating backend/.env file..." -ForegroundColor Yellow
if (Test-Path "backend\.env") {
    Write-Host "backend\.env already exists. Skipping..." -ForegroundColor Green
} else {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "Created backend\.env from template" -ForegroundColor Green
    Write-Host "❗ IMPORTANT: Edit backend\.env and add your API keys!" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter after you've edited backend\.env with your API keys"
}

# Step 2: Generate CloudFront Secret
Write-Host ""
Write-Host "[Step 2/7] Generating CloudFront Secret..." -ForegroundColor Yellow
$CloudFrontSecret = -join ((1..32) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 256) })
Write-Host "CloudFront Secret: $CloudFrontSecret" -ForegroundColor Green
Write-Host "❗ Save this! Add to GitHub Secret: CLOUDFRONT_SECRET" -ForegroundColor Red
Set-Content -Path "cloudfront_secret.txt" -Value $CloudFrontSecret
Write-Host "Also saved to: cloudfront_secret.txt" -ForegroundColor Green

# Step 3: Get AWS Account ID
Write-Host ""
Write-Host "[Step 3/7] Getting AWS Account ID..." -ForegroundColor Yellow
try {
    $AccountId = aws sts get-caller-identity --query Account --output text
    Write-Host "AWS Account ID: $AccountId" -ForegroundColor Green
} catch {
    Write-Host "Error getting Account ID. Make sure AWS CLI is configured." -ForegroundColor Red
    Write-Host "Run: aws configure" -ForegroundColor Yellow
    exit 1
}

# Step 4: Create ECR Repository
Write-Host ""
Write-Host "[Step 4/7] Creating ECR Repository..." -ForegroundColor Yellow
try {
    aws ecr create-repository --repository-name rayansh_portfolio --region us-east-1 2>$null
    Write-Host "ECR repository created: rayansh_portfolio" -ForegroundColor Green
} catch {
    Write-Host "ECR repository might already exist (this is OK)" -ForegroundColor Yellow
}

# Step 5: Bootstrap Terraform (create state bucket)
Write-Host ""
Write-Host "[Step 5/7] Creating Terraform State Bucket..." -ForegroundColor Yellow
Write-Host "Running bootstrap Terraform..." -ForegroundColor Cyan

Set-Location "terraform\bootstrap"
terraform init
terraform apply -auto-approve

if ($LASTEXITCODE -eq 0) {
    $StateBucket = terraform output -raw terraform_state_bucket
    Write-Host ""
    Write-Host "Terraform state bucket created: $StateBucket" -ForegroundColor Green
    Set-Content -Path "..\..\terraform_state_bucket.txt" -Value $StateBucket
    Write-Host "Saved to: terraform_state_bucket.txt" -ForegroundColor Green
} else {
    Write-Host "Error creating Terraform state bucket" -ForegroundColor Red
    Set-Location "..\..\"
    exit 1
}

Set-Location "..\..\"

# Step 6: Create terraform.tfvars
Write-Host ""
Write-Host "[Step 6/7] Creating terraform.tfvars..." -ForegroundColor Yellow

$TfvarsContent = @"
aws_region  = "us-east-1"
environment = "production"
project_name = "rayansh_portfolio"
instance_type = "t3.micro"
key_pair_name = "demo"
instance_root_volume_size = 30
vpc_cidr = "10.0.0.0/16"
public_subnet_cidr = "10.0.1.0/24"
private_subnet_cidr = "10.0.2.0/24"
bucket_prefix = "rayansh-portfolio"
enable_versioning = true
cloudfront_enabled = true
custom_domain = ""
backend_port = 8080
docker_image = "$AccountId.dkr.ecr.us-east-1.amazonaws.com/rayansh_portfolio:latest"
cloudfront_secret = "$CloudFrontSecret"
allowed_origins = []
"@

Set-Content -Path "terraform\terraform.tfvars" -Value $TfvarsContent
Write-Host "Created terraform\terraform.tfvars" -ForegroundColor Green

# Step 7: Create backend.tf
Write-Host ""
Write-Host "[Step 7/7] Creating terraform\backend.tf..." -ForegroundColor Yellow

$BackendContent = @"
terraform {
  backend "s3" {
    bucket  = "$StateBucket"
    key     = "infrastructure.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}
"@

Set-Content -Path "terraform\backend.tf" -Value $BackendContent
Write-Host "Created terraform\backend.tf" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete! 🎉" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated files:" -ForegroundColor Yellow
Write-Host "  - backend\.env (EDIT THIS WITH YOUR API KEYS!)" -ForegroundColor White
Write-Host "  - cloudfront_secret.txt" -ForegroundColor White
Write-Host "  - terraform_state_bucket.txt" -ForegroundColor White
Write-Host "  - terraform\terraform.tfvars" -ForegroundColor White
Write-Host "  - terraform\backend.tf" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Edit backend\.env with your API keys" -ForegroundColor White
Write-Host "2. Upload .env to AWS Parameter Store:" -ForegroundColor White
Write-Host "   .\upload-env.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Add GitHub Secrets (copy from generated files):" -ForegroundColor White
Write-Host "   - AWS_ACCESS_KEY_ID" -ForegroundColor White
Write-Host "   - AWS_SECRET_ACCESS_KEY" -ForegroundColor White
Write-Host "   - AWS_REGION = us-east-1" -ForegroundColor White
Write-Host "   - EC2_KEY_PAIR_NAME = demo" -ForegroundColor White
Write-Host "   - EC2_SSH_PRIVATE_KEY (content of demo.pem)" -ForegroundColor White
Write-Host "   - CLOUDFRONT_SECRET (from cloudfront_secret.txt)" -ForegroundColor Cyan
Write-Host "   - TERRAFORM_STATE_BUCKET (from terraform_state_bucket.txt)" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Run Terraform:" -ForegroundColor White
Write-Host "   cd terraform" -ForegroundColor Cyan
Write-Host "   terraform init" -ForegroundColor Cyan
Write-Host "   terraform plan -out=tfplan" -ForegroundColor Cyan
Write-Host "   terraform apply tfplan" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Push to GitHub:" -ForegroundColor White
Write-Host "   git add -A" -ForegroundColor Cyan
Write-Host "   git commit -m `"Setup infrastructure`"" -ForegroundColor Cyan
Write-Host "   git push origin master" -ForegroundColor Cyan
Write-Host ""
