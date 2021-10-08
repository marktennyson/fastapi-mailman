import typing as t

import pytest as pt

from fastapi_mailman import BadHeaderError, EmailMessage

if t.TYPE_CHECKING:
    from fastapi_mailman import Mail


@pt.mark.anyio
async def test_send_message(mail: "Mail"):
    mail.backend = "locmem"
    msg = EmailMessage(
        subject="testing",
        to=["to@example.com"],
        body="testing",
    )
    await msg.send()
    assert len(mail.outbox) == 1
    sent_msg = mail.outbox[0]
    assert sent_msg.from_email == mail.default_sender


@pt.mark.anyio
async def test_send_message_using_connection(mail: "Mail"):
    async with mail.get_connection() as conn:
        msg = EmailMessage(
            subject="testing",
            to=["to@example.com"],
            body="testing",
            connection=conn,
        )
        await msg.send()
        assert len(mail.outbox) == 1
        sent_msg = mail.outbox[0]
        assert sent_msg.from_email == mail.default_sender

        await conn.send_messages([msg])
        assert len(mail.outbox) == 2


@pt.mark.anyio
async def test_send_single(mail: "Mail"):
    async with mail.get_connection() as conn:
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
        assert sent_msg.to == ["to@example.com"]
        assert sent_msg.body == "testing"
        assert sent_msg.from_email == mail.default_sender


@pt.mark.anyio
async def test_send_many(mail: "Mail"):
    async with mail.get_connection() as conn:
        msgs = []
        for _ in range(10):
            msg = EmailMessage(mailman=mail, subject="testing", to=["to@example.com"], body="testing")
            msgs.append(msg)
        await conn.send_messages(msgs)
        assert len(mail.outbox) == 10
        sent_msg = mail.outbox[0]
        assert sent_msg.from_email == mail.default_sender


@pt.mark.anyio
async def test_send_without_sender(mail: "Mail"):
    mail.default_sender = None
    msg = EmailMessage(mailman=mail, subject="testing", to=["to@example.com"], body="testing")
    await msg.send()
    assert len(mail.outbox) == 1
    sent_msg = mail.outbox[0]
    assert sent_msg.from_email is None


@pt.mark.anyio
async def test_send_without_to(mail: "Mail"):
    msg = EmailMessage(subject="testing", to=[], body="testing")
    assert await msg.send() == 0


@pt.mark.anyio
async def test_bad_header_subject(mail):
    msg = EmailMessage(subject="testing\n\r", body="testing", to=["to@example.com"])
    with pt.raises(BadHeaderError):
        await msg.send()
