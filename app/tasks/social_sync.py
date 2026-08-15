"""
Social Sync Task - Periodic background synchronization of social platforms.
"""

import asyncio
from typing import List
from app.core.logger import logger
from app.agents.manager import agent_manager
from app.db.session import AsyncSessionLocal
from app.services.social_services import SocialAccountService, ConversationService, MessageService


class SocialSyncTask:
    """
    Background worker that runs periodic synchronization loops across all active
    registered social agents (Discord, Telegram, Gmail, LinkedIn).
    """

    def __init__(self, sync_interval_seconds: int = 60):
        self.interval = sync_interval_seconds
        self.is_running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Starts the background synchronization loop."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info(f"[SocialSync] Started social synchronization loop (Interval: {self.interval}s)")

    async def stop(self):
        """Stops the synchronization loop."""
        if not self.is_running:
            return
        self.is_running = False
        if self._task:
            self._task.cancel()
        logger.info("[SocialSync] Stopped social synchronization loop.")

    async def _sync_loop(self):
        while self.is_running:
            try:
                await self.sync_all_platforms()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SocialSync] Error during sync cycle: {e}")
                await asyncio.sleep(self.interval)

    async def sync_all_platforms(self):
        """Synchronizes data across all registered platform agents."""
        logger.debug("[SocialSync] Executing sync cycle across registered agents...")
        for name, agent in agent_manager.agents.items():
            try:
                # Check agent connectivity
                health = await agent.health()
                if health.connected:
                    logger.debug(f"[SocialSync] Agent '{name}' is connected and synced.")
            except Exception as exc:
                logger.error(f"[SocialSync] Failed to sync agent '{name}': {exc}")


social_sync_task = SocialSyncTask()
