"""WebSocket event names and helper for sending structured events."""

import json
from typing import Any

from fastapi import WebSocket


class WebSocketEvents:
    """Event names emitted to UI clients."""

    AGENT_THINKING = "agent_thinking"
    AGENT_REPLY = "agent_reply"
    AGENT_ERROR = "agent_error"
    SYSTEM_NOTIFICATION = "system_notification"


async def send_event(websocket: WebSocket, event: str, data: Any) -> None:
    """Send {"event": ..., "data": ...} as a JSON text frame."""
    await websocket.send_text(json.dumps({"event": event, "data": data}))
