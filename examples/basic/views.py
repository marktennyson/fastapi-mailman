from fastapi_mailman import EmailMessage

async def send_email():
    msg = EmailMessage("this is subject", "this is body", to=['aniketsarkar@yahoo.com'])
    await msg.send()