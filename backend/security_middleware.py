"""
Security Middleware for Rayansh's Portfolio API - IN-MEMORY VERSION
- Rate limiting (per IP and per session)
- IP blocking
- Request validation
- Daily quota tracking
All security data stored in memory (resets on restart)
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

# ============================================================================
# IN-MEMORY STORAGE FOR SECURITY DATA
# ============================================================================

_rate_limits = {}      # IP-based rate limiting
_blocked_ips = {}      # Blocked IPs
_session_limits = {}   # Session message counts
_daily_quota = {}      # Daily API quota

# ============================================================================
# RATE LIMITER CLASS (IP-based)
# ============================================================================

class RateLimiter:
    """IP-based rate limiting using in-memory storage"""

    def __init__(self):
        pass

    async def check_rate_limit(self, ip: str) -> Tuple[bool, Optional[str]]:
        """Check if IP exceeds rate limits"""
        global _rate_limits, _blocked_ips

        # Check if IP is blocked
        if ip in _blocked_ips:
            return False, "IP blocked due to rate limit violations"

        now = datetime.now()

        # Initialize rate limit data for this IP
        if ip not in _rate_limits:
            _rate_limits[ip] = {
                "minute": [],
                "hour": [],
                "day": []
            }

        # Clean old timestamps
        _rate_limits[ip]["minute"] = [t for t in _rate_limits[ip]["minute"] if now - t < timedelta(minutes=1)]
        _rate_limits[ip]["hour"] = [t for t in _rate_limits[ip]["hour"] if now - t < timedelta(hours=1)]
        _rate_limits[ip]["day"] = [t for t in _rate_limits[ip]["day"] if now - t < timedelta(days=1)]

        # Count requests
        minute_count = len(_rate_limits[ip]["minute"])
        hour_count = len(_rate_limits[ip]["hour"])
        day_count = len(_rate_limits[ip]["day"])

        # Check limits
        if minute_count >= 10:
            logger.warning(f"⚠️ Rate limit (minute) exceeded for IP: {ip} ({minute_count}/10)")
            return False, "Rate limit exceeded: Maximum 10 requests per minute"

        if hour_count >= 50:
            logger.warning(f"⚠️ Rate limit (hour) exceeded for IP: {ip} ({hour_count}/50)")
            return False, "Rate limit exceeded: Maximum 50 requests per hour"

        if day_count >= 60:
            logger.warning(f"⚠️ Rate limit (day) exceeded for IP: {ip} ({day_count}/60)")
            # Block IP for 24 hours
            _blocked_ips[ip] = now + timedelta(hours=24)
            return False, "Rate limit exceeded: Maximum 60 requests per day. IP blocked for 24 hours."

        # Record this request
        _rate_limits[ip]["minute"].append(now)
        _rate_limits[ip]["hour"].append(now)
        _rate_limits[ip]["day"].append(now)

        return True, None

    async def is_blocked(self, ip: str) -> Tuple[bool, Optional[str]]:
        """Check if IP is blocked"""
        global _blocked_ips
        if ip in _blocked_ips:
            if datetime.now() < _blocked_ips[ip]:
                return True, "IP blocked"
            else:
                # Block expired, remove it
                del _blocked_ips[ip]
        return False, None

    async def unblock_ip(self, ip: str):
        """Manually unblock an IP"""
        global _blocked_ips
        if ip in _blocked_ips:
            del _blocked_ips[ip]
            logger.info(f"✅ Unblocked IP: {ip}")

    async def get_blocked_ips(self) -> Dict[str, str]:
        """Get all currently blocked IPs"""
        global _blocked_ips
        now = datetime.now()
        # Clean expired blocks
        _blocked_ips = {ip: expiry for ip, expiry in _blocked_ips.items() if now < expiry}
        return {ip: expiry.isoformat() for ip, expiry in _blocked_ips.items()}


# ============================================================================
# SESSION LIMITER CLASS
# ============================================================================

class SessionLimiter:
    """Session-based message limiting using in-memory storage"""

    MAX_MESSAGES_PER_SESSION = 15

    def __init__(self):
        pass

    async def check_session_limit(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """Check if session has exceeded message limit"""
        global _session_limits
        count = _session_limits.get(session_id, 0)

        if count >= self.MAX_MESSAGES_PER_SESSION:
            return False, f"Session limit reached: Maximum {self.MAX_MESSAGES_PER_SESSION} messages per session"

        return True, None

    async def increment_session(self, session_id: str):
        """Increment session message count"""
        global _session_limits
        _session_limits[session_id] = _session_limits.get(session_id, 0) + 1

    async def get_session_count(self, session_id: str) -> int:
        """Get current session message count"""
        global _session_limits
        return _session_limits.get(session_id, 0)

    async def clear_session(self, session_id: str):
        """Clear session counter"""
        global _session_limits
        if session_id in _session_limits:
            del _session_limits[session_id]


# ============================================================================
# REQUEST VALIDATOR
# ============================================================================

class RequestValidator:
    """Validates requests for suspicious patterns"""

    SUSPICIOUS_PATTERNS = [
        r"<script",
        r"javascript:",
        r"onerror=",
        r"onclick=",
        r"\.\./\.\./",
        r"union\s+select",
        r"drop\s+table",
        r"exec\(",
        r"eval\(",
    ]

    MAX_MESSAGE_LENGTH = 2000

    @staticmethod
    def validate_message(message: str) -> Tuple[bool, Optional[str]]:
        """Validate message for length and suspicious patterns"""

        # Check length
        if len(message) > RequestValidator.MAX_MESSAGE_LENGTH:
            return False, f"Message too long (max {RequestValidator.MAX_MESSAGE_LENGTH} characters)"

        # Check for suspicious patterns
        message_lower = message.lower()
        for pattern in RequestValidator.SUSPICIOUS_PATTERNS:
            if re.search(pattern, message_lower):
                logger.warning(f"🚨 Suspicious pattern detected: {pattern}")
                return False, "Invalid message content detected"

        return True, None


# ============================================================================
# QUOTA TRACKER CLASS
# ============================================================================

class QuotaTracker:
    """Daily API quota tracking using in-memory storage"""

    DAILY_REQUEST_LIMIT = 500

    def __init__(self):
        pass

    async def check_quota(self) -> Tuple[bool, Optional[str]]:
        """Check if daily quota is exceeded"""
        global _daily_quota
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Reset if new day
        if "date" not in _daily_quota or _daily_quota["date"] != current_date:
            _daily_quota = {"date": current_date, "count": 0}

        if _daily_quota["count"] >= self.DAILY_REQUEST_LIMIT:
            return False, f"Daily quota exceeded: {self.DAILY_REQUEST_LIMIT} requests per day"

        return True, None

    async def increment_quota(self):
        """Increment daily quota counter"""
        global _daily_quota
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Reset if new day
        if "date" not in _daily_quota or _daily_quota["date"] != current_date:
            _daily_quota = {"date": current_date, "count": 0}

        _daily_quota["count"] += 1

    async def get_quota_data(self) -> Dict:
        """Get current quota data"""
        global _daily_quota
        return _daily_quota.copy() if _daily_quota else {"date": datetime.now().strftime('%Y-%m-%d'), "count": 0}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_client_ip(request: Request) -> str:
    """
    Extract real client IP from request
    Handles CloudFront, proxy, and direct connections
    """
    # CloudFront forwarded IP
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # First IP in the list is the original client
        return forwarded_for.split(",")[0].strip()

    # Direct connection
    if request.client:
        return request.client.host

    return "unknown"


# Global instances
rate_limiter = RateLimiter()
session_limiter = SessionLimiter()
quota_tracker = QuotaTracker()
