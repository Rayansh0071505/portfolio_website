# Check CloudWatch logs for backend errors
Write-Host "Checking last 50 log entries from backend..." -ForegroundColor Yellow
aws logs tail /rayansh_portfolio/backend --since 30m --format short --filter-pattern "ERROR" | Select-Object -Last 50

Write-Host "`n`nChecking last 20 log entries (all)..." -ForegroundColor Yellow
aws logs tail /rayansh_portfolio/backend --since 30m --format short | Select-Object -Last 20
