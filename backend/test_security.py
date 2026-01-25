"""
Security Feature Testing Script
Tests rate limiting, request validation, and session limits
"""
import requests
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"  # Change if your backend runs on different port
SESSION_ID = f"test_session_{int(time.time())}"

def print_separator():
    print("\n" + "="*70 + "\n")

def test_basic_chat():
    """Test 1: Basic chat functionality"""
    print("🧪 TEST 1: Basic Chat Functionality")
    print("-" * 70)

    response = requests.post(
        f"{API_BASE_URL}/api/chat",
        json={
            "message": "Hello, this is a test message",
            "session_id": SESSION_ID
        }
    )

    if response.status_code == 200:
        print("✅ PASS - Basic chat works")
        print(f"Response: {response.json()['message'][:100]}...")
    else:
        print(f"❌ FAIL - Status: {response.status_code}")
        print(f"Error: {response.text}")

def test_message_length_validation():
    """Test 2: Message length validation (500 char limit)"""
    print("🧪 TEST 2: Message Length Validation")
    print("-" * 70)

    long_message = "A" * 501  # Exceeds 500 character limit

    response = requests.post(
        f"{API_BASE_URL}/api/chat",
        json={
            "message": long_message,
            "session_id": SESSION_ID
        }
    )

    if response.status_code == 400:
        print("✅ PASS - Long message rejected")
        print(f"Error: {response.json()['detail']}")
    else:
        print(f"❌ FAIL - Expected 400, got {response.status_code}")

def test_xss_detection():
    """Test 3: XSS pattern detection"""
    print("🧪 TEST 3: XSS Pattern Detection")
    print("-" * 70)

    malicious_messages = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img onerror='alert(1)' src=x>",
    ]

    for msg in malicious_messages:
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={
                "message": msg,
                "session_id": f"{SESSION_ID}_xss"
            }
        )

        if response.status_code == 400:
            print(f"✅ PASS - Blocked: {msg[:50]}")
        else:
            print(f"❌ FAIL - Should block: {msg[:50]}")

def test_rate_limit_per_minute():
    """Test 4: Rate limiting (10 requests/minute)"""
    print("🧪 TEST 4: Rate Limiting (10 requests/minute)")
    print("-" * 70)

    success_count = 0
    test_session = f"{SESSION_ID}_ratelimit"

    print("Sending 12 requests rapidly...")

    for i in range(12):
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={
                "message": f"Test message {i+1}",
                "session_id": test_session
            }
        )

        if response.status_code == 200:
            success_count += 1
            print(f"  Request {i+1}: ✅ Allowed")
        elif response.status_code == 429:
            print(f"  Request {i+1}: 🚫 Rate limited")
            print(f"  Error: {response.json()['detail']}")
        else:
            print(f"  Request {i+1}: ❓ Unexpected status {response.status_code}")

        time.sleep(0.1)  # Small delay to avoid network issues

    if success_count <= 10:
        print(f"\n✅ PASS - Rate limit working ({success_count}/12 allowed)")
    else:
        print(f"\n❌ FAIL - Too many requests allowed ({success_count}/12)")

def test_session_message_limit():
    """Test 5: Session message limit (15 messages)"""
    print("🧪 TEST 5: Session Message Limit (15 messages)")
    print("-" * 70)

    test_session = f"{SESSION_ID}_session_limit"
    success_count = 0

    print("Sending 17 messages (should stop at 15)...")

    for i in range(17):
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            json={
                "message": f"Message {i+1}",
                "session_id": test_session
            }
        )

        if response.status_code == 200:
            success_count += 1
            print(f"  Message {i+1}: ✅ Allowed")
        elif response.status_code == 429:
            print(f"  Message {i+1}: 🚫 Session limit reached")
            print(f"  Error: {response.json()['detail']}")
        else:
            print(f"  Message {i+1}: ❓ Unexpected status {response.status_code}")

        time.sleep(0.5)  # Delay to avoid rate limit

    if success_count == 15:
        print(f"\n✅ PASS - Session limit working (exactly 15 allowed)")
    else:
        print(f"\n❌ FAIL - Expected 15, got {success_count}")

def test_security_stats():
    """Test 6: Security statistics endpoint"""
    print("🧪 TEST 6: Security Statistics Endpoint")
    print("-" * 70)

    response = requests.get(f"{API_BASE_URL}/api/security/stats")

    if response.status_code == 200:
        stats = response.json()
        print("✅ PASS - Security stats endpoint works")
        print(f"\n📊 Current Stats:")
        print(f"  - Daily Quota: {stats['daily_quota']['used']}/{stats['daily_quota']['limit']}")
        print(f"  - Blocked IPs: {len(stats['blocked_ips'])}")
        print(f"  - Rate Limits: {stats['limits']}")
    else:
        print(f"❌ FAIL - Status: {response.status_code}")

def test_empty_message():
    """Test 7: Empty message rejection"""
    print("🧪 TEST 7: Empty Message Rejection")
    print("-" * 70)

    response = requests.post(
        f"{API_BASE_URL}/api/chat",
        json={
            "message": "   ",  # Only whitespace
            "session_id": SESSION_ID
        }
    )

    if response.status_code == 400:
        print("✅ PASS - Empty message rejected")
        print(f"Error: {response.json()['detail']}")
    else:
        print(f"❌ FAIL - Expected 400, got {response.status_code}")

def run_all_tests():
    """Run all security tests"""
    print("\n" + "="*70)
    print("🛡️  PORTFOLIO API SECURITY TESTING SUITE")
    print("="*70)
    print(f"Testing API: {API_BASE_URL}")
    print(f"Session ID: {SESSION_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*70)

    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code != 200:
            print("\n❌ ERROR: API is not responding. Make sure the backend is running.")
            return
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to {API_BASE_URL}")
        print("Make sure the backend server is running:")
        print("  cd backend")
        print("  python main.py")
        return

    print_separator()

    # Run tests
    test_basic_chat()
    print_separator()

    test_message_length_validation()
    print_separator()

    test_xss_detection()
    print_separator()

    test_empty_message()
    print_separator()

    test_rate_limit_per_minute()
    print_separator()

    test_session_message_limit()
    print_separator()

    test_security_stats()
    print_separator()

    print("🎉 TESTING COMPLETE!")
    print("="*70)
    print("\n💡 TIP: Check backend logs for detailed security event logging")
    print("📊 View stats: GET http://127.0.0.1:8000/api/security/stats")
    print("\n")

if __name__ == "__main__":
    run_all_tests()
