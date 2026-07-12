from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.memory import MemoryEntry
from app.services.memory.redis_client import redis_client
from app.core.logger import logger

class MemoryService:
    @staticmethod
    async def store_memory(db: AsyncSession, key: str, value: str, user_id: int = None, category: str = "general") -> MemoryEntry:
        """Store associative memory in PostgreSQL and cache it in Redis."""
        # 1. Cache in Redis
        cache_key = f"mem:{user_id or 0}:{key}"
        await redis_client.set(cache_key, value)
        
        # 2. Save in PostgreSQL
        query = select(MemoryEntry).where(MemoryEntry.key == key, MemoryEntry.user_id == user_id)
        result = await db.execute(query)
        entry = result.scalars().first()
        
        if entry:
            entry.value = value
            entry.category = category
        else:
            entry = MemoryEntry(key=key, value=value, user_id=user_id, category=category)
            db.add(entry)
            
        await db.commit()
        await db.refresh(entry)
        logger.info(f"Memory stored for key '{key}' and user '{user_id}'")
        return entry

    @staticmethod
    async def retrieve_memory(db: AsyncSession, key: str, user_id: int = None) -> str | None:
        """Retrieve associative memory from Redis cache, falling back to PostgreSQL."""
        # 1. Read from Redis Cache
        cache_key = f"mem:{user_id or 0}:{key}"
        cached_value = await redis_client.get(cache_key)
        if cached_value:
            return cached_value
            
        # 2. Fallback to PostgreSQL
        query = select(MemoryEntry).where(MemoryEntry.key == key, MemoryEntry.user_id == user_id)
        result = await db.execute(query)
        entry = result.scalars().first()
        
        if entry:
            # Re-populate cache
            await redis_client.set(cache_key, entry.value)
            return entry.value
            
        return None
