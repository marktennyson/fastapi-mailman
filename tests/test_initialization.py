
import typing as t

if t.TYPE_CHECKING:
    from fastapi_mailman import Mail

def test_init_mail(mail:"Mail", config):
    new_mail = mail.init_mail(config)

    assert mail.state.__dict__ ==  new_mail.__dict__
