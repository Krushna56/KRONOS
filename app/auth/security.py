"""Compatibility wrappers for the canonical authentication helpers.

New application code should import directly from app.core.security.
"""

from app.core.security import (
    create_access_token as _create_access_token,
    decode_access_token,
    hash_password,
    pwd_context,
    verify_password,
)

# Preserve the old exported name for callers that still import it.
pws_context = pwd_context


def create_access_token(data: dict) -> str:
    """Create a token from the legacy {sub: ...} payload shape."""
    subject = data.get("sub")
    if subject is None:
        raise ValueError("JWT payload must include a subject ('sub').")
    return _create_access_token(subject)


def verify_token(token: str):
    """Return the decoded subject in the legacy payload shape, or None."""
    subject = decode_access_token(token)
    if subject is None:
        return None
    return {"sub": subject}
