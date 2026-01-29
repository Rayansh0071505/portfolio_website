import redis
import time

redis_url = "redis://default:mp8zusLL1At3bKBaRkqphtGjweGp0yWz@redis-19481.c89.us-east-1-3.ec2.cloud.redislabs.com:19481"

print(f"Testing connection to: {redis_url}")
print("Attempting to connect...")

start = time.time()
try:
    r = redis.from_url(redis_url, socket_timeout=5, socket_connect_timeout=5)
    r.ping()
    elapsed = time.time() - start
    print(f"✅ SUCCESS! Connected in {elapsed:.2f}s")
    print(f"   Redis info: {r.info('server')['redis_version']}")
except redis.exceptions.TimeoutError:
    elapsed = time.time() - start
    print(f"❌ TIMEOUT after {elapsed:.2f}s - Redis Cloud not accessible")
except Exception as e:
    elapsed = time.time() - start
    print(f"❌ ERROR after {elapsed:.2f}s: {e}")
