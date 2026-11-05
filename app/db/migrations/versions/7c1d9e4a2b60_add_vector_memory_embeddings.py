"""add vector embeddings to memory entries

Revision ID: 7c1d9e4a2b60
Revises: cfde88b88426
Create Date: 2026-11-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = "7c1d9e4a2b60"
down_revision: Union[str, Sequence[str], None] = "cfde88b88426"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("memory_entries", sa.Column("embedding", Vector(384), nullable=True))
    op.create_index(
        "ix_memory_entries_user_id",
        "memory_entries",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_memory_entries_user_id", table_name="memory_entries")
    op.drop_column("memory_entries", "embedding")
