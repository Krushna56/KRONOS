from __future__ import annotations
from datetime import datetime
from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin

class Conversation(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    platform_id: Mapped[int] = mapped_column(
        ForeignKey("platforms.id", ondelete="CASCADE"),
        nullable=False
    )
    
    account_id: Mapped[int] = mapped_column(
        ForeignKey("social_accounts.id", ondelete="CASCADE"),
        nullable=False
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    conversation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    reply_mode: Mapped[str] = mapped_column(
        String(50),
        default="suggest",
        nullable=False
    )

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    platform: Mapped[Platform] = relationship(
        back_populates="conversations"
    )

    account: Mapped[SocialAccount] = relationship(
        back_populates="conversations"
    )

    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    participants: Mapped[list[ConversationParticipant]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Conversation {self.title or self.external_id} type={self.conversation_type}>"