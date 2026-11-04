"""Regression tests for the security fixes (auth, robot key, Twilio, config)."""
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.guards import require_robot_key, verify_twilio_request
from app.core.security import create_access_token, decode_access_token


# ── JWT: one secret, one code path ──────────────────────────────────────────
def test_token_roundtrip_uses_settings_secret():
    token = create_access_token("krushna")
    assert decode_access_token(token) == "krushna"


def test_token_signed_with_old_hardcoded_secret_is_rejected():
    from jose import jwt
    forged = jwt.encode({"sub": "admin"}, "supersecretkey", algorithm="HS256")
    assert decode_access_token(forged) is None


def test_jwt_bearer_has_no_hardcoded_secret():
    import inspect
    import app.auth.jwt_bearer as jb
    src = inspect.getsource(jb)
    assert "supersecret" not in src


def test_hardcoded_admin_login_removed():
    import importlib.util
    assert importlib.util.find_spec("app.auth.auth_routes") is None


# ── Config guard ────────────────────────────────────────────────────────────
def test_production_rejects_weak_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(APP_ENV="production", DATABASE_URL="x", JWT_SECRET="mysecretkey", _env_file=None)


def test_production_accepts_strong_secret():
    s = Settings(APP_ENV="production", DATABASE_URL="x", JWT_SECRET="a" * 48, _env_file=None)
    assert s.is_production


def test_cors_is_not_wildcard_by_default():
    s = Settings(DATABASE_URL="x", JWT_SECRET="a" * 48, _env_file=None)
    assert "*" not in s.cors_origins_list


# ── Robot key ───────────────────────────────────────────────────────────────
def _robot_app():
    app = FastAPI()

    @app.post("/action", dependencies=[Depends(require_robot_key)])
    def action():
        return {"ok": True}

    return TestClient(app)


def test_robot_endpoint_rejects_missing_and_wrong_key():
    c = _robot_app()
    assert c.post("/action").status_code == 401
    assert c.post("/action", headers={"X-Robot-Key": "nope"}).status_code == 401


def test_robot_endpoint_accepts_correct_key():
    c = _robot_app()
    assert c.post("/action", headers={"X-Robot-Key": "test-robot-key"}).status_code == 200


def test_robot_fails_closed_when_key_unset(monkeypatch):
    from app.core import guards
    monkeypatch.setattr(guards.settings, "ROBOT_API_KEY", "")
    assert _robot_app().post("/action", headers={"X-Robot-Key": ""}).status_code == 401


# ── Twilio signature ────────────────────────────────────────────────────────
def _twilio_app():
    app = FastAPI()

    @app.post("/incoming", dependencies=[Depends(verify_twilio_request)])
    def incoming():
        return {"ok": True}

    return TestClient(app)


def test_twilio_webhook_rejects_unsigned_request():
    r = _twilio_app().post("/incoming", data={"From": "+911234567890"})
    assert r.status_code == 403


def test_twilio_webhook_accepts_valid_signature():
    from twilio.request_validator import RequestValidator
    params = {"From": "+911234567890", "CallSid": "CA123"}
    url = "http://testserver/incoming"
    sig = RequestValidator("test-twilio-token").compute_signature(url, params)
    r = _twilio_app().post("/incoming", data=params, headers={"X-Twilio-Signature": sig})
    assert r.status_code == 200


# ── WebSocket manager leak fix ──────────────────────────────────────────────
def test_ws_manager_disconnect_removes_connection():
    from app.websocket.manager import ConnectionManager
    m = ConnectionManager()
    ws = object()
    m.active_connections.append(ws)
    m.disconnect(ws)
    assert ws not in m.active_connections


# ── Robot HTTP accepts an owner JWT too (dashboard) ─────────────────────────
def test_robot_endpoint_accepts_owner_jwt():
    token = create_access_token("krushna")
    r = _robot_app().post("/action", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_robot_endpoint_rejects_garbage_jwt():
    r = _robot_app().post("/action", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401


# ── Chat endpoints expose persona + live calendar -> must require auth ──────
def test_chat_ask_endpoints_require_auth():
    import sys
    from unittest.mock import MagicMock
    sys.modules.setdefault("sounddevice", MagicMock())  # no PortAudio in CI
    from app.api.routes.chat import router
    from app.auth.jwt_bearer import get_current_user

    for route in router.routes:
        if getattr(route, "path", "").endswith(("/ask", "/ask-stream")):
            deps = [d.call for d in route.dependant.dependencies]
            assert get_current_user in deps, f"{route.path} is unauthenticated"
