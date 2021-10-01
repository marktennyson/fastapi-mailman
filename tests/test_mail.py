import pytest as pt
import typing as t

if t.TYPE_CHECKING:
    from fastapi_mailman import Mail
    from fastapi_mailman.config import ConnectionConfig


@pt.mark.anyio
async def test_send_mail(mail:"Mail", config:"ConnectionConfig"):
    mail.backend = "locmem"
    await mail.send_mail(
        subject="testing",
        message="test",
        from_email=config.dict().get("MAIL_DEFAULT_SENDER"),
        recipient_list=["tester@example.com"],
    )
    assert len(mail.outbox) == 1
    sent_msg = mail.outbox[0]
    assert sent_msg.from_email == config.dict().get("MAIL_DEFAULT_SENDER")

@pt.mark.anyio
async def test_send_mass_mail(mail:"Mail"):
    mail.backend = "locmem"
    message1 = (
        'Subject here',
        'Here is the message',
        'from@example.com',
        ['first@example.com', 'other@example.com'],
    )
    message2 = ('Another Subject', 'Here is another message', 'from@example.com', ['second@test.com'])
    await mail.send_mass_mail((message1, message2), fail_silently=False)
    assert len(mail.outbox) == 2
    msg1 = mail.outbox[0]
    assert msg1.subject == "Subject here"
    assert msg1.to == ['first@example.com', 'other@example.com']
    assert msg1.body == "Here is the message"
    assert msg1.from_email == "from@example.com"
    msg2 = mail.outbox[1]
    assert msg2.subject == "Another Subject"
    assert msg2.to == ['second@test.com']
    assert msg2.body == "Here is another message"
    assert msg2.from_email == "from@example.com"
