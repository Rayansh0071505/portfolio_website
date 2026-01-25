# 📧 Conversation Tracking & Email Summaries

## Overview
The AI chat now automatically tracks conversations and sends email summaries to `rayanshsrivastava.ai@gmail.com` using Mailgun.

## Features

### 1. **Smart Information Collection**
- ✅ **After 1st question**: Asks for user's name
- ✅ **After 3rd question**: Asks for LinkedIn profile
- ✅ **Automatic extraction**: Detects name/LinkedIn from messages

### 2. **Conversation Tracking**
- Message count per session
- Full conversation history
- User information (name, LinkedIn)
- Session timestamps
- Activity tracking

### 3. **Email Summaries**
- Sent when session ends (user leaves/closes chat)
- Beautiful HTML email with:
  - User information
  - Full conversation transcript
  - Session metadata
  - Timestamps for each message

## Setup

### 1. Get Mailgun Credentials

**Sign up for Mailgun:**
1. Go to https://www.mailgun.com/
2. Create account (Free: 100 emails/day for 3 months trial)
3. Verify email and complete sign up
4. Go to **Sending** → **Domain Settings**
5. Note your domain (e.g., `sandboxXXXXXXXX.mailgun.org`)
6. Go to **Settings** → **API Keys**
7. Copy your **Private API key** (starts with `key-...`)

**Official Documentation:**
- [Mailgun Getting Started](https://documentation.mailgun.com/docs/mailgun/get-started)
- [Python Email API Guide](https://www.mailgun.com/blog/it-and-engineering/send-email-using-python/)
- [Messages API Reference](https://documentation.mailgun.com/docs/mailgun/api-reference/send/mailgun/messages)

### 2. Configure Environment Variables

Add to `backend/.env`:

```env
# Mailgun Configuration
MAILGUN_SECRET=your_api_key_here
MAILGUN_DOMAIN=your_domain.mailgun.org
```

**Example:**
```env
MAILGUN_SECRET=key-1234567890abcdef
MAILGUN_DOMAIN=sandboxXXXXXXXX.mailgun.org
```

### 3. Verify Recipient Email (IMPORTANT for Sandbox Domains)

**For sandbox domains (sandboxXXXX.mailgun.org), you MUST authorize recipients:**

1. Go to **Mailgun Dashboard** → **Sending** → **Domain Settings**
2. Select your sandbox domain
3. Scroll to **Authorized Recipients** section
4. Click **"Add Recipient"**
5. Enter: `rayanshsrivastava.ai@gmail.com`
6. Click **"Add"**
7. **Check your Gmail inbox** for verification email from Mailgun
8. **Click the verification link** in the email

⚠️ **Important:** Emails will NOT send until the recipient email is verified!

**For production domains:** Once you verify a custom domain, you can send to any email without authorization.

## How It Works

### Flow Diagram:

```
User opens chat
  ↓
User asks 1st question → AI responds
  ↓
Message count = 2 → AI asks: "What's your name?"
  ↓
User provides name → Extracted & stored
  ↓
User asks 3rd question → AI responds
  ↓
Message count = 6 → AI asks: "Share your LinkedIn?"
  ↓
User provides LinkedIn → Extracted & stored
  ↓
User closes chat/navigates away
  ↓
Frontend calls /api/chat/end-session
  ↓
Backend sends email summary via Mailgun
  ↓
Email arrives at rayanshsrivastava.ai@gmail.com
```

### Name Extraction Patterns:

Automatically detects:
- "My name is John Doe"
- "I'm John"
- "I am John Doe"
- "This is John"
- "Call me John"

### LinkedIn Extraction:

Detects any message containing:
- `linkedin.com/in/username`
- Automatically adds `https://` if missing

## API Endpoints

### POST /api/chat
```json
{
  "message": "What's your experience?",
  "session_id": "session_abc123",
  "user_name": "John Doe"  // optional
}
```

**Response:**
```json
{
  "message": "I have 5+ years of experience...\n\nBy the way, I'd love to know who I'm talking to! What's your name?",
  "session_id": "session_abc123",
  "timestamp": "2026-01-24T12:00:00",
  "response_time": "2.3s",
  "model": "Vertex AI (Gemini 2.0 Flash)"
}
```

### POST /api/chat/end-session
```json
{
  "session_id": "session_abc123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Session ended. Summary will be emailed.",
  "timestamp": "2026-01-24T12:10:00"
}
```

### GET /api/session/{session_id}
Get current session information:

**Response:**
```json
{
  "session_id": "session_abc123",
  "message_count": 8,
  "user_name": "John Doe",
  "user_linkedin": "https://linkedin.com/in/johndoe",
  "started_at": "2026-01-24T12:00:00",
  "last_activity": "2026-01-24T12:09:45"
}
```

## Email Template

### Subject Line:
```
New Portfolio Chat: John Doe
```

### Email Content:
```
========================================
New Chat Session Summary
========================================

User Information:
- Name: John Doe
- LinkedIn: https://linkedin.com/in/johndoe
- Session ID: session_abc123
- Messages: 8
- Started: 2026-01-24T12:00:00

Conversation Transcript:
----------------------------------------

[2026-01-24T12:00:15] USER:
What's your experience with AI?

[2026-01-24T12:00:17] RAYANSH AI:
I have 5+ years of experience building production AI systems...

By the way, I'd love to know who I'm talking to! What's your name?

[2026-01-24T12:00:30] USER:
My name is John Doe

[2026-01-24T12:00:32] RAYANSH AI:
Nice to meet you, John! Let me tell you more about my work...

... (continues)
```

## Session Management

### Automatic Cleanup:
- Sessions older than 24 hours are automatically deleted
- Runs in background after each chat message
- Prevents memory buildup

### Manual Cleanup:
```python
from conversation_tracker import cleanup_old_sessions

# Clean sessions older than 12 hours
cleanup_old_sessions(max_age_hours=12)
```

## Testing

### Test Mailgun Configuration First:

**Before using the conversation tracker, verify Mailgun works:**

```bash
cd backend
python test_mailgun.py
```

This will:
1. Check if environment variables are set
2. Send a test email to rayanshsrivastava.ai@gmail.com
3. Show detailed error messages if something is wrong

Expected output:
```
✅ SUCCESS!
Message ID: <some-id@mailgun.org>
Response: Queued. Thank you.

📬 Check your email: rayanshsrivastava.ai@gmail.com
```

### Test Name Collection:
```bash
# Start server
cd backend
python main.py

# In browser or Postman:
POST http://localhost:8000/api/chat
{
  "message": "What projects have you worked on?"
}

# Response should include name prompt after 1st Q&A
```

### Test LinkedIn Collection:
```bash
# Continue conversation (3rd question)
POST http://localhost:8000/api/chat
{
  "message": "Tell me about RAG systems",
  "session_id": "session_abc123"
}

# Response should include LinkedIn prompt after 3rd Q&A
```

### Test Email:
```bash
# End session
POST http://localhost:8000/api/chat/end-session
{
  "session_id": "session_abc123"
}

# Check email: rayanshsrivastava.ai@gmail.com
```

## Production Considerations

### 1. **Use Redis for Session Storage**
Current implementation uses in-memory dict. For production:

```python
# Use Redis instead
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
```

### 2. **Rate Limiting**
Add rate limiting to prevent email spam:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat/end-session")
@limiter.limit("5/minute")
async def end_session(...):
    ...
```

### 3. **Email Queue**
Use task queue (Celery/Redis) for sending emails:

```python
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379')

@app.task
def send_email(session_id):
    send_conversation_email(session_id)
```

### 4. **GDPR Compliance**
- Add privacy notice to chat
- Provide opt-out option
- Auto-delete conversations after X days

## Troubleshooting

### Email not sending?
1. Check Mailgun API key is correct
2. Verify domain in Mailgun dashboard
3. Add recipient to authorized recipients (sandbox)
4. Check backend logs for errors

### Name/LinkedIn not extracted?
- Check message patterns in `conversation_tracker.py`
- Add more patterns if needed
- Users can still manually provide info

### Session not ending?
- Ensure frontend calls `endSession()` on unmount
- Check browser console for API errors
- Verify CORS settings allow POST requests

## Example Integration

### React Component:
```typescript
import { useEffect } from 'react';
import { endSession } from './chatApi';

function ChatComponent() {
  const sessionId = 'session_123';

  useEffect(() => {
    // End session when component unmounts
    return () => {
      endSession(sessionId);
    };
  }, [sessionId]);

  return <div>Chat UI</div>;
}
```

## Success Metrics

After implementing, you'll receive emails with:
- ✅ Who chatted with your AI
- ✅ What they asked about
- ✅ Their LinkedIn profile (for networking)
- ✅ Full conversation context
- ✅ When they visited

This helps you:
- **Follow up** with interested candidates/clients
- **Track** what people are asking
- **Improve** AI responses based on real conversations
- **Network** via LinkedIn connections

---

**Enjoy your automated conversation tracking! 🚀**
