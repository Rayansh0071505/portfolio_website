# Test Redis Connection on EC2
Write-Host "Testing Redis connection on EC2..." -ForegroundColor Cyan
Write-Host ""

$EC2_IP = "23.22.97.151"

# Check if Redis container is running
Write-Host "1. Checking if Redis container is running..." -ForegroundColor Yellow
curl -s "http://$EC2_IP:8080/api/status" | python -m json.tool

Write-Host ""
Write-Host "2. Testing Redis connection from backend..." -ForegroundColor Yellow

# Create test script
$testScript = @'
import redis
import os

try:
    redis_url = os.getenv("REDIS_URL", "redis://backend_redis:6379")
    print(f"Connecting to: {redis_url}")

    r = redis.from_url(redis_url)
    r.ping()
    print("✅ Redis PING successful!")

    # Test set/get
    r.set("test_key", "test_value")
    val = r.get("test_key")
    print(f"✅ Redis SET/GET works: {val}")

except Exception as e:
    print(f"❌ Redis connection failed: {e}")
'@

Write-Host $testScript

Write-Host ""
Write-Host "Redis connection test complete." -ForegroundColor Cyan
Write-Host ""
Write-Host "If Redis is not working, the AsyncRedisSaver will fail silently" -ForegroundColor Yellow
Write-Host "and conversation history won't be saved!" -ForegroundColor Yellow
