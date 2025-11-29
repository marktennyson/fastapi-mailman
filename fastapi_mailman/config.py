"""Configuration settings for FastAPI-Mailman."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003

from jinja2 import Environment, FileSystemLoader
from pydantic import EmailStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConnectionConfig(BaseSettings):
    """
    Email connection configuration settings.

    This class uses Pydantic v2 settings for configuration management,
    supporting both direct instantiation and environment variable loading.

    Attributes:
        MAIL_USERNAME: SMTP authentication username.
        MAIL_PASSWORD: SMTP authentication password.
        MAIL_BACKEND: Email backend to use (smtp, console, file, locmem, dummy).
        MAIL_SERVER: SMTP server hostname.
        MAIL_PORT: SMTP server port (default: 587 for TLS, 465 for SSL).
        MAIL_USE_TLS: Enable STARTTLS encryption.
        MAIL_USE_SSL: Enable SSL/TLS encryption.
        MAIL_DEFAULT_SENDER: Default sender email address.
        TEMPLATE_FOLDER: Path to email templates directory.
        MAIL_SSL_KEYFILE: Path to SSL key file.
        MAIL_SSL_CERTFILE: Path to SSL certificate file.
        MAIL_USE_LOCALTIME: Use local time in email headers.
        MAIL_FILE_PATH: Directory for file backend email storage.
        MAIL_TIMEOUT: Connection timeout in seconds.
        MAIL_DEFAULT_CHARSET: Default character encoding for emails.

    Example:
        ```python
        config = ConnectionConfig(
            MAIL_USERNAME="user@example.com",
            MAIL_PASSWORD="secret",
            MAIL_SERVER="smtp.example.com",
            MAIL_PORT=587,
            MAIL_USE_TLS=True,
        )
        ```
    """

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        extra="ignore",
    )

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_BACKEND: str = "smtp"
    MAIL_SERVER: str
    MAIL_PORT: int = 587
    MAIL_USE_TLS: bool = False
    MAIL_USE_SSL: bool = False
    MAIL_DEFAULT_SENDER: EmailStr | None = None
    TEMPLATE_FOLDER: Path | None = None
    MAIL_SSL_KEYFILE: str | None = None
    MAIL_SSL_CERTFILE: str | None = None
    MAIL_USE_LOCALTIME: bool = False
    MAIL_FILE_PATH: str | None = None
    MAIL_TIMEOUT: int | None = None
    MAIL_DEFAULT_CHARSET: str = "utf-8"

    @field_validator("MAIL_BACKEND", mode="before")
    @classmethod
    def validate_backend(cls, v: str | None) -> str:
        """Validate and set default backend."""
        return v or "smtp"

    @model_validator(mode="after")
    def validate_tls_ssl(self) -> ConnectionConfig:
        """Ensure TLS and SSL are not both enabled."""
        if self.MAIL_USE_TLS and self.MAIL_USE_SSL:
            raise ValueError("MAIL_USE_TLS and MAIL_USE_SSL are mutually exclusive")
        return self

    @model_validator(mode="after")
    def set_default_sender(self) -> ConnectionConfig:
        """Set default sender to username if not provided."""
        if self.MAIL_DEFAULT_SENDER is None:
            # Use object.__setattr__ since model is frozen after validation
            object.__setattr__(self, "MAIL_DEFAULT_SENDER", self.MAIL_USERNAME)
        return self

    def template_engine(self) -> Environment:
        """
        Create and return a Jinja2 template environment.

        Returns:
            Jinja2 Environment configured with the template folder.

        Raises:
            ValueError: If TEMPLATE_FOLDER was not configured.

        Example:
            ```python
            config = ConnectionConfig(
                MAIL_USERNAME="user@example.com",
                MAIL_PASSWORD="secret",
                MAIL_SERVER="smtp.example.com",
                TEMPLATE_FOLDER=Path("./templates"),
            )
            env = config.template_engine()
            template = env.get_template("welcome.html")
            ```
        """
        if not self.TEMPLATE_FOLDER:
            raise ValueError(
                "TEMPLATE_FOLDER must be set to use template_engine(). "
                "Provide a valid directory path when initializing ConnectionConfig."
            )
        return Environment(
            loader=FileSystemLoader(self.TEMPLATE_FOLDER),
            autoescape=True,
        )
