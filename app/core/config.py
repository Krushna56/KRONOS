"""
Central application settings (loaded from environment / .env).

Never hardcode secrets here. Copy `.env.example` to `.env` and fill it in.
"""

from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings

# Values that must never be used as a real JWT secret outside development.
_WEAK_JWT_SECRETS = {
    "",
    "changeme",
    "change-me",
    "secret",
    "mysecretkey",
    "supersecretkey",
    "supersecretjwtkey_kronos_ai_assistant_2026",
}


class Settings(BaseSettings):

    APP_NAME: str = "KRONOS"
    APP_ENV: str = "development"  # development | production

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"

    # ── Auth ────────────────────────────────────────────────────────
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    # After the first (owner) account exists, keep registration closed unless true.
    ALLOW_REGISTRATION: bool = False

    # Shared secret the Mini Robot hardware sends (X-Robot-Key header or
    # ?key= query param). Empty = robot endpoints are disabled (fail closed).
    ROBOT_API_KEY: str = ""

    # Comma-separated list of allowed browser origins for CORS.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000"

    # ── Platform Agent Credentials (optional) ──────────────────────
    DISCORD_BOT_TOKEN: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    GMAIL_TOKEN_JSON: str = ""
    GMAIL_CREDENTIALS_JSON: str = ""
    LINKEDIN_ACCESS_TOKEN: str = ""

    # ── Google Calendar ─────────────────────────────────────────────
    GOOGLE_CALENDAR_CREDENTIALS_JSON: str = "credentials.json"
    GOOGLE_CALENDAR_TOKEN_JSON: str = "calendar_token.json"

    # ── Telephony (Twilio) ──────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # ── AI ──────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    # Configurable so a retired model name doesn't require a code change.
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GROQ_API_KEY: str = ""  # Optional: ultra-low-latency STT via Groq Whisper

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"prod", "production"}

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _reject_weak_secrets_in_production(self) -> "Settings":
        if self.is_production:
            if self.JWT_SECRET in _WEAK_JWT_SECRETS or len(self.JWT_SECRET) < 32:
                raise ValueError(
                    "JWT_SECRET is weak/default. Set a random value of 32+ chars "
                    "(e.g. `python -c \"import secrets; print(secrets.token_urlsafe(48))\"`)."
                )
        return self


settings = Settings()
