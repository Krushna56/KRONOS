from __future__ import annotations
from sqlalchemy import (
    Column, 
    Integer,
    Text,
    Float
)

from app.core.database import Base

class Relationship(Base):

    __tablename__ = "relationship"

    id = Column(
        Integer,
        primary_key = True
    )

    person_id = Column(Text)

    trust_score = Column(Float)

    familarity_score = Column(Float)

    emotional_score = Column(Float)

    relationship_type = Column(Text)