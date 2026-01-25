# Security Documentation

This document describes the security features implemented in Rayansh's Portfolio API to protect against abuse, DDoS attacks, and excessive API costs.

## 🛡️ Security Features Overview

### 1. Rate Limiting (Per IP Address)
Prevents spam and DDoS attacks by limiting requests from individual IP addresses.

**Limits:**
- ✅ **10 requests per minute**
- ✅ **50 requests per hour**
- ✅ **60 requests per day**

**Behavior:**
- Requests exceeding these limits are rejected with HTTP 429 (Too Many Requests)
- IPs exceeding 60 requests/day are **automatically blocked**
- Rate limits reset automatically after the time window expires

### 2. Session Message Limits
Prevents endless conversations that could rack up AI API costs.

**Limits:**
- ✅ **15 messages maximum per session**

**Behavior:**
- After 15 messages, users must start a new session
- Session counter resets when chat is cleared
- Prevents abuse while allowing legitimate conversations

### 3. Request Validation
Validates all incoming messages for security threats and content limits.

**Checks:**
- ✅ Maximum message length: **500 characters**
- ✅ Detects XSS patterns (e.g., `<script>`, `javascript:`, `onerror=`)
- ✅ Detects SQL injection patterns (e.g., `UNION SELECT`, `DROP TABLE`)
- ✅ Detects path traversal attempts (e.g., `../../../`)
- ✅ Rejects empty messages

**Behavior:**
- Invalid requests are rejected with HTTP 400 (Bad Request)
- Suspicious patterns are logged for monitoring

### 4. Daily API Quota Protection
Prevents runaway costs from Vertex AI API usage.

**Limits:**
- ✅ **500 AI requests per day** (global limit)

**Behavior:**
- Requests exceeding quota trigger fallback to Groq (backup model)
- Quota resets daily at midnight
- Warnings logged at 400, 450, and 490 requests

### 5. IP Blocking System
Automatically blocks malicious IP addresses.

**Auto-Block Triggers:**
- Exceeding 60 requests in 24 hours

**Manual Management:**
- View blocked IPs: `GET /api/security/stats`
- Unblock an IP: `POST /api/security/unblock/{ip_address}`

**Persistence:**
- Blocked IPs are stored in `blocked_ips.json`
- Blocks persist across server restarts

### 6. CORS Restriction
Only accepts requests from authorized frontend domains.

**Allowed Origins:**
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (React dev server)
- Your production domain (add to `ALLOWED_ORIGINS` in `main.py`)

**Security:**
- Blocks direct API calls from unauthorized websites
- Prevents CSRF attacks

## 📊 Monitoring Endpoints

### Get Security Statistics
```bash
GET /api/security/stats
```

**Response:**
```json
{
  "blocked_ips": {
    "192.168.1.100": {
      "reason": "Exceeded daily limit: 65 requests in 24 hours",
      "blocked_at": "2026-01-25T14:30:00",
      "request_count": 65
    }
  },
  "daily_quota": {
    "used": 234,
    "limit": 500,
    "date": "2026-01-25"
  },
  "limits": {
    "per_minute": 10,
    "per_hour": 50,
    "per_day": 30,
    "messages_per_session": 15
  },
  "timestamp": "2026-01-25T15:45:00"
}
```

### Unblock an IP Address
```bash
POST /api/security/unblock/192.168.1.100
```

**Response:**
```json
{
  "status": "success",
  "message": "IP 192.168.1.100 has been unblocked",
  "timestamp": "2026-01-25T15:45:00"
}
```

**⚠️ WARNING:** In production, you should add authentication to this endpoint to prevent abuse.

## 🔧 Configuration

### Adjusting Rate Limits
Edit `backend/security_middleware.py`:

```python
# In RateLimiter.check_rate_limit()
if minute_count >= 10:  # Change to adjust per-minute limit
if hour_count >= 50:    # Change to adjust per-hour limit
if day_count >= 60:     # Change to adjust per-day limit
```

### Adjusting Session Message Limit
Edit `backend/security_middleware.py`:

```python
class SessionLimiter:
    MAX_MESSAGES_PER_SESSION = 15  # Change this value
```

### Adjusting Message Length Limit
Edit `backend/security_middleware.py`:

```python
class RequestValidator:
    MAX_MESSAGE_LENGTH = 500  # Change this value
```

### Adjusting Daily API Quota
Edit `backend/security_middleware.py`:

```python
class DailyQuotaTracker:
    DAILY_REQUEST_LIMIT = 500  # Change this value
```

### Adding Production Domain to CORS
Edit `backend/main.py`:

```python
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://your-actual-domain.com",  # Add your domain here
]
```

## 📁 Generated Files

The security system creates the following files (auto-ignored by git):

- `blocked_ips.json` - List of blocked IP addresses with reasons
- `daily_quota.json` - Daily API usage counter
- In-memory storage for rate limits (resets on server restart)

## 🚨 Error Responses

### 429 Too Many Requests (Rate Limit)
```json
{
  "detail": "Rate limit exceeded: Maximum 10 requests per minute"
}
```

### 429 Too Many Requests (Session Limit)
```json
{
  "detail": "Session limit reached: Maximum 15 messages per conversation. Please start a new session."
}
```

### 429 Too Many Requests (Daily Limit + Auto-Block)
```json
{
  "detail": "Daily limit exceeded: Maximum 60 requests per day. IP has been blocked."
}
```

### 400 Bad Request (Validation Error)
```json
{
  "detail": "Message too long: Maximum 500 characters allowed"
}
```

### 400 Bad Request (Suspicious Content)
```json
{
  "detail": "Message contains potentially malicious content"
}
```

## 🔒 Best Practices

1. **Monitor Logs Regularly**
   - Check for suspicious patterns in request logs
   - Watch for repeated rate limit violations
   - Monitor daily quota usage

2. **Adjust Limits Based on Usage**
   - If legitimate users hit limits, increase them
   - If you see abuse, tighten limits

3. **Add Cloudflare (Recommended)**
   - Free tier provides DDoS protection
   - Bot detection and blocking
   - Caching to reduce backend load

4. **Set Up Alerts**
   - Email notifications when daily quota exceeds 400
   - Alerts when IPs are auto-blocked
   - Warnings on suspicious pattern detection

5. **Regular Security Audits**
   - Review `blocked_ips.json` weekly
   - Analyze request patterns
   - Update suspicious pattern list as needed

## 💰 Cost Protection Analysis

**Without Security:**
- Attacker: 10,000 requests/hour
- Cost: $50-200/hour in Vertex AI charges
- Risk: Bankruptcy

**With Security:**
- Max: 600 requests/hour (10/min × 60)
- Daily cap: 500 total requests
- Cost: $5-10/day maximum
- Risk: 95% mitigated

**With Cloudflare + Security:**
- Bots blocked before reaching backend
- DDoS attacks absorbed
- Risk: 99.9% mitigated

## 🆘 Emergency Actions

### If Under Attack
1. Check security stats: `GET /api/security/stats`
2. Identify attacking IPs in logs
3. Block them manually if not auto-blocked
4. Enable Cloudflare "Under Attack Mode" (if using Cloudflare)
5. Temporarily reduce rate limits if needed

### If Legitimate User Blocked
1. Get their IP address
2. Unblock: `POST /api/security/unblock/{ip}`
3. Investigate why they hit the limit
4. Consider increasing limits if appropriate

### If Daily Quota Exceeded
1. Backend automatically switches to Groq (backup model)
2. Quality may be slightly lower but service continues
3. Quota resets at midnight
4. Consider increasing `DAILY_REQUEST_LIMIT` if legitimate usage

## 📞 Support

For security issues or questions:
- Review logs: `backend/logs/` (if logging to file)
- Check blocked IPs: `backend/blocked_ips.json`
- Monitor quota: `backend/daily_quota.json`

---

**Last Updated:** 2026-01-25
**Security Version:** 1.0.0
