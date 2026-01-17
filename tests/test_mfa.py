"""
Tests for P8s 2FA/MFA.
"""

import pytest


class TestGenerateSecret:
    """Test secret generation."""

    def test_generate_secret(self):
        """Test secret generation."""
        from p8s.auth.mfa import generate_secret

        secret = generate_secret()
        assert len(secret) > 20

    def test_secrets_unique(self):
        """Test secrets are unique."""
        from p8s.auth.mfa import generate_secret

        secrets = [generate_secret() for _ in range(10)]
        assert len(set(secrets)) == 10


class TestTOTPTokens:
    """Test TOTP token generation."""

    def test_get_totp_token(self):
        """Test TOTP token generation."""
        from p8s.auth.mfa import generate_secret, get_totp_token

        secret = generate_secret()
        token = get_totp_token(secret)

        assert len(token) == 6
        assert token.isdigit()

    def test_verify_totp_valid(self):
        """Test verifying valid TOTP."""
        from p8s.auth.mfa import generate_secret, get_totp_token, verify_totp

        secret = generate_secret()
        token = get_totp_token(secret)

        assert verify_totp(secret, token) is True

    def test_verify_totp_invalid(self):
        """Test verifying invalid TOTP."""
        from p8s.auth.mfa import generate_secret, verify_totp

        secret = generate_secret()
        assert verify_totp(secret, "000000") is False


class TestBackupCodes:
    """Test backup code generation."""

    def test_generate_backup_codes(self):
        """Test backup code generation."""
        from p8s.auth.mfa import generate_backup_codes

        codes = generate_backup_codes(10, 8)

        assert len(codes) == 10
        assert all(len(c) == 8 for c in codes)
        assert all(c.isdigit() for c in codes)


class TestTOTPDevice:
    """Test TOTPDevice class."""

    def test_device_import(self):
        """Test device can be imported."""
        from p8s.auth.mfa import TOTPDevice

        assert TOTPDevice is not None

    def test_create_device(self):
        """Test creating device."""
        from p8s.auth.mfa import TOTPDevice

        device = TOTPDevice.create("user123", name="Phone")

        assert device.user_id == "user123"
        assert device.name == "Phone"
        assert device.confirmed is False

    def test_device_get_token(self):
        """Test getting token from device."""
        from p8s.auth.mfa import TOTPDevice

        device = TOTPDevice.create("user123")
        token = device.get_token()

        assert len(token) == 6

    def test_device_verify(self):
        """Test verifying token."""
        from p8s.auth.mfa import TOTPDevice

        device = TOTPDevice.create("user123")
        token = device.get_token()

        assert device.verify(token) is True

    def test_device_provisioning_uri(self):
        """Test provisioning URI."""
        from p8s.auth.mfa import TOTPDevice

        device = TOTPDevice.create("user123")
        uri = device.get_provisioning_uri("user@example.com", "MyApp")

        assert uri.startswith("otpauth://totp/")
        assert "secret=" in uri
        assert "issuer=MyApp" in uri

    def test_device_confirm(self):
        """Test confirming device."""
        from p8s.auth.mfa import TOTPDevice

        device = TOTPDevice.create("user123")
        token = device.get_token()

        assert device.confirm(token) is True
        assert device.confirmed is True

    def test_device_to_dict(self):
        """Test converting to dict."""
        from p8s.auth.mfa import TOTPDevice

        device = TOTPDevice.create("user123", name="Phone")
        data = device.to_dict()

        assert data["user_id"] == "user123"
        assert data["name"] == "Phone"


class TestExports:
    """Test module exports."""

    def test_all_exports(self):
        """Test __all__ exports."""
        from p8s.auth.mfa import __all__

        assert "TOTPDevice" in __all__
        assert "generate_secret" in __all__
        assert "verify_totp" in __all__
