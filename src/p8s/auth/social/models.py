"""
P8s Social Account Models - Database models for social login.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from p8s.db import Model

if TYPE_CHECKING:
    from p8s.auth.models import User


class SocialAccount(Model, table=True):
    """
    Links a user to their social login provider accounts.

    Example:
        ```python
        # User logged in via Google
        account = SocialAccount(
            user_id=user.id,
            provider="google",
            provider_user_id="123456789",
            extra_data={"email": "user@gmail.com"},
        )
        ```
    """

    __tablename__ = "social_accounts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    provider: str = Field(index=True)  # "google", "github", "microsoft"
    provider_user_id: str = Field(index=True)  # ID from provider
    extra_data: dict[str, Any] = Field(default={}, sa_column=Column(JSON))

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_login: datetime | None = Field(default=None)

    # Note: Relationship to User removed to avoid circular dependency.
    # Use user_id directly with session.get(User, social_account.user_id)

    @classmethod
    async def get_or_create(
        cls,
        session,
        provider: str,
        provider_user_id: str,
        user_id: UUID,
        extra_data: dict | None = None,
    ) -> tuple["SocialAccount", bool]:
        """
        Get existing social account or create new one.

        Returns:
            Tuple of (account, created)
        """
        from sqlalchemy import select

        # Try to find existing
        result = await session.execute(
            select(cls).where(
                cls.provider == provider,
                cls.provider_user_id == provider_user_id,
            )
        )
        account = result.scalar_one_or_none()

        if account:
            # Update last login
            account.last_login = datetime.now(timezone.utc)
            if extra_data:
                account.extra_data = extra_data
            session.add(account)
            return account, False

        # Create new
        account = cls(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            extra_data=extra_data or {},
            last_login=datetime.now(timezone.utc),
        )
        session.add(account)
        await session.flush()
        return account, True
