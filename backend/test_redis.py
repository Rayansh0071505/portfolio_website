import os
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_redis_connection():
    """Test basic Redis connection and operations"""
    try:
        # Get Redis connection URL from environment
        redis_url = os.getenv("REDIS_SECRET")

        if not redis_url:
            print("❌ REDIS_SECRET not found in environment variables")
            return False

        print("🔄 Connecting to Redis...")
        print(f"Database name: database-poertfolio")

        # Connect to Redis
        r = redis.from_url(redis_url, decode_responses=True)

        # Test 1: Ping
        print("\n📡 Test 1: Ping")
        response = r.ping()
        print(f"✅ Ping successful: {response}")

        # Test 2: Set a key
        print("\n📝 Test 2: Set a key")
        r.set("test_key", "Hello from database-poertfolio!")
        print("✅ Key 'test_key' set successfully")

        # Test 3: Get a key
        print("\n📖 Test 3: Get a key")
        value = r.get("test_key")
        print(f"✅ Retrieved value: {value}")

        # Test 4: Set with expiration
        print("\n⏰ Test 4: Set key with expiration (10 seconds)")
        r.setex("temp_key", 10, "This will expire in 10 seconds")
        print("✅ Temporary key set successfully")

        # Test 5: Check if key exists
        print("\n🔍 Test 5: Check key existence")
        exists = r.exists("test_key")
        print(f"✅ Key 'test_key' exists: {exists}")

        # Test 6: Delete a key
        print("\n🗑️ Test 6: Delete a key")
        r.delete("test_key")
        print("✅ Key 'test_key' deleted successfully")

        # Test 7: Verify deletion
        print("\n✔️ Test 7: Verify deletion")
        exists_after = r.exists("test_key")
        print(f"✅ Key 'test_key' exists after deletion: {exists_after}")

        # Test 8: Hash operations
        print("\n📦 Test 8: Hash operations")
        r.hset("user:1", mapping={
            "name": "Test User",
            "email": "test@example.com",
            "database": "database-poertfolio"
        })
        user_data = r.hgetall("user:1")
        print(f"✅ Hash data stored and retrieved: {user_data}")

        # Test 9: List operations
        print("\n📋 Test 9: List operations")
        r.lpush("test_list", "item1", "item2", "item3")
        list_items = r.lrange("test_list", 0, -1)
        print(f"✅ List items: {list_items}")

        # Cleanup
        print("\n🧹 Cleanup")
        r.delete("user:1", "test_list", "temp_key")
        print("✅ Cleanup completed")

        # Connection info
        print("\n📊 Redis Info:")
        info = r.info("server")
        print(f"   Redis Version: {info.get('redis_version', 'Unknown')}")
        print(f"   OS: {info.get('os', 'Unknown')}")
        print(f"   Uptime (days): {info.get('uptime_in_days', 'Unknown')}")

        print("\n✅ All Redis tests passed successfully!")
        print(f"✅ Database 'database-poertfolio' is working correctly!")

        return True

    except redis.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        return False
    except redis.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            r.close()
            print("\n🔌 Connection closed")
        except:
            pass


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Redis Connection Test")
    print("=" * 50)

    success = test_redis_connection()

    if success:
        print("\n" + "=" * 50)
        print("✅ REDIS TEST COMPLETED SUCCESSFULLY")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ REDIS TEST FAILED")
        print("=" * 50)
