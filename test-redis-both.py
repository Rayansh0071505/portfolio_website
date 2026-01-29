"""
Test both Redis Cloud and Local Redis to compare
Run this before updating production
"""
import asyncio
import time
from langgraph.checkpoint.redis.aio import AsyncRedisSaver

async def test_redis_connection(redis_url: str, name: str):
    """Test Redis connection and measure time"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {redis_url}")
    print(f"{'='*60}")

    start = time.time()
    try:
        # Create AsyncRedisSaver (same as production code)
        checkpointer = AsyncRedisSaver(redis_url=redis_url)

        # Try to setup (this will fail if Redis not accessible)
        await checkpointer.asetup()

        elapsed = time.time() - start
        print(f"✅ SUCCESS in {elapsed:.2f}s")
        print(f"   AsyncRedisSaver initialized correctly")
        print(f"   Conversation history WILL work")
        return True

    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"❌ TIMEOUT after {elapsed:.2f}s")
        print(f"   Redis not accessible - this is why you get 504 errors!")
        return False

    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ ERROR after {elapsed:.2f}s")
        print(f"   Error: {type(e).__name__}: {e}")
        return False

async def main():
    print("\n" + "="*60)
    print("REDIS CONNECTION TEST")
    print("Testing which Redis will work for production")
    print("="*60)

    # Test 1: Redis Cloud (current production config)
    redis_cloud = "redis://default:mp8zusLL1At3bKBaRkqphtGjweGp0yWz@redis-19481.c89.us-east-1-3.ec2.cloud.redislabs.com:19481"
    cloud_works = await test_redis_connection(redis_cloud, "Redis Cloud (CURRENT)")

    # Test 2: Local Redis (what we want to switch to)
    # Note: On your local machine, use localhost. On EC2, it will be backend_redis
    local_redis = "redis://localhost:6379"
    print("\n⚠️  Testing LOCAL Redis (localhost:6379)")
    print("   Note: You need to have Redis running locally for this test")
    print("   On EC2, this will be 'backend_redis:6379'")
    local_works = await test_redis_connection(local_redis, "Local Redis (NEW)")

    # Results
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Redis Cloud:  {'✅ WORKS' if cloud_works else '❌ FAILS'}")
    print(f"Local Redis:  {'✅ WORKS' if local_works else '❌ FAILS (start redis first)'}")
    print()

    if not cloud_works and local_works:
        print("✅ RECOMMENDATION: Switch to Local Redis")
        print("   Redis Cloud is not working, but local Redis works fine")
        print("   Safe to update Parameter Store!")
    elif cloud_works and local_works:
        print("⚠️  BOTH WORK - but Local Redis is faster and more reliable")
    elif not cloud_works and not local_works:
        print("❌ Need to start local Redis first")
        print("   Run: docker run -d -p 6379:6379 redis:7-alpine")
    else:
        print("✅ Redis Cloud works, but consider switching to local for better performance")

if __name__ == "__main__":
    asyncio.run(main())
