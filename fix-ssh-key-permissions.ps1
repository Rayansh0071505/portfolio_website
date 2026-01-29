# Fix SSH Key Permissions on Windows
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix demo.pem Permissions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$keyPath = "demo.pem"

if (-not (Test-Path $keyPath)) {
    Write-Host "ERROR: demo.pem not found" -ForegroundColor Red
    exit 1
}

Write-Host "Fixing permissions for: $keyPath" -ForegroundColor Yellow
Write-Host ""

# Get current user
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
Write-Host "Current user: $currentUser" -ForegroundColor Green

# Remove inheritance
icacls $keyPath /inheritance:r

# Remove all existing permissions
icacls $keyPath /remove:g "NT AUTHORITY\Authenticated Users"
icacls $keyPath /remove:g "BUILTIN\Users"
icacls $keyPath /remove:g "Everyone"

# Grant read permission only to current user
icacls $keyPath /grant:r "${currentUser}:(R)"

Write-Host ""
Write-Host "Current permissions:" -ForegroundColor Cyan
icacls $keyPath

Write-Host ""
Write-Host "✅ Permissions fixed!" -ForegroundColor Green
Write-Host ""
Write-Host "Now redeploying backend..." -ForegroundColor Yellow
