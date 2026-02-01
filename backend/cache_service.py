"""
Semantic Caching Service using AWS ElastiCache Valkey with Vector Search
Based on AWS blog: https://aws.amazon.com/blogs/database/announcing-vector-search-for-amazon-elasticache/
"""
import os
import logging
from typing import Optional, List, Any
from hashlib import md5
import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import get_redis_cache_url

logger = logging.getLogger(__name__)

# Global cache instances
_valkey_client = None
_cache_embeddings = None
_cache_enabled = False


def get_cache_embeddings():
    """
    Get embeddings model for semantic caching
    Uses same model as RAG for consistency (384-dim)
    """
    global _cache_embeddings

    if _cache_embeddings is None:
        logger.info("🔄 Initializing embeddings for semantic cache...")
        _cache_embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("✅ Cache embeddings initialized (384-dim)")

    return _cache_embeddings


def get_valkey_client():
    """
    Get or create Valkey client for ElastiCache

    Returns:
        Valkey client or None if not available
    """
    global _valkey_client, _cache_enabled

    if _valkey_client is not None:
        return _valkey_client

    try:
        # Get Valkey URL from config
        valkey_url = get_redis_cache_url()

        if not valkey_url or valkey_url == "redis://localhost:6379":
            # Valkey not configured in production
            if os.getenv("ENVIRONMENT") == "production":
                logger.warning("⚠️ Valkey cache URL not configured - semantic caching disabled")
                return None
            logger.info("ℹ️ Using localhost Valkey for development")

        # Import Valkey client
        try:
            import valkey
        except ImportError:
            logger.warning("⚠️ valkey package not installed - falling back to redis")
            import redis as valkey

        # Parse URL
        if valkey_url.startswith("redis://"):
            # Extract host and port
            parts = valkey_url.replace("redis://", "").split(":")
            host = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 6379
        else:
            host = "localhost"
            port = 6379

        # Create Valkey client
        client = valkey.Valkey(
            host=host,
            port=port,
            decode_responses=False,  # We'll handle encoding ourselves
            socket_timeout=5,
            socket_connect_timeout=5,
        )

        # Test connection with timeout
        try:
            client.ping()
            _valkey_client = client
            _cache_enabled = True
            logger.info(f"✅ Valkey client connected to {host}:{port}")
            logger.info(f"💡 Semantic cache ready - will save API costs on similar questions")
            return _valkey_client
        except Exception as ping_error:
            logger.warning(f"⚠️ Cannot connect to Valkey at {host}:{port}: {ping_error}")
            logger.info("ℹ️ ElastiCache may be unreachable from EC2 - check VPC/security groups")
            _cache_enabled = False
            return None

    except Exception as e:
        logger.error(f"❌ Failed to initialize Valkey client: {e}")
        logger.info("ℹ️ Continuing without semantic caching")
        _cache_enabled = False
        return None


def cache_key_for_query(query: str) -> str:
    """
    Generate a cache key for a query using MD5 hash

    Args:
        query: The query string

    Returns:
        MD5 hash of the query
    """
    return md5(query.encode("utf-8")).hexdigest()


def extract_user_question(prompt: str) -> str:
    """
    Extract just the user's question from the full LangChain prompt
    Ignores system instructions and conversation history

    Args:
        prompt: Full LangChain prompt (system + history + question)

    Returns:
        Just the user's latest question
    """
    try:
        import re

        # DEBUG: Log first 500 chars of prompt to understand format
        logger.info(f"🔍 DEBUG: Prompt preview (first 500 chars): {prompt[:500]}")

        # Try multiple extraction patterns

        # Pattern 1: Look for content="..." or content='...'
        matches = re.findall(r'content=["\']([^"\']+)["\']', prompt)
        if matches:
            # Get the last match (most recent user message)
            last_question = matches[-1]
            logger.info(f"✅ Extracted via pattern 1: '{last_question[:100]}'")
            return last_question

        # Pattern 2: Look for HumanMessage with content
        if "HumanMessage" in prompt:
            parts = prompt.split("HumanMessage")
            if len(parts) > 1:
                last_human = parts[-1]
                # Try to extract content
                match = re.search(r'content=["\'](.+?)["\']', last_human, re.DOTALL)
                if match:
                    question = match.group(1)
                    logger.info(f"✅ Extracted via pattern 2: '{question[:100]}'")
                    return question

        # Pattern 3: Look for "input": "..." pattern
        match = re.search(r'"input"\s*:\s*"([^"]+)"', prompt)
        if match:
            question = match.group(1)
            logger.info(f"✅ Extracted via pattern 3: '{question[:100]}'")
            return question

        # Fallback: Log warning and use full prompt (will fail should_cache filter)
        logger.warning(f"⚠️ Could not extract user question from prompt, using full prompt")
        logger.info(f"🔍 Full prompt (first 1000 chars): {prompt[:1000]}")
        return prompt

    except Exception as e:
        logger.warning(f"⚠️ Failed to extract user question: {e}")
        logger.info(f"🔍 Prompt that failed: {prompt[:500]}")
        return prompt


def lookup_cache(prompt: str, llm_string: str, similarity_threshold: float = 0.85) -> Optional[str]:
    """
    Lookup cached LLM response using SEMANTIC SIMILARITY search
    Caches based on USER QUESTION only (ignores conversation history)

    Args:
        prompt: The full LangChain prompt (system + history + question)
        llm_string: LLM identifier string
        similarity_threshold: Minimum cosine similarity (0-1) to consider a cache hit

    Returns:
        Cached response if found, None otherwise
    """
    if not _cache_enabled:
        return None

    try:
        client = get_valkey_client()
        if not client:
            return None

        # Extract ONLY the user's question (ignore history)
        user_question = extract_user_question(prompt)

        logger.info(f"🔍 SEMANTIC SEARCH: Looking for similar questions (query length: {len(user_question)} chars)")

        # Generate embedding for the user's question
        embeddings_model = get_cache_embeddings()
        query_embedding = embeddings_model.embed_query(user_question)

        logger.info(f"🧮 Generated embedding vector (384-dim) for semantic search")

        # Search for similar cached questions using embeddings
        # Get all cache keys and compute similarity
        import numpy as np

        best_match = None
        best_similarity = 0.0

        # Pattern to match cache keys for this LLM
        pattern = f"{llm_string}:*"

        # Scan all keys (use SCAN for production to avoid blocking)
        for key in client.scan_iter(match=pattern, count=100):
            try:
                # Get stored embedding for this key
                embedding_key = key.decode('utf-8') + ":embedding"
                stored_embedding_bytes = client.get(embedding_key)

                if stored_embedding_bytes:
                    # Deserialize embedding
                    stored_embedding = json.loads(stored_embedding_bytes.decode('utf-8'))

                    # Compute cosine similarity
                    similarity = np.dot(query_embedding, stored_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                    )

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = key

            except Exception as e:
                logger.warning(f"⚠️ Error processing key {key}: {e}")
                continue

        # Check if we found a match above threshold
        if best_match and best_similarity >= similarity_threshold:
            cached_response = client.get(best_match)
            if cached_response:
                logger.info(f"✅ SEMANTIC CACHE HIT! Similarity: {best_similarity:.2%} (threshold: {similarity_threshold:.0%}) 💰")
                logger.info(f"📊 Matched cached question, saving API costs!")
                return cached_response.decode('utf-8')

        if best_match:
            logger.info(f"❌ SEMANTIC CACHE MISS: Best similarity {best_similarity:.2%} < threshold {similarity_threshold:.0%}")
        else:
            logger.info(f"❌ SEMANTIC CACHE MISS: No cached questions found")

        return None

    except Exception as e:
        logger.error(f"⚠️ Semantic cache lookup error: {e}")
        return None


def should_cache(user_question: str) -> bool:
    """
    Determine if a user question should be cached

    Filters out:
    - Very short responses (likely names or personal info)
    - Personal information patterns

    Args:
        user_question: The extracted user question

    Returns:
        True if should cache, False otherwise
    """
    # Strip whitespace
    question = user_question.strip()

    # Don't cache very short responses (< 15 chars) - likely names or personal info
    if len(question) < 15:
        logger.info(f"⏭️ SKIPPING CACHE: Too short ({len(question)} chars) - likely personal info: '{question}'")
        return False

    # Don't cache if it looks like a name pattern (no question mark, very short, capitalized words)
    if len(question) < 30 and '?' not in question:
        # Check if it's likely a name: "John", "My name is John", "I'm Sarah"
        name_patterns = [
            r'^[A-Z][a-z]+$',  # Single capitalized word: "John"
            r'^My name is ',   # "My name is John"
            r"^I'm [A-Z]",     # "I'm John"
            r"^I am [A-Z]",    # "I am John"
        ]
        import re
        for pattern in name_patterns:
            if re.search(pattern, question):
                logger.info(f"⏭️ SKIPPING CACHE: Looks like personal info - '{question}'")
                return False

    return True


def update_cache(prompt: str, llm_string: str, response: str):
    """
    Save LLM response to cache PERMANENTLY (no expiration)
    Caches based on USER QUESTION only (ignores conversation history)

    Args:
        prompt: The full LangChain prompt (system + history + question)
        llm_string: LLM identifier string
        response: The LLM response to cache

    Note: Cache entries never expire - only removed via manual clear
    """
    if not _cache_enabled:
        return

    try:
        client = get_valkey_client()
        if not client:
            return

        # Extract ONLY the user's question (ignore history)
        user_question = extract_user_question(prompt)

        # Check if we should cache this question
        if not should_cache(user_question):
            return

        logger.info(f"💾 SAVING TO SEMANTIC CACHE: Question → Response (question length: {len(user_question)} chars)")

        # Cache key based on user question ONLY (not full prompt!)
        cache_key = cache_key_for_query(f"{llm_string}:{user_question}")

        # Generate embedding for semantic search
        embeddings_model = get_cache_embeddings()
        question_embedding = embeddings_model.embed_query(user_question)

        logger.info(f"🧮 Generated 384-dim embedding vector for semantic search")

        # Store response PERMANENTLY (no TTL)
        client.set(cache_key, response.encode('utf-8'))

        # Store embedding for semantic similarity search (as JSON)
        embedding_key = cache_key + ":embedding"
        client.set(embedding_key, json.dumps(question_embedding).encode('utf-8'))

        logger.info(f"✅ SEMANTIC CACHE SAVED: '{user_question[:50]}...' → Response + Embedding (never expires)")
        logger.info(f"🔍 Future similar questions will match via semantic search (>85% similarity)")

    except Exception as e:
        logger.error(f"⚠️ Cache update error: {e}")


def clear_cache():
    """
    Clear all cached LLM responses

    WARNING: This deletes ALL cache keys. Use carefully!
    """
    try:
        client = get_valkey_client()
        if not client:
            logger.warning("⚠️ Cache not available")
            return

        logger.warning(f"⚠️ CLEARING ALL CACHE: Deleting all cached responses...")

        # Flush all keys (DANGEROUS in production if sharing Valkey!)
        # For production, implement pattern-based deletion
        client.flushdb()

        logger.info(f"✅ Cache cleared successfully")

    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")


# LangChain-compatible cache class
class ValkeyCache:
    """
    LangChain-compatible cache using Valkey for exact-match caching
    Can be used with set_llm_cache() to enable global caching
    """

    def lookup(self, prompt: str, llm_string: str):
        """
        LangChain cache interface: lookup cached response

        Args:
            prompt: The input prompt
            llm_string: LLM identifier string

        Returns:
            List of Generation objects if cache hit, None otherwise
        """
        try:
            from langchain_core.outputs import Generation

            cached_text = lookup_cache(prompt, llm_string)
            if cached_text:
                # Return as LangChain Generation object
                return [Generation(text=cached_text)]
            return None
        except Exception as e:
            logger.error(f"⚠️ Cache lookup error: {e}")
            return None

    def update(self, prompt: str, llm_string: str, return_val):
        """
        LangChain cache interface: store response in cache

        Args:
            prompt: The input prompt
            llm_string: LLM identifier string
            return_val: List of Generation objects from LLM
        """
        try:
            if return_val and len(return_val) > 0:
                # Extract text from first Generation object
                response_text = return_val[0].text
                update_cache(prompt, llm_string, response_text)
        except Exception as e:
            logger.error(f"⚠️ Cache update error: {e}")

    def clear(self, **kwargs):
        """LangChain cache interface: clear cache"""
        clear_cache()

    # Async methods for LangChain async LLM calls
    async def alookup(self, prompt: str, llm_string: str):
        """Async version of lookup"""
        return self.lookup(prompt, llm_string)

    async def aupdate(self, prompt: str, llm_string: str, return_val):
        """Async version of update"""
        self.update(prompt, llm_string, return_val)

    async def aclear(self, **kwargs):
        """Async version of clear"""
        clear_cache()


def get_valkey_cache():
    """
    Get LangChain-compatible Valkey cache instance

    Returns:
        ValkeyCache instance if available, None otherwise
    """
    if _cache_enabled and get_valkey_client():
        return ValkeyCache()
    return None


# Initialize cache on module import
def init_cache():
    """Initialize Valkey cache on startup"""
    try:
        client = get_valkey_client()
        if client:
            logger.info("✅ Semantic cache initialized with Valkey (PERMANENT storage)")
            logger.info("💡 Watch logs for: '✅ CACHE HIT' (saved $$$) or '❌ CACHE MISS' (new query)")
            logger.info("💡 Cache entries never expire - manually clear if needed")
        else:
            logger.info("ℹ️ Semantic cache not available - running without caching")
    except Exception as e:
        logger.error(f"❌ Failed to initialize cache: {e}")


# Auto-initialize on import
init_cache()
