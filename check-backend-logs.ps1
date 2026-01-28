# Check Backend Logs
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Checking Backend Logs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$EC2_IP = "23.22.97.151"
Write-Host "Backend IP: $EC2_IP" -ForegroundColor Green
Write-Host ""

# Test direct backend call
Write-Host "Testing direct backend call..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://$EC2_IP:8080/" -Method Get -TimeoutSec 5
    Write-Host "Backend Status: $($response.status)" -ForegroundColor Green
    Write-Host "AI Initialized: $($response.ai_initialized)" -ForegroundColor $(if ($response.ai_initialized) { "Green" } else { "Red" })
} catch {
    Write-Host "ERROR: Cannot reach backend" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "Fetching backend logs via SSH..." -ForegroundColor Yellow
Write-Host ""

# Check if demo.pem exists
if (-not (Test-Path "demo.pem")) {
    Write-Host "ERROR: demo.pem not found in current directory" -ForegroundColor Red
    exit 1
}

# Get container logs
ssh -i demo.pem -o StrictHostKeyChecking=no ec2-user@$EC2_IP "docker logs backend_api --tail 50"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
