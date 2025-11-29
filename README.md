# 📬 FastAPI-Mailman

<img src="https://raw.githubusercontent.com/marktennyson/fastapi-mailman/master/logos/fastapi_mailman_logo.png" alt="FastAPI-Mailman Logo">

## Django-style email sending for FastAPI

[![PyPI](https://img.shields.io/pypi/v/fastapi-mailman?color=blue)](https://pypi.org/project/fastapi-mailman/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/fastapi-mailman?color=brightgreen)](https://pypi.org/project/fastapi-mailman/)
[![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-mailman)](https://pypi.org/project/fastapi-mailman/)
[![License](https://img.shields.io/pypi/l/fastapi-mailman?color=blue)](https://github.com/marktennyson/fastapi-mailman/blob/master/LICENSE)
[![Typing: typed](https://img.shields.io/badge/typing-typed-blue)](https://github.com/marktennyson/fastapi-mailman)

FastAPI-Mailman brings Django's robust email implementation to FastAPI applications with full async support. Production-ready, fully typed, and designed for modern Python.

## ✨ Features

- 🚀 **Full Async Support** - Built for async/await from the ground up
- 📧 **Multiple Backends** - SMTP, Console, File, In-Memory, and Dummy backends
- 🔒 **Type Safe** - Fully typed with PEP 561 compliance
- 🎨 **Jinja2 Templates** - Built-in template support for HTML emails
- 🔌 **Extensible** - Easy to create custom backends
- ⚡ **Pydantic v2** - Modern configuration with Pydantic Settings
- 🧪 **Test-Friendly** - In-memory backend for easy testing

## 📦 Installation

```bash
pip install fastapi-mailman
```

With development dependencies:
```bash
pip install fastapi-mailman[dev]
```

## 🚀 Quick Start

```python
from fastapi import FastAPI
from fastapi_mailman import Mail, EmailMessage
from fastapi_mailman.config import ConnectionConfig

app = FastAPI()

# Configure email settings
config = ConnectionConfig(
    MAIL_USERNAME="your-email@gmail.com",
    MAIL_PASSWORD="your-app-password",
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_DEFAULT_SENDER="your-email@gmail.com",
)

# Initialize Mail
mail = Mail(config)


@app.post("/send-email")
async def send_email():
    """Send a simple email."""
    msg = EmailMessage(
        subject="Hello from FastAPI-Mailman!",
        body="This is a test email.",
        to=["recipient@example.com"],
    )
    await msg.send()
    return {"message": "Email sent!"}


@app.post("/send-html-email")
async def send_html_email():
    """Send an email with HTML content."""
    await mail.send_mail(
        subject="Welcome!",
        message="Plain text version",
        recipient_list=["recipient@example.com"],
        html_message="<h1>Welcome!</h1><p>HTML version</p>",
    )
    return {"message": "HTML email sent!"}
```

## 📚 Documentation

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `MAIL_USERNAME` | str | Required | SMTP authentication username |
| `MAIL_PASSWORD` | str | Required | SMTP authentication password |
| `MAIL_SERVER` | str | Required | SMTP server hostname |
| `MAIL_PORT` | int | 587 | SMTP server port |
| `MAIL_USE_TLS` | bool | False | Enable STARTTLS |
| `MAIL_USE_SSL` | bool | False | Enable SSL/TLS |
| `MAIL_DEFAULT_SENDER` | str | None | Default sender email |
| `MAIL_BACKEND` | str | "smtp" | Email backend to use |
| `MAIL_TIMEOUT` | int | None | Connection timeout (seconds) |
| `TEMPLATE_FOLDER` | Path | None | Path to email templates |

### Available Backends

- **smtp** - Send emails via SMTP server (default)
- **console** - Print emails to stdout (development)
- **file** - Write emails to files (development/testing)
- **locmem** - Store emails in memory (testing)
- **dummy** - Discard emails (testing)

### Using the Console Backend (Development)

```python
config = ConnectionConfig(
    MAIL_USERNAME="dev@localhost",
    MAIL_PASSWORD="",
    MAIL_SERVER="localhost",
    MAIL_BACKEND="console",  # Emails will be printed to stdout
)
```

### Testing with In-Memory Backend

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
        subject="Test",
        message="Hello",
        recipient_list=["recipient@example.com"],
    )
    
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Test"
```

### Email with Attachments

```python
from fastapi_mailman import EmailMessage

msg = EmailMessage(
    subject="Document Attached",
    body="Please find the document attached.",
    to=["recipient@example.com"],
)

# Attach from file
msg.attach_file("/path/to/document.pdf")

# Attach content directly
msg.attach("report.csv", csv_content, "text/csv")

await msg.send()
```

### Mass Mailing

```python
# Send multiple emails efficiently using a single connection
messages = [
    ("Welcome!", "Welcome to our service.", "from@example.com", ["user1@example.com"]),
    ("Newsletter", "Latest updates...", "from@example.com", ["user2@example.com"]),
]

await mail.send_mass_mail(messages)
```

### Using Jinja2 Templates

```python
from pathlib import Path

config = ConnectionConfig(
    MAIL_USERNAME="your-email@gmail.com",
    MAIL_PASSWORD="your-app-password",
    MAIL_SERVER="smtp.gmail.com",
    TEMPLATE_FOLDER=Path("./templates"),
)

mail = Mail(config)

# In your templates folder: templates/welcome.html
env = config.template_engine()
template = env.get_template("welcome.html")
html_content = template.render(username="John", activation_link="...")

await mail.send_mail(
    subject="Welcome!",
    message="Welcome to our service.",
    recipient_list=["user@example.com"],
    html_message=html_content,
)
```

## 🔗 Links

- [📖 Documentation](https://marktennyson.github.io/fastapi-mailman)
- [📦 PyPI](https://pypi.org/project/fastapi-mailman)
- [🐙 GitHub](https://github.com/marktennyson/fastapi-mailman)
- [🐛 Issue Tracker](https://github.com/marktennyson/fastapi-mailman/issues)

## 🤝 Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/marktennyson/fastapi-mailman.git
cd fastapi-mailman

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
ruff format .

# Run type checking
mypy fastapi_mailman
```

## 👥 Contributors

<a href="https://github.com/marktennyson/fastapi-mailman/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=marktennyson/fastapi-mailman" />
</a>

## 📄 License

[MIT License](https://github.com/marktennyson/fastapi-mailman/blob/master/LICENSE)

Copyright (c) 2021-2025 Aniket Sarkar

---

Made with ❤️ for the FastAPI community
