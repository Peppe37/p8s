"""
Tests for P8s Password Reset.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestGenerateToken:
    """Test token generation."""

    def test_generate_token(self):
        """Test token generation."""
        from p8s.auth.password import generate_token

        token = generate_token()
        assert len(token) > 20
        assert isinstance(token, str)


class TestHashToken:
    """Test token hashing."""

    def test_hash_token(self):
        """Test token hashing."""
        from p8s.auth.password import hash_token

        hashed = hash_token("test_token", "secret")
        assert len(hashed) == 64  # SHA256 hex
        assert hashed != "test_token"

    def test_hash_deterministic(self):
        """Test hashing is deterministic."""
        from p8s.auth.password import hash_token

        hash1 = hash_token("token", "secret")
        hash2 = hash_token("token", "secret")
        assert hash1 == hash2


class TestTimestampedToken:
    """Test timestamped token creation/verification."""

    def test_create_timestamped_token(self):
        """Test creating timestamped token."""
        from p8s.auth.password import create_timestamped_token

        token = create_timestamped_token("user123", "secret")
        assert isinstance(token, str)
        assert len(token) > 50  # Base64 encoded

    def test_verify_valid_token(self):
        """Test verifying valid token."""
        from p8s.auth.password import create_timestamped_token, verify_timestamped_token

        token = create_timestamped_token("user123", "secret")
        user_id, _ = verify_timestamped_token(token, "secret")

        assert user_id == "user123"

    def test_verify_invalid_token(self):
        """Test verifying invalid token."""
        from p8s.auth.password import verify_timestamped_token

        user_id, _ = verify_timestamped_token("invalid", "secret")
        assert user_id is None

    def test_verify_wrong_secret(self):
        """Test token fails with wrong secret."""
        from p8s.auth.password import create_timestamped_token, verify_timestamped_token

        token = create_timestamped_token("user123", "secret1")
        user_id, _ = verify_timestamped_token(token, "secret2")

        assert user_id is None


class TestPasswordResetService:
    """Test PasswordResetService."""

    def test_service_import(self):
        """Test service can be imported."""
        from p8s.auth.password import PasswordResetService

        assert PasswordResetService is not None

    def test_service_init(self):
        """Test service initialization."""
        from p8s.auth.password import PasswordResetService

        service = PasswordResetService(
            secret_key="test_secret",
            token_expiry_hours=48,
        )

        assert service.secret_key == "test_secret"
        assert service.token_expiry_hours == 48

    def test_create_reset_token(self):
        """Test creating reset token."""
        from p8s.auth.password import PasswordResetService

        service = PasswordResetService(secret_key="secret")
        token = service.create_reset_token("user123")

        assert isinstance(token, str)

    def test_verify_reset_token(self):
        """Test verifying reset token."""
        from p8s.auth.password import PasswordResetService

        service = PasswordResetService(secret_key="secret")
        token = service.create_reset_token("user123")
        user_id = service.verify_reset_token(token)

        assert user_id == "user123"

    def test_verify_invalid_token(self):
        """Test invalid token returns None."""
        from p8s.auth.password import PasswordResetService

        service = PasswordResetService(secret_key="secret")
        user_id = service.verify_reset_token("invalid")

        assert user_id is None

    @pytest.mark.asyncio
    async def test_send_reset_email(self):
        """Test sending reset email."""
        from p8s.auth.password import PasswordResetService

        mock_sender = AsyncMock()
        service = PasswordResetService(
            secret_key="secret",
            email_sender=mock_sender,
        )

        result = await service.send_reset_email(
            email="test@example.com",
            reset_url="https://example.com/reset?token=abc",
        )

        assert result is True
        mock_sender.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_without_sender_raises(self):
        """Test error when email sender not configured."""
        from p8s.auth.password import PasswordResetService

        service = PasswordResetService(secret_key="secret")

        with pytest.raises(ValueError, match="not configured"):
            await service.send_reset_email("test@example.com", "url")


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.auth.password import __all__

        assert "PasswordResetService" in __all__
        assert "generate_token" in __all__
        assert "create_timestamped_token" in __all__
