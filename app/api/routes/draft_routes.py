"""
Draft management endpoints — accept/reject AI-generated SUGGEST/APPROVAL replies.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.auth.jwt_bearer import get_current_user
from app.db.models.user import User
from app.services.reply_orchestrator import ReplyOrchestrator
from app.schemas.social_schema import MessageResponse

router = APIRouter(
    prefix="/api/social/drafts",
    tags=["AI Drafts"]
)


@router.post("/{draft_id}/send", response_model=MessageResponse)
async def approve_and_send_draft(
    draft_id: int,
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve a SUGGEST/APPROVAL mode draft and send it via the platform agent.
    This initiates the human-simulation delay before dispatch.
    """
    orchestrator = ReplyOrchestrator(db)
    sent = await orchestrator.send_draft(draft_id, conversation_id)
    if not sent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft message not found or could not be sent."
        )
    return sent
