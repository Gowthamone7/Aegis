"""
EKA Authentication & Authorization

JWT (HS256, 8-hour expiry) + bcrypt password hashing.
FastAPI OAuth2 dependency included.

Role constants: DEVELOPER, MANAGER, VIEWER, ADMIN
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .config import settings

log = logging.getLogger(__name__)

# ─────────────────────────── role constants ───────────────────────────────────

DEVELOPER = "developer"
MANAGER = "manager"
VIEWER = "viewer"
ADMIN = "admin"

VALID_ROLES = {DEVELOPER, MANAGER, VIEWER, ADMIN}

# Role hierarchy — higher index = more privileged
_ROLE_RANK = {VIEWER: 0, DEVELOPER: 1, MANAGER: 2, ADMIN: 3}

# ─────────────────────────── user context ────────────────────────────────────

@dataclass
class UserContext:
    username: str
    tenant: str
    role: str

    def has_role(self, *roles: str) -> bool:
        """Return True if the user's role is in the provided set."""
        return self.role in roles

    def rank(self) -> int:
        return _ROLE_RANK.get(self.role, 0)


# ─────────────────────────── password helpers ─────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt. Returns utf-8 string."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Return True if *password* matches the bcrypt *hashed* string."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─────────────────────────── JWT helpers ──────────────────────────────────────

_ALGORITHM = "HS256"
_EXPIRY_HOURS = 8


def create_token(username: str, tenant: str, role: str) -> str:
    """Create a signed JWT for the given user."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": username,
        "tenant": tenant,
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=_EXPIRY_HOURS),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[_ALGORITHM],
        options={"require": ["sub", "tenant", "role", "exp", "iat"]},
    )


# ─────────────────────────── FastAPI dependency ───────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserContext:
    """
    FastAPI dependency.  Validates the Bearer JWT and returns a UserContext.
    Raises HTTP 401 on any auth failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        log.debug("JWT decode error: %s", exc)
        raise credentials_exception

    username: str = payload.get("sub", "")
    tenant: str = payload.get("tenant", "")
    role: str = payload.get("role", VIEWER)

    if not username or not tenant:
        raise credentials_exception

    return UserContext(username=username, tenant=tenant, role=role)


def require_role(*roles: str):
    """
    FastAPI dependency factory — raises 403 if the user's role is not in *roles*.

    Usage::

        @router.get("/admin-only")
        async def handler(user: UserContext = Depends(require_role(ADMIN))):
            ...
    """
    def _check(user: UserContext = Depends(get_current_user)) -> UserContext:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not permitted. Required: {list(roles)}",
            )
        return user

    return _check
