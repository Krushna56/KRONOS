import os
from datetime import timedelta

import pytest

os.environ.setdefault("APP_NAME", "KRONOS_TEST")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("JWT_SECRET", "test-only-secret-value-with-at-least-32-characters")

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token


def test_access_token_round_trip(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "x" * 48)
    token = create_access_token("test-user")
    assert decode_access_token(token) == "test-user"


def test_expired_access_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "x" * 48)
    token = create_access_token("test-user", expires_delta=timedelta(seconds=-1))
    assert decode_access_token(token) is None


def test_short_jwt_secret_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET", "too-short")
    with pytest.raises(RuntimeError, match="at least 32 characters"):
        create_access_token("test-user")
