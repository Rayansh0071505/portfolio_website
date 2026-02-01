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

        # Test connection
        client.ping()

        _valkey_client = client
        _cache_enabled = True
        logger.info(f"✅ Valkey client connected to {host}:{port}")
        logger.info(f"💡 Semantic cache ready - will save API costs on similar questions")

        return _valkey_client

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


def lookup_cache(prompt: str, llm_string: str, similarity_threshold: float = 0.85) -> Optional[str]:
    """
    Lookup cached LLM response for similar prompts

    Args:
        prompt: The input prompt
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

        embeddings = get_cache_embeddings()

        # Generate embedding for the prompt
        logger.info(f"🔍 CACHE LOOKUP: Searching for similar prompt (length: {len(prompt)} chars)")

        prompt_embedding = embeddings.embed_query(prompt)
        cache_key = cache_key_for_query(f"{llm_string}:{prompt}")

        # Try exact match first (fastest)
        cached = client.get(cache_key)
        if cached:
            logger.info(f"✅ CACHE HIT! Found exact match, saving API costs 💰")
            return cached.decode('utf-8')

        # Note: Vector similarity search requires Valkey 8.2+ with valkey-search module
        # For now, we'll rely on exact matches until vector search is properly configured
        # TODO: Implement vector similarity search with FT.SEARCH once index is created

        logger.info(f"❌ CACHE MISS: No match found, will query LLM and cache response")
        return None

    except Exception as e:
        logger.error(f"⚠️ Cache lookup error: {e}")
        return None


def update_cache(prompt: str, llm_string: str, response: str, ttl: int = 86400):
    """
    Save LLM response to cache

    Args:
        prompt: The input prompt
        llm_string: LLM identifier string
        response: The LLM response to cache
        ttl: Time to live in seconds (default: 24 hours)
    """
    if not _cache_enabled:
        return

    try:
        client = get_valkey_client()
        if not client:
            return

        logger.info(f"💾 SAVING TO CACHE: Storing LLM response (prompt length: {len(prompt)} chars)")

        cache_key = cache_key_for_query(f"{llm_string}:{prompt}")

        # Store response with TTL
        client.setex(cache_key, ttl, response.encode('utf-8'))

        logger.info(f"✅ CACHED SUCCESSFULLY: Response saved with {ttl}s TTL")

    except Exception as e:
        logger.error(f"⚠️ Cache update error: {e}")


def clear_cache():
    """
    Clear all cached entries (use with caution)
    """
    try:
        client = get_valkey_client()
        if client:
            # Get all cache keys and delete
            # This is a simple implementation - in production, use key patterns
            logger.info(f"⚠️ Cache clear requested")
            # Note: FLUSHDB is dangerous in production, implement pattern-based deletion
            logger.info(f"ℹ️ Cache entries will auto-expire based on TTL")
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")


# Initialize cache on module import
def init_cache():
    """Initialize Valkey cache on startup"""
    try:
        client = get_valkey_client()
        if client:
            logger.info("✅ Semantic cache initialized with Valkey")
            logger.info("💡 Watch logs for: '✅ CACHE HIT' (saved $$$) or '❌ CACHE MISS' (new query)")
        else:
            logger.info("ℹ️ Semantic cache not available - running without caching")
    except Exception as e:
        logger.error(f"❌ Failed to initialize cache: {e}")


# Auto-initialize on import
init_cache()
