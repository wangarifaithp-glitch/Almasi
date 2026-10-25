import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
SESSION_TTL = timedelta(hours=8)
RESET_TTL = timedelta(minutes=30)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_session_token(user_id: int, session_version: int, secret: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "version": session_version,
            "iat": now,
            "exp": now + SESSION_TTL,
        },
        secret,
        algorithm="HS256",
    )


def read_session_claims(token: str, secret: str) -> tuple[int, int] | None:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        subject = payload.get("sub")
        version = payload.get("version")
        if not isinstance(subject, str) or not isinstance(version, int) or version < 0:
            return None
        return int(subject), version
    except (jwt.PyJWTError, ValueError):
        return None


def create_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utc_naive_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
