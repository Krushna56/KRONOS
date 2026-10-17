from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform import Platform
from app.models.social_account import SocialAccount
from app.models.conversation import Conversation
from app.models.conversation_participant import ConversationParticipant
from app.models.message import Message
from app.models.attachment import Attachment

from app.repositories.social_repositories import (
    PlatformRepository,
    SocialAccountRepository,
    ConversationRepository,
    MessageRepository
)
from app.repositories.base import BaseRepository

class SocialAccountService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_repo = SocialAccountRepository(db)
        self.platform_repo = PlatformRepository(db)

    async def get_platform_by_name(self, name: str) -> Optional[Platform]:
        return await self.platform_repo.get_by_name(name)

    async def create_platform(self, name: str) -> Platform:
        existing = await self.platform_repo.get_by_name(name)
        if existing:
            return existing
        platform = Platform(name=name)
        return await self.platform_repo.create(platform)

    async def create_account(
        self,
        user_id: int,
        platform_name: str,
        platform_user_id: str,
        username: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ) -> SocialAccount:
        platform = await self.create_platform(platform_name)
        
        existing = await self.account_repo.get_by_platform_user_id(platform.id, platform_user_id)
        if existing:
            # Update tokens and info
            update_data = {
                "username": username,
                "display_name": display_name or existing.display_name,
                "email": email or existing.email,
                "access_token": access_token or existing.access_token,
                "refresh_token": refresh_token or existing.refresh_token
            }
            return await self.account_repo.update(existing, update_data)

        account = SocialAccount(
            user_id=user_id,
            platform_id=platform.id,
            platform_user_id=platform_user_id,
            username=username,
            display_name=display_name,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token
        )
        return await self.account_repo.create(account)

    async def get_account(self, account_id: int) -> Optional[SocialAccount]:
        return await self.account_repo.get(account_id)

    async def get_account_by_uuid(self, uuid: str) -> Optional[SocialAccount]:
        return await self.account_repo.get_by_uuid(uuid)

    async def list_accounts(self, skip: int = 0, limit: int = 100) -> List[SocialAccount]:
        return await self.account_repo.list(skip, limit)


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.platform_repo = PlatformRepository(db)
        self.participant_repo = BaseRepository(ConversationParticipant, db)

    async def get_or_create_conversation(
        self,
        platform_name: str,
        account_id: int,
        external_id: str,
        title: Optional[str] = None,
        conversation_type: str = "direct"
    ) -> Conversation:
        platform = await self.platform_repo.get_by_name(platform_name)
        if not platform:
            raise ValueError(f"Platform '{platform_name}' does not exist.")

        existing = await self.conv_repo.get_by_external_id(platform.id, external_id)
        if existing:
            return existing

        conv = Conversation(
            platform_id=platform.id,
            account_id=account_id,
            external_id=external_id,
            title=title,
            conversation_type=conversation_type
        )
        return await self.conv_repo.create(conv)

    async def add_participant(
        self,
        conversation_id: int,
        external_id: str,
        username: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> ConversationParticipant:
        # Check if already added
        query = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.external_id == external_id,
            ConversationParticipant.is_deleted == False
        )
        result = await self.db.execute(query)
        existing = result.scalars().first()
        if existing:
            return existing

        participant = ConversationParticipant(
            conversation_id=conversation_id,
            external_id=external_id,
            username=username,
            display_name=display_name,
            email=email
        )
        return await self.participant_repo.create(participant)

    async def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        return await self.conv_repo.get_with_relations(conversation_id)

    async def list_conversations(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        return await self.conv_repo.list_conversations_with_relations(skip, limit)


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.msg_repo = MessageRepository(db)
        self.conv_repo = ConversationRepository(db)
        self.attachment_repo = BaseRepository(Attachment, db)

    async def create_message(
        self,
        conversation_id: int,
        external_id: str,
        sender_id: str,
        content: str,
        is_outgoing: bool,
        reply_to_external_id: Optional[str] = None
    ) -> Message:
        # Check if already exists
        existing = await self.msg_repo.get_by_external_id(external_id)
        if existing:
            return existing

        reply_to_id = None
        if reply_to_external_id:
            parent = await self.msg_repo.get_by_external_id(reply_to_external_id)
            if parent:
                reply_to_id = parent.id

        message = Message(
            conversation_id=conversation_id,
            external_id=external_id,
            sender_id=sender_id,
            content=content,
            is_outgoing=is_outgoing,
            reply_to_id=reply_to_id
        )
        
        new_msg = await self.msg_repo.create(message)
        
        # Update conversation's last_message_at timestamp
        conv = await self.conv_repo.get(conversation_id)
        if conv:
            await self.conv_repo.update(conv, {"last_message_at": datetime.now(timezone.utc)})

        return new_msg

    async def add_attachment(
        self,
        message_id: int,
        filename: str,
        mime_type: str,
        file_size: int,
        url: str
    ) -> Attachment:
        attachment = Attachment(
            message_id=message_id,
            filename=filename,
            mime_type=mime_type,
            file_size=file_size,
            url=url
        )
        return await self.attachment_repo.create(attachment)

    async def list_messages_in_thread(self, conversation_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        return await self.msg_repo.list_by_conversation(conversation_id, skip, limit)
