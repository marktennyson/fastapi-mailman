from fastapi import FastAPI
from fastapi_mailman import Mail
from fastapi_mailman.config import ConnectionConfig

import pytest as pt
import typing as t


@pt.fixture
def app() -> "FastAPI":
    app = FastAPI(debug=True)
    return app

@pt.fixture
def config() -> "ConnectionConfig":
    config = ConnectionConfig(
    MAIL_USERNAME = 'aioflask@gmail.com',
    MAIL_PASSWORD = "kuvlcaajlwmqeurk",
    MAIL_BACKEND =  'smtp',
    MAIL_SERVER =  'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_DEFAULT_SENDER = 'info@acqude.com',
    )
    return config

@pt.fixture
def mail(config:"ConnectionConfig") -> "Mail":
    
    mail = Mail(config)
    return mail

@pt.fixture(autouse=True)
def capsys(capsys:"pt.CaptureFixture") -> "pt.CaptureFixture":
    return capsys