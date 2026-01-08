# Email

Django-style email sending with multiple backends.

## Quick Start

```python
from p8s.email import send_mail

send_mail(
    subject="Welcome!",
    message="Thanks for signing up.",
    from_email="noreply@example.com",
    recipient_list=["user@example.com"],
)
```

## HTML Emails

```python
from p8s.email import send_mail

send_mail(
    subject="Newsletter",
    message="Plain text version",
    from_email="news@example.com",
    recipient_list=["user@example.com"],
    html_message="<h1>HTML version</h1>",
)
```

## EmailMessage Class

```python
from p8s.email import EmailMessage

email = EmailMessage(
    subject="Report",
    body="See attachment.",
    from_email="reports@example.com",
    to=["manager@example.com"],
    cc=["team@example.com"],
)
email.attach_file("report.pdf")
email.send()
```

## Backends

### Console (Development)
```python
# Default - prints to console
backend = ConsoleBackend()
```

### SMTP (Production)
```python
from p8s.email import SMTPBackend

backend = SMTPBackend(
    host="smtp.gmail.com",
    port=587,
    username="user@gmail.com",
    password="app-password",
    use_tls=True,
)
```

### File (Testing)
```python
from p8s.email import FileBackend

backend = FileBackend(file_path="emails/")
```

## Async Support

```python
from p8s.email.utils import send_mail_async

await send_mail_async(
    subject="Async Email",
    message="Sent in background",
    from_email="noreply@example.com",
    recipient_list=["user@example.com"],
)
```

## Bulk Sending

```python
from p8s.email import send_mass_mail

messages = [
    ("Subject 1", "Body 1", "from@ex.com", ["to1@ex.com"]),
    ("Subject 2", "Body 2", "from@ex.com", ["to2@ex.com"]),
]
send_mass_mail(messages)
```
