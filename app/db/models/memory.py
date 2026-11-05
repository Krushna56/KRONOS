from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from app.db.base import Base


class MemoryEntry(Base):
    """A durable, user-owned fact that can be retrieved semantically."""

    __tablename__ = "memory_entries"
    __table_args__ = (Index("ix_memory_entries_user_id", "user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(160), nullable=False, index=True)
    value = Column(Text, nullable=False)
    category = Column(String(80), nullable=True, default="general", index=True)
    embedding = Column(Vector(384), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )
    # Nullable to preserve compatibility with legacy rows; all new API writes
    # require an authenticated user and always populate this column.
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
