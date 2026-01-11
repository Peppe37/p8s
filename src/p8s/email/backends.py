"""
P8s Email Backends - Configurable email sending backends.

Provides:
- SMTPBackend for production
- ConsoleBackend for development (prints to console)
- FileBackend for testing (writes to files)
"""

import logging
import smtplib
import ssl
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from p8s.email.message import EmailMessage

logger = logging.getLogger("p8s.email")


class EmailBackend(ABC):
    """
    Abstract base class for email backends.

    Subclass this to implement custom email backends.
    """

    def __init__(self, fail_silently: bool = False, **kwargs: Any) -> None:
        """
        Initialize backend.

        Args:
            fail_silently: If True, suppress exceptions.
            **kwargs: Backend-specific options.
        """
        self.fail_silently = fail_silently

    @abstractmethod
    def send_messages(self, messages: list["EmailMessage"]) -> int:
        """
        Send one or more messages.

        Args:
            messages: List of EmailMessage objects.

        Returns:
            Number of successfully sent messages.
        """
        pass

    def open(self) -> bool:
        """Open a connection (optional for some backends)."""
        return True

    def close(self) -> None:
        """Close the connection."""
        pass


class SMTPBackend(EmailBackend):
    """
    SMTP email backend for sending real emails.

    Example:
        ```python
        backend = SMTPBackend(
            host="smtp.gmail.com",
            port=587,
            username="user@gmail.com",
            password="app-password",
            use_tls=True,
        )
        backend.send_messages([message])
        ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 25,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = False,
        use_ssl: bool = False,
        timeout: int = 10,
        fail_silently: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize SMTP backend.

        Args:
            host: SMTP server hostname.
            port: SMTP server port.
            username: SMTP username (optional).
            password: SMTP password (optional).
            use_tls: Use STARTTLS.
            use_ssl: Use SSL/TLS from start.
            timeout: Connection timeout in seconds.
            fail_silently: Suppress exceptions.
        """
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.connection = None

    def open(self) -> bool:
        """Open SMTP connection."""
        if self.connection:
            return False

        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                self.connection = smtplib.SMTP_SSL(
                    self.host, self.port, timeout=self.timeout, context=context
                )
            else:
                self.connection = smtplib.SMTP(
                    self.host, self.port, timeout=self.timeout
                )
                if self.use_tls:
                    context = ssl.create_default_context()
                    self.connection.starttls(context=context)

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True
        except Exception as e:
            if not self.fail_silently:
                raise
            logger.error(f"Failed to open SMTP connection: {e}")
            return False

    def close(self) -> None:
        """Close SMTP connection."""
        if self.connection:
            try:
                self.connection.quit()
            except Exception:
                pass
            self.connection = None

    def send_messages(self, messages: list["EmailMessage"]) -> int:
        """Send messages via SMTP."""
        if not messages:
            return 0

        new_connection = self.open()
        if not self.connection:
            return 0

        sent_count = 0

        try:
            for message in messages:
                try:
                    self._send(message)
                    sent_count += 1
                except Exception as e:
                    if not self.fail_silently:
                        raise
                    logger.error(f"Failed to send email: {e}")
        finally:
            if new_connection:
                self.close()

        return sent_count

    def _send(self, message: "EmailMessage") -> None:
        """Send a single message."""
        msg = message.to_mime_message()

        recipients = message.recipients()
        if not recipients:
            return

        self.connection.sendmail(
            message.from_email,
            recipients,
            msg.as_string(),
        )


class ConsoleBackend(EmailBackend):
    """
    Email backend that prints emails to console.

    Useful for development and debugging.
    """

    def send_messages(self, messages: list["EmailMessage"]) -> int:
        """Print messages to console."""
        for message in messages:
            print("=" * 60)
            print(f"From: {message.from_email}")
            print(f"To: {', '.join(message.to)}")
            if message.cc:
                print(f"Cc: {', '.join(message.cc)}")
            if message.bcc:
                print(f"Bcc: {', '.join(message.bcc)}")
            print(f"Subject: {message.subject}")
            print("-" * 60)
            print(message.body)
            print("=" * 60)
            print()

        return len(messages)


class FileBackend(EmailBackend):
    """
    Email backend that writes emails to files.

    Useful for testing.
    """

    def __init__(
        self,
        file_path: str | Path = "emails",
        fail_silently: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize file backend.

        Args:
            file_path: Directory to write email files.
            fail_silently: Suppress exceptions.
        """
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.file_path = Path(file_path)
        self.file_path.mkdir(parents=True, exist_ok=True)

    def send_messages(self, messages: list["EmailMessage"]) -> int:
        """Write messages to files."""
        import time

        for message in messages:
            filename = f"{int(time.time() * 1000)}_{message.subject[:20]}.eml"
            filepath = self.file_path / filename

            try:
                with open(filepath, "w") as f:
                    f.write(f"From: {message.from_email}\n")
                    f.write(f"To: {', '.join(message.to)}\n")
                    f.write(f"Subject: {message.subject}\n")
                    f.write("\n")
                    f.write(message.body)
            except Exception as e:
                if not self.fail_silently:
                    raise
                logger.error(f"Failed to write email file: {e}")

        return len(messages)
