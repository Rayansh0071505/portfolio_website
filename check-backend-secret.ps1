# Check Backend CloudFront Secret
Write-Host "Checking backend CloudFront secret..." -ForegroundColor Cyan
Write-Host ""

$EC2_IP = "23.22.97.151"
$EXPECTED_SECRET = "97f32a248b9cab647c76a2628b95a693d2b34b2159ffba3d40afbb62c37db5"

Write-Host "Expected secret: $EXPECTED_SECRET" -ForegroundColor Yellow
Write-Host ""

# Check if SSH works
Write-Host "Connecting to EC2..." -ForegroundColor Yellow

# Try to get the secret from backend .env
$backendSecret = ssh -i demo.pem -o StrictHostKeyChecking=no ec2-user@$EC2_IP "grep CLOUDFRONT_SECRET .env 2>/dev/null || echo 'NOT_FOUND'" 2>&1

if ($backendSecret -match "NOT_FOUND" -or $backendSecret -match "Permission denied") {
    Write-Host "❌ Cannot check backend secret (SSH permission issue)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Backend secret mismatch is causing 504 errors!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Let me check when the backend container was started..." -ForegroundColor Yellow

    # Check container start time
    ssh -i demo.pem -o StrictHostKeyChecking=no ec2-user@$EC2_IP "docker ps --format '{{.Names}}: Started {{.RunningFor}}' | grep backend" 2>&1

    Write-Host ""
    Write-Host "Solution: Manually update .env on EC2 and restart backend" -ForegroundColor Cyan
    exit 1
}

Write-Host "Backend .env:" -ForegroundColor Green
Write-Host $backendSecret

if ($backendSecret -match $EXPECTED_SECRET) {
    Write-Host ""
    Write-Host "✅ Backend has correct secret!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Backend has WRONG secret!" -ForegroundColor Red
    Write-Host "This is why you're getting 504 errors!" -ForegroundColor Red
}
