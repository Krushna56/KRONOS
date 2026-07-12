from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.core.config import settings
from app.db.base import Base

# Create standard SQLAlchemy async engine using database URL from config settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

async def get_db():
    """Dependency for obtaining an async session inside API routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

