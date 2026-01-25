"""
FastAPI Backend for Rayansh's Personal AI Assistant
with Conversation Tracking and Email Summaries
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
import logging

# Import the AI assistant and conversation tracker
from personal_ai import rayansh_ai
from conversation_tracker import ConversationTracker, send_conversation_email, cleanup_old_sessions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Rayansh's Personal AI API",
    description="AI-powered chat assistant with conversation tracking",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Chat with Rayansh's AI assistant with conversation tracking

    - Tracks message count
    - Asks for name after 1st question
    - Asks for LinkedIn after 3rd question
    - Stores conversation for email summary
    """
    try:
        # Generate session ID if not provided
        if not request.session_id:
            request.session_id = f"session_{uuid.uuid4().hex[:16]}"

        logger.info(f"💬 Chat request from session {request.session_id}: {request.message[:50]}...")

        # Initialize conversation tracker
        tracker = ConversationTracker(request.session_id)

        # Extract name or LinkedIn from message if present
        extracted_name = tracker.extract_name_from_message(request.message)
        if extracted_name and not tracker.get_session().get("user_name"):
            tracker.set_user_name(extracted_name)

        extracted_linkedin = tracker.extract_linkedin_from_message(request.message)
        if extracted_linkedin and not tracker.get_session().get("user_linkedin"):
            tracker.set_user_linkedin(extracted_linkedin)

        # Add user message to tracker
        tracker.add_message("user", request.message)

        # Get AI response
        response = await rayansh_ai.chat(
            message=request.message,
            session_id=request.session_id,
            user_name=request.user_name or tracker.get_session().get("user_name")
        )

        ai_message = response["message"]

        # Check if we should ask for name (after 1st question)
        if tracker.should_ask_for_name():
            ai_message += tracker.get_intro_prompt()
            tracker.mark_asked_for_name()
            logger.info(f"🙋 Asking for name in session {request.session_id}")

        # Check if we should ask for LinkedIn (after 3rd question)
        elif tracker.should_ask_for_linkedin():
            ai_message += tracker.get_linkedin_prompt()
            tracker.mark_asked_for_linkedin()
            logger.info(f"🔗 Asking for LinkedIn in session {request.session_id}")

        # Add AI response to tracker
        tracker.add_message("assistant", ai_message)

        # Schedule cleanup of old sessions in background
        background_tasks.add_task(cleanup_old_sessions, max_age_hours=24)

        return ChatResponse(
            message=ai_message,
            session_id=request.session_id,
            timestamp=response["timestamp"],
            response_time=response["response_time"],
            model=response["model"]
        )

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
        "model": "Groq (Llama 3.3)" if rayansh_ai.use_backup else "Vertex AI (Gemini 2.0 Flash)",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
