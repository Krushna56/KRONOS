import redis.asyncio as redis
from app.core.config import settings
from app.core.logger import logger

try:
    redis_client = redis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )
except Exception as e:
    logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}")
    redis_client = None