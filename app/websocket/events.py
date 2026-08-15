import json
from typing import Any
from fastapi import WebSocket


async def send_event(websocket: WebSocket, event: str, data: Any):
    """Encodes and sends an event packet over a WebSocket connection."""
    payload = {
        "event": event,
        "data": data
    }
    await websocket.send_text(
        json.dumps(payload)
    )


class WebSocketEvents:
    # System events
    SYSTEM_CONNECTED = "system_connected"
    SYSTEM_NOTIFICATION = "system_notification"
    ERROR = "error"

    # Chat & Agent events
    AGENT_THINKING = "agent_thinking"
    AGENT_REPLY = "agent_reply"
    VOICE_STATE_CHANGED = "voice_state_changed"
    SPEECH_DETECTED = "speech_detected"
    TASK_PROGRESS = "task_progress"