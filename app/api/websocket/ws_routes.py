import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager
from app.core.logger import logger

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket connection endpoint at /ws/{client_id}."""
    await manager.connect(client_id, websocket)
    try:
        # Send initial welcome packet
        await manager.send_personal_message(
            {
                "type": "system_notification",
                "sender": "system",
                "content": f"Welcome to AI Clone assistant channel, {client_id}!"
            },
            websocket
        )
        
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received websocket packet from {client_id}: {data}")
            
            try:
                packet = json.loads(data)
                content = packet.get("content", "")
                
                # Echo and acknowledge message
                response = {
                    "type": "chat_message",
                    "sender": "assistant",
                    "content": f"I received your message via WebSocket: '{content}'"
                }
            except json.JSONDecodeError:
                response = {
                    "type": "error",
                    "sender": "system",
                    "content": "Invalid JSON packet format"
                }
                
            await manager.send_personal_message(response, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id, websocket)
