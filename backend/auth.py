"""Auth utilities: password hashing and JWT signing/verification.

- Passwords are hashed with bcrypt via passlib.
- JWTs are signed with HS256 and include the user name, the active mode
  (personal/demo) and an expiration timestamp. The mode is enforced by the
  dependencies `require_personal_user` / `require_demo_user` so a token issued
  for one mode cannot be used on the other mode's endpoint.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

import jwt
from fastapi import Depends, Header, HTTPException
from passlib.hash import bcrypt

from config import settings

Mode = Literal["personal", "demo"]

ACCESS_TOKEN_TTL_PERSONAL = timedelta(days=7)
ACCESS_TOKEN_TTL_DEMO = timedelta(hours=1)

JWT_ALG = "HS256"
JWT_ISSUER = "expensy"


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    if not plain or not hashed:
        return False
    try:
        return bcrypt.verify(plain, hashed)
    except ValueError:
        return False


def _ttl_for_mode(mode: Mode) -> timedelta:
    return ACCESS_TOKEN_TTL_DEMO if mode == "demo" else ACCESS_TOKEN_TTL_PERSONAL


def create_access_token(name: str | None, mode: Mode) -> tuple[str, datetime]:
    """Create a signed JWT and return (token, expires_at)."""
    now = datetime.now(timezone.utc)
    expires_at = now + _ttl_for_mode(mode)
    payload = {
        "iss": JWT_ISSUER,
        "sub": name or mode,
        "name": name,
        "mode": mode,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALG)
    return token, expires_at


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[JWT_ALG],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "mode"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Sesion expirada") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Sesion invalida") from exc


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """Read the Bearer token from `Authorization` and return the JWT payload."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sesion invalida o expirada")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Sesion invalida o expirada")
    return _decode_token(token)


def _require_mode(expected: Mode):
    def _dep(payload: dict = Depends(get_current_user)) -> dict:
        mode = payload.get("mode")
        if mode != expected:
            raise HTTPException(
                status_code=401,
                detail="Sesion no valida para este modo",
            )
        return payload

    return _dep


require_personal_user = _require_mode("personal")
require_demo_user = _require_mode("demo")
