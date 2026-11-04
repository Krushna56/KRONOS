"""
Reply Queue - Asynchronous Background Task Queue for Social Message Processing.
"""

import asyncio
from typing import Optional, Dict, Any
from app.core.logger import logger
from app.db.session import AsyncSessionLocal
from app.services.reply_orchestrator import ReplyOrchestrator


class ReplyQueue:
    """
    In-memory async queue for processing inbound social message reply pipelines.
    Decouples immediate webhook/socket ingestion from LLM generation and delay delays.
    """

    def __init__(self, max_concurrency: int = 5):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.max_concurrency = max_concurrency
        self.workers: list[asyncio.Task] = []
        self.is_running = False

    async def enqueue(self, conversation_id: int, message_id: int, metadata: Optional[Dict[str, Any]] = None):
        """Enqueue an inbound message job for processing."""
        job = {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "metadata": metadata or {}
        }
        await self.queue.put(job)
        logger.info(f"[ReplyQueue] Enqueued job for conv_id={conversation_id}, msg_id={message_id}. (Queue size: {self.queue.qsize()})")

    async def start_workers(self):
        """Start worker tasks to consume the queue."""
        if self.is_running:
            return
        self.is_running = True
        for i in range(self.max_concurrency):
            task = asyncio.create_task(self._worker_loop(i))
            self.workers.append(task)
        logger.info(f"[ReplyQueue] Started {self.max_concurrency} reply queue workers.")

    async def stop_workers(self):
        """Stop all worker tasks gracefully."""
        self.is_running = False
        for task in self.workers:
            task.cancel()
        self.workers.clear()
        logger.info("[ReplyQueue] Stopped reply queue workers.")

    async def _worker_loop(self, worker_id: int):
        while self.is_running:
            try:
                job = await self.queue.get()
                conv_id = job["conversation_id"]
                msg_id = job["message_id"]

                logger.info(f"[ReplyQueue-Worker-{worker_id}] Processing message {msg_id} in conversation {conv_id}")

                async with AsyncSessionLocal() as db:
                    orchestrator = ReplyOrchestrator(db)
                    await orchestrator.handle_inbound(conv_id, msg_id)

                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[ReplyQueue-Worker-{worker_id}] Error processing job: {e}")
                self.queue.task_done()


reply_queue = ReplyQueue()
