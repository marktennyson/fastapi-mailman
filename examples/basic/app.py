"""
FastAPI-Mailman Basic Example

This example demonstrates basic email sending functionality with FastAPI-Mailman.

To run:
1. Copy .env.example to .env and fill in your SMTP credentials
2. Install dependencies: pip install fastapi-mailman uvicorn python-dotenv
3. Run: uvicorn app:app --reload
4. Visit: http://localhost:8000/docs
"""

from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from fastapi_mailman import EmailMessage, EmailMultiAlternatives, Mail
from fastapi_mailman.config import ConnectionConfig

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="FastAPI-Mailman Example",
    description="Example email sending API",
    version="1.0.0",
)

# Configure email
config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "true").lower() == "true",
    MAIL_USE_SSL=os.getenv("MAIL_USE_SSL", "false").lower() == "true",
    MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME", "")),
)

# Initialize Mail
mail = Mail(config)


# Request/Response Models
class EmailRequest(BaseModel):
    """Email request model."""

    to: list[EmailStr]
    subject: str
    body: str
    html_body: str | None = None


class EmailResponse(BaseModel):
    """Email response model."""

    success: bool
    message: str


# Routes
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "FastAPI-Mailman Example API", "docs": "/docs"}


@app.post("/send-simple", response_model=EmailResponse)
async def send_simple_email(request: EmailRequest) -> EmailResponse:
    """
    Send a simple email using the helper method.

    This is the easiest way to send emails.
    """
    try:
        await mail.send_mail(
            subject=request.subject,
            message=request.body,
            recipient_list=request.to,
            html_message=request.html_body,
        )
        return EmailResponse(success=True, message="Email sent successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-message", response_model=EmailResponse)
async def send_email_message(request: EmailRequest) -> EmailResponse:
    """
    Send an email using EmailMessage class directly.

    This provides more control over the email.
    """
    try:
        msg = EmailMessage(
            subject=request.subject,
            body=request.body,
            to=request.to,
        )
        await msg.send()
        return EmailResponse(success=True, message="Email sent successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-html", response_model=EmailResponse)
async def send_html_email(request: EmailRequest) -> EmailResponse:
    """
    Send an email with both plain text and HTML versions.

    Uses EmailMultiAlternatives for multipart/alternative emails.
    """
    try:
        msg = EmailMultiAlternatives(
            subject=request.subject,
            body=request.body,
            to=request.to,
        )

        if request.html_body:
            msg.attach_alternative(request.html_body, "text/html")

        await msg.send()
        return EmailResponse(success=True, message="HTML email sent successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-mass", response_model=EmailResponse)
async def send_mass_email() -> EmailResponse:
    """
    Send multiple emails efficiently using a single connection.

    Demonstrates send_mass_mail functionality.
    """
    try:
        messages = [
            ("Welcome!", "Welcome to our service.", mail.default_sender, ["user1@example.com"]),
            ("Newsletter", "Latest updates...", mail.default_sender, ["user2@example.com"]),
        ]

        count = await mail.send_mass_mail(messages, fail_silently=True)
        return EmailResponse(success=True, message=f"Sent {count} emails")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
