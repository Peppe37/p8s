"""
P8s Email Utilities - Django-style email functions.

Provides:
- send_mail() for simple emails
- send_mass_mail() for bulk sending
- get_connection() for getting email backend
"""

from typing import Any

from p8s.email.backends import ConsoleBackend, EmailBackend, SMTPBackend
from p8s.email.message import EmailMessage


def get_connection(
    backend: str | None = None,
    fail_silently: bool = False,
    **kwargs: Any,
) -> EmailBackend:
    """
    Get email backend connection.

    Args:
        backend: Backend type ("smtp", "console", "file") or None for default.
        fail_silently: Suppress exceptions.
        **kwargs: Backend-specific options.

    Returns:
        EmailBackend instance.
    """
    # Try to get from settings
    if backend is None:
        try:
            from p8s.core.settings import get_settings

            settings = get_settings()
            email_settings = getattr(settings, "email", None)
            if email_settings:
                backend = getattr(email_settings, "backend", "console")
                # Merge settings into kwargs
                for key in [
                    "host",
                    "port",
                    "username",
                    "password",
                    "use_tls",
                    "use_ssl",
                ]:
                    if hasattr(email_settings, key) and key not in kwargs:
                        kwargs[key] = getattr(email_settings, key)
        except Exception:
            backend = "console"

    backend = backend or "console"

    if backend == "smtp":
        return SMTPBackend(fail_silently=fail_silently, **kwargs)
    elif backend == "console":
        return ConsoleBackend(fail_silently=fail_silently, **kwargs)
    elif backend == "file":
        from p8s.email.backends import FileBackend

        return FileBackend(fail_silently=fail_silently, **kwargs)
    else:
        raise ValueError(f"Unknown email backend: {backend}")


def send_mail(
    subject: str,
    message: str,
    from_email: str | None = None,
    recipient_list: list[str] | None = None,
    fail_silently: bool = False,
    html_message: str | None = None,
    **kwargs: Any,
) -> int:
    """
    Send a single email.

    Django-compatible API.

    Example:
        ```python
        from p8s.email import send_mail

        send_mail(
            subject="Hello",
            message="This is a test email.",
            from_email="noreply@example.com",
            recipient_list=["user@example.com"],
        )
        ```

    Args:
        subject: Email subject.
        message: Plain text message body.
        from_email: Sender email (uses default if None).
        recipient_list: List of recipient addresses.
        fail_silently: Suppress exceptions.
        html_message: Optional HTML version of the message.
        **kwargs: Additional EmailMessage options.

    Returns:
        Number of emails sent (0 or 1).
    """
    if html_message:
        from p8s.email.message import EmailMultiAlternatives

        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
            **kwargs,
        )
        email.attach_alternative(html_message, "text/html")
    else:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=recipient_list,
            **kwargs,
        )

    return email.send(fail_silently=fail_silently)


def send_mass_mail(
    datatuple: list[tuple[str, str, str, list[str]]],
    fail_silently: bool = False,
) -> int:
    """
    Send multiple emails efficiently.

    Example:
        ```python
        from p8s.email import send_mass_mail

        messages = [
            ("Subject 1", "Body 1", "from@example.com", ["to1@example.com"]),
            ("Subject 2", "Body 2", "from@example.com", ["to2@example.com"]),
        ]
        send_mass_mail(messages)
        ```

    Args:
        datatuple: List of (subject, message, from_email, recipient_list) tuples.
        fail_silently: Suppress exceptions.

    Returns:
        Number of emails sent.
    """
    connection = get_connection(fail_silently=fail_silently)

    messages = [
        EmailMessage(
            subject=subject, body=message, from_email=from_email, to=recipient_list
        )
        for subject, message, from_email, recipient_list in datatuple
    ]

    return connection.send_messages(messages)


async def send_mail_async(
    subject: str,
    message: str,
    from_email: str | None = None,
    recipient_list: list[str] | None = None,
    fail_silently: bool = False,
    html_message: str | None = None,
    **kwargs: Any,
) -> int:
    """
    Send email asynchronously.

    Uses asyncio.to_thread for non-blocking execution.

    Args:
        subject: Email subject.
        message: Plain text message body.
        from_email: Sender email.
        recipient_list: List of recipient addresses.
        fail_silently: Suppress exceptions.
        html_message: Optional HTML version.
        **kwargs: Additional options.

    Returns:
        Number of emails sent.
    """
    import asyncio

    return await asyncio.to_thread(
        send_mail,
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently,
        html_message,
        **kwargs,
    )
