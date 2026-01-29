# Manual Fix for demo.pem Permissions
Write-Host "Fixing demo.pem permissions..." -ForegroundColor Yellow

# Method 1: Using icacls
icacls demo.pem /reset
icacls demo.pem /inheritance:r
icacls demo.pem /grant:r "$($env:USERNAME):(R)"

Write-Host ""
Write-Host "Permissions after fix:" -ForegroundColor Cyan
icacls demo.pem

Write-Host ""
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
ssh -i demo.pem -o StrictHostKeyChecking=no ec2-user@23.22.97.151 "echo 'SSH works!'"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ SSH connection successful!" -ForegroundColor Green
} else {
    Write-Host "❌ SSH still failing" -ForegroundColor Red
}
