from __future__ import annotations
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin

class SocialAccount(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "social_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    platform_id: Mapped[int] = mapped_column(
        ForeignKey("platforms.id", ondelete="CASCADE"),
        nullable=False
    )

    platform_user_id: Mapped[str] = mapped_column(
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

    access_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    refresh_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    platform: Mapped[Platform] = relationship(
        back_populates="accounts"
    )

    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SocialAccount {self.username}@{self.platform.name if self.platform else self.platform_id}>"