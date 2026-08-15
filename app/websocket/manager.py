import json
from typing import Dict, List, Optional, Union
from fastapi import WebSocket
from app.core.logger import logger


class ConnectionManager:
    """
    Manages active WebSocket connections, enabling personal messaging,
    client-id routing, and system broadcasts.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id_or_ws: Union[str, WebSocket], websocket: Optional[WebSocket] = None):
        """Accepts connection and tracks by websocket and optional client_id."""
        if isinstance(client_id_or_ws, WebSocket):
            ws = client_id_or_ws
            client_id = None
        else:
            client_id = str(client_id_or_ws)
            ws = websocket

        if ws is None:
            raise ValueError("WebSocket instance must be provided")

        await ws.accept()
        if ws not in self.active_connections:
            self.active_connections.append(ws)

        if client_id:
            self.client_connections[client_id] = ws
            logger.info(f"WebSocket client '{client_id}' connected (Total: {len(self.active_connections)})")
        else:
            logger.info(f"Anonymous WebSocket client connected (Total: {len(self.active_connections)})")

    def disconnect(self, client_id_or_ws: Union[str, WebSocket], websocket: Optional[WebSocket] = None):
        """Removes connection from active pool and client dictionary."""
        ws = None
        if isinstance(client_id_or_ws, WebSocket):
            ws = client_id_or_ws
            # Find and remove from dict if present
            for cid, cws in list(self.client_connections.items()):
                if cws == ws:
                    del self.client_connections[cid]
                    break
        else:
            client_id = str(client_id_or_ws)
            ws = websocket or self.client_connections.get(client_id)
            if client_id in self.client_connections:
                del self.client_connections[client_id]

        if ws and ws in self.active_connections:
            self.active_connections.remove(ws)
            logger.info(f"WebSocket client disconnected (Remaining: {len(self.active_connections)})")

    async def send_personal_message(self, message: Union[str, dict], websocket: WebSocket):
        """Sends a JSON or string message directly to a WebSocket client."""
        if isinstance(message, dict):
            payload = json.dumps(message)
        else:
            payload = str(message)
        await websocket.send_text(payload)

    async def send_message(self, message: Union[str, dict], websocket: WebSocket):
        """Alias for send_personal_message for backward compatibility."""
        await self.send_personal_message(message, websocket)

    async def send_to_client(self, client_id: str, message: Union[str, dict]) -> bool:
        """Sends a message to a specific client identified by client_id."""
        ws = self.client_connections.get(client_id)
        if ws:
            await self.send_personal_message(message, ws)
            return True
        return False

    async def broadcast(self, message: Union[str, dict]):
        """Broadcasts a message to all connected WebSocket clients."""
        if isinstance(message, dict):
            payload = json.dumps(message)
        else:
            payload = str(message)

        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket connection: {e}")
                if connection in self.active_connections:
                    self.active_connections.remove(connection)


manager = ConnectionManager()