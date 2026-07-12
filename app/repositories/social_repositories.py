from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.platform import Platform
from app.models.social_account import SocialAccount
from app.models.conversation import Conversation
from app.models.conversation_participant import ConversationParticipant
from app.models.message import Message
from app.models.attachment import Attachment

class PlatformRepository(BaseRepository[Platform]):
    def __init__(self, db: AsyncSession):
        super().__init__(Platform, db)

    async def get_by_name(self, name: str) -> Optional[Platform]:
        query = select(Platform).where(Platform.name == name, Platform.is_deleted == False)
        result = await self.db.execute(query)
        return result.scalars().first()


class SocialAccountRepository(BaseRepository[SocialAccount]):
    def __init__(self, db: AsyncSession):
        super().__init__(SocialAccount, db)

    async def get_by_platform_user_id(self, platform_id: int, platform_user_id: str) -> Optional[SocialAccount]:
        query = select(SocialAccount).where(
            SocialAccount.platform_id == platform_id,
            SocialAccount.platform_user_id == platform_user_id,
            SocialAccount.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_by_user(self, user_id: int) -> List[SocialAccount]:
        query = select(SocialAccount).where(SocialAccount.user_id == user_id, SocialAccount.is_deleted == False)
        result = await self.db.execute(query)
        return list(result.scalars().all())


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: AsyncSession):
        super().__init__(Conversation, db)

    async def get_by_external_id(self, platform_id: int, external_id: str) -> Optional[Conversation]:
        query = select(Conversation).where(
            Conversation.platform_id == platform_id,
            Conversation.external_id == external_id,
            Conversation.is_deleted == False
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_with_relations(self, conversation_id: int) -> Optional[Conversation]:
        query = (
            select(Conversation)
            .options(
                selectinload(Conversation.participants),
                selectinload(Conversation.platform),
                selectinload(Conversation.account)
            )
            .where(Conversation.id == conversation_id, Conversation.is_deleted == False)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_conversations_with_relations(self, skip: int = 0, limit: int = 100) -> List[Conversation]:
        query = (
            select(Conversation)
            .options(
                selectinload(Conversation.participants),
                selectinload(Conversation.platform),
                selectinload(Conversation.account)
            )
            .where(Conversation.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())


class MessageRepository(BaseRepository[Message]):
    def __init__(self, db: AsyncSession):
        super().__init__(Message, db)

    async def get_by_external_id(self, external_id: str) -> Optional[Message]:
        query = (
            select(Message)
            .options(selectinload(Message.attachments))
            .where(Message.external_id == external_id, Message.is_deleted == False)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_by_conversation(self, conversation_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        query = (
            select(Message)
            .options(selectinload(Message.attachments))
            .where(Message.conversation_id == conversation_id, Message.is_deleted == False)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
