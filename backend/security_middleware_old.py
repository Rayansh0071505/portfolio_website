"""
Security Middleware for Rayansh's Portfolio API
- Rate limiting (per IP and per session) - REDIS BACKED
- IP blocking - REDIS BACKED
- Request validation
- Daily quota tracking - REDIS BACKED
All security data now persists in Redis for scalability and persistence
"""
import json
import re
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
import redis.asyncio as redis_async
from config import get_redis_secret

logger = logging.getLogger(__name__)

# ============================================================================
# REDIS CONNECTION FOR SECURITY DATA
# ============================================================================

_security_redis_client = None

async def get_security_redis():
    """Get Redis client for security data (singleton)"""
    global _security_redis_client
    if _security_redis_client is None:
        redis_url = get_redis_secret()
        if not redis_url:
            raise ValueError("REDIS_SECRET not found in config or environment")
        _security_redis_client = redis_async.from_url(redis_url, decode_responses=True)
        logger.info("✅ Redis client initialized for security middleware")
    return _security_redis_client

# ============================================================================
# RATE LIMITING (REDIS-BACKED)
# ============================================================================

class RateLimiter:
    """Redis-backed rate limiter for distributed systems"""

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        """Get Redis client (lazy initialization)"""
        if self._redis is None:
            self._redis = await get_security_redis()
        return self._redis

    async def is_blocked(self, ip: str) -> Tuple[bool, Optional[str]]:
        """Check if IP is blocked (from Redis)"""
        try:
            redis_client = await self._get_redis()
            block_key = f"security:blocked:{ip}"

            block_data = await redis_client.hgetall(block_key)

            if block_data:
                reason = block_data.get('reason', 'Rate limit exceeded')
                blocked_at = block_data.get('blocked_at', 'Unknown')
                return True, f"IP blocked: {reason} (Blocked at: {blocked_at})"

            return False, None
        except Exception as e:
            logger.error(f"❌ Error checking blocked IP in Redis: {e}")
            return False, None

    async def block_ip(self, ip: str, reason: str):
        """Block an IP address (store in Redis permanently)"""
        try:
            redis_client = await self._get_redis()
            block_key = f"security:blocked:{ip}"

            # Store block info (no expiration - permanent block)
            await redis_client.hset(block_key, mapping={
                'reason': reason,
                'blocked_at': datetime.now().isoformat(),
                'ip': ip
            })

            logger.warning(f"🚫 BLOCKED IP in Redis: {ip} - Reason: {reason}")
        except Exception as e:
            logger.error(f"❌ Error blocking IP in Redis: {e}")

    async def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        try:
            redis_client = await self._get_redis()
            block_key = f"security:blocked:{ip}"
            await redis_client.delete(block_key)
            logger.info(f"✅ Unblocked IP in Redis: {ip}")
        except Exception as e:
            logger.error(f"❌ Error unblocking IP in Redis: {e}")

    async def get_blocked_ips(self) -> Dict[str, dict]:
        """Get all blocked IPs from Redis"""
        try:
            redis_client = await self._get_redis()
            blocked_ips = {}

            async for key in redis_client.scan_iter(match="security:blocked:*"):
                ip = key.replace("security:blocked:", "")
                block_data = await redis_client.hgetall(key)
                blocked_ips[ip] = block_data

            return blocked_ips
        except Exception as e:
            logger.error(f"❌ Error getting blocked IPs from Redis: {e}")
            return {}

    async def check_rate_limit(self, ip: str) -> Tuple[bool, Optional[str]]:
        """
        Check if IP exceeds rate limits using Redis
        Returns: (is_allowed, error_message)
        """
        try:
            # First check if blocked
            is_blocked, block_reason = await self.is_blocked(ip)
            if is_blocked:
                return False, block_reason

            redis_client = await self._get_redis()
            now = datetime.now()

            # Redis keys for rate limiting with TTL
            minute_key = f"security:rate:minute:{ip}"
            hour_key = f"security:rate:hour:{ip}"
            day_key = f"security:rate:day:{ip}"

            # Increment counters atomically
            pipe = redis_client.pipeline()

            # Increment and get counts
            pipe.incr(minute_key)
            pipe.incr(hour_key)
            pipe.incr(day_key)

            # Set TTL if key is new (only sets if key doesn't have TTL)
            pipe.expire(minute_key, 60)       # 60 seconds
            pipe.expire(hour_key, 3600)       # 1 hour
            pipe.expire(day_key, 86400)       # 24 hours

            results = await pipe.execute()

            minute_count = results[0]
            hour_count = results[1]
            day_count = results[2]

            # Check limits
            if minute_count > 10:
                logger.warning(f"⚠️ Rate limit (minute) exceeded for IP: {ip} ({minute_count}/10)")
                # Decrement since we're rejecting
                await redis_client.decr(minute_key)
                await redis_client.decr(hour_key)
                await redis_client.decr(day_key)
                return False, "Rate limit exceeded: Maximum 10 requests per minute"

            if hour_count > 50:
                logger.warning(f"⚠️ Rate limit (hour) exceeded for IP: {ip} ({hour_count}/50)")
                await redis_client.decr(minute_key)
                await redis_client.decr(hour_key)
                await redis_client.decr(day_key)
                return False, "Rate limit exceeded: Maximum 50 requests per hour"

            if day_count > 60:
                # AUTO-BLOCK: More than 60 requests in a day
                logger.warning(f"🚨 Daily limit exceeded for IP: {ip} ({day_count}/60)")
                await self.block_ip(ip, f"Exceeded daily limit: {day_count} requests in 24 hours")
                return False, "Daily limit exceeded: Maximum 60 requests per day. IP has been blocked."

            return True, None

        except Exception as e:
            logger.error(f"❌ Error checking rate limit in Redis: {e}")
            # Fail open (allow request) to avoid blocking all traffic on Redis error
            return True, None

# Global rate limiter instance
rate_limiter = RateLimiter()

# ============================================================================
# SESSION MESSAGE LIMITS (REDIS-BACKED)
# ============================================================================

class SessionLimiter:
    """Track message count per session using Redis"""

    MAX_MESSAGES_PER_SESSION = 15

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        """Get Redis client (lazy initialization)"""
        if self._redis is None:
            self._redis = await get_security_redis()
        return self._redis

    async def check_session_limit(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """Check if session has exceeded message limit (from Redis)"""
        try:
            redis_client = await self._get_redis()
            session_key = f"security:session:{session_id}"

            count_str = await redis_client.get(session_key)
            count = int(count_str) if count_str else 0

            if count >= self.MAX_MESSAGES_PER_SESSION:
                logger.warning(f"⚠️ Session limit exceeded: {session_id} ({count}/{self.MAX_MESSAGES_PER_SESSION})")
                return False, f"Session limit reached: Maximum {self.MAX_MESSAGES_PER_SESSION} messages per conversation. Please start a new session."

            return True, None
        except Exception as e:
            logger.error(f"❌ Error checking session limit in Redis: {e}")
            # Fail open (allow request)
            return True, None

    async def increment_session(self, session_id: str):
        """Increment message count for session (in Redis with TTL)"""
        try:
            redis_client = await self._get_redis()
            session_key = f"security:session:{session_id}"

            # Increment counter
            count = await redis_client.incr(session_key)

            # Set TTL to 24 hours if new key
            await redis_client.expire(session_key, 86400)

            # Warn when approaching limit
            if count == self.MAX_MESSAGES_PER_SESSION - 2:
                logger.info(f"ℹ️ Session {session_id} approaching limit: {count}/{self.MAX_MESSAGES_PER_SESSION}")
        except Exception as e:
            logger.error(f"❌ Error incrementing session in Redis: {e}")

    async def clear_session(self, session_id: str):
        """Clear session count from Redis"""
        try:
            redis_client = await self._get_redis()
            session_key = f"security:session:{session_id}"
            await redis_client.delete(session_key)
            logger.info(f"🗑️ Cleared session count from Redis: {session_id}")
        except Exception as e:
            logger.error(f"❌ Error clearing session in Redis: {e}")

# Global session limiter instance
session_limiter = SessionLimiter()

# ============================================================================
# REQUEST VALIDATION
# ============================================================================

class RequestValidator:
    """Validate incoming requests for security threats"""

    MAX_MESSAGE_LENGTH = 500

    # Suspicious patterns (basic XSS/SQL injection detection)
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>',  # XSS
        r'javascript:',     # XSS
        r'onerror\s*=',    # XSS
        r'onclick\s*=',    # XSS
        r'(union|select|insert|update|delete|drop)\s+(all|distinct|from|table)',  # SQL injection
        r';\s*(drop|delete|truncate)\s+',  # SQL injection
        r'\.\./\.\./\.\./',  # Path traversal
    ]

    @staticmethod
    def validate_message(message: str) -> tuple[bool, Optional[str]]:
        """Validate message content"""

        # Check length
        if len(message) > RequestValidator.MAX_MESSAGE_LENGTH:
            logger.warning(f"⚠️ Message too long: {len(message)} chars (max: {RequestValidator.MAX_MESSAGE_LENGTH})")
            return False, f"Message too long: Maximum {RequestValidator.MAX_MESSAGE_LENGTH} characters allowed"

        # Check if empty
        if not message or not message.strip():
            return False, "Message cannot be empty"

        # Check for suspicious patterns
        message_lower = message.lower()
        for pattern in RequestValidator.SUSPICIOUS_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.warning(f"🚨 Suspicious pattern detected: {pattern}")
                return False, "Message contains potentially malicious content"

        return True, None

# ============================================================================
# DAILY QUOTA TRACKER (REDIS-BACKED - for Vertex AI cost protection)
# ============================================================================

class DailyQuotaTracker:
    """Track daily API usage to prevent cost overruns using Redis"""

    DAILY_REQUEST_LIMIT = 500  # Max 500 Vertex AI requests per day

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        """Get Redis client (lazy initialization)"""
        if self._redis is None:
            self._redis = await get_security_redis()
        return self._redis

    async def check_quota(self) -> Tuple[bool, Optional[str]]:
        """Check if daily quota is exceeded (from Redis)"""
        try:
            redis_client = await self._get_redis()
            current_date = datetime.now().strftime('%Y-%m-%d')
            quota_key = f"security:quota:{current_date}"

            count_str = await redis_client.get(quota_key)
            count = int(count_str) if count_str else 0

            if count >= self.DAILY_REQUEST_LIMIT:
                logger.error(f"🚨 DAILY QUOTA EXCEEDED: {count}/{self.DAILY_REQUEST_LIMIT}")
                return False, f"Daily API quota exceeded ({self.DAILY_REQUEST_LIMIT} requests). Please try again tomorrow."

            return True, None
        except Exception as e:
            logger.error(f"❌ Error checking quota in Redis: {e}")
            # Fail open (allow request)
            return True, None

    async def increment_quota(self):
        """Increment daily quota counter (in Redis with midnight expiration)"""
        try:
            redis_client = await self._get_redis()
            current_date = datetime.now().strftime('%Y-%m-%d')
            quota_key = f"security:quota:{current_date}"

            # Increment counter
            count = await redis_client.incr(quota_key)

            # Calculate seconds until midnight
            now = datetime.now()
            midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
            seconds_until_midnight = int((midnight - now).total_seconds())

            # Set TTL to expire at midnight
            await redis_client.expire(quota_key, seconds_until_midnight)

            # Warn at thresholds
            if count in [400, 450, 490]:
                logger.warning(f"⚠️ Daily quota warning: {count}/{self.DAILY_REQUEST_LIMIT}")

        except Exception as e:
            logger.error(f"❌ Error incrementing quota in Redis: {e}")

    async def get_quota_data(self) -> dict:
        """Get current quota data for monitoring"""
        try:
            redis_client = await self._get_redis()
            current_date = datetime.now().strftime('%Y-%m-%d')
            quota_key = f"security:quota:{current_date}"

            count_str = await redis_client.get(quota_key)
            count = int(count_str) if count_str else 0

            return {
                'date': current_date,
                'count': count,
                'limit': self.DAILY_REQUEST_LIMIT
            }
        except Exception as e:
            logger.error(f"❌ Error getting quota data from Redis: {e}")
            return {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'count': 0,
                'limit': self.DAILY_REQUEST_LIMIT
            }

# Global quota tracker instance
quota_tracker = DailyQuotaTracker()

# ============================================================================
# IP EXTRACTION UTILITY
# ============================================================================

def get_client_ip(request) -> str:
    """
    Extract real client IP from request
    Handles proxies (Cloudflare, nginx, etc.)
    """
    # Check X-Forwarded-For header (set by proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take first IP in the chain (original client)
        ip = forwarded_for.split(",")[0].strip()
        return ip

    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"
