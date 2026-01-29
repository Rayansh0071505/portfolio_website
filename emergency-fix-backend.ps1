# Emergency fix: Manually start backend on new instance
# Run this to fix the stuck deployment

$EC2_IP = "23.22.97.151"

Write-Host "=====================================================" -ForegroundColor Red
Write-Host "EMERGENCY BACKEND FIX" -ForegroundColor Red
Write-Host "=====================================================" -ForegroundColor Red
Write-Host ""

Write-Host "This will:" -ForegroundColor Yellow
Write-Host "1. Kill any stuck processes on EC2" -ForegroundColor Gray
Write-Host "2. Get latest Docker image" -ForegroundColor Gray
Write-Host "3. Start backend container" -ForegroundColor Gray
Write-Host ""

# Get account ID
$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$IMAGE = "${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/rayansh_portfolio:latest"

Write-Host "Connecting to EC2: $EC2_IP" -ForegroundColor Yellow
Write-Host ""

# Create the fix script
$SCRIPT = @"
#!/bin/bash
set +e  # Don't exit on errors

echo "======================================================"
echo "1. Killing stuck processes..."
echo "======================================================"
pkill -9 aws 2>/dev/null || true
pkill -9 docker 2>/dev/null || true

echo ""
echo "======================================================"
echo "2. Stopping all containers..."
echo "======================================================"
docker stop `$(docker ps -aq) 2>/dev/null || true
docker rm `$(docker ps -aq) 2>/dev/null || true

echo ""
echo "======================================================"
echo "3. Setting up directories..."
echo "======================================================"
sudo mkdir -p /opt/backend
cd /opt/backend
sudo chown -R ec2-user:ec2-user /opt/backend

echo ""
echo "======================================================"
echo "4. Fetching .env from Parameter Store..."
echo "======================================================"
timeout 10 aws ssm get-parameter --name "/rayansh_portfolio/env" --region us-east-1 --query 'Parameter.Value' --output text > .env 2>&1 || {
  echo "Failed to fetch .env - using existing if available"
}

if [ -f .env ]; then
  echo "✅ .env file exists ($(wc -c < .env) bytes)"
else
  echo "❌ ERROR: No .env file!"
  exit 1
fi

echo ""
echo "======================================================"
echo "5. Getting latest Docker image..."
echo "======================================================"
ACCOUNT_ID=`$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "$ACCOUNT_ID")
IMAGE="`${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/rayansh_portfolio:latest"

aws ecr get-login-password --region us-east-1 2>/dev/null | docker login --username AWS --password-stdin `${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com 2>/dev/null || echo "ECR login may have failed"

docker pull `${IMAGE} 2>&1 | tail -5

echo ""
echo "======================================================"
echo "6. Starting backend container..."
echo "======================================================"
docker run -d \
  --name backend_api \
  -p 8080:8080 \
  -e PYTHONUNBUFFERED=1 \
  --env-file .env \
  -v /data:/app/data \
  --restart unless-stopped \
  --log-driver=awslogs \
  --log-opt awslogs-region=us-east-1 \
  --log-opt awslogs-group=/rayansh_portfolio/backend \
  --log-opt awslogs-stream=backend_api \
  --log-opt awslogs-create-group=true \
  `${IMAGE}

echo ""
echo "======================================================"
echo "7. Waiting for backend to start..."
echo "======================================================"
sleep 15

if curl -f http://localhost:8080/ 2>/dev/null; then
  echo "✅ Backend is UP!"
  curl -s http://localhost:8080/ | head -3
else
  echo "❌ Backend failed - checking logs..."
  docker logs backend_api --tail 30
fi
"@

# Execute via SSH
$SCRIPT | ssh -i "demo.pem" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_IP 'bash -s' 2>&1

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Testing from outside..." -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Start-Sleep -Seconds 3

$test = curl.exe -s -m 5 "http://${EC2_IP}:8080/" 2>&1
if ($test -like "*healthy*") {
    Write-Host "✅ SUCCESS! Backend is responding!" -ForegroundColor Green
    Write-Host $test
} else {
    Write-Host "❌ Backend not responding" -ForegroundColor Red
    Write-Host $test
}
