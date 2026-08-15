from __future__ import annotations
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import UUIDMixin, TimestampMixin, SoftDeleteMixin

class Platform(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    # Relationships
    accounts: Mapped[list[SocialAccount]] = relationship(
        back_populates="platform",
        cascade="all, delete-orphan"
    )

    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="platform",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Platform {self.name}>"
