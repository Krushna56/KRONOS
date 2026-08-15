from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# Platform Schemas
class PlatformBase(BaseModel):
    name: str

class PlatformCreate(PlatformBase):
    pass

class PlatformResponse(PlatformBase):
    id: int
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)

# SocialAccount Schemas
class SocialAccountBase(BaseModel):
    platform_id: int
    platform_user_id: str
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None

class SocialAccountCreate(SocialAccountBase):
    user_id: int
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class SocialAccountResponse(SocialAccountBase):
    id: int
    uuid: UUID
    user_id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)

# Participant Schemas
class ParticipantBase(BaseModel):
    external_id: str
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None

class ParticipantResponse(ParticipantBase):
    id: int
    uuid: UUID
    conversation_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Conversation Schemas
class ConversationBase(BaseModel):
    platform_id: int
    account_id: int
    external_id: str
    title: Optional[str] = None
    conversation_type: str

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: int
    uuid: UUID
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    participants: List[ParticipantResponse] = []

    model_config = ConfigDict(from_attributes=True)

# Attachment Schemas
class AttachmentBase(BaseModel):
    filename: str
    mime_type: str
    file_size: int
    url: str

class AttachmentCreate(AttachmentBase):
    pass

class AttachmentResponse(AttachmentBase):
    id: int
    uuid: UUID
    message_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Message Schemas
class MessageBase(BaseModel):
    conversation_id: int
    external_id: str
    sender_id: str
    content: str
    is_outgoing: bool
    reply_to_id: Optional[int] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    attachments: List[AttachmentResponse] = []

    model_config = ConfigDict(from_attributes=True)
