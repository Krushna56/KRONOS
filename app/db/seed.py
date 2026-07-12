"""
Seed script - Module 5

Populates the database with the default platforms (Discord, Telegram, Gmail, LinkedIn)
and prints a verification summary.

Run with: python -m app.db.seed
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import AsyncSessionLocal
from app.models.platform import Platform
from app.core.logger import logger


PLATFORMS = ["discord", "telegram", "gmail", "linkedin"]


async def seed_platforms(db: AsyncSession) -> None:
    for name in PLATFORMS:
        result = await db.execute(
            select(Platform).where(Platform.name == name, Platform.is_deleted == False)
        )
        existing = result.scalars().first()
        if existing:
            logger.info(f"[SEED] Platform already exists: {name}")
        else:
            platform = Platform(name=name)
            db.add(platform)
            logger.info(f"[SEED] Created platform: {name}")

    await db.commit()
    logger.info("[SEED] Platform seeding complete.")


async def verify(db: AsyncSession) -> None:
    result = await db.execute(select(Platform).where(Platform.is_deleted == False))
    platforms = result.scalars().all()
    print(f"\n{'='*40}")
    print(f"  Phase 3 Database Seed Verification")
    print(f"{'='*40}")
    print(f"  Platforms in DB: {len(platforms)}")
    for p in platforms:
        print(f"    - [{p.id}] {p.name} (uuid: {p.uuid})")
    print(f"{'='*40}\n")


async def main():
    async with AsyncSessionLocal() as db:
        await seed_platforms(db)
        await verify(db)


if __name__ == "__main__":
    asyncio.run(main())
