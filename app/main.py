"""
AI Clone — FastAPI Application Entry Point
Phase 3: Social Agents
"""

import sys
import io

# ── Force UTF-8 stdout and stderr on Windows (prevents UnicodeEncodeError for emoji logs) ──
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import sys
from pathlib import Path

# Ensure project root is on sys.path for absolute imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import logger

# Routers
from app.api.routes import health, auth, chat, jobs
from app.api.routes.message_routes import router as message_router
from app.api.routes.social_routes import router as social_router
from app.api.routes.draft_routes import router as draft_router
from app.auth.auth_routes import router as auth_router
from app.api.routes.telephony_routes import router as telephony_router
from app.api.routes.robot_routes import router as robot_router
from app.api.websocket import ws_routes

# WebSocket connection manager
from app.websocket.manager import manager as ws_manager

# Agent framework
from app.core.dependencies import manager as agent_manager
from app.agents.platforms.discord.agent import DiscordAgent
from app.agents.platforms.telegram.agent import TelegramAgent
from app.agents.platforms.gmail.agent import GmailAgent
from app.agents.platforms.linkedin.agent import LinkedInAgent

# Background AI runtime
from app.tasks.runtime import ai_runtime


# ─────────────────────────────────────────────
#  Register all platform agents
# ─────────────────────────────────────────────
agent_manager.add(DiscordAgent("discord"))
agent_manager.add(TelegramAgent("telegram"))
agent_manager.add(GmailAgent("gmail"))
agent_manager.add(LinkedInAgent("linkedin"))


# ─────────────────────────────────────────────
#  Lifespan: startup & shutdown
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 AI Clone starting up — connecting social agents...")

    # Start background AI runtime
    asyncio.create_task(ai_runtime())

    # Connect all registered agents
    await agent_manager.connect_all()

    logger.info("✅ All agents connected. Server ready.")
    yield

    # Graceful shutdown
    logger.info("🛑 AI Clone shutting down — disconnecting agents...")
    await agent_manager.disconnect_all()
    logger.info("✅ All agents disconnected. Goodbye.")


# ─────────────────────────────────────────────
#  FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade agentic personal AI backend — Phase 3 (Social Agents)",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  Routers
# ─────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(health.router,   prefix="/api/health", tags=["Health"])
app.include_router(auth.router,     prefix="/api/auth",   tags=["Auth"])
app.include_router(chat.router,     tags=["Chat"])  # prefix already set in chat.py
app.include_router(jobs.router,     prefix="/api/jobs",   tags=["Jobs"])
app.include_router(ws_routes.router, tags=["WebSockets"])
app.include_router(message_router)
app.include_router(social_router)
app.include_router(draft_router)
app.include_router(telephony_router)
app.include_router(robot_router)


# ─────────────────────────────────────────────
from fastapi.responses import FileResponse, HTMLResponse

@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
@app.get("/", response_class=HTMLResponse, tags=["Dashboard"])
async def dashboard_view():
    """Interactive Mission Control Dashboard for AI Clone, Mini Robot & Telephony."""
    dashboard_path = Path(__file__).resolve().parent / "templates" / "dashboard.html"
    return FileResponse(dashboard_path)

@app.get("/api/status", tags=["Root"])
async def root_endpoint():
    """Application root metadata."""
    return {
        "application": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "3.0.0",
        "status": "online",
        "docs_url": "/docs",
        "phase": "Phase 3 — Social Agents & Voice Clone",
    }


@app.get("/agents/health", tags=["Agents"])
async def get_agents_health():
    """Retrieve health status of all registered social agents."""
    return await agent_manager.health()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Primary WebSocket endpoint for real-time communication."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.send_message(f"AI received: {data}", websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# ─────────────────────────────────────────────
#  Startup log
# ─────────────────────────────────────────────
logger.info(f"FastAPI application '{settings.APP_NAME}' initialized in '{settings.APP_ENV}' mode.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)