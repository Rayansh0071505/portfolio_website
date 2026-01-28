"""
Conversation Tracker - Tracks user interactions and sends email summaries
Uses Groq (primary) and Vertex AI (backup) for generating email summaries
Now with Redis for persistent session storage
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests
import base64
import json
import tempfile
import redis.asyncio as redis_async
from langchain_groq import ChatGroq
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, HumanMessage
from config import get_redis_secret, get_groq_api_key, get_google_key, get_mailgun_domain, get_mailgun_secret

logger = logging.getLogger(__name__)

# ============================================================================
# REDIS CONNECTION FOR SESSION STORAGE
# ============================================================================

_redis_client = None

async def get_redis_client():
    """Get Redis client for session storage"""
    global _redis_client
    if _redis_client is None:
        redis_url = get_redis_secret()
        if not redis_url:
            raise ValueError("REDIS_SECRET not found in config or environment")
        _redis_client = redis_async.from_url(redis_url, decode_responses=True)
        logger.info("✅ Redis client initialized for session storage")
    return _redis_client

# ============================================================================
# AI MODELS FOR EMAIL SUMMARY GENERATION
# ============================================================================

_summary_groq_llm = None
_summary_vertex_llm = None
_google_creds_loaded_summary = False


def get_summary_groq_llm():
    """Get Groq LLM for email summaries (PRIMARY - Free)"""
    global _summary_groq_llm
    if _summary_groq_llm is None:
        groq_api_key = get_groq_api_key()
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in config or environment")

        _summary_groq_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=2048,
            groq_api_key=groq_api_key,
            max_retries=1,
            timeout=30
        )
        logger.info("✅ Groq LLM initialized for email summaries (PRIMARY)")
    return _summary_groq_llm


def get_summary_vertex_llm():
    """Get Vertex AI Gemini for email summaries (BACKUP)"""
    global _summary_vertex_llm, _google_creds_loaded_summary

    if _summary_vertex_llm is None:
        # Load Google credentials if not already loaded
        if not _google_creds_loaded_summary:
            google_key_base64 = get_google_key()
            if google_key_base64:
                try:
                    google_creds_json = base64.b64decode(google_key_base64).decode('utf-8')
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
                        temp_file.write(google_creds_json)
                        credentials_path = temp_file.name
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                    logger.info("✅ Google Cloud credentials configured for email summaries")
                except Exception as e:
                    logger.error(f"❌ Failed to decode GOOGLE_KEY: {str(e)}")
            _google_creds_loaded_summary = True

        # Get project ID
        google_key = get_google_key()
        project_id = None
        if google_key:
            try:
                decoded_key = base64.b64decode(google_key)
                key_data = json.loads(decoded_key)
                project_id = key_data.get("project_id")
            except Exception as e:
                logger.error(f"❌ Error extracting project ID: {e}")

        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID")

        _summary_vertex_llm = ChatVertexAI(
            model_name="gemini-2.5-flash-lite",
            project=project_id,
            temperature=0.3,
            max_tokens=2048,
            timeout=30,
            max_retries=1,
        )
        logger.info("✅ Vertex AI Gemini initialized for email summaries (BACKUP)")
    return _summary_vertex_llm


def generate_conversation_summary(messages: List[Dict], user_name: str = "Unknown User", user_linkedin: str = "Not provided") -> str:
    """
    Generate a concise summary of the conversation using AI
    Uses Groq (primary) and Vertex AI (backup)

    Args:
        messages: List of conversation messages
        user_name: User's name
        user_linkedin: User's LinkedIn URL

    Returns:
        AI-generated summary of the conversation
    """
    try:
        # Prepare conversation text
        conversation_text = ""
        for msg in messages:
            role = "USER" if msg["role"] == "user" else "RAYANSH AI"
            content = msg["content"]
            conversation_text += f"{role}: {content}\n\n"

        # Prompt for summary
        system_prompt = """You are a professional conversation summarizer. Create a concise, informative summary of this portfolio chat conversation.

Focus on:
- Main topics discussed
- User's primary interests or questions
- Key information shared about Rayansh's experience
- Overall tone and engagement level

Keep the summary to 3-5 bullet points, professional and clear."""

        user_prompt = f"""Summarize this conversation between a visitor ({user_name}) and Rayansh's AI assistant:

{conversation_text}

Provide a concise summary suitable for an email notification."""

        # Try Groq first (PRIMARY)
        try:
            logger.info("🤖 Generating email summary with Groq (PRIMARY)...")
            groq_llm = get_summary_groq_llm()

            messages_to_send = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = groq_llm.invoke(messages_to_send)
            summary = response.content
            logger.info("✅ Email summary generated with Groq")
            return summary

        except Exception as groq_error:
            logger.warning(f"⚠️ Groq failed for email summary: {groq_error}")
            logger.info("🔄 Falling back to Vertex AI for email summary...")

            # Fallback to Vertex AI (BACKUP)
            try:
                vertex_llm = get_summary_vertex_llm()

                messages_to_send = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]

                response = vertex_llm.invoke(messages_to_send)
                summary = response.content
                logger.info("✅ Email summary generated with Vertex AI (backup)")
                return summary

            except Exception as vertex_error:
                logger.error(f"❌ Vertex AI also failed for email summary: {vertex_error}")
                # Return basic summary if both fail
                return f"Conversation with {user_name} - {len(messages)} messages exchanged."

    except Exception as e:
        logger.error(f"❌ Error generating conversation summary: {e}")
        return f"Conversation with {user_name} - {len(messages)} messages exchanged."

class ConversationTracker:
    """Track conversation state and collect user info using Redis"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.redis_key = f"session:{session_id}"
        self._redis_client = None

    async def _get_redis(self):
        """Get Redis client (lazy initialization)"""
        if self._redis_client is None:
            self._redis_client = await get_redis_client()
        return self._redis_client

    async def initialize(self):
        """Initialize session in Redis if not exists"""
        redis_client = await self._get_redis()

        # Check if session exists
        exists = await redis_client.exists(self.redis_key)

        if not exists:
            # Create new session with 24 hour expiration
            session_data = {
                "messages": json.dumps([]),
                "message_count": 0,
                "user_name": "",
                "user_linkedin": "",
                "user_email": "",
                "user_ip": "",
                "asked_for_name": "false",
                "asked_for_linkedin": "false",
                "started_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            await redis_client.hset(self.redis_key, mapping=session_data)
            # Set expiration to 24 hours
            await redis_client.expire(self.redis_key, 86400)
            logger.info(f"📝 New session created in Redis: {self.session_id}")

    async def get_session(self) -> Dict:
        """Get session data from Redis"""
        try:
            redis_client = await self._get_redis()
            data = await redis_client.hgetall(self.redis_key)

            if not data:
                return {}

            # Convert Redis hash to dict with proper types
            return {
                "messages": json.loads(data.get("messages", "[]")),
                "message_count": int(data.get("message_count", 0)),
                "user_name": data.get("user_name") or None,
                "user_linkedin": data.get("user_linkedin") or None,
                "user_email": data.get("user_email") or None,
                "user_ip": data.get("user_ip") or None,
                "asked_for_name": data.get("asked_for_name") == "true",
                "asked_for_linkedin": data.get("asked_for_linkedin") == "true",
                "started_at": data.get("started_at"),
                "last_activity": data.get("last_activity")
            }
        except Exception as e:
            logger.error(f"❌ Error getting session from Redis: {str(e)}")
            return {}

    async def update_session(self, **kwargs):
        """Update session data in Redis"""
        try:
            redis_client = await self._get_redis()

            # Prepare updates
            updates = {}
            for key, value in kwargs.items():
                if isinstance(value, bool):
                    updates[key] = "true" if value else "false"
                elif isinstance(value, (list, dict)):
                    updates[key] = json.dumps(value)
                else:
                    updates[key] = str(value) if value is not None else ""

            # Always update last_activity
            updates["last_activity"] = datetime.now().isoformat()

            # Update Redis hash
            await redis_client.hset(self.redis_key, mapping=updates)

            # Refresh expiration to 24 hours
            await redis_client.expire(self.redis_key, 86400)

        except Exception as e:
            logger.error(f"❌ Error updating session in Redis: {str(e)}")

    async def add_message(self, role: str, content: str):
        """Add message to conversation history in Redis"""
        try:
            session = await self.get_session()
            messages = session.get("messages", [])
            messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

            # Update Redis with new message and incremented count
            await self.update_session(
                messages=messages,
                message_count=session.get("message_count", 0) + 1
            )
        except Exception as e:
            logger.error(f"❌ Error adding message to Redis: {str(e)}")

    async def get_message_count(self) -> int:
        """Get current message count from Redis"""
        session = await self.get_session()
        return session.get("message_count", 0)

    async def should_ask_for_name(self) -> bool:
        """Check if we should ask for user's name and contact (after 1st question)"""
        session = await self.get_session()
        return (
            session.get("message_count") == 1 and  # After first user message (before AI response added)
            not session.get("asked_for_name") and
            not session.get("user_name")
        )

    async def should_ask_for_linkedin(self) -> bool:
        """No longer needed - we ask for both name and contact together"""
        return False

    def extract_name_from_message(self, message: str, session: Optional[Dict] = None) -> Optional[str]:
        """Try to extract name from user message"""
        # Simple patterns for name extraction
        lower_msg = message.lower().strip()

        # Pattern: "my name is X", "i'm X", "i am X", "this is X", "call me X"
        patterns = [
            "my name is ",
            "i'm ",
            "i am ",
            "this is ",
            "call me ",
            "name's ",
        ]

        for pattern in patterns:
            if pattern in lower_msg:
                # Extract the name after the pattern
                idx = lower_msg.index(pattern) + len(pattern)
                name_part = message[idx:].strip()
                # Get first 1-3 words as name
                name_words = name_part.split()[:3]
                # Remove common words
                name_words = [w for w in name_words if w.lower() not in ['and', 'the', 'a']]
                if name_words:
                    return ' '.join(name_words).strip('.,!?')

        # If message is just a single word/name after we asked for it
        if session and session.get("asked_for_name") and not session.get("user_name"):
            # Check if message is short (likely just a name)
            words = message.strip().split()
            if 1 <= len(words) <= 3 and not any(char in message for char in ['@', 'http', '?', '!']):
                # Likely just a name
                return message.strip().title()

        return None

    def extract_linkedin_from_message(self, message: str) -> Optional[str]:
        """Try to extract LinkedIn URL from user message"""
        # Check if message contains linkedin.com
        if "linkedin.com" in message.lower():
            # Extract URL
            words = message.split()
            for word in words:
                if "linkedin.com" in word.lower():
                    # Clean up URL
                    url = word.strip('.,!?<>()"\'')
                    if not url.startswith('http'):
                        url = 'https://' + url
                    return url
        return None

    def extract_email_from_message(self, message: str) -> Optional[str]:
        """Try to extract email from user message"""
        import re
        # Simple email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, message)
        if match:
            return match.group(0)
        return None

    def get_intro_prompt(self) -> str:
        """Get introduction prompt to ask for name and contact info"""
        return "\n\nBy the way, I'd love to know who I'm talking to! What's your name, and could you share your LinkedIn profile or email?"

    def get_linkedin_prompt(self) -> str:
        """No longer used - we ask for everything together"""
        return ""

    async def mark_asked_for_name(self):
        """Mark that we've asked for name"""
        await self.update_session(asked_for_name=True)

    async def mark_asked_for_linkedin(self):
        """Mark that we've asked for LinkedIn"""
        await self.update_session(asked_for_linkedin=True)

    async def set_user_name(self, name: str):
        """Set user's name"""
        await self.update_session(user_name=name)
        logger.info(f"✅ User name set: {name}")

    async def set_user_linkedin(self, linkedin: str):
        """Set user's LinkedIn"""
        await self.update_session(user_linkedin=linkedin)
        logger.info(f"✅ User LinkedIn set: {linkedin}")

    async def set_user_email(self, email: str):
        """Set user's email"""
        await self.update_session(user_email=email)
        logger.info(f"✅ User email set: {email}")

    async def set_user_ip(self, ip: str):
        """Set user's IP address"""
        await self.update_session(user_ip=ip)
        logger.info(f"📍 User IP set: {ip}")

    async def get_conversation_summary(self) -> str:
        """Generate conversation summary for email"""
        session = await self.get_session()

        summary = f"""
========================================
CONVERSATION SUMMARY
========================================

Session ID: {self.session_id}
Started: {session.get('started_at')}
Ended: {datetime.now().isoformat()}
Total Messages: {session.get('message_count')}

User Information:
- Name: {session.get('user_name') or 'Not provided'}
- LinkedIn: {session.get('user_linkedin') or 'Not provided'}

Conversation:
----------------------------------------
"""

        for msg in session.get("messages", []):
            role = "USER" if msg["role"] == "user" else "RAYANSH AI"
            time = msg["timestamp"]
            content = msg["content"]
            summary += f"\n[{time}] {role}:\n{content}\n\n"

        summary += """
========================================
END OF CONVERSATION
========================================
"""

        return summary

    async def delete_session(self):
        """Delete session from Redis"""
        try:
            redis_client = await self._get_redis()
            deleted = await redis_client.delete(self.redis_key)
            if deleted:
                logger.info(f"🗑️ Session deleted from Redis: {self.session_id}")
            else:
                logger.warning(f"⚠️ Session not found in Redis: {self.session_id}")
        except Exception as e:
            logger.error(f"❌ Error deleting session from Redis: {str(e)}")


async def send_conversation_email(session_id: str):
    """
    Send conversation summary via Mailgun API
    Official Documentation: https://documentation.mailgun.com/docs/mailgun/api-reference/send/mailgun/messages
    """
    try:
        tracker = ConversationTracker(session_id)
        await tracker.initialize()
        session = await tracker.get_session()

        # Don't send email if less than 3 messages
        if session.get("message_count", 0) < 3:
            logger.info(f"⏭️ Skipping email for session {session_id} - too few messages ({session.get('message_count')})")
            return

        # Mailgun configuration - API requires domain name
        mailgun_domain = get_mailgun_domain()
        mailgun_api_key = get_mailgun_secret()

        if not mailgun_api_key:
            logger.error("❌ MAILGUN_SECRET not set in environment variables")
            return

        if not mailgun_domain:
            logger.error("❌ MAILGUN_DOMAIN not set in environment variables")
            return

        # Prepare email content
        user_name = session.get("user_name", "Unknown User")
        user_linkedin = session.get("user_linkedin", "Not provided")
        user_email = session.get("user_email", "Not provided")
        user_ip = session.get("user_ip", "Unknown")
        message_count = session.get("message_count", 0)
        started_at = session.get("started_at", "Unknown")

        # Generate AI summary (using Groq primary, Vertex AI backup)
        logger.info("📝 Generating AI summary for email...")
        ai_summary = generate_conversation_summary(
            messages=session.get("messages", []),
            user_name=user_name,
            user_linkedin=user_linkedin
        )

        # Email subject
        subject = f"💬 New Portfolio Chat: {user_name}"

        # Plain text version (fallback)
        text_body = f"""
NEW PORTFOLIO CHAT CONVERSATION
================================

USER INFORMATION
----------------
Name: {user_name}
LinkedIn: {user_linkedin}
Email: {user_email}
IP Address: {user_ip}
Session ID: {session_id}
Total Messages: {message_count}
Started: {started_at}

AI SUMMARY (Generated by Groq)
-------------------------------
{ai_summary}

CONVERSATION TRANSCRIPT
-----------------------
"""
        for msg in session.get("messages", []):
            role = "USER" if msg["role"] == "user" else "RAYANSH AI"
            timestamp = msg.get("timestamp", "")
            content = msg["content"]
            text_body += f"\n[{timestamp}] {role}:\n{content}\n"

        text_body += "\n================================\nEnd of Conversation\n================================"

        # HTML version (styled)
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #3b82f6 0%, #14b8a6 100%); padding: 30px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">💬 New Chat Conversation</h1>
            <p style="color: #e0f2fe; margin: 10px 0 0 0; font-size: 14px;">From your portfolio AI assistant</p>
        </div>

        <!-- User Info Card -->
        <div style="padding: 30px;">
            <div style="background: #f1f5f9; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 30px;">
                <h2 style="margin: 0 0 15px 0; color: #1e293b; font-size: 18px; font-weight: 600;">👤 User Information</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; color: #64748b; font-weight: 500; width: 30%;">Name:</td>
                        <td style="padding: 8px 0; color: #1e293b; font-weight: 600;">{user_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #64748b; font-weight: 500;">LinkedIn:</td>
                        <td style="padding: 8px 0;">
                            {f'<a href="{user_linkedin}" style="color: #3b82f6; text-decoration: none;">{user_linkedin}</a>' if user_linkedin != "Not provided" else '<span style="color: #94a3b8;">Not provided</span>'}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #64748b; font-weight: 500;">Email:</td>
                        <td style="padding: 8px 0;">
                            {f'<a href="mailto:{user_email}" style="color: #3b82f6; text-decoration: none;">{user_email}</a>' if user_email != "Not provided" else '<span style="color: #94a3b8;">Not provided</span>'}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #64748b; font-weight: 500;">IP Address:</td>
                        <td style="padding: 8px 0; color: #64748b; font-family: monospace; font-size: 13px;">{user_ip}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #64748b; font-weight: 500;">Messages:</td>
                        <td style="padding: 8px 0; color: #1e293b;">{message_count}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #64748b; font-weight: 500;">Session ID:</td>
                        <td style="padding: 8px 0; color: #64748b; font-size: 12px; font-family: monospace;">{session_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #64748b; font-weight: 500;">Started:</td>
                        <td style="padding: 8px 0; color: #64748b; font-size: 13px;">{started_at}</td>
                    </tr>
                </table>
            </div>

            <!-- AI Summary -->
            <div style="background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 30px;">
                <h2 style="margin: 0 0 15px 0; color: #92400e; font-size: 18px; font-weight: 600;">🤖 AI Summary</h2>
                <p style="margin: 0; color: #78350f; font-size: 14px; line-height: 1.8; white-space: pre-wrap;">{ai_summary}</p>
                <p style="margin: 10px 0 0 0; color: #d97706; font-size: 12px; font-style: italic;">Generated by Groq (Llama 3.3)</p>
            </div>

            <!-- Conversation Transcript -->
            <h2 style="margin: 0 0 20px 0; color: #1e293b; font-size: 18px; font-weight: 600;">📝 Conversation Transcript</h2>
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px;">
"""

        # Add messages
        for idx, msg in enumerate(session.get("messages", [])):
            role = "USER" if msg["role"] == "user" else "RAYANSH AI"
            role_color = "#3b82f6" if msg["role"] == "user" else "#14b8a6"
            bg_color = "#eff6ff" if msg["role"] == "user" else "#f0fdfa"
            content = msg["content"].replace('\n', '<br>').replace('  ', '&nbsp;&nbsp;')
            timestamp = msg.get("timestamp", "")

            html_body += f"""
                <div style="margin-bottom: 20px; padding: 15px; background: {bg_color}; border-radius: 8px; border-left: 3px solid {role_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="color: {role_color}; font-weight: 700; font-size: 14px;">{role}</span>
                        <span style="color: #94a3b8; font-size: 11px;">{timestamp[:19] if timestamp else ''}</span>
                    </div>
                    <p style="margin: 0; color: #334155; font-size: 14px; line-height: 1.6;">{content}</p>
                </div>
"""

        html_body += """
            </div>
        </div>

        <!-- Footer -->
        <div style="background: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                🤖 Automated summary from Rayansh's AI Portfolio Assistant
            </p>
        </div>

    </div>
</body>
</html>
"""

        # Mailgun API endpoint: https://api.mailgun.net/v3/YOUR_DOMAIN/messages
        api_endpoint = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

        # Send via Mailgun API (using requests library as per documentation)
        logger.info(f"📧 Sending email via Mailgun to rayanshsrivastava1@gmail.com...")

        response = requests.post(
            api_endpoint,
            auth=("api", mailgun_api_key),  # Authentication as per Mailgun docs
            data={
                "from": f"Rayansh AI Assistant <noreply@{mailgun_domain}>",
                "to": ["rayanshsrivastava1@gmail.com"],
                "subject": subject,
                "text": text_body,
                "html": html_body,
                "o:tag": ["portfolio-chat", "conversation-summary"],  # Optional: tags for tracking
                "o:tracking": "yes",  # Optional: enable tracking
            },
            timeout=15
        )

        # Check response
        if response.status_code == 200:
            response_data = response.json()
            message_id = response_data.get("id", "unknown")
            logger.info(f"✅ Email sent successfully! Message ID: {message_id}")
            logger.info(f"📬 Recipient: rayanshsrivastava1@gmail.com | Session: {session_id}")
        else:
            logger.error(f"❌ Mailgun API error: {response.status_code}")
            logger.error(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error sending email: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error sending email: {str(e)}")


async def cleanup_old_sessions(max_age_hours: int = 24):
    """Clean up sessions older than max_age_hours from Redis"""
    try:
        from datetime import timedelta

        redis_client = await get_redis_client()
        current_time = datetime.now()
        deleted_count = 0

        # Scan all session keys
        async for key in redis_client.scan_iter(match="session:*"):
            try:
                # Get last_activity from session
                last_activity_str = await redis_client.hget(key, "last_activity")

                if last_activity_str:
                    last_activity = datetime.fromisoformat(last_activity_str)
                    age = current_time - last_activity

                    if age > timedelta(hours=max_age_hours):
                        await redis_client.delete(key)
                        deleted_count += 1
                        logger.info(f"🗑️ Cleaned up old session: {key}")
            except Exception as e:
                logger.error(f"❌ Error processing session {key}: {str(e)}")

        if deleted_count > 0:
            logger.info(f"✅ Cleaned up {deleted_count} old sessions from Redis")

    except Exception as e:
        logger.error(f"❌ Error cleaning sessions: {str(e)}")
