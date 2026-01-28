from __future__ import annotations

import hashlib
import hmac
import os
import time
from urllib.parse import quote

from fastapi import HTTPException, Request


def is_localhost(host: str) -> bool:
    return host in {"127.0.0.1", "::1", "testclient"}


def require_localhost(request: Request) -> None:
    host = request.client.host if request.client else ""
    if not is_localhost(host):
        raise HTTPException(status_code=403, detail="仅允许本机访问管理后台")


ADMIN_SESSION_COOKIE = "admin_session"
ADMIN_SESSION_VERSION = "v1"
ADMIN_SESSION_MAX_AGE_SECONDS = int(os.getenv("MBTI_ADMIN_SESSION_MAX_AGE_SECONDS", str(60 * 60 * 24 * 14)))


def _app_secret() -> str:
    return os.getenv("MBTI_APP_SECRET", "dev-secret-change-me")


def get_admin_credentials() -> tuple[str | None, str | None]:
    return os.getenv("MBTI_ADMIN_USERNAME"), os.getenv("MBTI_ADMIN_PASSWORD")


def is_admin_configured() -> bool:
    username, password = get_admin_credentials()
    return bool(username) and bool(password)


def _sign_admin_payload(payload: str, *, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256)
    return digest.hexdigest()


def make_admin_session(username: str, *, secret: str | None = None, issued_at: int | None = None) -> str:
    secret = secret or _app_secret()
    issued_at = int(time.time()) if issued_at is None else int(issued_at)
    payload = f"{ADMIN_SESSION_VERSION}:{username}:{issued_at}"
    sig = _sign_admin_payload(payload, secret=secret)
    return f"{payload}:{sig}"


def _is_valid_admin_session(value: str, *, secret: str, username: str, now: int | None = None) -> bool:
    if not value:
        return False
    parts = value.split(":", 3)
    if len(parts) != 4:
        return False
    version, cookie_username, issued_at_str, sig = parts
    if version != ADMIN_SESSION_VERSION:
        return False
    if cookie_username != username:
        return False
    try:
        issued_at = int(issued_at_str)
    except ValueError:
        return False

    now = int(time.time()) if now is None else int(now)
    if now - issued_at > ADMIN_SESSION_MAX_AGE_SECONDS:
        return False

    payload = f"{version}:{cookie_username}:{issued_at}"
    expected = _sign_admin_payload(payload, secret=secret)
    return hmac.compare_digest(sig, expected)


def is_admin_authenticated(request: Request) -> bool:
    username, password = get_admin_credentials()
    if not username or not password:
        return False

    cookie = request.cookies.get(ADMIN_SESSION_COOKIE)
    return bool(cookie) and _is_valid_admin_session(cookie, secret=_app_secret(), username=username)


def require_admin(request: Request) -> None:
    username, password = get_admin_credentials()
    if not username or not password:
        require_localhost(request)
        return

    cookie = request.cookies.get(ADMIN_SESSION_COOKIE)
    if cookie and _is_valid_admin_session(cookie, secret=_app_secret(), username=username):
        return

    next_url = request.url.path
    if request.url.query:
        next_url += f"?{request.url.query}"
    location = f"/admin/login?next={quote(next_url)}"
    raise HTTPException(status_code=303, headers={"Location": location})
