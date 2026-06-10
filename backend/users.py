"""User lookup backed by the `USERS_JSON` env var.

The list is loaded once on first access and cached in process memory. Each
entry is `{"name": str, "password_hash": str}`. A demo password hash is
read from `DEMO_PASSWORD_HASH` separately and does not require a username.
"""

from __future__ import annotations

import json
import logging

from config import settings
from auth import verify_password

logger = logging.getLogger(__name__)

_users_cache: dict[str, str] | None = None


def _load_users() -> dict[str, str]:
    raw = settings.users_json.strip()
    if not raw:
        logger.warning("USERS_JSON is empty; no personal users will be accepted")
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("USERS_JSON is not valid JSON: %s", exc)
        return {}

    users: dict[str, str] = {}
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        password_hash = entry.get("password_hash")
        if isinstance(name, str) and isinstance(password_hash, str):
            users[name.strip()] = password_hash
    return users


def _users() -> dict[str, str]:
    global _users_cache
    if _users_cache is None:
        _users_cache = _load_users()
    return _users_cache


def verify_user(name: str, password: str) -> bool:
    if not name:
        return False
    password_hash = _users().get(name.strip())
    if not password_hash:
        return False
    return verify_password(password, password_hash)


def verify_demo_password(password: str) -> bool:
    expected = (settings.demo_password_hash or "").strip()
    if not expected:
        return False
    return verify_password(password, expected)
