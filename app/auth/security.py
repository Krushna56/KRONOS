from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token as core_create_access_token,
    decode_access_token
)
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

def create_access_token(data: dict | str):
    if isinstance(data, dict):
        subject = data.get("sub", "")
    else:
        subject = str(data)
    return core_create_access_token(subject=subject)

def verify_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None

            
