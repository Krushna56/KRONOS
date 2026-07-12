from __future__ import annotations
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin

class ConversationParticipant(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "conversation_participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    username: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    # Relationships
    conversation: Mapped[Conversation] = relationship(
        back_populates="participants"
    )

    def __repr__(self):
        return f"<ConversationParticipant {self.username} in {self.conversation_id}>"
