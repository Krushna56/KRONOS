import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://postgres:Ai%405605@127.0.0.1:5433/aiclone"

engine = create_async_engine(DATABASE_URL)

async def test():
    async with engine.connect() as conn:
        print("DATABASE CONNECTED")

asyncio.run(test())