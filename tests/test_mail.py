"""Tests for mail sending functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi_mailman import Mail
    from fastapi_mailman.config import ConnectionConfig


class TestSendMail:
    """Tests for the send_mail method."""

    async def test_send_mail_basic(
        self,
        mail: Mail,
        config: ConnectionConfig,
    ) -> None:
        """Test basic send_mail functionality."""
        mail.backend = "locmem"

        await mail.send_mail(
            subject="testing",
            message="test message",
            from_email=config.MAIL_DEFAULT_SENDER,
            recipient_list=["tester@example.com"],
        )

        assert len(mail.outbox) == 1
        sent_msg = mail.outbox[0]
        assert sent_msg.from_email == config.MAIL_DEFAULT_SENDER

    async def test_send_mail_with_html(
        self,
        mail: Mail,
        config: ConnectionConfig,
    ) -> None:
        """Test send_mail with HTML alternative."""
        mail.backend = "locmem"

        await mail.send_mail(
            subject="testing",
            message="plain text",
            from_email=config.MAIL_DEFAULT_SENDER,
            recipient_list=["tester@example.com"],
            html_message="<h1>HTML content</h1>",
        )

        assert len(mail.outbox) == 1
        sent_msg = mail.outbox[0]
        assert len(sent_msg.alternatives) == 1
        assert sent_msg.alternatives[0][0] == "<h1>HTML content</h1>"
        assert sent_msg.alternatives[0][1] == "text/html"


class TestSendMassMail:
    """Tests for the send_mass_mail method."""

    async def test_send_mass_mail(self, mail: Mail) -> None:
        """Test sending multiple messages efficiently."""
        mail.backend = "locmem"

        message1 = (
            "Subject here",
            "Here is the message",
            "from@example.com",
            ["first@example.com", "other@example.com"],
        )
        message2 = (
            "Another Subject",
            "Here is another message",
            "from@example.com",
            ["second@test.com"],
        )

        await mail.send_mass_mail((message1, message2), fail_silently=False)

        assert len(mail.outbox) == 2

        msg1 = mail.outbox[0]
        assert msg1.subject == "Subject here"
        assert msg1.to == ["first@example.com", "other@example.com"]
        assert msg1.body == "Here is the message"
        assert msg1.from_email == "from@example.com"

        msg2 = mail.outbox[1]
        assert msg2.subject == "Another Subject"
        assert msg2.to == ["second@test.com"]
        assert msg2.body == "Here is another message"
        assert msg2.from_email == "from@example.com"

    async def test_send_mass_mail_empty(self, mail: Mail) -> None:
        """Test send_mass_mail with empty list."""
        mail.backend = "locmem"

        result = await mail.send_mass_mail([], fail_silently=False)
        assert result == 0
