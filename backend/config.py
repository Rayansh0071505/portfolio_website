"""
Configuration Management with AWS Parameter Store
Secure secret storage - no .env files needed in production
"""
import os
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Environment detection
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"


class Config:
    """Configuration loader - uses AWS Parameter Store in production, .env in development"""

    def __init__(self):
        self._ssm_client = None
        self._cache = {}

    def _get_ssm_client(self):
        """Get AWS SSM client (lazy initialization)"""
        if self._ssm_client is None:
            try:
                self._ssm_client = boto3.client('ssm', region_name='us-east-1')
                logger.info("✅ AWS SSM client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize SSM client: {e}")
                raise
        return self._ssm_client

    def get_parameter(self, param_name: str, decrypt: bool = True) -> Optional[str]:
        """
        Get parameter from AWS Parameter Store

        Args:
            param_name: Parameter name (e.g., '/personal_portfolio/redis_secret')
            decrypt: Whether to decrypt SecureString parameters

        Returns:
            Parameter value or None if not found
        """
        # Check cache first
        if param_name in self._cache:
            return self._cache[param_name]

        try:
            ssm = self._get_ssm_client()
            response = ssm.get_parameter(Name=param_name, WithDecryption=decrypt)
            value = response['Parameter']['Value']

            # Cache the value
            self._cache[param_name] = value
            logger.info(f"✅ Retrieved parameter: {param_name}")
            return value

        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.error(f"❌ Parameter not found: {param_name}")
            else:
                logger.error(f"❌ Error retrieving parameter {param_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error retrieving {param_name}: {e}")
            return None

    def get_secret(self, key: str, default: Optional[str] = None) -> str:
        """
        Get secret - uses Parameter Store in production, .env in development

        Args:
            key: Secret key (e.g., 'REDIS_SECRET')
            default: Default value if not found

        Returns:
            Secret value
        """
        # In development, use environment variables (.env)
        if not IS_PRODUCTION:
            value = os.getenv(key, default)
            if value:
                logger.info(f"✅ Using env var: {key}")
                return value

        # In production, use AWS Parameter Store
        param_name = f"/personal_portfolio/{key.lower()}"
        value = self.get_parameter(param_name)

        if value is None:
            # Fallback to environment variable
            value = os.getenv(key, default)
            if value:
                logger.warning(f"⚠️ Using env var fallback for: {key}")
            else:
                logger.error(f"❌ Secret not found: {key}")

        return value or default or ""


# Global configuration instance
config = Config()


# Convenience functions
def get_redis_secret() -> str:
    """Get Redis connection string"""
    return config.get_secret("REDIS_SECRET")


def get_groq_api_key() -> str:
    """Get Groq API key"""
    return config.get_secret("GROQ_API_KEY")


def get_google_key() -> str:
    """Get Google Cloud key (base64)"""
    return config.get_secret("GOOGLE_KEY")


def get_pinecone_api_key() -> str:
    """Get Pinecone API key"""
    return config.get_secret("PINECONE_API_KEY")


def get_mailgun_domain() -> str:
    """Get Mailgun domain"""
    return config.get_secret("MAILGUN_DOMAIN")


def get_mailgun_secret() -> str:
    """Get Mailgun API key"""
    return config.get_secret("MAILGUN_SECRET")


def get_cloudfront_secret() -> str:
    """Get CloudFront custom header secret"""
    return config.get_secret("CLOUDFRONT_SECRET")


def get_redis_cache_url() -> str:
    """
    Get ElastiCache Valkey URL for semantic caching

    Priority:
    1. Environment variable (for local dev)
    2. AWS Parameter Store (for production - auto-updated by Terraform)
    3. Fallback to localhost
    """
    # Try environment variable first (local dev)
    redis_url = os.getenv("REDIS_CACHE_URL")
    if redis_url and redis_url != "redis://localhost:6379":
        logger.info(f"✅ Using REDIS_CACHE_URL from environment variable")
        return redis_url

    # In production, read from Parameter Store (auto-updated by Terraform!)
    if IS_PRODUCTION:
        try:
            param_value = config.get_parameter("/personal_portfolio/redis_cache_url", decrypt=False)
            if param_value:
                logger.info(f"✅ Using REDIS_CACHE_URL from Parameter Store (auto-updated by Terraform)")
                return param_value
        except Exception as e:
            logger.warning(f"⚠️ Failed to get REDIS_CACHE_URL from Parameter Store: {e}")

    # Fallback to localhost (development)
    logger.info(f"ℹ️ Using localhost Redis (development fallback)")
    return "redis://localhost:6379"


# For backward compatibility with existing code
def get_secret(key: str, default: Optional[str] = None) -> str:
    """Get any secret by key"""
    return config.get_secret(key, default)
