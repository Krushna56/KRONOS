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

