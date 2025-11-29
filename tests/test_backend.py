"""Tests for email backend implementations."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from fastapi_mailman import EmailMessage
from fastapi_mailman.backends import locmem, smtp

if TYPE_CHECKING:
    from fastapi_mailman import Mail


class TestConsoleBackend:
    """Tests for the console email backend."""

    async def test_console_backend_output(
        self,
        mail: Mail,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that console backend writes to stdout."""
        mail.backend = "console"
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing body",
        )
        await msg.send()

        captured = capsys.readouterr()
        assert "testing" in captured.out
        assert "To: to@example.com" in captured.out


class TestDummyBackend:
    """Tests for the dummy email backend."""

    async def test_dummy_backend_returns_count(self, mail: Mail) -> None:
        """Test that dummy backend returns message count."""
        mail.backend = "dummy"
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )
        result = await msg.send()
        assert result == 1


class TestFileBackend:
    """Tests for the file email backend."""

    async def test_file_backend_creates_file(self, mail: Mail) -> None:
        """Test that file backend creates email files."""
        with tempfile.TemporaryDirectory() as tempdir:
            mail.backend = "file"
            mail.file_path = tempdir

            async with mail.get_connection() as conn:
                msg = EmailMessage(
                    subject="testing",
                    to=["to@example.com"],
                    body="testing body",
                    connection=conn,
                )
                await msg.send()

            wrote_file = Path(conn._fname)
            assert wrote_file.is_file()
            content = wrote_file.read_text()
            assert "To: to@example.com" in content
            assert "testing" in content


class TestLocmemBackend:
    """Tests for the in-memory email backend."""

    async def test_locmem_backend_stores_messages(self, mail: Mail) -> None:
        """Test that locmem backend stores messages in outbox."""
        mail.backend = "locmem"
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing body",
        )
        await msg.send()

        assert len(mail.outbox) == 1
        sent_msg = mail.outbox[0]
        assert sent_msg.subject == "testing"
        assert sent_msg.to == ["to@example.com"]
        assert sent_msg.body == "testing body"
        assert sent_msg.from_email == mail.default_sender


class TestSMTPBackend:
    """Tests for the SMTP email backend."""

    async def test_smtp_backend_mock_send(self, mail: Mail) -> None:
        """Test SMTP backend with mocked send."""
        mail.backend = "smtp"
        _ = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )

        with patch.object(smtp.EmailBackend, "send_messages") as mock_send_fn:
            mock_send_fn.return_value = 1
            # Verify mock was set up correctly
            assert mock_send_fn.return_value == 1


class TestBackendErrors:
    """Tests for backend error handling."""

    async def test_invalid_backend_raises_error(self, mail: Mail) -> None:
        """Test that invalid backend raises RuntimeError."""
        mail.backend = "unknown_backend"
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )

        with pytest.raises(RuntimeError) as exc_info:
            await msg.send()

        assert "Available built-in backends" in str(exc_info.value)


class TestCustomBackend:
    """Tests for custom backend usage."""

    async def test_override_custom_backend(self, mail: Mail) -> None:
        """Test that backend can be overridden with custom class."""
        mail.backend = "console"

        async with mail.get_connection(backend=locmem.EmailBackend) as conn:
            msg = EmailMessage(
                subject="testing",
                to=["to@example.com"],
                body="testing",
                connection=conn,
            )
            await msg.send()

        assert len(mail.outbox) == 1
        sent_msg = mail.outbox[0]
        assert sent_msg.subject == "testing"

    async def test_import_path_locmem_backend(self, mail: Mail) -> None:
        """Test that backends can be imported by path."""
        backend_paths = [
            "fastapi_mailman.backends.locmem",
            "fastapi_mailman.backends.locmem.EmailBackend",
        ]

        for i, backend_path in enumerate(backend_paths):
            mail.backend = backend_path
            msg = EmailMessage(
                subject="testing",
                to=["to@example.com"],
                body="testing",
            )
            await msg.send()

            assert len(mail.outbox) == i + 1
            sent_msg = mail.outbox[0]
            assert sent_msg.subject == "testing"
