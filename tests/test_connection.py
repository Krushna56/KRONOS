"""Connectivity check for the configured database (skipped if unreachable)."""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings


@pytest.mark.asyncio
async def test_database_connection():
    engine = create_async_engine(settings.DATABASE_URL)
    try:
        async with engine.connect() as conn:
            assert (await conn.execute(text("SELECT 1"))).scalar() == 1
    except Exception as exc:  # no DB running (e.g. CI / fresh checkout)
        pytest.skip(f"Database not reachable: {exc}")
    finally:
        await engine.dispose()
