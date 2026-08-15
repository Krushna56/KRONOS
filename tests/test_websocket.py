import unittest
from unittest.mock import AsyncMock
from app.websocket.manager import ConnectionManager
from app.websocket.events import WebSocketEvents


class TestWebSocketManager(unittest.IsolatedAsyncioTestCase):
    async def test_connect_and_disconnect(self):
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        # Connect with client_id
        await manager.connect("client_123", mock_ws)
        self.assertEqual(len(manager.active_connections), 1)
        self.assertIn("client_123", manager.client_connections)

        # Send personal message
        await manager.send_personal_message({"event": "test"}, mock_ws)
        mock_ws.send_text.assert_called_once_with('{"event": "test"}')

        # Broadcast
        mock_ws.reset_mock()
        await manager.broadcast({"broadcast": "hello"})
        mock_ws.send_text.assert_called_once_with('{"broadcast": "hello"}')

        # Disconnect
        manager.disconnect("client_123", mock_ws)
        self.assertEqual(len(manager.active_connections), 0)
        self.assertNotIn("client_123", manager.client_connections)


if __name__ == "__main__":
    unittest.main()
