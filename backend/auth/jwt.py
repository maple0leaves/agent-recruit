"""JWT token creation and verification using PyJWT (not python-jose)."""
from datetime import datetime, timedelta, timezone
import jwt
from config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS


def create_access_token(user_id: str, role: str) -> str:
    """Create a short-lived JWT access token with user id and role."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, role: str) -> str:
    """Create a long-lived JWT refresh token stored in HttpOnly cookie."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Returns the payload dict.

    Raises jwt.PyJWTError on invalid/expired tokens.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
