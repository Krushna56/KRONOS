import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager
from app.websocket.conversation_service import ws_conversation_service
from app.core.logger import logger

router = APIRouter()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Duplex WebSocket connection endpoint at /ws/{client_id}."""
    await manager.connect(client_id, websocket)
    try:
        # Send initial welcome packet
        await manager.send_personal_message(
            {
                "type": "system_notification",
                "sender": "system",
                "content": f"Connected to KRONOS AI Assistant channel for client '{client_id}'."
            },
            websocket
        )

        while True:
            data = await websocket.receive_text()
            logger.info(f"Received websocket packet from {client_id}: {data}")

            try:
                packet = json.loads(data)
                content = packet.get("content") or packet.get("message", "")
                if not content and isinstance(packet, str):
                    content = packet
            except json.JSONDecodeError:
                content = data

            if content:
                await ws_conversation_service.handle_user_message(
                    websocket=websocket,
                    client_id=client_id,
                    content=str(content)
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id, websocket)
    except Exception as exc:
        logger.error(f"WebSocket error on client '{client_id}': {exc}")
        manager.disconnect(client_id, websocket)
