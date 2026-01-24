"""
FastAPI Backend for Rayansh's Personal AI Assistant
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
import logging

# Import the AI assistant
from backend.personal_ai import rayansh_ai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Rayansh's Personal AI API",
    description="AI-powered chat assistant representing Rayansh Srivastava",
    version="1.0.0"
)

# CORS middleware - allow frontend to access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],  # Add your frontend URLs
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
async def chat(request: ChatRequest):
    """
    Chat with Rayansh's AI assistant

    Args:
        message: User's message
        session_id: Optional session ID for conversation continuity
        user_name: Optional user name

    Returns:
        AI response with metadata
    """
    try:
        # Generate session ID if not provided
        if not request.session_id:
            request.session_id = f"session_{uuid.uuid4().hex[:16]}"

        logger.info(f"💬 Chat request from session {request.session_id}: {request.message[:50]}...")

        # Get AI response
        response = await rayansh_ai.chat(
            message=request.message,
            session_id=request.session_id,
            user_name=request.user_name
        )

        return ChatResponse(**response)

    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/api/chat/clear/{session_id}")
async def clear_session(session_id: str):
    """
    Clear chat history for a session

    Args:
        session_id: Session ID to clear

    Returns:
        Success message
    """
    try:
        rayansh_ai.clear_session(session_id)
        return {
            "status": "success",
            "message": f"Session {session_id} cleared. Generate a new session_id for fresh conversation.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")

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
        host="127.0.0.1",
        port=8080,
        reload=True,
        log_level="info"
    )
