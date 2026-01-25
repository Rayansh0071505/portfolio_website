"""
FastAPI Backend for Rayansh's Personal AI Assistant
with Conversation Tracking and Email Summaries
SECURITY: Rate limiting, IP blocking, request validation, quota tracking
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
import logging

# Import the AI assistant and conversation tracker
from personal_ai import rayansh_ai
from conversation_tracker import ConversationTracker, send_conversation_email, cleanup_old_sessions

# Import security middleware
from security_middleware import (
    rate_limiter,
    session_limiter,
    RequestValidator,
    quota_tracker,
    get_client_ip
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Rayansh's Personal AI API",
    description="AI-powered chat assistant with conversation tracking",
    version="1.0.0"
)

# CORS middleware - SECURITY: Only allow requests from your frontend
# TODO: Replace with your actual production domain when deployed
ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative React dev server
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    # Add your production domain here, e.g.:
    # "https://your-portfolio-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Restricted to frontend only
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only allow needed methods
    allow_headers=["Content-Type"],  # Only allow needed headers
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_name: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    timestamp: str
    response_time: str
    model: str
    follow_up: Optional[str] = None  # For automatic follow-up messages

class SessionEndRequest(BaseModel):
    session_id: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    ai_initialized: bool

# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize AI agent on startup"""
    try:
        logger.info("🚀 Initializing Rayansh AI Assistant...")
        await rayansh_ai.initialize()
        logger.info("✅ Rayansh AI Assistant ready!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI: {str(e)}")

# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_initialized": rayansh_ai.agent is not None
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, request: Request, background_tasks: BackgroundTasks):
    """
    Chat with Rayansh's AI assistant with conversation tracking

    SECURITY CHECKS:
    - IP-based rate limiting (10/min, 50/hour, 30/day)
    - Session message limits (15 max)
    - Request validation (message length, suspicious patterns)
    - Daily API quota (500/day)
    - Auto IP blocking on violations

    CONVERSATION TRACKING:
    - Asks for name after 1st question
    - Asks for LinkedIn after 3rd question
    - Stores conversation for email summary
    """
    try:
        # ========== SECURITY LAYER 1: IP EXTRACTION ==========
        client_ip = get_client_ip(request)
        logger.info(f"📥 Request from IP: {client_ip}")

        # ========== SECURITY LAYER 2: RATE LIMITING ==========
        is_allowed, rate_error = rate_limiter.check_rate_limit(client_ip)
        if not is_allowed:
            logger.warning(f"🚫 Rate limit blocked: {client_ip} - {rate_error}")
            raise HTTPException(status_code=429, detail=rate_error)

        # ========== SECURITY LAYER 3: REQUEST VALIDATION ==========
        is_valid, validation_error = RequestValidator.validate_message(chat_request.message)
        if not is_valid:
            logger.warning(f"⚠️ Invalid request from {client_ip}: {validation_error}")
            raise HTTPException(status_code=400, detail=validation_error)

        # Generate session ID if not provided
        if not chat_request.session_id:
            chat_request.session_id = f"session_{uuid.uuid4().hex[:16]}"

        # ========== SECURITY LAYER 4: SESSION MESSAGE LIMIT ==========
        is_allowed_session, session_error = session_limiter.check_session_limit(chat_request.session_id)
        if not is_allowed_session:
            logger.warning(f"⚠️ Session limit reached: {chat_request.session_id}")
            raise HTTPException(status_code=429, detail=session_error)

        # ========== SECURITY LAYER 5: DAILY QUOTA CHECK ==========
        quota_ok, quota_error = quota_tracker.check_quota()
        if not quota_ok:
            logger.error(f"🚨 Daily quota exceeded - using backup model")
            # Don't block request, just log - backup model (Groq) will be used
            # raise HTTPException(status_code=503, detail=quota_error)

        logger.info(f"💬 Chat request from session {chat_request.session_id} (IP: {client_ip}): {chat_request.message[:50]}...")

        # Initialize conversation tracker
        tracker = ConversationTracker(chat_request.session_id)

        # Store user IP (first time only)
        if not tracker.get_session().get("user_ip"):
            tracker.set_user_ip(client_ip)

        # Extract name, LinkedIn, or email from message if present
        extracted_name = tracker.extract_name_from_message(chat_request.message)
        if extracted_name and not tracker.get_session().get("user_name"):
            tracker.set_user_name(extracted_name)

        extracted_linkedin = tracker.extract_linkedin_from_message(chat_request.message)
        if extracted_linkedin and not tracker.get_session().get("user_linkedin"):
            tracker.set_user_linkedin(extracted_linkedin)

        extracted_email = tracker.extract_email_from_message(chat_request.message)
        if extracted_email and not tracker.get_session().get("user_email"):
            tracker.set_user_email(extracted_email)

        # Add user message to tracker
        tracker.add_message("user", chat_request.message)

        # Get AI response
        response = await rayansh_ai.chat(
            message=chat_request.message,
            session_id=chat_request.session_id,
            user_name=chat_request.user_name or tracker.get_session().get("user_name")
        )

        # ========== INCREMENT SECURITY COUNTERS ==========
        session_limiter.increment_session(chat_request.session_id)
        quota_tracker.increment_quota()

        ai_message = response["message"]
        follow_up_message = None

        # Check if user just provided contact info (after we asked)
        session = tracker.get_session()
        if session.get("asked_for_name") and (extracted_name or extracted_email or extracted_linkedin):
            # User just provided their info - acknowledge it warmly
            parts = []
            if extracted_name:
                parts.append(f"Nice to meet you, {extracted_name}!")
            if extracted_email or extracted_linkedin:
                contact_info = []
                if extracted_email:
                    contact_info.append("email")
                if extracted_linkedin:
                    contact_info.append("LinkedIn")
                parts.append(f"Thanks for sharing your {' and '.join(contact_info)}.")

            if parts:
                # If they ONLY provided name (no other content), give a personalized greeting
                if len(chat_request.message.strip().split()) <= 3:
                    ai_message = f"Nice to meet you, {extracted_name}! How can I help you today?"
                else:
                    acknowledgment = " ".join(parts) + " "
                    ai_message = acknowledgment + ai_message

        # Check if we should ask for name and contact (after 1st question)
        elif tracker.should_ask_for_name():
            follow_up_message = tracker.get_intro_prompt()
            tracker.mark_asked_for_name()
            logger.info(f"🙋 Asking for name and contact in session {chat_request.session_id}")

        # Add AI response to tracker
        tracker.add_message("assistant", ai_message)

        # Add follow-up to tracker if exists
        if follow_up_message:
            tracker.add_message("assistant", follow_up_message)

        # Schedule cleanup of old sessions in background
        background_tasks.add_task(cleanup_old_sessions, max_age_hours=24)

        return ChatResponse(
            message=ai_message,
            session_id=chat_request.session_id,
            timestamp=response["timestamp"],
            response_time=response["response_time"],
            model=response["model"],
            follow_up=follow_up_message
        )

    except HTTPException:
        # Re-raise HTTP exceptions (rate limits, validation errors, etc.)
        raise
    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/api/chat/end-session")
async def end_session(request: SessionEndRequest, background_tasks: BackgroundTasks):
    """
    End a chat session and send email summary

    Call this when user:
    - Closes the chat window
    - Navigates away
    - Explicitly ends conversation
    """
    try:
        logger.info(f"🏁 Ending session: {request.session_id}")

        # Send email summary in background
        background_tasks.add_task(send_conversation_email, request.session_id)

        return {
            "status": "success",
            "message": f"Session {request.session_id} ended. Summary will be emailed.",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error ending session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")

@app.post("/api/chat/clear/{session_id}")
async def clear_session(session_id: str, background_tasks: BackgroundTasks):
    """
    Clear chat history for a session and send email summary
    """
    try:
        # Send email before clearing
        background_tasks.add_task(send_conversation_email, session_id)

        # Clear the session
        rayansh_ai.clear_session(session_id)

        # Clear session limiter counter
        session_limiter.clear_session(session_id)

        return {
            "status": "success",
            "message": f"Session {session_id} cleared and summary emailed.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    try:
        tracker = ConversationTracker(session_id)
        session = tracker.get_session()

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "message_count": session.get("message_count", 0),
            "user_name": session.get("user_name"),
            "user_linkedin": session.get("user_linkedin"),
            "user_email": session.get("user_email"),
            "user_ip": session.get("user_ip"),
            "started_at": session.get("started_at"),
            "last_activity": session.get("last_activity")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting session info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/status")
async def get_status():
    """Get AI assistant status"""
    return {
        "ai_initialized": rayansh_ai.agent is not None,
        "using_backup": rayansh_ai.use_backup,
        "model": "Groq (Llama 3.3)" if rayansh_ai.use_backup else "Vertex AI (Gemini 2.5 Flash)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/security/stats")
async def get_security_stats():
    """
    Get security statistics (for monitoring)
    Shows rate limit status and blocked IPs
    """
    return {
        "blocked_ips": rate_limiter.blocked_ips,
        "daily_quota": {
            "used": quota_tracker.quota_data.get("count", 0),
            "limit": quota_tracker.DAILY_REQUEST_LIMIT,
            "date": quota_tracker.quota_data.get("date")
        },
        "limits": {
            "per_minute": 10,
            "per_hour": 50,
            "per_day": 30,
            "messages_per_session": session_limiter.MAX_MESSAGES_PER_SESSION
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/security/unblock/{ip_address}")
async def unblock_ip(ip_address: str):
    """
    Manually unblock an IP address
    NOTE: You should add authentication to this endpoint in production
    """
    if ip_address in rate_limiter.blocked_ips:
        del rate_limiter.blocked_ips[ip_address]
        rate_limiter._save_blocked_ips()
        logger.info(f"✅ Unblocked IP: {ip_address}")
        return {
            "status": "success",
            "message": f"IP {ip_address} has been unblocked",
            "timestamp": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=404, detail=f"IP {ip_address} is not blocked")

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )
