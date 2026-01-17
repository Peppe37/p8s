"""
P8s Auth Security - Password hashing and JWT tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from p8s.core.settings import get_settings


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password.

    Returns:
        Hashed password.
    """
    # BCrypt has a 72-byte limit for passwords
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password.
        hashed_password: Hashed password.

    Returns:
        True if password matches.
    """
    # Truncate to match hashing behavior
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token.
        expires_delta: Custom expiration time.

    Returns:
        Encoded JWT token.
    """
    settings = get_settings()

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.auth.access_token_expire_minutes
        )

    to_encode.update(
        {
            "exp": expire,
            "type": "access",
        }
    )

    return jwt.encode(
        to_encode,
        settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
    )


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token.
        expires_delta: Custom expiration time.

    Returns:
        Encoded JWT token.
    """
    settings = get_settings()

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.auth.refresh_token_expire_days
        )

    to_encode.update(
        {
            "exp": expire,
            "type": "refresh",
        }
    )

    return jwt.encode(
        to_encode,
        settings.auth.secret_key,
        algorithm=settings.auth.algorithm,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode a JWT token.

    Args:
        token: The JWT token.

    Returns:
        Decoded payload or None if invalid.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.auth.secret_key,
            algorithms=[settings.auth.algorithm],
        )
        return payload
    except JWTError:
        return None


def create_tokens(user_id: str) -> tuple[str, str]:
    """
    Create both access and refresh tokens for a user.

    Args:
        user_id: User ID to encode.

    Returns:
        Tuple of (access_token, refresh_token).
    """
    data = {"sub": str(user_id)}

    return (
        create_access_token(data),
        create_refresh_token(data),
    )
