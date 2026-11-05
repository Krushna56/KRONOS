from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MemoryCreate(BaseModel):
    key: str = Field(min_length=1, max_length=160)
    value: str = Field(min_length=1, max_length=8000)
    category: str = Field(default="general", min_length=1, max_length=80)


class MemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    value: str
    category: str | None
    created_at: datetime | None
    updated_at: datetime | None


class MemorySearchResponse(BaseModel):
    items: list[MemoryResponse]
    query: str
