"""
Reusable mixins shared by all database models 
"""

from __future__ import annotations 

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime
from sqlalchemy import Boolean
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class UUIDMixin:
    """
    Internal UUID.

    Never exposed to external platforms.

    Useful for APIs and distributed systems.
    """

    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        default=uuid4,
        unique=True,
        nullable=False,
        index=True,
    )


class TimestampMixin:
    """
    Automatically managed timestamps.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Soft delete support.

    Instead of deleting rows, mark them deleted.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )