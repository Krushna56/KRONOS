from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

from app.core.database import SessionLocal
from app.models.message_models import Message

from app.ingestion.embedder import generate_embedding
from app.emotion.detector import detect_emotion

router = APIRouter()

class IncomingMessage(BaseModel):

    sender_id: str

    platform: str

    message: str

@router.post("/ingest")
async def ingest_message(data: IncomingMessage):

    db = SessionLocal()

    embedding = generate_embedding(
        data.message
    )    

    emotion = detect_emotion(
        data.message
    )

    new_message = Message(
        sender_id=data.sender_id,
        platform=data.platform,
        message=data.message,
        embedding=embedding,
        emotion=emotion,
        sentiment=emotion,
        created_at = datetime.utcnow()
    )

    db.add(new_message)
    db.commit()
    db.close()

    return{
        "status": "stored",
        "emotion": emotion
    }