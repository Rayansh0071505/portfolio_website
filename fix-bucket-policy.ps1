# Fix S3 Bucket Policy for CloudFront Access
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fixing S3 Bucket Policy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

cd terraform

# Get current bucket name
Write-Host "Getting S3 bucket name..." -ForegroundColor Yellow
$BUCKET = terraform output -raw frontend_bucket_name

if ([string]::IsNullOrEmpty($BUCKET)) {
    Write-Host "ERROR: Could not get bucket name from Terraform" -ForegroundColor Red
    exit 1
}

Write-Host "S3 Bucket: $BUCKET" -ForegroundColor Green
Write-Host ""

# Check if policy exists
Write-Host "Checking current policy..." -ForegroundColor Yellow
$policyExists = aws s3api get-bucket-policy --bucket $BUCKET 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "No policy found - will create one" -ForegroundColor Yellow
} else {
    Write-Host "Policy already exists - will update it" -ForegroundColor Yellow
}
Write-Host ""

# Apply the bucket policy using Terraform
Write-Host "Applying bucket policy with Terraform..." -ForegroundColor Yellow
terraform apply -target="aws_s3_bucket_policy.frontend" -auto-approve

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Bucket policy applied successfully!" -ForegroundColor Green
    Write-Host ""

    # Verify the policy
    Write-Host "Verifying policy..." -ForegroundColor Yellow
    aws s3api get-bucket-policy --bucket $BUCKET --output json | ConvertFrom-Json | Select-Object -ExpandProperty Policy | ConvertFrom-Json | ConvertTo-Json -Depth 10

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Policy Fixed! ✅" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Wait 1-2 minutes, then test your CloudFront URL:" -ForegroundColor Yellow
    $CF_DOMAIN = terraform output -raw cloudfront_domain_name
    Write-Host "https://$CF_DOMAIN" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 Use incognito/private window to avoid browser cache" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Terraform failed - trying manual approach..." -ForegroundColor Red
    Write-Host ""

    # Get OAI ARN
    $OAI_ARN = aws cloudfront list-cloud-front-origin-access-identities --query "CloudFrontOriginAccessIdentityList.Items[?Comment=='OAI for rayansh_portfolio frontend'].S3CanonicalUserId" --output text

    if ([string]::IsNullOrEmpty($OAI_ARN)) {
        Write-Host "ERROR: Could not find CloudFront OAI" -ForegroundColor Red
        exit 1
    }

    # Create policy JSON
    $POLICY = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudFrontAccess",
      "Effect": "Allow",
      "Principal": {
        "CanonicalUser": "$OAI_ARN"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET/*"
    },
    {
      "Sid": "CloudFrontListBucket",
      "Effect": "Allow",
      "Principal": {
        "CanonicalUser": "$OAI_ARN"
      },
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::$BUCKET"
    }
  ]
}
"@

    # Save to file
    $POLICY | Out-File -FilePath policy.json -Encoding utf8 -NoNewline

    # Apply policy
    Write-Host "Applying policy manually..." -ForegroundColor Yellow
    aws s3api put-bucket-policy --bucket $BUCKET --policy file://policy.json

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Manual policy applied successfully!" -ForegroundColor Green
        Remove-Item policy.json
    } else {
        Write-Host ""
        Write-Host "❌ Failed to apply policy" -ForegroundColor Red
        exit 1
    }
}

cd ..
