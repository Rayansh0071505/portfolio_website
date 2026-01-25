"""
Security Middleware for Rayansh's Portfolio API
- Rate limiting (per IP and per session)
- IP blocking
- Request validation
- Daily quota tracking
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

# Storage files
BLOCKED_IPS_FILE = Path(__file__).parent / "blocked_ips.json"
RATE_LIMIT_FILE = Path(__file__).parent / "rate_limits.json"
SESSION_LIMITS_FILE = Path(__file__).parent / "session_limits.json"

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """In-memory rate limiter with persistent blocked IPs"""

    def __init__(self):
        # Structure: {ip: {'minute': [(timestamp, count)], 'hour': [...], 'day': [...]}}
        self.requests: Dict[str, Dict] = defaultdict(lambda: {
            'minute': [],
            'hour': [],
            'day': []
        })
        self.blocked_ips = self._load_blocked_ips()

    def _load_blocked_ips(self) -> Dict[str, dict]:
        """Load blocked IPs from file"""
        if BLOCKED_IPS_FILE.exists():
            try:
                with open(BLOCKED_IPS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading blocked IPs: {e}")
        return {}

    def _save_blocked_ips(self):
        """Save blocked IPs to file"""
        try:
            with open(BLOCKED_IPS_FILE, 'w') as f:
                json.dump(self.blocked_ips, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving blocked IPs: {e}")

    def is_blocked(self, ip: str) -> tuple[bool, Optional[str]]:
        """Check if IP is blocked"""
        if ip in self.blocked_ips:
            block_info = self.blocked_ips[ip]
            reason = block_info.get('reason', 'Rate limit exceeded')
            blocked_at = block_info.get('blocked_at', 'Unknown')
            return True, f"IP blocked: {reason} (Blocked at: {blocked_at})"
        return False, None

    def block_ip(self, ip: str, reason: str):
        """Block an IP address"""
        self.blocked_ips[ip] = {
            'reason': reason,
            'blocked_at': datetime.now().isoformat(),
            'request_count': self._get_daily_count(ip)
        }
        self._save_blocked_ips()
        logger.warning(f"🚫 BLOCKED IP: {ip} - Reason: {reason}")

    def _cleanup_old_requests(self, ip: str):
        """Remove requests outside time windows"""
        now = datetime.now()

        # Clean minute window (keep last 60 seconds)
        self.requests[ip]['minute'] = [
            ts for ts in self.requests[ip]['minute']
            if (now - ts).total_seconds() <= 60
        ]

        # Clean hour window (keep last 60 minutes)
        self.requests[ip]['hour'] = [
            ts for ts in self.requests[ip]['hour']
            if (now - ts).total_seconds() <= 3600
        ]

        # Clean day window (keep last 24 hours)
        self.requests[ip]['day'] = [
            ts for ts in self.requests[ip]['day']
            if (now - ts).total_seconds() <= 86400
        ]

    def _get_daily_count(self, ip: str) -> int:
        """Get request count for current day"""
        self._cleanup_old_requests(ip)
        return len(self.requests[ip]['day'])

    def check_rate_limit(self, ip: str) -> tuple[bool, Optional[str]]:
        """
        Check if IP exceeds rate limits
        Returns: (is_allowed, error_message)
        """
        # First check if blocked
        is_blocked, block_reason = self.is_blocked(ip)
        if is_blocked:
            return False, block_reason

        # Clean old requests
        self._cleanup_old_requests(ip)

        now = datetime.now()

        # Count requests in each window
        minute_count = len(self.requests[ip]['minute'])
        hour_count = len(self.requests[ip]['hour'])
        day_count = len(self.requests[ip]['day'])

        # Check limits
        if minute_count >= 10:
            logger.warning(f"⚠️ Rate limit (minute) exceeded for IP: {ip} ({minute_count}/10)")
            return False, "Rate limit exceeded: Maximum 10 requests per minute"

        if hour_count >= 50:
            logger.warning(f"⚠️ Rate limit (hour) exceeded for IP: {ip} ({hour_count}/50)")
            return False, "Rate limit exceeded: Maximum 50 requests per hour"

        if day_count >= 60:
            # AUTO-BLOCK: More than 60 requests in a day
            logger.warning(f"🚨 Daily limit exceeded for IP: {ip} ({day_count}/60)")
            self.block_ip(ip, f"Exceeded daily limit: {day_count} requests in 24 hours")
            return False, "Daily limit exceeded: Maximum 60 requests per day. IP has been blocked."

        # Record this request
        self.requests[ip]['minute'].append(now)
        self.requests[ip]['hour'].append(now)
        self.requests[ip]['day'].append(now)

        return True, None

# Global rate limiter instance
rate_limiter = RateLimiter()

# ============================================================================
# SESSION MESSAGE LIMITS
# ============================================================================

class SessionLimiter:
    """Track message count per session"""

    MAX_MESSAGES_PER_SESSION = 15

    def __init__(self):
        self.session_counts: Dict[str, int] = defaultdict(int)

    def check_session_limit(self, session_id: str) -> tuple[bool, Optional[str]]:
        """Check if session has exceeded message limit"""
        count = self.session_counts[session_id]

        if count >= self.MAX_MESSAGES_PER_SESSION:
            logger.warning(f"⚠️ Session limit exceeded: {session_id} ({count}/{self.MAX_MESSAGES_PER_SESSION})")
            return False, f"Session limit reached: Maximum {self.MAX_MESSAGES_PER_SESSION} messages per conversation. Please start a new session."

        return True, None

    def increment_session(self, session_id: str):
        """Increment message count for session"""
        self.session_counts[session_id] += 1
        count = self.session_counts[session_id]

        # Warn when approaching limit
        if count == self.MAX_MESSAGES_PER_SESSION - 2:
            logger.info(f"ℹ️ Session {session_id} approaching limit: {count}/{self.MAX_MESSAGES_PER_SESSION}")

    def clear_session(self, session_id: str):
        """Clear session count"""
        if session_id in self.session_counts:
            del self.session_counts[session_id]

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
# DAILY QUOTA TRACKER (for Vertex AI cost protection)
# ============================================================================

class DailyQuotaTracker:
    """Track daily API usage to prevent cost overruns"""

    DAILY_REQUEST_LIMIT = 500  # Max 500 Vertex AI requests per day

    def __init__(self):
        self.quota_file = Path(__file__).parent / "daily_quota.json"
        self.quota_data = self._load_quota()

    def _load_quota(self) -> dict:
        """Load quota data from file"""
        if self.quota_file.exists():
            try:
                with open(self.quota_file, 'r') as f:
                    data = json.load(f)
                    # Reset if it's a new day
                    if data.get('date') != datetime.now().strftime('%Y-%m-%d'):
                        return {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0}
                    return data
            except Exception as e:
                logger.error(f"Error loading quota: {e}")

        return {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0}

    def _save_quota(self):
        """Save quota data to file"""
        try:
            with open(self.quota_file, 'w') as f:
                json.dump(self.quota_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving quota: {e}")

    def check_quota(self) -> tuple[bool, Optional[str]]:
        """Check if daily quota is exceeded"""
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Reset if new day
        if self.quota_data['date'] != current_date:
            self.quota_data = {'date': current_date, 'count': 0}
            self._save_quota()

        if self.quota_data['count'] >= self.DAILY_REQUEST_LIMIT:
            logger.error(f"🚨 DAILY QUOTA EXCEEDED: {self.quota_data['count']}/{self.DAILY_REQUEST_LIMIT}")
            return False, f"Daily API quota exceeded ({self.DAILY_REQUEST_LIMIT} requests). Please try again tomorrow."

        return True, None

    def increment_quota(self):
        """Increment daily quota counter"""
        self.quota_data['count'] += 1
        self._save_quota()

        # Warn at thresholds
        count = self.quota_data['count']
        if count in [400, 450, 490]:
            logger.warning(f"⚠️ Daily quota warning: {count}/{self.DAILY_REQUEST_LIMIT}")

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
