import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.memory import MemoryEntry
from app.ingestion.embedder import generate_embedding
from app.memory.retrieval import retrieve_similar_memories


async def save_memory(
    db: AsyncSession,
    user_id: int,
    key: str,
    value: str,
    category: str = "general",
) -> MemoryEntry:
    """Create or update a memory by (user_id, key)."""
    normalized_key = key.strip()
    normalized_value = value.strip()
    normalized_category = (category or "general").strip() or "general"

    if not normalized_key or not normalized_value:
        raise ValueError("Memory key and value must not be empty.")

    embedding_text = f"{normalized_key}: {normalized_value}"
    embedding = await asyncio.to_thread(generate_embedding, embedding_text)

    statement = select(MemoryEntry).where(
        MemoryEntry.user_id == user_id,
        MemoryEntry.key == normalized_key,
    )
    result = await db.execute(statement)
    entry = result.scalars().first()

    if entry is None:
        entry = MemoryEntry(
            user_id=user_id,
            key=normalized_key,
            value=normalized_value,
            category=normalized_category,
            embedding=embedding,
        )
        db.add(entry)
    else:
        entry.value = normalized_value
        entry.category = normalized_category
        entry.embedding = embedding

    await db.commit()
    await db.refresh(entry)
    return entry


async def list_memories(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[MemoryEntry]:
    statement = (
        select(MemoryEntry)
        .where(MemoryEntry.user_id == user_id)
        .order_by(MemoryEntry.updated_at.desc())
        .offset(max(skip, 0))
        .limit(max(1, min(limit, 100)))
    )
    result = await db.execute(statement)
    return list(result.scalars().all())


async def search_memories(
    db: AsyncSession,
    user_id: int,
    query: str,
    limit: int = 5,
) -> list[MemoryEntry]:
    return await retrieve_similar_memories(db, user_id, query, limit)


async def delete_memory(
    db: AsyncSession,
    user_id: int,
    memory_id: int,
) -> bool:
    statement = select(MemoryEntry).where(
        MemoryEntry.id == memory_id,
        MemoryEntry.user_id == user_id,
    )
    result = await db.execute(statement)
    entry = result.scalars().first()
    if entry is None:
        return False

    await db.delete(entry)
    await db.commit()
    return True


async def build_memory_context(
    db: AsyncSession,
    user_id: int,
    query: str,
    limit: int = 5,
) -> str:
    """Format relevant memories as bounded, plain-text model context."""
    entries = await search_memories(db, user_id, query, limit)
    if not entries:
        return ""

    return "\n".join(
        f"- {entry.key} ({entry.category}): {entry.value}"
        for entry in entries
    )
