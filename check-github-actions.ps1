# Check GitHub Actions Workflow Status
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Actions Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get repo info from git
$repoUrl = git config --get remote.origin.url
if ($repoUrl -match "github.com[:/](.+)/(.+?)(\.git)?$") {
    $owner = $matches[1]
    $repo = $matches[2]
    Write-Host "Repository: $owner/$repo" -ForegroundColor Green
    Write-Host ""

    # Check latest workflow runs
    Write-Host "Opening GitHub Actions page in browser..." -ForegroundColor Yellow
    Start-Process "https://github.com/$owner/$repo/actions"

    Write-Host ""
    Write-Host "Check the Actions tab to see if workflows are running." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Expected workflow: 'Deploy Frontend and Backend'" -ForegroundColor Yellow
    Write-Host "Should trigger on: changes to backend/** or project/**" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "If workflow is NOT running, possible issues:" -ForegroundColor Red
    Write-Host "1. Workflow file has syntax errors" -ForegroundColor Yellow
    Write-Host "2. GitHub Actions is disabled on your repo" -ForegroundColor Yellow
    Write-Host "3. Workflow permissions issue" -ForegroundColor Yellow
} else {
    Write-Host "Could not parse repository URL" -ForegroundColor Red
}
