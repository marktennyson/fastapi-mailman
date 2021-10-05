import pytest as pt
from fastapi import FastAPI

from fastapi_mailman import Mail
from fastapi_mailman.config import ConnectionConfig


@pt.fixture
def app() -> "FastAPI":
    app = FastAPI(debug=True)
    return app


@pt.fixture
def config() -> "ConnectionConfig":
    config = ConnectionConfig(
        MAIL_USERNAME='example@domain.com',
        MAIL_PASSWORD="7655tgrf443%$",
        MAIL_BACKEND='smtp',
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_DEFAULT_SENDER='example@domain.com',
    )
    return config


@pt.fixture
def mail(config: "ConnectionConfig") -> "Mail":

    mail = Mail(config)
    mail.backend = "locmem"
    return mail


@pt.fixture(autouse=True)
def capsys(capsys: "pt.CaptureFixture") -> "pt.CaptureFixture":
    return capsys
