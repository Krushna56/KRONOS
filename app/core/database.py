from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base

database_url = settings.DATABASE_URL
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace(
        "postgresql+asyncpg://",
        "postgresql://",
        1,
    )

engine = create_engine(database_url)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Export the same declarative base used by all application models and Alembic.
__all__ = ["Base", "engine", "SessionLocal"]
