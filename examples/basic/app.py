from typing import Optional

from fastapi import FastAPI
import uvicorn as uv
from fastapi_mailman import Mail, EmailMessage
from fastapi_mailman.config import ConnectionConfig

app = FastAPI(debug=True)

config = ConnectionConfig(
    MAIL_USERNAME = 'example@domain.com',
    MAIL_PASSWORD = "7655tgrf443%$",
    MAIL_BACKEND =  'smtp',
    MAIL_SERVER =  'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_DEFAULT_SENDER = 'example@domain.com',
    )
mail = Mail(config)

@app.get("/")
async def read_root():
    msg = EmailMessage(mail, 'this is subject', 'this is message', to=['aniketsarkar@yahoo.com'])
    await msg.send()
    # await mail.send_mail("this is subject", "this is message", None, ["aniketsarkar@yahoo.com"])
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    uv.run(app, port=8082, debug=True)
