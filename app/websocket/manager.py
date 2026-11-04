import json
from typing import Dict, List, Optional, Union

from fastapi import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections (optionally keyed by client id)."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_connections: Dict[str, WebSocket] = {}

    async def connect(self, *args) -> None:
        """connect(websocket) or connect(client_id, websocket)."""
        if len(args) == 1:
            websocket = args[0]
        elif len(args) == 2:
            client_id, websocket = args
            self.client_connections[client_id] = websocket
        else:
            raise TypeError("connect() takes (websocket) or (client_id, websocket)")
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, *args) -> None:
        """disconnect(websocket) or disconnect(client_id, websocket)."""
        websocket: Optional[WebSocket] = args[-1] if args else None
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        for cid, ws in list(self.client_connections.items()):
            if ws is websocket or (len(args) == 2 and cid == args[0]):
                del self.client_connections[cid]

    @staticmethod
    def _encode(message: Union[str, dict, list]) -> str:
        return message if isinstance(message, str) else json.dumps(message)

    async def send_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    async def send_personal_message(self, message, websocket: WebSocket) -> None:
        await websocket.send_text(self._encode(message))

    async def broadcast(self, message) -> None:
        payload = self._encode(message)
        for ws in list(self.active_connections):
            try:
                await ws.send_text(payload)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()
