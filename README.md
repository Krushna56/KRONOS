# KRONOS — a personal AI assistant

KRONOS is a FastAPI backend for a personal "AI clone" / JARVIS-style assistant: it talks to
you by voice, replies on your behalf across platforms (with approval modes), keeps memory
in Postgres + pgvector, and can drive a small robot and answer phone calls.

> **Status: Phase 3 (in development).** Some pieces are working, others are scaffolding.
> See [What works today](#what-works-today) for an honest breakdown.

## Architecture

```
app/
├── main.py                 FastAPI entry point (lifespan connects the social agents)
├── api/                    REST + WebSocket routes (auth, chat, social, drafts, robot, telephony, calendar)
├── agents/                 BaseAgent / Registry / Manager + platforms: discord, telegram, gmail, linkedin
├── services/               LLM (Gemini), prompt builder, reply orchestrator, memory, calendar
├── persona/                Style profile, tone analysis, clone engine (replies in your voice)
├── voice/                  Audio bus, Silero VAD, wake word, STT (Google/Groq Whisper), TTS
├── robot/                  Mini-robot WebSocket bridge
├── tasks/                  Reply queue, social sync, scheduler, telephony call agent
├── db/ models/ repositories/   SQLAlchemy models, Alembic migrations, data access
├── auth/ core/             JWT auth, config, guards (robot key, Twilio signature), logging
└── templates/dashboard.html   Mission-control dashboard
tests/                      pytest suite
docs/archive/               Older design notes (historical; structure has since changed)
```

## Quick start

```bash
python -m venv venv
venv\Scripts\activate            # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt

cp .env.example .env              # then edit .env — set real secrets (see comments inside)
docker compose up -d              # Postgres (pgvector) + Redis
alembic upgrade head              # create tables

python -m app.main                # or: uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> (API) or <http://127.0.0.1:8000/> (dashboard).

First run: `POST /api/auth/register` creates the **owner** account. Registration then closes
automatically (set `ALLOW_REGISTRATION=true` to reopen). Log in at `POST /api/auth/login`.

## Security model

- **JWT** (signed with `JWT_SECRET`) protects all user-facing routes, and `?token=<JWT>` protects user WebSockets.
- **Robot** endpoints require `ROBOT_API_KEY` (`X-Robot-Key` header or `?key=`). Unset = disabled.
- **Twilio webhooks** are verified via `X-Twilio-Signature` using `TWILIO_AUTH_TOKEN`.
- **CORS** is limited to `CORS_ORIGINS` (no wildcard).
- In `APP_ENV=production` the app refuses to start with a weak `JWT_SECRET`.
- Auto-replies default to **SUGGEST** (drafts need your approval). `AUTO` mode sends as you; use it deliberately.

## What works today

| Area | State |
|---|---|
| Auth, DB models, migrations, health | ✅ working |
| Agent framework + health checks | ✅ working (needs platform tokens to connect) |
| Reply orchestrator (AUTO/SUGGEST/APPROVAL/MANUAL, drafts, human delay) | ✅ implemented |
| Voice: audio bus, VAD, STT | ✅ implemented · wake word + streaming TTS 🚧 in progress |
| LLM (Gemini via `GEMINI_MODEL`) | ✅ single-shot generation · tool-calling / planning 🚧 not yet |
| Memory | 🚧 pgvector retrieval exists; auto-embedding & prompt injection incomplete |
| Jobs API | 🧪 mock data only |
| Desktop control, proactive engine | ❌ planned |

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/test_security_hardening.py tests/test_auth.py tests/test_websocket.py tests/test_tasks_and_orchestrator.py
```

Some tests (`test_connection`, `test_memory`) need a running Postgres; `test_vad` / `test_voice_pipeline`
need an audio device (PortAudio).

## Roadmap

- [x] Agent abstraction, DB foundation, VAD engine
- [ ] LLM tool-calling "brain" (replace placeholder planner)
- [ ] Wake word wiring + streaming TTS + barge-in
- [ ] Memory: embed every message, retrieve into prompts
- [ ] Real Discord / Telegram / Gmail / LinkedIn integrations end-to-end
- [ ] Proactive engine (briefings, reminders), desktop/browser skills

## Author

Krushna Kumbhar — [@Krushna56](https://github.com/Krushna56)
