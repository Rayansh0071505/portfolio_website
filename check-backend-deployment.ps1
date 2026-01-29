# Check Backend Deployment Status
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Checking Backend Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$EC2_IP = "23.22.97.151"

Write-Host "Connecting to EC2 instance..." -ForegroundColor Yellow
Write-Host ""

# Check if demo.pem exists
if (-not (Test-Path "demo.pem")) {
    Write-Host "ERROR: demo.pem not found" -ForegroundColor Red
    exit 1
}

# SSH into EC2 and check Docker containers
Write-Host "=== Docker Container Status ===" -ForegroundColor Cyan
ssh -i demo.pem -o StrictHostKeyChecking=no ec2-user@$EC2_IP "docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.CreatedAt}}'"

Write-Host ""
Write-Host "=== Backend Container Logs (last 30 lines) ===" -ForegroundColor Cyan
ssh -i demo.pem -o StrictHostKeyChecking=no ec2-user@$EC2_IP "docker logs backend_api --tail 30"

Write-Host ""
Write-Host "=== Testing Backend Directly ===" -ForegroundColor Cyan
ssh -i demo.pem -o StrictHostKeyChecking=no ec2-user@$EC2_IP "curl -X POST http://localhost:8080/api/chat -H 'Content-Type: application/json' -d '{\"message\":\"test\"}' 2>&1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
