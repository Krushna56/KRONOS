from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.conversation import ChatConversation, ChatMessage

from app.schemas.chat_schema import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse
)

from app.auth.jwt_bearer import get_current_user

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"]
)


# =========================================================
# CREATE CONVERSATION
# =========================================================

@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_conversation(
    conv_in: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new conversation for the authenticated user.
    """

    title = conv_in.title or "New Conversation"

    new_conv = ChatConversation(
        title=title,
        user_id=current_user.id
    )

    db.add(new_conv)

    await db.commit()
    await db.refresh(new_conv)

    return new_conv


# =========================================================
# LIST CONVERSATIONS
# =========================================================

@router.get(
    "/conversations",
    response_model=List[ConversationResponse]
)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all conversations for the authenticated user.
    """

    query = (
        select(ChatConversation)
        .where(ChatConversation.user_id == current_user.id)
        .order_by(ChatConversation.created_at.desc())
    )

    result = await db.execute(query)

    conversations = result.scalars().all()

    return conversations


# =========================================================
# GET CONVERSATION MESSAGES
# =========================================================

@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageResponse]
)
async def get_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all messages from a conversation.
    """

    # Verify ownership
    query = select(ChatConversation).where(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    )

    result = await db.execute(query)

    conversation = result.scalars().first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Fetch messages
    msg_query = (
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
    )

    msg_result = await db.execute(msg_query)

    messages = msg_result.scalars().all()

    return messages


# =========================================================
# POST MESSAGE
# =========================================================

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse
)
async def post_message(
    conversation_id: int,
    msg_in: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Post a user message and generate assistant response.
    """

    # Verify ownership
    query = select(ChatConversation).where(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    )

    result = await db.execute(query)

    conversation = result.scalars().first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # ============================================
    # SAVE USER MESSAGE
    # ============================================

    user_message = ChatMessage(
        conversation_id=conversation_id,
        sender="user",
        content=msg_in.content
    )

    db.add(user_message)

    await db.commit()
    await db.refresh(user_message)

    # ============================================
    # AI RESPONSE PLACEHOLDER
    # ============================================

    ai_response_content = (
        f"Thank you for your message: "
        f"'{msg_in.content}'. "
        f"As your Phase 1 personal AI assistant, "
        f"I am fully integrated with your postgres database!"
    )

    # ============================================
    # SAVE ASSISTANT MESSAGE
    # ============================================

    assistant_message = ChatMessage(
        conversation_id=conversation_id,
        sender="assistant",
        content=ai_response_content
    )

    db.add(assistant_message)

    await db.commit()
    await db.refresh(assistant_message)

    # Return user message
    return user_message


# =========================================================
# FAST CLONE ASK (FOR UI / ROBOT / VOICE / CALLS)
# =========================================================

from pydantic import BaseModel
from typing import Optional
import sys, io
from app.core.logger import logger
from app.persona.clone_engine import clone_engine

# Force UTF-8 stdout so emoji prints never crash on Windows cp1252
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class AskRequest(BaseModel):
    message: str
    channel: Optional[str] = "voice"

@router.post("/ask")
async def ask_clone(request: AskRequest):
    """
    Direct endpoint for Voice UI, Mini Robot, or Telephony to get a response
    in Krushna's exact authentic tone.
    """
    logger.info(f"📥 [USER QUESTION] [{request.channel.upper()}]: \"{request.message}\"")

    try:
        reply = await asyncio.wait_for(
            clone_engine.generate_reply(
                incoming_message=request.message,
                channel=request.channel or "voice"
            ),
            timeout=30
        )
    except asyncio.TimeoutError:
        logger.warning("generate_reply timed out, using fallback message")
        reply = "I’m currently experiencing a brief delay. Please try again shortly."

    logger.info(f"🤖 [CLONE REPLY] [{request.channel.upper()}]: \"{reply}\"")
    
    return {"reply": reply, "channel": request.channel}


# =========================================================
# REAL-TIME STREAMING ENDPOINT (SSE) — token by token
# =========================================================

from fastapi.responses import StreamingResponse
import asyncio
import json

@router.post("/ask-stream")
async def ask_clone_stream(request: AskRequest):
    """
    Real-time SSE streaming endpoint. Streams reply word-by-word for instant UI updates.
    """
    logger.info(f"📥 [STREAM QUESTION] [{request.channel.upper()}]: \"{request.message}\"")

    async def event_generator():
        import os, httpx
        streamed = False
        gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()

        # Check calendar intent for stream as well
        calendar_keywords = [
            "calendar", "calender", "schedule", "plan", "plans", "meeting", "meetings",
            "aaj kya hai", "aaj kya karna", "agenda", "appointment", "routine", "aaj ka scene"
        ]
        q_lower = request.message.lower()
        calendar_context = ""
        if any(kw in q_lower for kw in calendar_keywords):
            try:
                from app.services.calendar_service import calendar_service
                cal_summary = calendar_service.get_today_summary()
                calendar_context = f"\n[LIVE GOOGLE CALENDAR SCHEDULE FOR TODAY]:\n{cal_summary}\nAnswer the user based on these exact events from their Google Calendar."
            except Exception as e:
                logger.warning(f"Failed to fetch calendar context for stream: {e}")

        if gemini_key:
            system = clone_engine.profile.to_system_prompt_directive()
            if request.channel == "call":
                system += "\n[CALL SCENARIO]: Be very brief and conversational."
            if calendar_context:
                system += f"\n{calendar_context}"
            payload = {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": request.message}]}],
                "generationConfig": {"temperature": 0.8, "maxOutputTokens": 2048}
            }
            models_to_try = ["gemini-2.5-flash", "gemini-flash-latest"]
            for model_name in models_to_try:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:streamGenerateContent?alt=sse&key={gemini_key}"
                )
                try:
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        async with client.stream("POST", url, json=payload) as resp:
                            if resp.status_code == 200:
                                buffer = ""
                                async for line in resp.aiter_lines():
                                    if line.startswith("data:"):
                                        raw = line[5:].strip()
                                        if not raw or raw == "[DONE]":
                                            continue
                                        try:
                                            chunk = json.loads(raw)
                                            parts = (
                                                chunk.get("candidates", [{}])[0]
                                                .get("content", {})
                                                .get("parts", [{}])
                                            )
                                            token = parts[0].get("text", "") if parts else ""
                                            if token:
                                                buffer += token
                                                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
                                        except Exception:
                                            pass
                                logger.info(f"🤖 [STREAM COMPLETED] [{model_name}]: \"{buffer.strip()}\"")
                                yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"
                                streamed = True
                                break
                            else:
                                logger.warning(f"[STREAM] {model_name} HTTP {resp.status_code}")
                except Exception as e:
                    logger.warning(f"[STREAM] {model_name} error: {e}")

        if not streamed:
            full_reply = await clone_engine.generate_reply(
                incoming_message=request.message,
                channel=request.channel or "voice"
            )
            logger.info(f"🤖 [FALLBACK STREAM]: \"{full_reply}\"")
            words = full_reply.split(" ")
            for i, word in enumerate(words):
                token = word + (" " if i < len(words) - 1 else "")
                yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
                await asyncio.sleep(0.04)
            yield f"data: {json.dumps({'token': '', 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )



