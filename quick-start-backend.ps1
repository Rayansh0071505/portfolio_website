# Quick start backend manually on new instance
$EC2_IP = "23.22.97.151"
$ACCOUNT_ID = "444059582963"
$IMAGE = "${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/rayansh_portfolio:latest"

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "MANUAL BACKEND STARTUP" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

$SCRIPT = @"
#!/bin/bash
set -e

echo "1. Installing Docker if needed..."
if ! command -v docker &> /dev/null; then
  sudo yum install -y docker
  sudo systemctl start docker
  sudo systemctl enable docker
  sudo usermod -a -G docker ec2-user
fi

echo "2. Creating directories..."
sudo mkdir -p /opt/backend /data
sudo chown -R ec2-user:ec2-user /opt/backend /data
cd /opt/backend

echo "3. Fetching .env..."
if [ ! -f .env ]; then
  # Try to get from Parameter Store
  aws ssm get-parameter --name "/rayansh_portfolio/env" --region us-east-1 --query 'Parameter.Value' --output text > .env 2>/dev/null || {
    echo "Could not fetch .env - you need to upload it manually"
    exit 1
  }
fi

echo "4. Logging into ECR and pulling image..."
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com
sudo docker pull ${IMAGE}

echo "5. Stopping old container..."
sudo docker stop backend_api 2>/dev/null || true
sudo docker rm backend_api 2>/dev/null || true

echo "6. Starting backend..."
sudo docker run -d \
  --name backend_api \
  -p 8080:8080 \
  -e PYTHONUNBUFFERED=1 \
  --env-file .env \
  -v /data:/app/data \
  --restart unless-stopped \
  ${IMAGE}

echo "7. Waiting for startup..."
sleep 15

if curl -f http://localhost:8080/ 2>/dev/null; then
  echo "✅ Backend is UP!"
else
  echo "❌ Failed - checking logs..."
  sudo docker logs backend_api --tail 50
fi
"@

Write-Host "Connecting via SSH..." -ForegroundColor Yellow
$SCRIPT | ssh -i "demo.pem" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_IP 'bash -s' 2>&1

Write-Host ""
Write-Host "Testing from outside..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
$test = curl.exe -s -m 5 "http://${EC2_IP}:8080/" 2>&1
if ($test -like "*healthy*") {
    Write-Host "✅ SUCCESS!" -ForegroundColor Green
    Write-Host $test
} else {
    Write-Host "❌ Not responding" -ForegroundColor Red
}
