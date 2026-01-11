"""
P8s Email Message - Email message classes.

Provides:
- EmailMessage for simple emails
- EmailMultiAlternatives for HTML emails
"""

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any


class EmailMessage:
    """
    Email message class.

    Example:
        ```python
        from p8s.email import EmailMessage

        email = EmailMessage(
            subject="Hello",
            body="This is a test email.",
            from_email="noreply@example.com",
            to=["user@example.com"],
        )
        email.send()
        ```
    """

    content_subtype = "plain"

    def __init__(
        self,
        subject: str = "",
        body: str = "",
        from_email: str | None = None,
        to: list[str] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: list[str] | None = None,
        headers: dict[str, str] | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> None:
        """
        Initialize email message.

        Args:
            subject: Email subject.
            body: Email body text.
            from_email: Sender email address.
            to: List of recipient addresses.
            cc: List of CC addresses.
            bcc: List of BCC addresses.
            reply_to: List of reply-to addresses.
            headers: Additional headers.
            attachments: List of (filename, content, mimetype) tuples.
        """
        self.subject = subject
        self.body = body
        self.from_email = from_email or self._get_default_from()
        self.to = to or []
        self.cc = cc or []
        self.bcc = bcc or []
        self.reply_to = reply_to or []
        self.headers = headers or {}
        self.attachments = attachments or []

    def _get_default_from(self) -> str:
        """Get default from email from settings."""
        try:
            from p8s.core.settings import get_settings

            settings = get_settings()
            return getattr(settings, "default_from_email", "noreply@example.com")
        except Exception:
            return "noreply@example.com"

    def recipients(self) -> list[str]:
        """Get all recipients (to + cc + bcc)."""
        return self.to + self.cc + self.bcc

    def attach(
        self, filename: str, content: bytes, mimetype: str = "application/octet-stream"
    ) -> None:
        """
        Attach a file to the email.

        Args:
            filename: Attachment filename.
            content: File content as bytes.
            mimetype: MIME type of the attachment.
        """
        self.attachments.append((filename, content, mimetype))

    def attach_file(self, path: str | Path) -> None:
        """
        Attach a file from filesystem.

        Args:
            path: Path to the file.
        """
        import mimetypes

        path = Path(path)
        mimetype, _ = mimetypes.guess_type(str(path))

        with open(path, "rb") as f:
            content = f.read()

        self.attach(path.name, content, mimetype or "application/octet-stream")

    def to_mime_message(self) -> MIMEMultipart:
        """Convert to MIME message for sending."""
        msg = MIMEMultipart()
        msg["Subject"] = self.subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to)

        if self.cc:
            msg["Cc"] = ", ".join(self.cc)

        if self.reply_to:
            msg["Reply-To"] = ", ".join(self.reply_to)

        for key, value in self.headers.items():
            msg[key] = value

        # Add body
        msg.attach(MIMEText(self.body, self.content_subtype))

        # Add attachments
        for filename, content, mimetype in self.attachments:
            maintype, subtype = mimetype.split("/", 1)
            part = MIMEBase(maintype, subtype)
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)

        return msg

    def send(self, fail_silently: bool = False) -> int:
        """
        Send this email.

        Args:
            fail_silently: If True, suppress exceptions.

        Returns:
            1 if sent successfully, 0 otherwise.
        """
        from p8s.email.utils import get_connection

        backend = get_connection(fail_silently=fail_silently)
        return backend.send_messages([self])


class EmailMultiAlternatives(EmailMessage):
    """
    Email message with alternative content types (e.g., HTML).

    Example:
        ```python
        from p8s.email import EmailMultiAlternatives

        email = EmailMultiAlternatives(
            subject="Hello",
            body="This is plain text.",
            from_email="noreply@example.com",
            to=["user@example.com"],
        )
        email.attach_alternative("<h1>Hello</h1>", "text/html")
        email.send()
        ```
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.alternatives: list[tuple[str, str]] = []

    def attach_alternative(self, content: str, mimetype: str) -> None:
        """
        Attach alternative content (e.g., HTML version).

        Args:
            content: Alternative content.
            mimetype: MIME type (e.g., "text/html").
        """
        self.alternatives.append((content, mimetype))

    def to_mime_message(self) -> MIMEMultipart:
        """Convert to MIME message with alternatives."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = self.subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to)

        if self.cc:
            msg["Cc"] = ", ".join(self.cc)

        if self.reply_to:
            msg["Reply-To"] = ", ".join(self.reply_to)

        for key, value in self.headers.items():
            msg[key] = value

        # Add plain text body
        msg.attach(MIMEText(self.body, "plain"))

        # Add alternatives
        for content, mimetype in self.alternatives:
            subtype = mimetype.split("/")[1] if "/" in mimetype else mimetype
            msg.attach(MIMEText(content, subtype))

        return msg
