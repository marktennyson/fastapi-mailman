# FastAPI-Mailman

**Django-style email sending for FastAPI applications**

FastAPI-Mailman brings Django's robust email implementation to FastAPI with full async support. It's production-ready, fully typed, and designed for modern Python 3.10+.

## Features

- 🚀 **Full Async Support** - Built for async/await from the ground up
- 📧 **Multiple Backends** - SMTP, Console, File, In-Memory, and Dummy backends
- 🔒 **Type Safe** - Fully typed with PEP 561 compliance
- 🎨 **Jinja2 Templates** - Built-in template support for HTML emails
- 🔌 **Extensible** - Easy to create custom backends
- ⚡ **Pydantic v2** - Modern configuration with Pydantic Settings
- 🧪 **Test-Friendly** - In-memory backend for easy testing

## Installation

```bash
pip install fastapi-mailman
```

## Quick Start

```python
from fastapi import FastAPI
from fastapi_mailman import Mail, EmailMessage
from fastapi_mailman.config import ConnectionConfig

app = FastAPI()

# Configure email
config = ConnectionConfig(
    MAIL_USERNAME="your-email@gmail.com",
    MAIL_PASSWORD="your-app-password",
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_DEFAULT_SENDER="your-email@gmail.com",
)

mail = Mail(config)


@app.post("/send-email")
async def send_email():
    msg = EmailMessage(
        subject="Hello from FastAPI-Mailman!",
        body="This is a test email.",
        to=["recipient@example.com"],
    )
    await msg.send()
    return {"message": "Email sent!"}
```

## Configuration

FastAPI-Mailman uses Pydantic Settings for configuration. All options can be set via environment variables or passed directly to `ConnectionConfig`.

### Available Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `MAIL_USERNAME` | str | **Required** | SMTP authentication username |
| `MAIL_PASSWORD` | str | **Required** | SMTP authentication password |
| `MAIL_SERVER` | str | **Required** | SMTP server hostname |
| `MAIL_PORT` | int | `587` | SMTP server port |
| `MAIL_USE_TLS` | bool | `False` | Enable STARTTLS |
| `MAIL_USE_SSL` | bool | `False` | Enable SSL/TLS |
| `MAIL_DEFAULT_SENDER` | str | `None` | Default sender email |
| `MAIL_BACKEND` | str | `"smtp"` | Email backend to use |
| `MAIL_TIMEOUT` | int | `None` | Connection timeout (seconds) |
| `MAIL_SSL_KEYFILE` | str | `None` | Path to SSL key file |
| `MAIL_SSL_CERTFILE` | str | `None` | Path to SSL certificate file |
| `MAIL_USE_LOCALTIME` | bool | `False` | Use local time in headers |
| `MAIL_FILE_PATH` | str | `None` | Directory for file backend |
| `TEMPLATE_FOLDER` | Path | `None` | Path to email templates |
| `MAIL_DEFAULT_CHARSET` | str | `"utf-8"` | Default character encoding |

!!! note "TLS vs SSL"
    `MAIL_USE_TLS` and `MAIL_USE_SSL` are mutually exclusive. Use TLS (port 587) for most modern SMTP servers, or SSL (port 465) for legacy servers.

## Sending Messages

### Basic Email

```python
from fastapi_mailman import EmailMessage

msg = EmailMessage(
    subject="Hello",
    body="This is the message body.",
    from_email="sender@example.com",
    to=["recipient@example.com"],
    cc=["cc@example.com"],
    bcc=["bcc@example.com"],
    reply_to=["reply@example.com"],
)
await msg.send()
```

### HTML Email

Use `EmailMultiAlternatives` to send both plain text and HTML:

```python
from fastapi_mailman import EmailMultiAlternatives

msg = EmailMultiAlternatives(
    subject="Welcome!",
    body="Welcome to our service.",  # Plain text version
    to=["user@example.com"],
)
msg.attach_alternative(
    "<h1>Welcome!</h1><p>Welcome to our service.</p>",
    "text/html"
)
await msg.send()
```

Or use the convenient `send_mail` helper:

```python
await mail.send_mail(
    subject="Welcome!",
    message="Welcome to our service.",
    recipient_list=["user@example.com"],
    html_message="<h1>Welcome!</h1><p>Welcome to our service.</p>",
)
```

### Attachments

```python
msg = EmailMessage(
    subject="Document Attached",
    body="Please find the document attached.",
    to=["recipient@example.com"],
)

# Attach from file path
msg.attach_file("/path/to/document.pdf")

# Attach content directly
msg.attach("report.csv", csv_content, "text/csv")

await msg.send()
```

### Mass Mailing

Send multiple emails efficiently using a single connection:

```python
messages = [
    ("Welcome!", "Welcome message", "from@example.com", ["user1@example.com"]),
    ("Newsletter", "Latest updates", "from@example.com", ["user2@example.com"]),
]

count = await mail.send_mass_mail(messages)
print(f"Sent {count} emails")
```

## Email Backends

FastAPI-Mailman supports multiple backends for different use cases.

### SMTP Backend (Default)

Production backend that sends emails through an SMTP server.

```python
config = ConnectionConfig(
    MAIL_USERNAME="user@example.com",
    MAIL_PASSWORD="password",
    MAIL_SERVER="smtp.example.com",
    MAIL_BACKEND="smtp",  # This is the default
)
```

### Console Backend

Prints emails to stdout. Useful for development.

```python
config = ConnectionConfig(
    MAIL_USERNAME="dev@localhost",
    MAIL_PASSWORD="",
    MAIL_SERVER="localhost",
    MAIL_BACKEND="console",
)
```

### File Backend

Writes emails to files. Useful for development and debugging.

```python
config = ConnectionConfig(
    MAIL_USERNAME="dev@localhost",
    MAIL_PASSWORD="",
    MAIL_SERVER="localhost",
    MAIL_BACKEND="file",
    MAIL_FILE_PATH="/tmp/emails",
)
```

### In-Memory Backend (locmem)

Stores emails in memory. Perfect for testing.

```python
config = ConnectionConfig(
    MAIL_USERNAME="test@example.com",
    MAIL_PASSWORD="test",
    MAIL_SERVER="localhost",
    MAIL_BACKEND="locmem",
)

mail = Mail(config)
await mail.send_mail("Test", "Hello", recipient_list=["test@example.com"])

# Access sent emails
assert len(mail.outbox) == 1
assert mail.outbox[0].subject == "Test"
```

### Dummy Backend

Discards all emails. Useful when you want to test code paths without any side effects.

```python
config = ConnectionConfig(
    MAIL_USERNAME="dev@localhost",
    MAIL_PASSWORD="",
    MAIL_SERVER="localhost",
    MAIL_BACKEND="dummy",
)
```

### Custom Backend

Create your own backend by subclassing `BaseEmailBackend`:

```python
from fastapi_mailman.backends.base import BaseEmailBackend

class CustomBackend(BaseEmailBackend):
    async def send_messages(self, email_messages):
        for message in email_messages:
            # Your custom sending logic here
            pass
        return len(email_messages)

# Use the custom backend
connection = mail.get_connection(backend=CustomBackend)
await connection.send_messages(messages)
```

## Connection Management

### Using Context Manager

The recommended way to manage connections:

```python
async with mail.get_connection() as conn:
    msg1 = EmailMessage(subject="First", body="...", to=["a@example.com"], connection=conn)
    await msg1.send()

    msg2 = EmailMessage(subject="Second", body="...", to=["b@example.com"], connection=conn)
    await msg2.send()
# Connection is automatically closed
```

### Manual Connection Management

```python
connection = mail.get_connection()
await connection.open()

try:
    msg = EmailMessage(subject="Test", body="...", to=["test@example.com"], connection=connection)
    await msg.send()
finally:
    await connection.close()
```

## Testing

Use the `locmem` backend for testing:

```python
import pytest
from fastapi_mailman import Mail
from fastapi_mailman.config import ConnectionConfig


@pytest.fixture
def mail():
    config = ConnectionConfig(
        MAIL_USERNAME="test@example.com",
        MAIL_PASSWORD="test",
        MAIL_SERVER="localhost",
        MAIL_BACKEND="locmem",
    )
    return Mail(config)


async def test_send_email(mail):
    await mail.send_mail(
        subject="Test Subject",
        message="Test body",
        recipient_list=["recipient@example.com"],
    )

    # Verify the email was "sent"
    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.subject == "Test Subject"
    assert sent.to == ["recipient@example.com"]
```

## Template Support

Use Jinja2 templates for HTML emails:

```python
from pathlib import Path

config = ConnectionConfig(
    MAIL_USERNAME="user@example.com",
    MAIL_PASSWORD="password",
    MAIL_SERVER="smtp.example.com",
    TEMPLATE_FOLDER=Path("./templates"),
)

mail = Mail(config)

# Get template engine
env = config.template_engine()
template = env.get_template("welcome.html")
html_content = template.render(username="John", activation_link="https://...")

await mail.send_mail(
    subject="Welcome!",
    message="Welcome to our service.",
    recipient_list=["user@example.com"],
    html_message=html_content,
)
```

## Header Injection Protection

FastAPI-Mailman protects against header injection attacks by forbidding newlines in header values:

```python
from fastapi_mailman import EmailMessage
from fastapi_mailman.errors import BadHeaderError

try:
    msg = EmailMessage(
        subject="Test\nInjection",  # Newline in subject!
        body="...",
        to=["test@example.com"],
    )
    msg.message()  # Raises BadHeaderError
except BadHeaderError:
    print("Invalid header detected!")
```

## API Reference

### Mail Class

The main entry point for sending emails.

```python
class Mail:
    def __init__(self, config: ConnectionConfig) -> None: ...

    def get_connection(
        self,
        backend: str | type[BaseEmailBackend] | None = None,
        fail_silently: bool = False,
        **kwargs,
    ) -> BaseEmailBackend: ...

    async def send_mail(
        self,
        subject: str,
        message: str,
        from_email: str | None = None,
        recipient_list: Sequence[str] | None = None,
        fail_silently: bool = False,
        auth_user: str | None = None,
        auth_password: str | None = None,
        connection: BaseEmailBackend | None = None,
        html_message: str | None = None,
    ) -> int: ...

    async def send_mass_mail(
        self,
        datatuple: Sequence[tuple[str, str, str, Sequence[str]]],
        fail_silently: bool = False,
        auth_user: str | None = None,
        auth_password: str | None = None,
        connection: BaseEmailBackend | None = None,
    ) -> int: ...
```

### EmailMessage Class

Represents a single email message.

```python
class EmailMessage:
    def __init__(
        self,
        subject: str = "",
        body: str = "",
        from_email: str | None = None,
        to: list[str] | tuple[str, ...] | None = None,
        cc: list[str] | tuple[str, ...] | None = None,
        bcc: list[str] | tuple[str, ...] | None = None,
        reply_to: list[str] | tuple[str, ...] | None = None,
        attachments: list[...] | None = None,
        headers: dict[str, Any] | None = None,
        connection: BaseEmailBackend | None = None,
        mailman: Mail | None = None,
    ) -> None: ...

    async def send(self, fail_silently: bool = False) -> int: ...

    def attach(
        self,
        filename: str | MIMEBase | None = None,
        content: Any = None,
        mimetype: str | None = None,
    ) -> None: ...

    def attach_file(self, path: str | Path, mimetype: str | None = None) -> None: ...
```

### EmailMultiAlternatives Class

Email message with support for alternative content types (e.g., HTML).

```python
class EmailMultiAlternatives(EmailMessage):
    def attach_alternative(self, content: str, mimetype: str) -> None: ...
```
