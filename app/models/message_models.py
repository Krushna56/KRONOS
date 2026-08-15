from __future__ import annotations
from sqlalchemy import Column, Integer, Text, TIMESTAMP
from pgvector.sqlalchemy import Vector

from app.core.database import Base

class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)

    sender_id = Column(Text)
    platform = Column(Text)
    message = Column(Text)
    embedding = Column(Vector(384))
    emotion = Column(Text)
    sentiment = Column(Text)
    created_at = Column(TIMESTAMP)
