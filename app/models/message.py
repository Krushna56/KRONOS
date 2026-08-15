from __future__ import annotations
from sqlalchemy import ForeignKey, Text, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin

class Message(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    sender_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    is_outgoing: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    reply_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True
    )

    # Relationships
    conversation: Mapped[Conversation] = relationship(
        back_populates="messages"
    )

    attachments: Mapped[list[Attachment]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan"
    )

    parent_message: Mapped[Message | None] = relationship(
        back_populates="replies",
        remote_side=[id]
    )

    replies: Mapped[list[Message]] = relationship(
        back_populates="parent_message",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Message {self.external_id} sender={self.sender_id} is_outgoing={self.is_outgoing}>"