"""Tests for EmailMessage and related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from fastapi_mailman import EmailMessage, EmailMultiAlternatives
from fastapi_mailman.errors import BadHeaderError, MailmanNotInitializedError
from fastapi_mailman.globals import set_mailman

if TYPE_CHECKING:
    from fastapi_mailman import Mail


class TestEmailMessage:
    """Tests for EmailMessage class."""

    async def test_basic_message(self, mail: Mail) -> None:
        """Test creating and sending a basic message."""
        mail.backend = "locmem"

        msg = EmailMessage(
            subject="Test Subject",
            body="Test body",
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )

        await msg.send()

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Test Subject"

    async def test_cc_and_bcc(self, mail: Mail) -> None:
        """Test CC and BCC recipients."""
        mail.backend = "locmem"

        msg = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )

        recipients = msg.recipients()
        assert "to@example.com" in recipients
        assert "cc@example.com" in recipients
        assert "bcc@example.com" in recipients

    async def test_empty_recipients_not_sent(self, mail: Mail) -> None:
        """Test that messages with no recipients aren't sent."""
        mail.backend = "locmem"

        msg = EmailMessage(
            subject="Test",
            body="Body",
        )

        result = await msg.send()
        assert result == 0
        # Outbox may not exist if no messages were sent via locmem backend
        assert not hasattr(mail, "outbox") or len(mail.outbox) == 0

    def test_invalid_recipient_type_raises(self, mail: Mail) -> None:
        """Test that invalid recipient types raise TypeError."""
        with pytest.raises(TypeError, match='"to" argument must be a list or tuple'):
            EmailMessage(
                subject="Test",
                body="Body",
                to="not-a-list@example.com",  # type: ignore
            )

    def test_mailman_not_initialized_raises(self) -> None:
        """Test that creating message without Mail raises error."""
        set_mailman(None)

        with pytest.raises(MailmanNotInitializedError):
            EmailMessage(
                subject="Test",
                body="Body",
                to=["to@example.com"],
            )


class TestEmailMultiAlternatives:
    """Tests for EmailMultiAlternatives class."""

    async def test_attach_alternative(self, mail: Mail) -> None:
        """Test attaching alternative content."""
        mail.backend = "locmem"

        msg = EmailMultiAlternatives(
            subject="Test",
            body="Plain text",
            to=["to@example.com"],
        )
        msg.attach_alternative("<h1>HTML</h1>", "text/html")

        await msg.send()

        assert len(mail.outbox) == 1
        sent = mail.outbox[0]
        assert len(sent.alternatives) == 1
        assert sent.alternatives[0] == ("<h1>HTML</h1>", "text/html")

    def test_attach_alternative_validation(self, mail: Mail) -> None:
        """Test that attach_alternative validates inputs."""
        msg = EmailMultiAlternatives(
            subject="Test",
            body="Plain text",
            to=["to@example.com"],
        )

        with pytest.raises(ValueError, match="Both content and mimetype"):
            msg.attach_alternative(None, "text/html")  # type: ignore


class TestAttachments:
    """Tests for email attachments."""

    async def test_attach_content(self, mail: Mail) -> None:
        """Test attaching content directly."""
        mail.backend = "locmem"

        msg = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
        )
        msg.attach("file.txt", "content", "text/plain")

        await msg.send()

        assert len(mail.outbox) == 1
        assert len(mail.outbox[0].attachments) == 1

    def test_attach_without_content_raises(self, mail: Mail) -> None:
        """Test that attach without content raises ValueError."""
        msg = EmailMessage(
            subject="Test",
            body="Body",
            to=["to@example.com"],
        )

        with pytest.raises(ValueError, match="content must be provided"):
            msg.attach("file.txt", None)


class TestHeaderValidation:
    """Tests for email header validation."""

    def test_newline_in_subject_raises(self, mail: Mail) -> None:
        """Test that newlines in subject raise BadHeaderError."""
        msg = EmailMessage(
            subject="Test\nInjection",
            body="Body",
            to=["to@example.com"],
        )

        with pytest.raises(BadHeaderError, match="newlines"):
            msg.message()

    async def test_unicode_subject(self, mail: Mail) -> None:
        """Test Unicode in subject line."""
        mail.backend = "locmem"

        msg = EmailMessage(
            subject="Test 日本語 Subject",
            body="Body",
            to=["to@example.com"],
        )

        await msg.send()
        assert len(mail.outbox) == 1
