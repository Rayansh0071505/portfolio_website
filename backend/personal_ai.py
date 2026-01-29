"""
Rayansh's Personal AI Assistant - LangGraph Agent with RAG
Acts as Rayansh Srivastava with strict guardrails and zero hallucination
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import time
import base64
import tempfile
import json
from langchain_groq import ChatGroq
from langchain_google_vertexai import ChatVertexAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.agents import create_agent
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langchain_pinecone import PineconeVectorStore
import redis.asyncio as redis_async
from langchain_community.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone
import os
from dotenv import load_dotenv
from config import get_redis_secret, get_groq_api_key, get_google_key, get_pinecone_api_key

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# LAZY INITIALIZATION - Load heavy models only when needed
# ============================================================================

_embeddings = None
_vector_store = None
_primary_llm = None
_backup_llm = None
_google_creds_loaded = False
GCP_PROJECT_ID = None

def get_vector_store():
    """Lazy load vector store and embeddings (expensive operation)"""
    global _embeddings, _vector_store

    if _vector_store is None:
        pinecone_api_key = get_pinecone_api_key()
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not found in config or environment")

        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index("myself")  # Using the knowledge base index

        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        _vector_store = PineconeVectorStore(index=index, embedding=_embeddings)
        logger.info("✅ Vector store initialized")

    return _vector_store


def get_gcp_project_id():
    """Extract project ID from GOOGLE_KEY config."""
    global GCP_PROJECT_ID

    if GCP_PROJECT_ID:
        return GCP_PROJECT_ID

    google_key = get_google_key()
    if google_key:
        try:
            decoded_key = base64.b64decode(google_key)
            key_data = json.loads(decoded_key)
            project_id = key_data.get("project_id")
            logger.info(f"✅ Extracted GCP project ID: {project_id}")
            GCP_PROJECT_ID = project_id
            return project_id
        except Exception as e:
            logger.error(f"❌ Error extracting project ID: {e}")

    # Fallback to environment variable
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID")
    if project_id:
        logger.info(f"Using project ID from env var: {project_id}")
        GCP_PROJECT_ID = project_id
    return project_id


def get_google_credentials():
    """Load Google credentials from config (base64 encoded)"""
    google_key_base64 = get_google_key()

    if google_key_base64:
        try:
            google_creds_json = base64.b64decode(google_key_base64).decode('utf-8')

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
                temp_file.write(google_creds_json)
                credentials_path = temp_file.name

            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            logger.info("✅ Google Cloud credentials configured")
            return credentials_path
        except Exception as e:
            logger.error(f"❌ Failed to decode GOOGLE_KEY: {str(e)}")
            return None
    else:
        logger.warning("⚠️ GOOGLE_KEY not found - Gemini may not work")
        return None


def ensure_google_credentials():
    """Ensure Google credentials are loaded (call before using Gemini)"""
    global _google_creds_loaded
    if not _google_creds_loaded:
        get_google_credentials()
        _google_creds_loaded = True


def get_primary_llm():
    """Get Vertex AI Gemini as primary for user-facing chat (best quality)"""
    global _primary_llm
    if _primary_llm is None:
        ensure_google_credentials()
        project_id = get_gcp_project_id()
        _primary_llm = ChatVertexAI(
            model_name="gemini-2.5-flash-lite",
            project=project_id,
            temperature=0.7,
            max_tokens=3096,
            timeout=30,
            max_retries=0,
        )
        logger.info("✅ Vertex AI Gemini initialized (PRIMARY - Chat)")
    return _primary_llm


def get_backup_llm():
    """Get Groq LLM as backup for chat (fallback if Vertex AI fails)"""
    global _backup_llm
    if _backup_llm is None:
        groq_api_key = get_groq_api_key()
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in config or environment")

        _backup_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=3096,
            groq_api_key=groq_api_key,
            max_retries=0,
            timeout=30
        )
        logger.info("✅ Groq LLM initialized (BACKUP - Chat)")
    return _backup_llm


# ============================================================================
# RAG TOOL - Query Knowledge Base
# ============================================================================

@tool
async def search_rayansh_knowledge(query: str) -> str:
    """
    Search Rayansh's professional knowledge base for accurate information.
    Use this tool to find facts about Rayansh's experience, projects, skills, or background.

    IMPORTANT: Formulate comprehensive queries for better results.
    Good: "Rayansh's experience with production AI agents and LLM systems"
    Bad: "agents"

    Args:
        query: The search query about Rayansh (be specific and comprehensive)

    Returns:
        Relevant information from Rayansh's knowledge base
    """
    try:
        vector_store = get_vector_store()

        # Multi-query retrieval: Generate related queries for better coverage
        queries = [query]

        # Add expanded queries based on common patterns
        if "certification" in query.lower() or "certified" in query.lower():
            queries.append("TensorFlow certification Google IBM Data Analysis LinkedIn Top Voice")
        if "tech stack" in query.lower() or "technologies" in query.lower() or "tools" in query.lower():
            queries.append("LangChain LangGraph Vertex AI Pinecone PyTorch FastAPI AWS GCP")
        if "companies" in query.lower() or "worked" in query.lower() or "experience" in query.lower():
            queries.append("Saturnin Everest Commerce Group Ooodles Moe-Assist Playback companies timeline")
        if "team" in query.lower() or "lead" in query.lower() or "leadership" in query.lower():
            queries.append("team lead leadership management distributed time zones")
        if "state of art" in query.lower() or "sota" in query.lower() or "advanced" in query.lower():
            queries.append("Gemini GPT-4 LLaMA Mistral diffusion models production systems")

        # Search with all queries and deduplicate
        all_results = []
        seen_content = set()

        for q in queries:
            results = vector_store.similarity_search_with_score(q, k=8)
            for doc, score in results:
                content_hash = hash(doc.page_content[:100])  # Hash first 100 chars
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    all_results.append((doc, score))

        # Sort by relevance and take top 10
        all_results.sort(key=lambda x: x[1])
        all_results = all_results[:10]

        if not all_results:
            return "No relevant information found in knowledge base."

        # Format results with source diversity
        context_parts = []
        sources_seen = {}

        for i, (doc, score) in enumerate(all_results, 1):
            source = doc.metadata.get("source", "unknown")
            content = doc.page_content.strip()

            # Track sources for diversity
            if source not in sources_seen:
                sources_seen[source] = 0
            sources_seen[source] += 1

            context_parts.append(f"[Source: {source} | Relevance: {score:.3f}]\n{content}")

        combined_context = "\n\n---\n\n".join(context_parts)
        logger.info(f"✅ RAG retrieved {len(all_results)} chunks from {len(sources_seen)} sources (searched {len(queries)} queries) for: {query[:50]}...")

        return combined_context

    except Exception as e:
        logger.error(f"❌ Error searching knowledge base: {str(e)}")
        return f"Error retrieving information: {str(e)}"


# ============================================================================
# SYSTEM PROMPT - Strict Guardrails
# ============================================================================

SYSTEM_PROMPT = """You are Rayansh Srivastava's AI form. You represent Rayansh in conversations.

QUICK REFERENCE (Always available - no search needed):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: Rayansh Srivastava
Title: AI/ML Solution Engineer | Founding AI Engineer
Experience: 5+ years across startups on 3 continents

IMPORTANT: When asked "tell me about yourself" or similar intro questions, provide a comprehensive overview covering:
- Current role and experience highlights
- Recent companies worked at (2-3 most recent)
- Core expertise areas (2-3 key skills)
- Notable achievements with numbers/metrics
Keep intro responses substantial (3-4 paragraphs) to give good first impression.

Companies (Most Recent to Oldest):
1. Saturnin (Nov 2025 - Jan 2026) - Founding AI Engineer
   → Multi-agent RAG system for investor intelligence
2. Everest Commerce Group (Mar 2025 - Nov 2025) - AI Solution Engineer
   → Peak OS platform, Peak Ads automation, multi-agent systems
3. Ooodles (Apr 2024 - Mar 2025) - AI/ML Engineer
   → Product catalog pipeline, chatbot systems
4. Moe-Assist (Dec 2023 - May 2024) - AI/ML Engineer (Team Lead)
   → Influencer discovery platform, analytics
5. Playback (Jan 2023 - Dec 2023) - ML Engineer (Project Lead)
   → Proprietary video generation engine

Core Tech Stack:
1. Machine Learning -Deep Learning, NLP, Computer Vision, Time Series Analysis, LLMs, Generative AI, Statistical Machine Learning,GANs
2. Languages - C++, Python
3. Databases- MongoDB, Big Query, SQL
4 .Solution Engineering -Business Problem Mapping, AI Solution Design, System Architecture, Stakeholder Alignment, Technical Consulting, Product Strategy,Workflow Design, AI Transformation
5. ML-OPS - AWS (Cloud & Serverless) , CI/CD, Docker, Render Cloud,Grafana,GitHub Actions, , GCP, Azure,MLFlow, EC2, ECS, Lambda ,Airflow, DVC, Ray, vllm
6. Automation -Workflow Automation, MultiAgent Systems, Process Automation, AI Orchestration 
7. Generative AI Tools - OpenAI GPT Models, AWS Bedrock, Azure OpenAI,Vertex AI (Gemini), Hugging Face ,Transformers, Open-SourceLLMs (LLaMA, Mistral, Falcon),LangChain, LangGraph, LlamaIndex,RAG Pipelin
8. Frameworks, Hosting & Libraries - TensorFlow, OpenCV, Scikitlearn, FastAPI, Streamlit, Pytorch

Certifications:
- TensorFlow Developer Certification (Google)
- Data Analysis Using Python (IBM)
- LinkedIn Top Voice - AI/ML (2 times)

Key Achievements:
- Built 20+ autonomous AI agents
- Led teams across 3 time zones (EST, CET, IST)
- Proprietary diffusion models (3x faster than commercial)
- Voice cloning (80-90% similarity with 10-15 min audio)
- Deployed systems handling 10,000+ daily interactions
- 99.9% uptime on production systems

Contact:
- Email: rayanshsrivastava.ai@gmail.com
- LinkedIn: https://www.linkedin.com/in/rayansh-srivastava-419951219/
- GitHub: https://github.com/Rayansh0071505
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL GUARDRAILS - MUST FOLLOW:

1. IDENTITY:
   - You ARE Rayansh Srivastava speaking in first person ("I am", "my experience", "I worked on")
   - Never refer to Rayansh in third person ("he", "Rayansh did")
   - Respond as if you are Rayansh himself

2. ZERO HALLUCINATION:
   - ONLY provide information found in the knowledge base via the search_rayansh_knowledge tool
   - If information is not in the knowledge base, say: "I don't have that specific information to share right now."
   - NEVER make up projects, companies, skills, or dates
   - NEVER infer or assume details not explicitly stated in the knowledge base

3. STRICT TOPIC BOUNDARIES:
   - ONLY discuss topics related to Rayansh's professional profile, experience, projects, and skills
   - Politely decline questions about:
     * Other people or companies (unless Rayansh worked there)
     * General AI/ML advice (unless specifically about Rayansh's approach)
     * Unrelated topics (politics, news, general knowledge)
   - Redirect off-topic questions: "I'm here to discuss my professional background and experience. Is there anything you'd like to know about my work?"

4. KNOWLEDGE BASE DEPENDENCY:
   - For basic questions (name, companies, contact, certifications), use QUICK REFERENCE above - NO search needed
   - For detailed questions (projects, technical details, achievements), ALWAYS search with search_rayansh_knowledge tool
   - When searching, formulate a COMPREHENSIVE query that captures the full intent:
     * Good: "Rayansh's experience with state-of-the-art models, LLMs, and production AI systems"
     * Bad: "models"
   - The search returns 10 most relevant chunks from ALL knowledge base files
   - Combine information from QUICK REFERENCE + RAG search for complete answers

5. RESPONSE STYLE:
   - Professional yet approachable
   - Concise and clear
   - Highlight specific achievements with numbers/metrics when available
   - Be honest about limitations: "I don't have that information" is acceptable

6. EXAMPLES OF GOOD RESPONSES:
   ✅ "I worked at Saturnin as Founding AI Engineer where I built a multi-agent RAG system..."
   ✅ "My expertise includes Deep Learning, NLP, and Computer Vision. I've built 20+ autonomous AI agents..."
   ✅ "I don't have specific information about that project in my records."

7. EXAMPLES OF BAD RESPONSES (NEVER DO THIS):
   ❌ "Rayansh is an experienced engineer..." (third person)
   ❌ "I probably worked on..." (assuming without verification)
   ❌ "I think I know Python..." (uncertainty about core skills)
   ❌ Answering general AI questions not related to Rayansh's work

REMEMBER: You are Rayansh. Speak confidently about what's in the knowledge base, and honestly admit when information isn't available."""


# ============================================================================
# AGENT SETUP (LangGraph)
# ============================================================================

async def create_rayansh_agent(use_backup: bool = False):
    """Create the LangGraph agent with tools and Redis memory (modern pattern)"""

    # Select LLM
    try:
        if use_backup:
            llm = get_backup_llm()
            logger.info("🔄 Using backup LLM (Groq) for chat")
        else:
            llm = get_primary_llm()
            logger.info("🚀 Using primary LLM (Vertex AI) for chat")
    except Exception as e:
        logger.error(f"❌ Error initializing LLM: {str(e)}")
        if not use_backup:
            logger.info("🔄 Falling back to Groq...")
            return await create_rayansh_agent(use_backup=True)
        raise

    # Define tools
    tools = [search_rayansh_knowledge]

    # Create Redis checkpointer for persistent memory
    redis_url = get_redis_secret()
    if not redis_url:
        raise ValueError("REDIS_SECRET not found in config or environment")

    # Create async Redis checkpointer with TTL (auto-expire after 24 hours)
    checkpointer = AsyncRedisSaver.from_conn_string(
        redis_url,
        ttl={
            "default_ttl": 1440,  # 24 hours in minutes
            "refresh_on_read": True  # Reset expiration when conversation accessed
        }
    )

    # Setup Redis indices (required on first use)
    try:
        await checkpointer.asetup()
        logger.info("✅ Redis checkpointer initialized with 24h TTL")
    except Exception as e:
        logger.error(f"❌ Redis setup failed: {str(e)}")
        raise

    # Create agent using modern create_agent pattern
    agent = create_agent(
        tools=tools,
        model=llm,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    logger.info("✅ LangGraph agent created successfully")
    return agent, checkpointer


# ============================================================================
# ASYNC CHAT INTERFACE - Scalable for Multiple Users
# ============================================================================

class RayanshAI:
    """Async-safe AI assistant for Rayansh - supports concurrent users with Redis persistence"""

    def __init__(self):
        self.agent = None
        self.checkpointer = None
        self.use_backup = False

    async def initialize(self):
        """Initialize agent with Redis checkpointer (call once at startup)"""
        try:
            self.agent, self.checkpointer = await create_rayansh_agent(use_backup=self.use_backup)
            logger.info("✅ Rayansh AI Agent initialized with Redis persistence")
        except Exception as e:
            logger.error(f"❌ Failed to initialize agent: {str(e)}")
            if not self.use_backup:
                logger.info("🔄 Retrying with backup LLM (Groq)...")
                self.use_backup = True
                self.agent, self.checkpointer = await create_rayansh_agent(use_backup=True)

    async def chat(
        self,
        message: str,
        session_id: str = "default",
        user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async chat with Rayansh AI (supports multiple concurrent users)

        Args:
            message: User's message
            session_id: Unique session identifier for conversation history
            user_name: Optional user name for personalization

        Returns:
            Response dict with message, sources, and metadata
        """
        start_time = time.time()

        try:
            # Ensure agent is initialized
            if self.agent is None:
                await self.initialize()

            # Add user context if provided
            user_message = f"[User: {user_name}] {message}" if user_name else message

            # Prepare input with LangGraph format (modern pattern)
            input_data = {
                "messages": [HumanMessage(content=user_message)]
            }

            # Config with thread_id for conversation memory
            config = {
                "configurable": {
                    "thread_id": session_id
                }
            }

            # Run agent (async with ainvoke - modern pattern)
            response = await self.agent.ainvoke(input_data, config)

            # Extract AI message from response
            assistant_text = None
            if isinstance(response, dict) and "messages" in response:
                messages = response["messages"]

                # Get the last AI message
                for msg in reversed(messages):
                    if hasattr(msg, "type") and msg.type == "ai":
                        if (
                            isinstance(msg.content, list)
                            and len(msg.content) > 0
                            and isinstance(msg.content[0], dict)
                            and "text" in msg.content[0]
                        ):
                            assistant_text = msg.content[0]["text"]
                        else:
                            assistant_text = str(msg.content)
                        break
                    elif hasattr(msg, "content") and msg.content:
                        if (
                            isinstance(msg.content, list)
                            and len(msg.content) > 0
                            and isinstance(msg.content[0], dict)
                            and "text" in msg.content[0]
                        ):
                            assistant_text = msg.content[0]["text"]
                        else:
                            assistant_text = str(msg.content)
                        break

            if not assistant_text:
                assistant_text = "I apologize, but I couldn't generate a response."

            elapsed_time = time.time() - start_time

            logger.info(f"✅ Response generated in {elapsed_time:.2f}s for session {session_id}")

            return {
                "message": assistant_text,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "response_time": f"{elapsed_time:.2f}s",
                "model": "Groq (Llama 3.3)" if self.use_backup else "Vertex AI (Gemini 2.5 Flash)"
            }

        except Exception as e:
            logger.error(f"❌ Error in chat: {str(e)}")

            elapsed_time = time.time() - start_time

            # Fallback to backup LLM if primary fails
            if not self.use_backup:
                logger.info("🔄 Primary LLM (Vertex AI) failed, switching to backup (Groq)...")
                self.use_backup = True
                self.agent, self.checkpointer = await create_rayansh_agent(use_backup=True)
                return await self.chat(message, session_id, user_name)

            return {
                "message": "I apologize, but I'm experiencing technical difficulties. Please try again.",
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "response_time": f"{elapsed_time:.2f}s",
                "model": "Error"
            }

    async def clear_session(self, session_id: str):
        """
        Clear chat history for a session from Redis
        Deletes all conversation context and checkpoints for the given session
        """
        try:
            if self.checkpointer:
                # Get Redis client from checkpointer
                redis_client = self.checkpointer.conn

                # Delete all keys associated with this thread_id (session_id)
                # LangGraph stores checkpoints with pattern: checkpoint:thread_id:*
                pattern = f"*{session_id}*"
                cursor = 0
                deleted_count = 0

                async for key in redis_client.scan_iter(match=pattern):
                    await redis_client.delete(key)
                    deleted_count += 1

                logger.info(f"🗑️ Session cleared from Redis: {session_id} ({deleted_count} keys deleted)")
            else:
                logger.warning(f"⚠️ Checkpointer not initialized, cannot clear session: {session_id}")
        except Exception as e:
            logger.error(f"❌ Error clearing session {session_id}: {str(e)}")


# ============================================================================
# GLOBAL INSTANCE - Singleton for Production
# ============================================================================

rayansh_ai = RayanshAI()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def ask_rayansh(message: str, session_id: str = "default") -> str:
    """
    Simple async function to ask Rayansh a question

    Args:
        message: Your question
        session_id: Session ID for conversation continuity

    Returns:
        Rayansh's response
    """
    response = await rayansh_ai.chat(message, session_id)
    return response["message"]


# ============================================================================
# MAIN - Testing
# ============================================================================

import asyncio

async def main():
    """Interactive continuous chat with the agent"""
    print("\n" + "="*60)
    print("🤖 Rayansh's Personal AI Assistant (Interactive Mode)")
    print("="*60)
    print("Type 'exit' or 'quit' to stop.\n")

    # Initialize
    await rayansh_ai.initialize()

    session_id = "interactive-session"

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()

            if user_input.lower() in {"exit", "quit"}:
                print("\n👋 Exiting chat. Bye Rayansh!")
                break

            if not user_input:
                continue

            print("\n🤖 AI: ", end="", flush=True)

            response = await rayansh_ai.chat(user_input, session_id=session_id)

            print(response["message"])
            print(f"\n⏱️ {response['response_time']} | 🧠 {response['model']}")

        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Bye Rayansh!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())

