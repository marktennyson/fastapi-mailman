# 📬 Fastapi-Mailman
<img src="https://raw.githubusercontent.com/marktennyson/fastapi-mailman/master/logos/fastapi_mailman_logo.png"></img>

### 🔥 Porting Django's email implementation to your FastAPI applications.
![PyPI](https://img.shields.io/pypi/v/fastapi-mailman?color=blue)
![PyPI - Downloads](https://img.shields.io/pypi/dm/fastapi-mailman?color=brightgreen)
[![dev workflow](https://github.com/marktennyson/fastapi-mailman/actions/workflows/dev.yml/badge.svg?branch=master)](https://github.com/marktennyson/fastapi-mailman/actions/workflows/dev.yml)
![GitHub commits since latest release (by SemVer)](https://img.shields.io/github/commits-since/waynerv/fastapi-mailman/latest?color=cyan)
![PyPI - License](https://img.shields.io/pypi/l/fastapi-mailman?color=blue)

Fastapi-Mailman is a Fastapi extension providing simple email sending capabilities. It's actually a hard fork of `waynerv's` `flask-mailman` module. I have tried to implement the same features for the `Fastapi` too.

It was meant to replace the basic Fastapi-Mail with a better warranty and more features.

## ⛲ Key Features:
1. Easy to use. 
2. Backend based email sender.
3. Customisable backend class. 
4. Proper testcases. 
5. Proper documentation.

## 🔗 Important Links:
[Github Repo](https://github.com/marktennyson/fastapi-mailman)    
[PYPI](https://pypi.org/project/fastapi-mailman)    
[Documentation](https://marktennyson.github.io/fastapi-mailman)    

## 💯 Usage

Fastapi-Mail ported Django's email implementation to your Fastapi applications, which may be the best mail sending implementation that's available for python.

The way of using this extension is almost the same as Django.

Documentation: [https://marktennyson.github.io/fastapi-mailman.](https://marktennyson.github.io/fastapi-mailman)

## 🪜 Basic Example
```python
from fastapi import FastAPI
import uvicorn as uv
from fastapi_mailman import Mail, EmailMessage
from fastapi_mailman.config import ConnectionConfig

app = FastAPI(debug=True)

config = config = ConnectionConfig(
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

@app.get("/send-base")
async def send_base():
    msg = EmailMessage('this is subject', 'this is message', to=['aniketsarkar@yahoo.com'])
    await msg.send()
    return {"Hello": "World"}

@app.get("/send-mail")
async def check_send_mail():
    await mail.send_mail("this is subject", "this is message", None, ["aniketsarkar@yahoo.com"])
    return {"Hello": "World"}


if __name__ == "__main__":
    uv.run(app, port=8082, debug=True)
```
## 🚇 Development

#### 🧑‍💻 Contribution procedure.
1. Create a new issue on github.
2. Fork and clone this repository.
3. Make some changes as required.
4. Write unit test to showcase its functionality.
5. Submit a pull request under the `master` branch.

#### 🖨️ Run this project on your local machine.
To run this project on your local machine please [click here](https://marktennyson.github.io/fastapi-mailman/Contributing)

### ❤️ Contributors
Credits goes to these peoples:

<a href="https://github.com/marktennyson/fastapi-mailman/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=marktennyson/fastapi-mailman" />
</a>

## 📝 License

GNU General Public License v3 or later (GPLv3+)

Copyright (c) 2021 Aniket Sarkar(aniketsarkar@yahoo.com)
