"""
WebSocket Conversation Service - Real-time conversational pipeline over WebSockets.
"""

from typing import Dict, Any, Optional
from fastapi import WebSocket
from app.core.logger import logger
from app.websocket.events import send_event, WebSocketEvents
from app.services.ai.llm_service import llm_service
from app.services.ai.prompt_builder import PromptBuilder


class WebSocketConversationService:
    """
    Handles live duplex chat interactions between WebSocket clients and KRONOS AI.
    """

    def __init__(self):
        self.active_sessions: Dict[str, list] = {}

    async def handle_user_message(
        self,
        websocket: WebSocket,
        client_id: str,
        content: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes a user message received over WebSocket:
        1. Emits AGENT_THINKING event to UI
        2. Queries LLM service
        3. Emits AGENT_REPLY event and returns final packet
        """
        logger.info(f"[WS Conversation] Received message from client '{client_id}': {content}")

        # 1. Notify UI that assistant is thinking
        await send_event(
            websocket,
            WebSocketEvents.AGENT_THINKING,
            {"message": "Thinking...", "client_id": client_id}
        )

        # 2. Build prompt and generate response
        system_prompt = PromptBuilder.build_system_prompt("KRONOS")
        user_prompt = PromptBuilder.build_user_prompt(
            user_query=content,
            context=context or "Live WebSocket Chat Session"
        )

        try:
            ai_response = await llm_service.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
        except Exception as e:
            logger.error(f"[WS Conversation] Error generating LLM response: {e}")
            ai_response = f"I received your message '{content}', but encountered a processing error."

        # 3. Emit response event back to client
        response_data = {
            "type": "chat_message",
            "sender": "assistant",
            "content": ai_response,
            "client_id": client_id
        }

        await send_event(
            websocket,
            WebSocketEvents.AGENT_REPLY,
            response_data
        )

        return response_data


ws_conversation_service = WebSocketConversationService()
