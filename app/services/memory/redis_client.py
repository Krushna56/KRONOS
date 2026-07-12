import redis.asyncio as redis
from app.core.config import settings

from fastapi import APIRouter
from app.services.memory.redis_client import redis_client

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

router = APIRouter()

@router.get("/redis-test")
async def redis_test():

    await redis_client.set("test", "hello")

    value = await redis_client.get("test")

    return {"redis": value}