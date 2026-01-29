# Test backend and watch CloudWatch logs
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Testing Backend + Watching CloudWatch Logs" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

$sessionId = "test_$(Get-Date -Format 'yyyyMMddHHmmss')"
$apiUrl = "http://23.22.97.151:8080/api/chat"

# Questions that cause crash
$questions = @(
    "hi",
    "tell me your tech stack",
    "have you work in voice model",
    "in which company you worked in it",
    "explain your role in everest"
)

Write-Host "Session ID: $sessionId" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting tests in 5 seconds... Open another terminal and run: .\view-logs.ps1" -ForegroundColor Green
Start-Sleep -Seconds 5

foreach ($i in 0..($questions.Count-1)) {
    $num = $i + 1
    $question = $questions[$i]

    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host "Question $num : $question" -ForegroundColor White
    Write-Host "=====================================================" -ForegroundColor Cyan

    $body = @{
        message = $question
        session_id = $sessionId
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -ContentType "application/json" -TimeoutSec 40

        Write-Host "✅ Response received" -ForegroundColor Green
        Write-Host "   Model: $($response.model)" -ForegroundColor Gray
        Write-Host "   Time: $($response.response_time)" -ForegroundColor Gray
        Write-Host "   Message: $($response.message.Substring(0, [Math]::Min(100, $response.message.Length)))..." -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Backend crashed or timed out! Check logs with: .\view-logs.ps1" -ForegroundColor Yellow
        break
    }

    Write-Host ""
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "Test complete! View logs with: .\view-logs.ps1" -ForegroundColor Green
