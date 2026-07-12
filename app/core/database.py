from sqlalchemy.orm.context import AutoflushOnlyORMCompileState
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import DATABASE_URL

# Convert async connection string to sync protocol for the synchronous engine
sync_db_url = DATABASE_URL
if sync_db_url and sync_db_url.startswith("postgresql+asyncpg://"):
    sync_db_url = sync_db_url.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(sync_db_url)

SessionLocal = sessionmaker(
    autocommit = False,
    autoflush=False,
    bind = engine
)

Base = declarative_base()