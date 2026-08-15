from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    sender: str
    content: str

class MessageCreate(BaseModel):
    content: str

class MessageResponse(MessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    title: str | None = None

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
