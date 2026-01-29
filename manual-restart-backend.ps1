# Manually restart backend container on EC2
# Use when deployment is stuck

$EC2_IP = "23.22.97.151"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Manual Backend Restart" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Getting AWS Account ID..." -ForegroundColor Yellow
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$IMAGE_NAME = "$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/rayansh_portfolio:latest"

Write-Host "Image: $IMAGE_NAME" -ForegroundColor Gray
Write-Host ""

Write-Host "Connecting to EC2 and restarting container..." -ForegroundColor Yellow

# Create restart script
$SCRIPT = @"
set -e

# Get AWS account ID
ACCOUNT_ID=`$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "$ACCOUNT_ID")
IMAGE_NAME="`${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/rayansh_portfolio:latest"

echo "Stopping old container..."
docker stop backend_api 2>/dev/null || true
docker rm backend_api 2>/dev/null || true

echo "Starting backend container..."
docker run -d \
  --name backend_api \
  -p 8080:8080 \
  -e PYTHONUNBUFFERED=1 \
  --env-file /opt/backend/.env \
  -v /data:/app/data \
  --restart unless-stopped \
  --log-driver=awslogs \
  --log-opt awslogs-region=us-east-1 \
  --log-opt awslogs-group=/rayansh_portfolio/backend \
  --log-opt awslogs-stream=backend_api \
  --log-opt awslogs-create-group=true \
  `${IMAGE_NAME}

echo "Waiting for backend to start..."
sleep 10

# Check if running
if curl -f http://localhost:8080/ 2>/dev/null; then
  echo "✅ Backend is UP!"
else
  echo "❌ Backend failed to start. Checking logs..."
  docker logs backend_api --tail 20
fi
"@

# Execute via SSH
$SCRIPT | ssh -i "demo.pem" -o StrictHostKeyChecking=no ec2-user@$EC2_IP 'bash -s'

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Testing backend..." -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 5

$response = curl.exe -s "http://${EC2_IP}:8080/"
Write-Host $response

if ($response -like "*healthy*") {
    Write-Host ""
    Write-Host "✅ Backend is HEALTHY!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Backend is NOT responding properly" -ForegroundColor Red
}
