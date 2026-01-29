# Force Redeploy Backend with Latest Image (Fixed)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Force Redeploy Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$EC2_IP = "23.22.97.151"
$AWS_ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$IMAGE_NAME = "$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rayansh_portfolio:latest"

Write-Host "AWS Account: $AWS_ACCOUNT_ID" -ForegroundColor Green
Write-Host "Image: $IMAGE_NAME" -ForegroundColor Green
Write-Host ""

# Check if demo.pem exists
if (-not (Test-Path "demo.pem")) {
    Write-Host "ERROR: demo.pem not found" -ForegroundColor Red
    exit 1
}

Write-Host "Connecting to EC2 and redeploying backend..." -ForegroundColor Yellow
Write-Host ""

# Create the deployment script
$deployScript = @"
#!/bin/bash
set -e

echo "=== Downloading .env from Parameter Store ==="
aws ssm get-parameter --name "/rayansh_portfolio/env" --region us-east-1 --query 'Parameter.Value' --output text > .env
if [ ! -s .env ]; then
    echo "❌ Failed to download .env from Parameter Store"
    exit 1
fi
echo "✅ .env downloaded successfully"

echo ""
echo "=== Logging into ECR ==="
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

echo ""
echo "=== Pulling latest image ==="
docker pull $IMAGE_NAME

echo ""
echo "=== Stopping old container ==="
docker stop backend_api || true
docker rm backend_api || true

echo ""
echo "=== Starting new container ==="
docker run -d --name backend_api \
  --network backend_network \
  -p 8080:8080 \
  --env-file .env \
  --restart unless-stopped \
  $IMAGE_NAME

echo ""
echo "=== Waiting for backend to start ==="
sleep 5

echo ""
echo "=== Checking health ==="
for i in {1..30}; do
  if curl -f http://localhost:8080/ 2>/dev/null; then
    echo ""
    echo "✅ Backend is healthy!"
    echo ""
    echo "=== Recent logs ==="
    docker logs backend_api --tail 10
    exit 0
  fi
  echo -n "."
  sleep 2
done

echo ""
echo "❌ Backend failed to start"
echo ""
echo "=== Full logs ==="
docker logs backend_api
exit 1
"@

# Save script to temp file
$tempScript = [System.IO.Path]::GetTempFileName()
$deployScript | Out-File -FilePath $tempScript -Encoding ASCII

# Copy script to EC2
Write-Host "Uploading deployment script..." -ForegroundColor Yellow
scp -i demo.pem -o StrictHostKeyChecking=no $tempScript ec2-user@${EC2_IP}:/tmp/redeploy.sh

# Execute script
Write-Host "Executing deployment..." -ForegroundColor Yellow
Write-Host ""
ssh -i demo.pem -o StrictHostKeyChecking=no ec2-user@$EC2_IP "chmod +x /tmp/redeploy.sh && /tmp/redeploy.sh"

$exitCode = $LASTEXITCODE

# Cleanup
Remove-Item $tempScript

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "✅ Backend Redeployed Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Test your CloudFront URL now:" -ForegroundColor Yellow
    Write-Host "https://dihzp5za95inb.cloudfront.net" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "💡 Clear browser cache or use incognito mode" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Deployment failed! Check the logs above." -ForegroundColor Red
    exit 1
}
