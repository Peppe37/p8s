"""
P8s Email - Django-style email sending.

Provides:
- send_mail() function
- EmailMessage class
- Template-based emails
- Multiple backend support (SMTP, Console, File)
"""

from p8s.email.backends import (
    ConsoleBackend,
    EmailBackend,
    FileBackend,
    SMTPBackend,
)
from p8s.email.message import EmailMessage, EmailMultiAlternatives
from p8s.email.utils import send_mail, send_mass_mail

__all__ = [
    # Backends
    "EmailBackend",
    "SMTPBackend",
    "ConsoleBackend",
    "FileBackend",
    # Message classes
    "EmailMessage",
    "EmailMultiAlternatives",
    # Functions
    "send_mail",
    "send_mass_mail",
]
