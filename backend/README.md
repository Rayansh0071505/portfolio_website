# Portfolio Backend - Knowledge Base System

## Overview
This backend system indexes all knowledge base files into Pinecone vector database for intelligent retrieval using AI.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the backend directory:
```env
PINECONE_KEY=your_pinecone_api_key
MISTRAL_API_KEY=your_mistral_api_key
```

### 3. Load Knowledge Base into Pinecone
Run the embedding script to index all knowledge base files:
```bash
python knowledge_embedding.py
```

This will:
- Automatically create Pinecone index `myself` if it doesn't exist
- Read all `.txt` and `.md` files from the `knowledge_base/` folder
- Split them intelligently using **custom semantic chunking**:
  - Splits text into sentences
  - Calculates embeddings for each sentence
  - Groups sentences based on semantic similarity
  - Creates coherent chunks with related content
- Generate embeddings using `sentence-transformers/all-MiniLM-L6-v2`
- Index them into Pinecone index named `myself`

## Knowledge Base Files

Current knowledge base includes:
- `SATURNIN_PROJECT_SUMMARY.txt` - Saturnin investor platform project
- `ECG_EVEREST_COMMERCE_GROUP.txt` - Everest Commerce Group work
- `OOODLES.txt` - Ooodles e-commerce automation
- `MOE_ASSIST.txt` - Moe-Assist influencer platform
- `PLAYBACK.txt` - Playback generative video engine
- `ABOUT_RAYANSH.txt` - Personal story and philosophy
- `RAYANSH_PROFESSIONAL_PROFILE.txt` - Complete professional profile

## Usage

### Load Knowledge Base
```python
from knowledge_embedding import load_knowledge_base

load_knowledge_base()
```

### Query Knowledge Base
```python
from knowledge_embedding import query_knowledge_base

results = query_knowledge_base("What projects has Rayansh worked on?", top_k=5)
for result in results:
    print(f"Source: {result['source']}")
    print(f"Content: {result['content']}")
    print(f"Score: {result['score']}")
```

## Tech Stack
- **LangChain**: Document processing, vector store integration, and agent framework
- **Pinecone**: Vector database for semantic search
- **HuggingFace**: Sentence transformers for embeddings
- **Vertex AI (Gemini)**: Primary LLM for conversational AI
- **Groq (Llama 3.3)**: Backup LLM for high availability
- **FastAPI**: Web framework for APIs

## Index Configuration
- **Index Name**: `myself`
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- **Chunking Strategy**: Custom semantic chunking algorithm
  - Splits by sentence boundaries
  - Calculates cosine similarity between consecutive sentences
  - Groups semantically similar sentences together
  - Similarity threshold: 0.5 (configurable)
  - Max chunk size: 1000 characters
- **Auto-Creation**: Index is automatically created if it doesn't exist

## Personal AI Assistant

### Overview
`personal_ai.py` provides an intelligent conversational AI that represents Rayansh Srivastava with:
- **Zero hallucination**: Only answers from verified knowledge base
- **Strict guardrails**: Stays on topic, refuses to make up information
- **RAG-powered**: Uses semantic search to retrieve accurate facts
- **Dual LLM**: Vertex AI (primary) + Groq (backup) for high availability
- **Async/Concurrent**: Supports multiple users simultaneously
- **Session management**: Maintains conversation context per user

### Environment Variables Required
```env
PINECONE_KEY=your_pinecone_api_key
GOOGLE_KEY=base64_encoded_google_credentials_json
GROQ_API_KEY=your_groq_api_key
```

### Usage

**Initialize and Chat:**
```python
from personal_ai import rayansh_ai
import asyncio

async def example():
    # Initialize (call once at startup)
    await rayansh_ai.initialize()

    # Chat with session management
    response = await rayansh_ai.chat(
        message="What projects have you worked on?",
        session_id="user123",
        user_name="John"
    )

    print(response["message"])
    print(f"Model: {response['model']}")
    print(f"Time: {response['response_time']}")

asyncio.run(example())
```

**Simple Question:**
```python
from personal_ai import ask_rayansh
import asyncio

async def quick_question():
    answer = await ask_rayansh("Tell me about your experience with RAG systems")
    print(answer)

asyncio.run(quick_question())
```

**Test the Agent:**
```bash
python personal_ai.py
```

### Features

**Strict Guardrails:**
- Only discusses Rayansh's professional background
- Always verifies facts via RAG before responding
- Refuses to answer off-topic questions politely
- Never hallucinates projects, skills, or experiences
- Speaks in first person as Rayansh

**Production Ready:**
- Lazy loading of heavy models (efficient memory usage)
- Automatic fallback to backup LLM if primary fails
- Async architecture for concurrent users
- Session-based conversation history
- Comprehensive error handling and logging

**Scalability:**
- Thread-safe design
- Independent session management per user
- No blocking operations
- Efficient vector search with top-k retrieval
