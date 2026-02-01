"""
Semantic Caching Service using LangChain's RedisSemanticCache
Automatically caches LLM responses based on semantic similarity
"""
import os
import logging
from typing import Optional, List, Any
from langchain_community.cache import RedisSemanticCache
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.caches import RETURN_VAL_TYPE
from langchain_core.outputs import Generation
from config import get_redis_cache_url

logger = logging.getLogger(__name__)


class LoggingRedisSemanticCache(RedisSemanticCache):
    """
    Custom RedisSemanticCache with detailed logging for cache hits/misses
    """

    def lookup(self, prompt: str, llm_string: str) -> RETURN_VAL_TYPE:
        """
        Override lookup to log cache hits/misses
        """
        logger.info(f"🔍 CACHE LOOKUP: Searching for similar prompt (length: {len(prompt)} chars)")

        result = super().lookup(prompt, llm_string)

        if result:
            logger.info(f"✅ CACHE HIT! Found cached response, saving API costs 💰")
        else:
            logger.info(f"❌ CACHE MISS: No similar prompt found, will query LLM and cache response")

        return result

    def update(self, prompt: str, llm_string: str, return_val: RETURN_VAL_TYPE) -> None:
        """
        Override update to log when responses are saved to cache
        """
        logger.info(f"💾 SAVING TO CACHE: Storing LLM response for future reuse (prompt length: {len(prompt)} chars)")

        super().update(prompt, llm_string, return_val)

        logger.info(f"✅ CACHED SUCCESSFULLY: Response saved to Redis with semantic embeddings")

# Global cache instance (lazy initialization)
_semantic_cache = None
_cache_embeddings = None


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


def get_semantic_cache() -> Optional[RedisSemanticCache]:
    """
    Get or create global RedisSemanticCache instance

    This cache is shared across ALL users for maximum cost savings.
    Perfect for public portfolio Q&A where questions are similar.

    Returns:
        RedisSemanticCache instance or None if Redis not available
    """
    global _semantic_cache

    try:
        # Get Redis URL from config
        redis_url = get_redis_cache_url()

        if not redis_url or redis_url == "redis://localhost:6379":
            # Redis not configured in production
            if os.getenv("ENVIRONMENT") == "production":
                logger.warning("⚠️ Redis cache URL not configured - semantic caching disabled")
                return None
            logger.info("ℹ️ Using localhost Redis for development")

        # Initialize embeddings
        embeddings = get_cache_embeddings()

        if _semantic_cache is None:
            # Create global cache instance with logging
            cache = LoggingRedisSemanticCache(
                redis_url=redis_url,
                embedding=embeddings,
                score_threshold=0.2  # Distance threshold (lower = more strict)
                                     # 0.2 means ~80% similarity required for cache hit
                                     # Range: 0.1 (very strict) to 0.5 (loose)
            )

            # Store global cache
            _semantic_cache = cache
            logger.info(f"✅ Semantic cache initialized globally with LOGGING (threshold: 0.2)")
            logger.info(f"💡 Watch logs for: '✅ CACHE HIT' (saved $$$) or '❌ CACHE MISS' (new query)")

        return _semantic_cache

    except Exception as e:
        logger.error(f"❌ Failed to initialize semantic cache: {e}")
        logger.info("ℹ️ Continuing without semantic caching")
        return None


def clear_cache():
    """
    Clear global semantic cache

    Note: RedisSemanticCache doesn't have a built-in clear method.
    Cache entries will expire based on Redis eviction policy (allkeys-lru).
    """
    try:
        cache = get_semantic_cache()
        if cache:
            # RedisSemanticCache doesn't have a clear method
            # We'd need to manually delete keys or flush Redis
            # For now, we rely on LRU eviction policy
            logger.info(f"⚠️ Cache clear requested - Redis will auto-evict based on LRU policy")
    except Exception as e:
        logger.error(f"❌ Failed to clear cache: {e}")
