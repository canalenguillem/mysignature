"""Gestión de JWT (access/refresh) y dependencia de usuario actual.

- Access token: JWT firmado (HS256), TTL corto (15 min).
- Refresh token: JWT firmado, TTL 7 días, además persistido en Redis para
  poder invalidarlo en logout (`refresh:{user_id}`), según docs/DATABASE.md §3.

Referencia: docs/BACKEND_SPEC.md §app/security/jwt_handler.py · docs/ARCHITECTURE.md
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db, get_redis
from app.models.user import User
from app.utils.errors import UnauthenticatedError

_bearer = HTTPBearer(auto_error=False)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: str, expires_in: int | None = None) -> str:
    """Crea un access token JWT. `expires_in` en minutos."""
    minutes = expires_in if expires_in is not None else settings.JWT_EXPIRATION_MINUTES
    now = _now()
    payload = {
        "sub": str(subject),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: int, db: Session | None = None) -> str:
    """Crea un refresh token JWT y lo registra en Redis para poder revocarlo."""
    now = _now()
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)).timestamp()
        ),
        "jti": secrets.token_hex(16),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    redis_client = get_redis()
    redis_client.set(
        f"refresh:{user_id}",
        token,
        ex=settings.JWT_REFRESH_EXPIRATION_DAYS * 24 * 3600,
    )
    return token


def decode_token(token: str) -> dict:
    """Decodifica y valida un JWT; lanza UnauthenticatedError si es inválido."""
    try:
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise UnauthenticatedError("Invalid or expired token") from exc


def verify_refresh_token(token: str) -> int:
    """Valida un refresh token (firma + presencia en Redis) y devuelve user_id."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise UnauthenticatedError("Invalid refresh token")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthenticatedError("Invalid refresh token")

    stored = get_redis().get(f"refresh:{user_id}")
    if stored != token:
        raise UnauthenticatedError("Refresh token has been revoked")
    return int(user_id)


def revoke_refresh_token(user_id: int) -> None:
    get_redis().delete(f"refresh:{user_id}")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Dependencia FastAPI: resuelve el `User` a partir del access token."""
    if credentials is None or not credentials.credentials:
        raise UnauthenticatedError("Not authenticated")

    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise UnauthenticatedError("Invalid access token")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthenticatedError("Invalid access token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise UnauthenticatedError("User not found or inactive")
    return user
