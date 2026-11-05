import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.memory import MemoryEntry
from app.ingestion.embedder import generate_embedding


async def retrieve_similar_memories(
    db: AsyncSession,
    user_id: int,
    query: str,
    limit: int = 5,
) -> list[MemoryEntry]:
    """Retrieve only the requesting user's memories by cosine similarity."""
    if not query or not query.strip():
        return []

    vector = await asyncio.to_thread(generate_embedding, query)
    statement = (
        select(MemoryEntry)
        .where(
            MemoryEntry.user_id == user_id,
            MemoryEntry.embedding.is_not(None),
        )
        .order_by(MemoryEntry.embedding.cosine_distance(vector))
        .limit(max(1, min(limit, 20)))
    )
    result = await db.execute(statement)
    return list(result.scalars().all())
