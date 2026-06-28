"""Session store — in-memory, 10-minute TTL.

Exports
-------
* ``create_session(cookies)`` — returns ``session_id``
* ``use_session(session_id)`` — applies cookies, returns them (or raises 401)
* ``clean_expired_sessions()`` — removes TTL-expired entries
* ``_sessions`` — raw dict (used by lifespan shutdown)
"""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import HTTPException
from worker import apply_cookies

SESSION_TTL = 600  # seconds

_sessions: dict[str, dict] = {}
"""session_id -> {"cookies": dict, "created_at": float}"""

logger = logging.getLogger(__name__)


def create_session(cookies: dict) -> str:
    session_id = uuid.uuid4().hex
    _sessions[session_id] = {"cookies": cookies.copy(), "created_at": time.time()}
    return session_id


def use_session(session_id: str | None) -> dict | None:
    """Look up session, apply its cookies to the global client.

    Returns the cookies dict (or ``None`` if no session given).
    Raises ``HTTPException(401)`` if expired or not found.
    """
    if session_id is None:
        return None

    entry = _sessions.get(session_id)
    if entry is None:
        raise HTTPException(status_code=401, detail="Session not found")

    age = time.time() - entry["created_at"]
    if age > SESSION_TTL:
        del _sessions[session_id]
        raise HTTPException(status_code=401, detail="Session expired (10 min TTL)")

    cookies = entry["cookies"]
    apply_cookies(cookies)
    return cookies


def clean_expired_sessions():
    now = time.time()
    expired = [sid for sid, e in _sessions.items() if now - e["created_at"] > SESSION_TTL]
    for sid in expired:
        del _sessions[sid]
