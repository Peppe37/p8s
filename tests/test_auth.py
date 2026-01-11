"""
Tests for P8s auth module.
"""

import pytest
from uuid import UUID
from datetime import datetime, timedelta

from p8s.auth.security import create_access_token, verify_password, get_password_hash
from p8s.auth.models import User, UserRole


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_same_password(self):
        """Test that same password generates different hashes."""
        password = "mysecretpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Hashes should be different due to unique salt
        assert hash1 != hash2
        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "test-user-123"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long

    def test_access_token_is_jwt_format(self):
        """Test that token is in JWT format (3 parts separated by dots)."""
        data = {"sub": "test-user-123"}
        token = create_access_token(data)

        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature


class TestUserModel:
    """Test User model."""

    def test_user_creation(self):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashedpwd",
        )

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True  # default
        assert user.role == UserRole.USER  # default

    def test_user_has_uuid_id(self):
        """Test that user has UUID primary key."""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashedpwd",
        )

        assert user.id is not None
        assert isinstance(user.id, UUID)

    def test_user_is_active_default(self):
        """Test user is_active defaults to True."""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashedpwd",
        )

        assert user.is_active is True

    def test_user_role_default(self):
        """Test user role defaults to USER."""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashedpwd",
        )

        assert user.role == UserRole.USER

    def test_superuser_creation(self):
        """Test creating a superuser."""
        user = User(
            email="admin@example.com",
            username="admin",
            password_hash="hashedpwd",
            role=UserRole.SUPERUSER,
        )

        assert user.role == UserRole.SUPERUSER
        assert user.is_admin is True

    def test_user_is_admin_property(self):
        """Test is_admin property."""
        user = User(
            email="admin@example.com",
            username="admin",
            password_hash="hashedpwd",
            role=UserRole.ADMIN,
        )

        assert user.is_admin is True

        regular_user = User(
            email="user@example.com",
            username="user",
            password_hash="hashedpwd",
            role=UserRole.USER,
        )

        assert regular_user.is_admin is False

    def test_user_full_name_property(self):
        """Test full_name property."""
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashedpwd",
            first_name="John",
            last_name="Doe",
        )

        assert user.full_name == "John Doe"

    def test_superuser_has_all_permissions(self):
        """Test that superuser has all permissions."""
        user = User(
            email="admin@example.com",
            username="admin",
            password_hash="hashedpwd",
            role=UserRole.SUPERUSER,
        )

        assert user.has_perm("any.permission") is True
        assert user.has_perm("admin.anything") is True
