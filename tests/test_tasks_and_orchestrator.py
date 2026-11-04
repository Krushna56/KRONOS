import unittest
import asyncio
from unittest.mock import AsyncMock
from app.tasks.reply_queue import ReplyQueue
from app.tasks.social_sync import SocialSyncTask
from app.websocket.conversation_service import WebSocketConversationService


class TestTasksAndOrchestration(unittest.IsolatedAsyncioTestCase):
    async def test_reply_queue_lifecycle(self):
        queue = ReplyQueue(max_concurrency=2)
        self.assertFalse(queue.is_running)

        await queue.start_workers()
        self.assertTrue(queue.is_running)
        self.assertEqual(len(queue.workers), 2)

        # Enqueue job
        await queue.enqueue(conversation_id=1, message_id=101)
        self.assertGreaterEqual(queue.queue.qsize(), 0)

        # Stop workers
        await queue.stop_workers()
        self.assertFalse(queue.is_running)
        self.assertEqual(len(queue.workers), 0)

    async def test_social_sync_task(self):
        sync = SocialSyncTask(sync_interval_seconds=10)
        self.assertFalse(sync.is_running)

        await sync.start()
        self.assertTrue(sync.is_running)
        self.assertIsNotNone(sync._task)

        await sync.sync_all_platforms()

        await sync.stop()
        self.assertFalse(sync.is_running)

    async def test_websocket_conversation_service(self):
        service = WebSocketConversationService()
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock()

        response = await service.handle_user_message(
            websocket=mock_ws,
            client_id="test_user_1",
            content="Hello KRONOS"
        )

        self.assertIsNotNone(response)
        self.assertEqual(response["sender"], "assistant")
        self.assertEqual(response["client_id"], "test_user_1")
        self.assertGreaterEqual(mock_ws.send_text.call_count, 2)  # Thinking + Reply events


if __name__ == "__main__":
    unittest.main()
