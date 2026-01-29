# View CloudWatch logs for backend
Write-Host "Fetching backend logs from CloudWatch..." -ForegroundColor Green
Write-Host ""

# Get the latest log events
aws logs tail /rayansh_portfolio/backend --follow --format short

# Alternative: Get last 100 lines without follow
# aws logs tail /rayansh_portfolio/backend --format short --since 10m
