from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.auth.jwt_bearer import get_current_user
from app.db.models.user import User

from app.schemas.social_schema import (
    PlatformCreate, PlatformResponse,
    SocialAccountCreate, SocialAccountResponse,
    ConversationCreate, ConversationResponse,
    ParticipantBase, ParticipantResponse,
    MessageCreate, MessageResponse,
    AttachmentCreate, AttachmentResponse
)
from app.services.social_services import (
    SocialAccountService,
    ConversationService,
    MessageService
)

router = APIRouter(
    prefix="/api/social",
    tags=["Social Agents"]
)

# =========================================================
# PLATFORMS
# =========================================================

@router.post("/platforms", response_model=PlatformResponse, status_code=status.HTTP_201_CREATED)
async def create_platform(
    platform_in: PlatformCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SocialAccountService(db)
    return await service.create_platform(platform_in.name)

@router.get("/platforms", response_model=List[PlatformResponse])
async def list_platforms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SocialAccountService(db)
    return await service.platform_repo.list()

# =========================================================
# SOCIAL ACCOUNTS
# =========================================================

@router.post("/accounts", response_model=SocialAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_in: SocialAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SocialAccountService(db)
    platform = await service.get_platform_by_name(account_in.username) # fallback check or create
    return await service.create_account(
        user_id=account_in.user_id,
        platform_name=account_in.username,  # uses platform name passed through body logic
        platform_user_id=account_in.platform_user_id,
        username=account_in.username,
        display_name=account_in.display_name,
        email=account_in.email,
        access_token=account_in.access_token,
        refresh_token=account_in.refresh_token
    )

@router.get("/accounts", response_model=List[SocialAccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SocialAccountService(db)
    return await service.list_accounts()

@router.get("/accounts/{uuid}", response_model=SocialAccountResponse)
async def get_account(
    uuid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = SocialAccountService(db)
    account = await service.get_account_by_uuid(uuid)
    if not account:
        raise HTTPException(status_code=404, detail="Social Account not found")
    return account

# =========================================================
# CONVERSATIONS
# =========================================================

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_in: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ConversationService(db)
    acc_service = SocialAccountService(db)
    account = await acc_service.get_account(conv_in.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Social Account not found")
    
    platform = await acc_service.platform_repo.get(conv_in.platform_id)
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    return await service.get_or_create_conversation(
        platform_name=platform.name,
        account_id=conv_in.account_id,
        external_id=conv_in.external_id,
        title=conv_in.title,
        conversation_type=conv_in.conversation_type
    )

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ConversationService(db)
    return await service.list_conversations()

@router.get("/conversations/{id}", response_model=ConversationResponse)
async def get_conversation(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ConversationService(db)
    conv = await service.get_conversation(id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.post("/conversations/{id}/participants", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
async def add_participant(
    id: int,
    participant_in: ParticipantBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ConversationService(db)
    conv = await service.conv_repo.get(id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return await service.add_participant(
        conversation_id=id,
        external_id=participant_in.external_id,
        username=participant_in.username,
        display_name=participant_in.display_name,
        email=participant_in.email
    )

# =========================================================
# MESSAGES
# =========================================================

@router.post("/conversations/{id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    id: int,
    message_in: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MessageService(db)
    conv_service = ConversationService(db)
    conv = await conv_service.conv_repo.get(id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return await service.create_message(
        conversation_id=id,
        external_id=message_in.external_id,
        sender_id=message_in.sender_id,
        content=message_in.content,
        is_outgoing=message_in.is_outgoing,
        reply_to_external_id=None
    )

@router.get("/conversations/{id}/messages", response_model=List[MessageResponse])
async def list_messages(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MessageService(db)
    return await service.list_messages_in_thread(id)

@router.post("/messages/{id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def add_attachment(
    id: int,
    attachment_in: AttachmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MessageService(db)
    msg = await service.msg_repo.get(id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    return await service.add_attachment(
        message_id=id,
        filename=attachment_in.filename,
        mime_type=attachment_in.mime_type,
        file_size=attachment_in.file_size,
        url=attachment_in.url
    )
