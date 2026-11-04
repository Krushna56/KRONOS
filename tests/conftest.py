"""Test defaults so `import app...` works without a real .env."""
import os

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-0123456789abcdef")
os.environ.setdefault("ROBOT_API_KEY", "test-robot-key")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-twilio-token")
