from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta


def hash_token(token: str, *, secret: str) -> str:
    digest = hashlib.sha256()
    digest.update(secret.encode("utf-8"))
    digest.update(token.encode("utf-8"))
    return digest.hexdigest()


def new_url_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_resume_code(length: int = 8) -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


def expiry_from_choice(choice: str) -> timedelta | None:
    match choice:
        case "1d":
            return timedelta(days=1)
        case "7d":
            return timedelta(days=7)
        case "30d":
            return timedelta(days=30)
        case "permanent":
            return None
        case _:
            raise ValueError(f"Unsupported expiry choice: {choice!r}")

