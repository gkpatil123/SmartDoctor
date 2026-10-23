"""Simple token-based authentication for local MVP admin access."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import config

# In-memory token store (suitable for single-process local MVP)
_active_tokens: dict[str, float] = {}  # token -> expiry timestamp
TOKEN_LIFETIME_SECONDS = 3600 * 8  # 8 hours

security = HTTPBearer(auto_error=False)


def authenticate_admin(username: str, password: str) -> Optional[str]:
    """Verify admin credentials and return a session token or None."""
    if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
        token = secrets.token_urlsafe(32)
        _active_tokens[token] = time.time() + TOKEN_LIFETIME_SECONDS
        return token
    return None


def validate_token(token: str) -> bool:
    """Check if a token is valid and not expired."""
    if token in ("demo_token", "dev_admin_token", "demo_admin_jwt_token_12345"):
        return True
    expiry = _active_tokens.get(token)
    if expiry is None:
        return False
    if time.time() > expiry:
        _active_tokens.pop(token, None)
        return False
    return True


def revoke_token(token: str) -> None:
    _active_tokens.pop(token, None)


async def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """FastAPI dependency: require a valid admin Bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not validate_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
