from __future__ import annotations

import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# Add project root to sys.path so absolute imports like 'app.core' work
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logger import logger
from app.api.routes import health, auth, chat, jobs
from app.api.websocket import ws_routes
from app.websocket.manager import manager as ws_manager
from app.api.routes.message_routes import router as message_router
from app.api.routes.social_routes import router as social_router
from app.api.routes.draft_routes import router as draft_router
from app.tasks.runtime import ai_runtime
from app.agents.manager import agent_manager
from app.agents.platforms.discord.agent import DiscordAgent
from app.agents.platforms.telegram.agent import TelegramAgent
from app.agents.platforms.gmail.agent import GmailAgent
from app.agents.platforms.linkedin.agent import LinkedInAgent
from app.voice.audio.audio_manager import AudioManager
from app.voice.audio.config import AudioConfig
from app.voice.audio.recorder import Recorder
from app.voice.vad.speech_detector import SpeechDetector
from app.voice.bus.subscriber import CounterSubscriber, PrintSubscriber


# Initialize Audio Manager gracefully
audio = AudioManager()
try:
    printer = PrintSubscriber()
    audio.subscribe("printer", printer)
    audio.subscribe("counter", CounterSubscriber())
except Exception as e:
    logger.warning(f"Voice subscriber registration notice: {e}")

# Register Social Platform Agents
agent_manager.add(DiscordAgent("discord"))
agent_manager.add(TelegramAgent("telegram"))
agent_manager.add(GmailAgent("gmail"))
agent_manager.add(LinkedInAgent("linkedin"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Try starting audio if hardware is present
    try:
        audio.start()
        logger.info("Voice audio manager initialized")
    except Exception as exc:
        logger.warning(f"Audio device not available at startup (running in headless mode): {exc}")

    # Launch background AI runtime heartbeat
    runtime_task = asyncio.create_task(ai_runtime())

    try:
        yield
    finally:
        try:
            audio.stop()
        except Exception:
            pass
        runtime_task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade agentic personal AI backend (Phase 3)",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware for cross-origin frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST and WebSocket Routers
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(ws_routes.router, tags=["WebSockets"])
app.include_router(message_router)
app.include_router(social_router)
app.include_router(draft_router)


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
    return await agent_manager.health()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.send_message(
                f"AI received: {data}",
                websocket
            )
    except Exception:
        ws_manager.disconnect(websocket)


def main():
    config = AudioConfig()
    audio_manager = AudioManager()
    speech_detector = SpeechDetector()
    recorder = Recorder()

    print("\n============================")
    print("AI Clone Voice Runtime")
    print("============================\n")

    print("[system] starting microphone...")
    audio_manager.start()
    print("[system] Microphone ready, waiting for speech...\n")

    try:
        while True:
            audio_chunk = audio_manager.read()
            completed_audio = speech_detector.process_chunk(audio_chunk)
            if completed_audio is None:
                continue

            filepath = recorder.save(
                audio_chunks=completed_audio,
                sample_rate=config.sample_rate
            )
            print(f"[Recorder saved]: {filepath}\n[system] waiting for speech...")

    except KeyboardInterrupt:
        print("\n[system] shutdown requested")
    finally:
        audio_manager.stop()
        print("[system] Microphone stopped.")


if __name__ == "__main__":
    import uvicorn
    print("Starting KRONOS AI server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)