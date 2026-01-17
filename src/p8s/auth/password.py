"""
P8s Password Reset - Django-style password reset flow.

Provides complete password reset via email:
- Secure token generation
- Email sending
- Token validation
- Password update

Example:
    ```python
    from p8s.auth.password import PasswordResetService

    service = PasswordResetService(
        secret_key="your-secret",
        email_sender=send_email,
    )

    # Request reset
    token = await service.create_reset_token(user)
    await service.send_reset_email(user, token)

    # Confirm reset
    await service.reset_password(token, new_password)
    ```
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Coroutine
from base64 import urlsafe_b64encode, urlsafe_b64decode

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# Token settings
TOKEN_EXPIRY_HOURS = 24
TOKEN_BYTES = 32


def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(token: str, secret_key: str) -> str:
    """
    Hash a token with HMAC for storage.

    Args:
        token: Plain token
        secret_key: Application secret

    Returns:
        Hashed token
    """
    return hmac.new(
        secret_key.encode(),
        token.encode(),
        hashlib.sha256
    ).hexdigest()


def create_timestamped_token(user_id: str, secret_key: str) -> str:
    """
    Create a timestamped token for password reset.

    Args:
        user_id: User identifier
        secret_key: Application secret

    Returns:
        Token string containing timestamp and signature
    """
    timestamp = int(datetime.now(timezone.utc).timestamp())
    token = generate_token()

    # Create signature
    data = f"{user_id}:{timestamp}:{token}"
    signature = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:16]

    # Encode token
    token_data = f"{user_id}:{timestamp}:{token}:{signature}"
    return urlsafe_b64encode(token_data.encode()).decode()


def verify_timestamped_token(
    encoded_token: str,
    secret_key: str,
    max_age_hours: int = TOKEN_EXPIRY_HOURS,
) -> tuple[str | None, str | None]:
    """
    Verify a timestamped token.

    Args:
        encoded_token: Base64 encoded token
        secret_key: Application secret
        max_age_hours: Maximum token age

    Returns:
        Tuple of (user_id, token) or (None, None) if invalid
    """
    try:
        token_data = urlsafe_b64decode(encoded_token.encode()).decode()
        parts = token_data.split(":")

        if len(parts) != 4:
            return None, None

        user_id, timestamp_str, token, signature = parts
        timestamp = int(timestamp_str)

        # Check expiry
        created = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        if datetime.now(timezone.utc) - created > timedelta(hours=max_age_hours):
            return None, None

        # Verify signature
        data = f"{user_id}:{timestamp}:{token}"
        expected_sig = hmac.new(
            secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()[:16]

        if not hmac.compare_digest(signature, expected_sig):
            return None, None

        return user_id, token

    except (ValueError, UnicodeDecodeError):
        return None, None


class PasswordResetService:
    """
    Service for handling password reset flow.

    Example:
        ```python
        service = PasswordResetService(
            secret_key=settings.secret_key,
            email_sender=email_service.send,
            user_model=User,
        )

        # In password reset request endpoint
        token = await service.create_reset_token(user)
        reset_url = f"https://example.com/reset?token={token}"
        await service.send_reset_email(user.email, reset_url)

        # In password reset confirm endpoint
        success = await service.reset_password(
            token=token,
            new_password=new_password,
            session=session,
        )
        ```
    """

    def __init__(
        self,
        secret_key: str,
        user_model: type | None = None,
        email_sender: Callable[..., Coroutine[Any, Any, None]] | None = None,
        token_expiry_hours: int = TOKEN_EXPIRY_HOURS,
    ):
        """
        Initialize password reset service.

        Args:
            secret_key: Application secret key
            user_model: User model class
            email_sender: Async function to send emails
            token_expiry_hours: Token validity period
        """
        self.secret_key = secret_key
        self.user_model = user_model
        self.email_sender = email_sender
        self.token_expiry_hours = token_expiry_hours

    def create_reset_token(self, user_id: str) -> str:
        """
        Create a password reset token for a user.

        Args:
            user_id: User identifier (typically UUID or ID)

        Returns:
            Encoded reset token
        """
        return create_timestamped_token(str(user_id), self.secret_key)

    def verify_reset_token(self, token: str) -> str | None:
        """
        Verify a password reset token.

        Args:
            token: Encoded reset token

        Returns:
            User ID if valid, None otherwise
        """
        user_id, _ = verify_timestamped_token(
            token,
            self.secret_key,
            self.token_expiry_hours,
        )
        return user_id

    async def send_reset_email(
        self,
        email: str,
        reset_url: str,
        subject: str = "Password Reset Request",
    ) -> bool:
        """
        Send password reset email.

        Args:
            email: User's email address
            reset_url: Full URL with token
            subject: Email subject

        Returns:
            True if sent successfully
        """
        if not self.email_sender:
            raise ValueError("Email sender not configured")

        body = f"""
You have requested a password reset.

Click the link below to reset your password:
{reset_url}

This link will expire in {self.token_expiry_hours} hours.

If you did not request this reset, please ignore this email.
"""
        try:
            await self.email_sender(
                to=email,
                subject=subject,
                body=body,
            )
            return True
        except Exception:
            return False

    async def reset_password(
        self,
        token: str,
        new_password: str,
        session: AsyncSession,
        password_hasher: Callable[[str], str] | None = None,
    ) -> bool:
        """
        Reset user's password using token.

        Args:
            token: Reset token
            new_password: New password
            session: Database session
            password_hasher: Function to hash password

        Returns:
            True if password was reset
        """
        if not self.user_model:
            raise ValueError("User model not configured")

        user_id = self.verify_reset_token(token)
        if not user_id:
            return False

        # Find user
        query = select(self.user_model).where(
            self.user_model.id == user_id
        )
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        # Hash password
        if password_hasher:
            hashed = password_hasher(new_password)
        else:
            # Simple hash (should use proper hasher like bcrypt)
            hashed = hashlib.sha256(new_password.encode()).hexdigest()

        user.password = hashed
        session.add(user)
        await session.flush()

        return True


__all__ = [
    "PasswordResetService",
    "generate_token",
    "hash_token",
    "create_timestamped_token",
    "verify_timestamped_token",
]
