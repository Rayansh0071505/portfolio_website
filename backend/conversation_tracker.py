"""
Conversation Tracker - Tracks user interactions and sends email summaries
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# In-memory session storage (use Redis for production)
sessions: Dict[str, Dict] = {}

class ConversationTracker:
    """Track conversation state and collect user info"""

    def __init__(self, session_id: str):
        self.session_id = session_id

        # Initialize session if not exists
        if session_id not in sessions:
            sessions[session_id] = {
                "messages": [],
                "message_count": 0,
                "user_name": None,
                "user_linkedin": None,
                "asked_for_name": False,
                "asked_for_linkedin": False,
                "started_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }

    def get_session(self) -> Dict:
        """Get session data"""
        return sessions.get(self.session_id, {})

    def update_session(self, **kwargs):
        """Update session data"""
        if self.session_id in sessions:
            sessions[self.session_id].update(kwargs)
            sessions[self.session_id]["last_activity"] = datetime.now().isoformat()

    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        session = self.get_session()
        session["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        session["message_count"] += 1
        session["last_activity"] = datetime.now().isoformat()

    def get_message_count(self) -> int:
        """Get current message count"""
        return self.get_session().get("message_count", 0)

    def should_ask_for_name(self) -> bool:
        """Check if we should ask for user's name (after 1st question)"""
        session = self.get_session()
        return (
            session.get("message_count") == 2 and  # After first Q&A
            not session.get("asked_for_name") and
            not session.get("user_name")
        )

    def should_ask_for_linkedin(self) -> bool:
        """Check if we should ask for LinkedIn (after 3rd question)"""
        session = self.get_session()
        return (
            session.get("message_count") == 6 and  # After third Q&A
            not session.get("asked_for_linkedin") and
            not session.get("user_linkedin")
        )

    def extract_name_from_message(self, message: str) -> Optional[str]:
        """Try to extract name from user message"""
        # Simple patterns for name extraction
        lower_msg = message.lower()

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

    def get_intro_prompt(self) -> str:
        """Get introduction prompt to ask for name"""
        return "\n\nBy the way, I'd love to know who I'm talking to! What's your name?"

    def get_linkedin_prompt(self) -> str:
        """Get LinkedIn prompt"""
        session = self.get_session()
        name = session.get("user_name", "")
        if name:
            return f"\n\nThanks for the great questions, {name}! I'd love to connect with you. Could you share your LinkedIn profile?"
        else:
            return "\n\nI'd love to connect with you! Could you share your LinkedIn profile?"

    def mark_asked_for_name(self):
        """Mark that we've asked for name"""
        self.update_session(asked_for_name=True)

    def mark_asked_for_linkedin(self):
        """Mark that we've asked for LinkedIn"""
        self.update_session(asked_for_linkedin=True)

    def set_user_name(self, name: str):
        """Set user's name"""
        self.update_session(user_name=name)
        logger.info(f"✅ User name set: {name}")

    def set_user_linkedin(self, linkedin: str):
        """Set user's LinkedIn"""
        self.update_session(user_linkedin=linkedin)
        logger.info(f"✅ User LinkedIn set: {linkedin}")

    def get_conversation_summary(self) -> str:
        """Generate conversation summary for email"""
        session = self.get_session()

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


def send_conversation_email(session_id: str):
    """
    Send conversation summary via Mailgun API
    Official Documentation: https://documentation.mailgun.com/docs/mailgun/api-reference/send/mailgun/messages
    """
    try:
        tracker = ConversationTracker(session_id)
        session = tracker.get_session()

        # Don't send email if less than 3 messages
        if session.get("message_count", 0) < 3:
            logger.info(f"⏭️ Skipping email for session {session_id} - too few messages ({session.get('message_count')})")
            return

        # Mailgun configuration - API requires domain name
        mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        mailgun_api_key = os.getenv("MAILGUN_SECRET")

        if not mailgun_api_key:
            logger.error("❌ MAILGUN_SECRET not set in environment variables")
            return

        if not mailgun_domain:
            logger.error("❌ MAILGUN_DOMAIN not set in environment variables")
            return

        # Prepare email content
        user_name = session.get("user_name", "Unknown User")
        user_linkedin = session.get("user_linkedin", "Not provided")
        message_count = session.get("message_count", 0)
        started_at = session.get("started_at", "Unknown")

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
Session ID: {session_id}
Total Messages: {message_count}
Started: {started_at}

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
                🤖 Automated summary from Rayansh's AI Portfolio Assistant<br>
                Powered by Vertex AI & Groq | Built with LangChain & Pinecone
            </p>
        </div>

    </div>
</body>
</html>
"""

        # Mailgun API endpoint: https://api.mailgun.net/v3/YOUR_DOMAIN/messages
        api_endpoint = f"https://api.mailgun.net/v3/{mailgun_domain}/messages"

        # Send via Mailgun API (using requests library as per documentation)
        logger.info(f"📧 Sending email via Mailgun to rayanshsrivastava.ai@gmail.com...")

        response = requests.post(
            api_endpoint,
            auth=("api", mailgun_api_key),  # Authentication as per Mailgun docs
            data={
                "from": f"Rayansh AI Assistant <noreply@{mailgun_domain}>",
                "to": ["rayanshsrivastava.ai@gmail.com"],
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
            logger.info(f"📬 Recipient: rayanshsrivastava.ai@gmail.com | Session: {session_id}")
        else:
            logger.error(f"❌ Mailgun API error: {response.status_code}")
            logger.error(f"Response: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error sending email: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error sending email: {str(e)}")


def cleanup_old_sessions(max_age_hours: int = 24):
    """Clean up sessions older than max_age_hours"""
    try:
        from datetime import timedelta

        current_time = datetime.now()
        to_delete = []

        for session_id, session in sessions.items():
            last_activity = datetime.fromisoformat(session.get("last_activity"))
            age = current_time - last_activity

            if age > timedelta(hours=max_age_hours):
                to_delete.append(session_id)

        for session_id in to_delete:
            del sessions[session_id]
            logger.info(f"🗑️ Cleaned up old session: {session_id}")

    except Exception as e:
        logger.error(f"❌ Error cleaning sessions: {str(e)}")
