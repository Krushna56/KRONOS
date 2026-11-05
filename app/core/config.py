from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env."""

    APP_NAME: str = "KRONOS"
    APP_ENV: str = "development"

    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Comma-separated browser origins. Never combine wildcard origins with credentials.
    CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    )

    # Platform Agent Credentials (optional)
    DISCORD_BOT_TOKEN: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    GMAIL_TOKEN_JSON: str = ""
    GMAIL_CREDENTIALS_JSON: str = ""
    LINKEDIN_ACCESS_TOKEN: str = ""

    # Google Calendar
    GOOGLE_CALENDAR_CREDENTIALS_JSON: str = "Credintials.json"
    GOOGLE_CALENDAR_TOKEN_JSON: str = "calendar_token.json"

    # Telephony (Twilio)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # AI API Keys
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        """Reject weak or un-replaced example secrets during application startup."""
        normalized = value.strip().lower()
        if len(value) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters.")
        if normalized.startswith(("replace-with-", "change-me", "changeme")):
            raise ValueError("JWT_SECRET is still a placeholder; generate a unique secret.")
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Backwards-compatible module-level aliases. New code should use settings.*.
DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL
