"""Pytest configuration and fixtures for FastAPI-Mailman tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fastapi_mailman import Mail
from fastapi_mailman.config import ConnectionConfig
from fastapi_mailman.globals import set_mailman

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def config() -> ConnectionConfig:
    """Create a test ConnectionConfig instance."""
    return ConnectionConfig(
        MAIL_USERNAME="example@domain.com",
        MAIL_PASSWORD="7655tgrf443%$",
        MAIL_BACKEND="smtp",
        MAIL_SERVER="smtp.gmail.com",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_DEFAULT_SENDER="example@domain.com",
    )


@pytest.fixture
def mail(config: ConnectionConfig) -> Generator[Mail, None, None]:
    """Create a Mail instance configured for testing with locmem backend."""
    mail_instance = Mail(config)
    mail_instance.backend = "locmem"

    yield mail_instance

    # Cleanup: reset global state
    set_mailman(None)
    if hasattr(mail_instance, "outbox"):
        mail_instance.outbox.clear()


@pytest.fixture
def console_mail(config: ConnectionConfig) -> Generator[Mail, None, None]:
    """Create a Mail instance configured for console backend."""
    mail_instance = Mail(config)
    mail_instance.backend = "console"

    yield mail_instance

    set_mailman(None)
