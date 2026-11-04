"""
Request guards for non-JWT clients: the Mini Robot hardware, WebSocket
clients, and Twilio webhooks.
"""

import hmac
from typing import Optional

from fastapi import Header, HTTPException, Query, Request, WebSocket, status

from app.core.config import settings
from app.core.logger import logger
from app.core.security import decode_access_token


# ── Robot hardware ──────────────────────────────────────────────────────────
def _robot_key_valid(provided: Optional[str]) -> bool:
    expected = settings.ROBOT_API_KEY
    if not expected or not provided:  # fail closed when unset
        return False
    return hmac.compare_digest(provided.encode(), expected.encode())


async def require_robot_key(
    x_robot_key: Optional[str] = Header(default=None),
    key: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
) -> None:
    """
    HTTP dependency for robot routes. Accepts EITHER the shared robot key
    (X-Robot-Key header or ?key=) for the hardware, OR a valid owner JWT
    (Authorization: Bearer ...) so the dashboard can drive the robot.
    """
    if _robot_key_valid(x_robot_key or key):
        return
    if authorization and authorization.lower().startswith("bearer "):
        if decode_access_token(authorization[7:].strip()):
            return
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing robot key / token")


async def authorize_robot_ws(websocket: WebSocket) -> bool:
    """Call before accept(). Closes the socket and returns False if unauthorized."""
    provided = websocket.headers.get("x-robot-key") or websocket.query_params.get("key")
    if _robot_key_valid(provided):
        return True
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return False


# ── User WebSockets (JWT via ?token=) ───────────────────────────────────────
async def authorize_user_ws(websocket: WebSocket) -> Optional[str]:
    """Returns the username if the ?token= JWT is valid, else closes and returns None."""
    token = websocket.query_params.get("token")
    username = decode_access_token(token) if token else None
    if username is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return username


# ── Twilio webhooks ─────────────────────────────────────────────────────────
def _public_url(request: Request) -> str:
    """Reconstruct the URL Twilio called (matters behind ngrok / a proxy)."""
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", request.url.netloc))
    url = f"{proto}://{host}{request.url.path}"
    if request.url.query:
        url += f"?{request.url.query}"
    return url


async def verify_twilio_request(request: Request) -> None:
    """
    FastAPI dependency: verify the X-Twilio-Signature header.

    If TWILIO_AUTH_TOKEN is unset: allowed (with a warning) in development only,
    rejected everywhere else.
    """
    token = settings.TWILIO_AUTH_TOKEN
    if not token:
        if settings.is_production:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Telephony not configured")
        logger.warning("TWILIO_AUTH_TOKEN not set — skipping webhook signature check (dev only)")
        return

    from twilio.request_validator import RequestValidator

    form = await request.form()
    signature = request.headers.get("x-twilio-signature", "")
    if not RequestValidator(token).validate(_public_url(request), dict(form), signature):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid Twilio signature")
