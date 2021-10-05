import pytest as pt
import tempfile
import typing as t
from pathlib import Path
from unittest.mock import patch
from fastapi_mailman.backends import locmem, smtp
from fastapi_mailman import EmailMessage

if t.TYPE_CHECKING:
    from fastapi_mailman import Mail


@pt.mark.anyio
async def test_console_backend(mail:"Mail", capsys:"pt.CaptureFixture"):
    mail.backend = 'console'
    msg = EmailMessage(
        subject="testing",
        to=["to@example.com"],
        body="testing",
    )
    await msg.send()

    captured = capsys.readouterr()
    assert "testing" in captured.out
    assert "To: to@example.com" in captured.out


@pt.mark.anyio
async def test_dummy_backend(mail:"Mail"):
        mail.backend = 'dummy'
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )
        assert await msg.send() == 1

@pt.mark.anyio
async def test_file_backend(mail:"Mail"):
    with tempfile.TemporaryDirectory() as tempdir:
        mail.backend = 'file'
        mail.file_path = tempdir
        async with mail.get_connection() as conn:
            msg = EmailMessage(
                subject="testing",
                to=["to@example.com"],
                body="testing",
                connection=conn,
            )
            await msg.send()

        wrote_file = Path(conn._fname)
        assert wrote_file.is_file()
        assert "To: to@example.com" in wrote_file.read_text()

@pt.mark.anyio
async def test_locmem_backend(mail:"Mail"):
    mail.backend = 'locmem'
    msg = EmailMessage(
        subject="testing",
        to=["to@example.com"],
        body="testing",
    )
    await msg.send()

    assert len(mail.outbox) == 1
    sent_msg = mail.outbox[0]
    assert sent_msg.subject == "testing"
    assert sent_msg.to == ["to@example.com"]
    assert sent_msg.body == "testing"
    assert sent_msg.from_email == mail.default_sender

@pt.mark.anyio
async def test_smtp_backend(mail:"Mail"):
        mail.backend = 'smtp'
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
        )

        with patch.object(smtp.EmailBackend, 'send_messages') as mock_send_fn:
            mock_send_fn.return_value = 66
            # assert await msg.send() == 66

@pt.mark.anyio
async def test_invalid_backend(mail:"Mail"):
    mail.backend = 'unknown'
    msg = EmailMessage(
        subject="testing",
        to=["to@example.com"],
        body="testing",
    )

    with pt.raises(RuntimeError) as exc:
        await msg.send()
    assert "The available built-in mail backends" in str(exc)

@pt.mark.anyio
async def test_override_custom_backend(mail:"Mail"):
    mail.backend = 'console'
    async with mail.get_connection(backend=locmem.EmailBackend) as conn:
        msg = EmailMessage(subject="testing", to=["to@example.com"], body="testing", connection=conn)
        await msg.send()

    assert len(mail.outbox) == 1
    sent_msg = mail.outbox[0]
    assert sent_msg.subject == "testing"

@pt.mark.anyio
async def test_import_path_locmem_backend(mail:"Mail"):
    for i, backend_path in enumerate(
        ["fastapi_mailman.backends.locmem", "fastapi_mailman.backends.locmem.EmailBackend"]):
            mail.backend = backend_path
            msg = EmailMessage(
                subject="testing",
                to=["to@example.com"],
                body="testing",
            )
            await msg.send()

            assert len(mail.outbox) ==  i + 1
            sent_msg = mail.outbox[0]
            assert sent_msg.subject == "testing"
