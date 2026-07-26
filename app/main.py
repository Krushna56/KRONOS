from app.voice.bus.subscriber import CounterSubscriber
from dns.tsig import Key
import sys
from pathlib import Path

# Add project root to sys.path so absolute imports like 'app.core' work
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.voice import audio_manager
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger
from app.api.routes import health, auth, chat, jobs
from app.api.websocket import ws_routes
from fastapi import WebSocket
from app.websocket.manager import manager
from contextlib import asynccontextmanager
from app.tasks.runtime import ai_runtime
import asyncio

from app.api.routes.message_routes import router
from app.auth.auth_routes import router as auth_router
from app.api.routes.social_routes import router as social_router
from app.api.routes.draft_routes import router as draft_router

from app.core.dependencies import manager
from app.agents.platforms.discord.agent import DiscordAgent
from app.agents.platforms.telegram.agent import TelegramAgent
from app.agents.platforms.gmail.agent import GmailAgent
from app.agents.platforms.linkedin.agent import LinkedInAgent

from app.voice.audio_manager import AudioManager
from app.voice.config import AudioConfig
from app.voice.recorder import Recorder
from app.voice.vad.speech_detector import SpeechDetector
from voice.audio_manager import AudioManager
from voice.bus.events import PrintSubscriber



@asynccontextmanager
async def lifespan(app):
    asyncio.create_task(ai_runtime())

    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade agentic personal AI backend (Phase 1)",
    version="1.0.0",
    lifespan=lifespan
)


manager.add(DiscordAgent("discord"))
manager.add(TelegramAgent("telegram"))
manager.add(GmailAgent("gmail"))
manager.add(LinkedInAgent("linkedin"))


# CORS middleware for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST and WebSocket Routers
app.include_router(auth_router)
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(ws_routes.router, tags=["WebSockets"])
app.include_router(router)
app.include_router(social_router)
app.include_router(draft_router)


audio = AudioManager()

printer = PrintSubscriber()

audio.subscribe(printer)

audio.subscribe(PrintSubscriber())

audio.subscribe(CounterSubscriber())

audio.start()

try:
    while True:
        pass 
except KeyboardInterrupt:
    audio.stop()






@app.get("/")
async def root_endpoint():
    """Application root metadata information."""
    return {
        "application": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/agents/health")
async def get_agents_health():
    """Retrieve health status of all registered agents."""
    return await manager.health()

logger.info(f"FastAPI application '{settings.APP_NAME}' successfully initialized in '{settings.APP_ENV}' mode.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:

            data = await websocket.receive_text()
            
            await manager.send_message(
                f"AI received: {data}",
                websocket
            )
    except:
        manager.disconnect(websocket)

def main():
    
    config = AudioConfig()
    audio_manager = AudioManager()
    speech_detector = SpeechDetector()
    recorder = Recorder()

    print()
    print("============================")
    print("AI Clone Voice Runtime")
    print("============================")
    print()

    print("[system] starting microphone...")
    audio_manager.start()

    print("[system] Microphone ready")
    print("[system] waiting for speech")
    print()

    try:
        while True:

            audio_chunk = (
                audio_manager.read()
            )

            completed_audio = (
                speech_detector.process_chunk(
                    audio_chunk
                )
            )

            if completed_audio is None:
                continue

            filepath = recorder.save(
                audio_chunks = completed_audio,
                sample_rate=config.sample_rate
            )

            print(
                f"[Recorder saved]: "
                f"{filepath}"
            )

            print()
            print(
                "[system] waiting for speech..."
            )

    except KeyboardInterrupt:

        print()
        print("[system] shutdown requested")

    finally:

        audio_manager.stop()

        print("[system] Microphone stopped...")
    
    
if __name__ == "__main__":
    import uvicorn
    print("Starting server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)