
import typing as t

if t.TYPE_CHECKING:
    from fastapi_mailman import Mail
    from fastapi_mailman.config import ConnectionConfig

def test_init_mail(mail:"Mail", config:"ConnectionConfig"):
    new_mail = mail.init_mail(config)

    assert mail.state.__dict__ ==  new_mail.__dict__
