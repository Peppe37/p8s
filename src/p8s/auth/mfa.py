"""
P8s MFA/2FA - Two-Factor Authentication support.

Provides TOTP-based two-factor authentication:
- TOTP device management
- QR code generation
- Backup codes

Example:
    ```python
    from p8s.auth.mfa import TOTPDevice

    # Setup 2FA for user
    device = TOTPDevice.create(user_id="user123", name="My Phone")
    qr_code_uri = device.get_provisioning_uri("user@example.com", "MyApp")

    # Verify OTP
    is_valid = device.verify(otp_code="123456")
    ```
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import Optional


def generate_secret(length: int = 32) -> str:
    """
    Generate a random base32-encoded secret.

    Args:
        length: Number of bytes of randomness

    Returns:
        Base32 encoded secret
    """
    random_bytes = secrets.token_bytes(length)
    return base64.b32encode(random_bytes).decode("utf-8").rstrip("=")


def get_hotp_token(secret: str, counter: int) -> str:
    """
    Generate HOTP token.

    Args:
        secret: Base32 encoded secret
        counter: Counter value

    Returns:
        6-digit OTP
    """
    # Decode secret
    key = base64.b32decode(secret.upper() + "=" * ((8 - len(secret) % 8) % 8))

    # Pack counter as big-endian 8-byte
    counter_bytes = struct.pack(">Q", counter)

    # HMAC-SHA1
    hmac_digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()

    # Dynamic truncation
    offset = hmac_digest[-1] & 0x0F
    binary = struct.unpack(">I", hmac_digest[offset:offset + 4])[0] & 0x7FFFFFFF

    # 6 digits
    return str(binary % 1000000).zfill(6)


def get_totp_token(secret: str, time_step: int = 30) -> str:
    """
    Generate TOTP token for current time.

    Args:
        secret: Base32 encoded secret
        time_step: Time step in seconds (default 30)

    Returns:
        6-digit OTP
    """
    counter = int(time.time()) // time_step
    return get_hotp_token(secret, counter)


def verify_totp(secret: str, token: str, time_step: int = 30, window: int = 1) -> bool:
    """
    Verify a TOTP token.

    Args:
        secret: Base32 encoded secret
        token: OTP to verify
        time_step: Time step in seconds
        window: Number of steps to check before/after

    Returns:
        True if token is valid
    """
    counter = int(time.time()) // time_step

    for offset in range(-window, window + 1):
        expected = get_hotp_token(secret, counter + offset)
        if hmac.compare_digest(token, expected):
            return True

    return False


def generate_backup_codes(count: int = 10, length: int = 8) -> list[str]:
    """
    Generate backup codes.

    Args:
        count: Number of codes to generate
        length: Length of each code

    Returns:
        List of backup codes
    """
    codes = []
    for _ in range(count):
        code = "".join(secrets.choice("0123456789") for _ in range(length))
        codes.append(code)
    return codes


class TOTPDevice:
    """
    TOTP device for two-factor authentication.

    Example:
        ```python
        device = TOTPDevice.create("user123")
        uri = device.get_provisioning_uri("user@example.com", "MyApp")
        # Show QR code for `uri`

        # Later, verify
        if device.verify("123456"):
            print("Valid OTP!")
        ```
    """

    def __init__(
        self,
        user_id: str,
        secret: str,
        name: str = "default",
        confirmed: bool = False,
    ):
        """
        Initialize TOTP device.

        Args:
            user_id: User identifier
            secret: Base32 encoded secret
            name: Device name
            confirmed: Whether device has been confirmed
        """
        self.user_id = user_id
        self.secret = secret
        self.name = name
        self.confirmed = confirmed

    @classmethod
    def create(cls, user_id: str, name: str = "default") -> "TOTPDevice":
        """
        Create a new TOTP device.

        Args:
            user_id: User identifier
            name: Device name

        Returns:
            New TOTPDevice instance
        """
        secret = generate_secret()
        return cls(user_id=user_id, secret=secret, name=name)

    def get_token(self) -> str:
        """Get current TOTP token (mainly for testing)."""
        return get_totp_token(self.secret)

    def verify(self, token: str, window: int = 1) -> bool:
        """
        Verify an OTP token.

        Args:
            token: 6-digit OTP
            window: Time window for validation

        Returns:
            True if valid
        """
        return verify_totp(self.secret, token, window=window)

    def get_provisioning_uri(
        self,
        account_name: str,
        issuer: str = "P8s",
    ) -> str:
        """
        Get provisioning URI for QR code.

        Args:
            account_name: User's account name/email
            issuer: Service name

        Returns:
            otpauth:// URI
        """
        from urllib.parse import quote

        return (
            f"otpauth://totp/{quote(issuer)}:{quote(account_name)}"
            f"?secret={self.secret}"
            f"&issuer={quote(issuer)}"
            f"&algorithm=SHA1"
            f"&digits=6"
            f"&period=30"
        )

    def confirm(self, token: str) -> bool:
        """
        Confirm device with initial OTP.

        Args:
            token: OTP from authenticator app

        Returns:
            True if confirmed successfully
        """
        if self.verify(token):
            self.confirmed = True
            return True
        return False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "secret": self.secret,
            "name": self.name,
            "confirmed": self.confirmed,
        }


__all__ = [
    "TOTPDevice",
    "generate_secret",
    "get_totp_token",
    "verify_totp",
    "generate_backup_codes",
]
