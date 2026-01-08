"""
Tests for the email system.
"""

import pytest
from p8s.email.message import EmailMessage, EmailMultiAlternatives
from p8s.email.backends import ConsoleBackend, FileBackend


class TestEmailMessage:
    """Test EmailMessage class."""
    
    def test_create_email(self):
        """Test creating an email message."""
        email = EmailMessage(
            subject="Test Subject",
            body="Test body content",
            from_email="from@example.com",
            to=["to@example.com"],
        )
        
        assert email.subject == "Test Subject"
        assert email.body == "Test body content"
        assert email.from_email == "from@example.com"
        assert email.to == ["to@example.com"]
    
    def test_recipients(self):
        """Test recipients method."""
        email = EmailMessage(
            subject="Test",
            body="Body",
            to=["to1@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        
        recipients = email.recipients()
        assert len(recipients) == 3
        assert "to1@example.com" in recipients
        assert "cc@example.com" in recipients
        assert "bcc@example.com" in recipients
    
    def test_attach(self):
        """Test attaching content."""
        email = EmailMessage(subject="Test", body="Body")
        
        email.attach("file.txt", b"content", "text/plain")
        
        assert len(email.attachments) == 1
        assert email.attachments[0][0] == "file.txt"
    
    def test_to_mime_message(self):
        """Test converting to MIME message."""
        email = EmailMessage(
            subject="Test Subject",
            body="Test body",
            from_email="from@example.com",
            to=["to@example.com"],
        )
        
        mime = email.to_mime_message()
        
        assert mime["Subject"] == "Test Subject"
        assert mime["From"] == "from@example.com"
        assert "to@example.com" in mime["To"]


class TestEmailMultiAlternatives:
    """Test EmailMultiAlternatives class."""
    
    def test_attach_alternative(self):
        """Test attaching HTML alternative."""
        email = EmailMultiAlternatives(
            subject="Test",
            body="Plain text",
            to=["to@example.com"],
        )
        email.attach_alternative("<h1>HTML</h1>", "text/html")
        
        assert len(email.alternatives) == 1
        assert email.alternatives[0][0] == "<h1>HTML</h1>"
        assert email.alternatives[0][1] == "text/html"
    
    def test_mime_with_alternatives(self):
        """Test MIME message with alternatives."""
        email = EmailMultiAlternatives(
            subject="Test",
            body="Plain text",
            to=["to@example.com"],
        )
        email.attach_alternative("<h1>HTML</h1>", "text/html")
        
        mime = email.to_mime_message()
        assert mime.get_content_type() == "multipart/alternative"


class TestConsoleBackend:
    """Test ConsoleBackend."""
    
    def test_send_messages(self, capsys):
        """Test console backend prints emails."""
        backend = ConsoleBackend()
        
        email = EmailMessage(
            subject="Test",
            body="Body content",
            from_email="from@example.com",
            to=["to@example.com"],
        )
        
        count = backend.send_messages([email])
        captured = capsys.readouterr()
        
        assert count == 1
        assert "Test" in captured.out
        assert "from@example.com" in captured.out


class TestFileBackend:
    """Test FileBackend."""
    
    def test_send_messages(self, tmp_path):
        """Test file backend writes emails."""
        backend = FileBackend(file_path=tmp_path)
        
        email = EmailMessage(
            subject="TestEmail",
            body="Body content",
            from_email="from@example.com",
            to=["to@example.com"],
        )
        
        count = backend.send_messages([email])
        
        assert count == 1
        
        # Check file was created
        files = list(tmp_path.glob("*.eml"))
        assert len(files) == 1
        
        content = files[0].read_text()
        assert "TestEmail" in content
