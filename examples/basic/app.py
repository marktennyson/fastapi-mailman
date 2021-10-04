from typing import Optional
from dotenv import load_dotenv; load_dotenv()
from os import environ

from fastapi import FastAPI
import uvicorn as uv
from fastapi_mailman import Mail, EmailMessage
from fastapi_mailman.config import ConnectionConfig
import views

app = FastAPI(debug=True)

config = ConnectionConfig(
    MAIL_USERNAME = environ.get("MAIL_USERNAME"),
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD"),
    MAIL_BACKEND =  environ.get("MAIL_BACKEND"),
    MAIL_SERVER =  environ.get("MAIL_SERVER"),
    MAIL_PORT = environ.get("MAIL_PORT"),
    MAIL_USE_TLS = environ.get("MAIL_USE_TLS"),
    MAIL_USE_SSL = environ.get("MAIL_USE_SSL"),
    MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER"),
    )
mail = Mail(config)

@app.get("/")
async def read_root():
    # msg = EmailMessage('this is subject', 'this is message', to=['aniketsarkar@yahoo.com'])
    # await msg.send()
    await views.send_email()
    # await mail.send_mail("this is subject", "this is message", None, ["aniketsarkar@yahoo.com"])
    return {"Hello": "World"}


if __name__ == "__main__":
    uv.run(app, port=8082)