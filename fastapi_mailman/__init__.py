"""
FastAPI-Mailman - Django-style email sending for FastAPI.

A production-ready email library for FastAPI applications, porting Django's
email implementation with full async support.

Example:
    ```python
    from fastapi import FastAPI
    from fastapi_mailman import Mail, EmailMessage
    from fastapi_mailman.config import ConnectionConfig

    app = FastAPI()

    config = ConnectionConfig(
        MAIL_USERNAME="user@example.com",
        MAIL_PASSWORD="secret",
        MAIL_SERVER="smtp.example.com",
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
    )
    mail = Mail(config)

    @app.get("/send")
    async def send_email():
        msg = EmailMessage(
            subject="Hello",
            body="This is the message",
            to=["recipient@example.com"],
        )
        await msg.send()
        return {"status": "sent"}
    ```
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from fastapi_mailman.errors import MailmanNotInitializedError
from fastapi_mailman.globals import _get_global_mailman, set_mailman
from fastapi_mailman.message import (
    DEFAULT_ATTACHMENT_MIME_TYPE,
    BadHeaderError,
    EmailMessage,
    EmailMultiAlternatives,
    SafeMIMEMultipart,
    SafeMIMEText,
    forbid_multi_line_headers,
    make_msgid,
)
from fastapi_mailman.utils import DNS_NAME, CachedDnsName

if TYPE_CHECKING:
    import types as ty
    from collections.abc import Sequence

    from fastapi_mailman.backends.base import BaseEmailBackend
    from fastapi_mailman.config import ConnectionConfig

__version__ = "1.0.0"

__all__ = [
    "DEFAULT_ATTACHMENT_MIME_TYPE",
    "DNS_NAME",
    "BadHeaderError",
    "CachedDnsName",
    "EmailMessage",
    "EmailMultiAlternatives",
    "Mail",
    "SafeMIMEMultipart",
    "SafeMIMEText",
    "__version__",
    "forbid_multi_line_headers",
    "make_msgid",
]

# Available built-in backends
AVAILABLE_BACKENDS = frozenset({"console", "dummy", "file", "smtp", "locmem"})


class _MailMixin:
    """Mixin providing email sending functionality."""

    def _get_backend_from_module(
        self,
        backend_module_name: str,
        backend_class_name: str,
    ) -> type[BaseEmailBackend]:
        """
        Import and return a backend class from a module.

        Args:
            backend_module_name: The module path to import from.
            backend_class_name: The class name to retrieve.

        Returns:
            The backend class.
        """
        backend_module: ty.ModuleType = import_module(backend_module_name)
        return getattr(backend_module, backend_class_name)  # type: ignore[no-any-return]

    def import_backend(self, backend_name: Any) -> type[BaseEmailBackend]:
        """
        Import and return an email backend class.

        Supports:
        - Short names: 'smtp', 'console', 'file', 'locmem', 'dummy'
        - Full module paths: 'fastapi_mailman.backends.smtp'
        - Full class paths: 'fastapi_mailman.backends.smtp.EmailBackend'
        - Direct class references

        Args:
            backend_name: The backend identifier.

        Returns:
            The backend class.
        """
        if not isinstance(backend_name, str):
            return backend_name  # type: ignore[no-any-return]

        default_backend_loc = "fastapi_mailman.backends"
        default_backend_class = "EmailBackend"

        if "." not in backend_name:
            backend_module_name = f"{default_backend_loc}.{backend_name}"
            return self._get_backend_from_module(backend_module_name, default_backend_class)

        if backend_name.endswith(default_backend_class):
            backend_module_name, backend_class_name = backend_name.rsplit(".", 1)
            return self._get_backend_from_module(backend_module_name, backend_class_name)

        return self._get_backend_from_module(backend_name, default_backend_class)

    def get_connection(
        self,
        backend: str | type[BaseEmailBackend] | None = None,
        fail_silently: bool = False,
        **kwargs: Any,
    ) -> BaseEmailBackend:
        """
        Load an email backend and return an instance.

        Args:
            backend: The backend to use. Defaults to the configured backend.
            fail_silently: Whether to suppress connection errors.
            **kwargs: Additional arguments passed to the backend constructor.

        Returns:
            An email backend instance.

        Raises:
            MailmanNotInitializedError: If Mail is not initialized.
            RuntimeError: If the backend cannot be imported.
        """
        mailman = _get_global_mailman()
        if mailman is None:
            raise MailmanNotInitializedError()

        try:
            backend = backend or mailman.backend
            klass = self.import_backend(backend)
        except ImportError as exc:
            raise RuntimeError(
                f"Unable to import backend: {backend}. "
                f"Available built-in backends: {', '.join(sorted(AVAILABLE_BACKENDS))}"
            ) from exc

        return klass(mailman=mailman, fail_silently=fail_silently, **kwargs)

    async def send_mail(
        self,
        subject: str,
        message: str,
        from_email: str | None = None,
        recipient_list: Sequence[str] | None = None,
        fail_silently: bool = False,
        auth_user: str | None = None,
        auth_password: str | None = None,
        connection: BaseEmailBackend | None = None,
        html_message: str | None = None,
    ) -> int:
        """
        Send a single email message.

        This is a convenience wrapper for sending a single message to a
        recipient list. All members of the recipient list will see the
        other recipients in the 'To' field.

        Args:
            subject: The email subject.
            message: The email body (plain text).
            from_email: Sender's email. Defaults to MAIL_DEFAULT_SENDER.
            recipient_list: List of recipient emails.
            fail_silently: Whether to suppress sending errors.
            auth_user: SMTP auth username. Defaults to MAIL_USERNAME.
            auth_password: SMTP auth password. Defaults to MAIL_PASSWORD.
            connection: Reuse an existing connection.
            html_message: Optional HTML version of the message.

        Returns:
            Number of emails sent (0 or 1).

        Raises:
            MailmanNotInitializedError: If Mail is not initialized.
        """
        mailman = _get_global_mailman()
        if mailman is None:
            raise MailmanNotInitializedError()

        connection = connection or self.get_connection(
            username=auth_user,
            password=auth_password,
            fail_silently=fail_silently,
        )

        mail = EmailMultiAlternatives(
            subject,
            message,
            from_email,
            list(recipient_list) if recipient_list else [],
            connection=connection,
            mailman=mailman,
        )

        if html_message:
            mail.attach_alternative(html_message, "text/html")

        return await mail.send()

    async def send_mass_mail(
        self,
        datatuple: Sequence[tuple[str, str, str, Sequence[str]]],
        fail_silently: bool = False,
        auth_user: str | None = None,
        auth_password: str | None = None,
        connection: BaseEmailBackend | None = None,
    ) -> int:
        """
        Send multiple email messages efficiently.

        Given a datatuple of (subject, message, from_email, recipient_list),
        send each message to each recipient list using a single connection.

        Args:
            datatuple: Sequence of (subject, message, from_email, recipient_list).
            fail_silently: Whether to suppress sending errors.
            auth_user: SMTP auth username.
            auth_password: SMTP auth password.
            connection: Reuse an existing connection.

        Returns:
            Number of emails sent.

        Raises:
            MailmanNotInitializedError: If Mail is not initialized.

        Note:
            This API is frozen. For extending functionality, use
            EmailMessage directly.
        """
        mailman = _get_global_mailman()
        if mailman is None:
            raise MailmanNotInitializedError()

        connection = connection or self.get_connection(
            username=auth_user,
            password=auth_password,
            fail_silently=fail_silently,
        )

        messages = [
            EmailMessage(
                subject,
                message,
                sender,
                list(recipient),
                connection=connection,
                mailman=mailman,
            )
            for subject, message, sender, recipient in datatuple
        ]

        return await connection.send_messages(messages)


class Mail(_MailMixin):
    """
    Main email management class for FastAPI-Mailman.

    Manages email configuration and provides methods for sending emails.
    On initialization, registers itself as the global mailman instance.

    Attributes:
        config: The connection configuration.
        server: SMTP server hostname.
        port: SMTP server port.
        username: SMTP authentication username.
        password: SMTP authentication password.
        use_tls: Whether to use STARTTLS.
        use_ssl: Whether to use SSL/TLS.
        default_sender: Default sender email address.
        timeout: Connection timeout in seconds.
        ssl_keyfile: Path to SSL key file.
        ssl_certfile: Path to SSL certificate file.
        use_localtime: Whether to use local time in headers.
        file_path: Directory for file backend storage.
        default_charset: Default character encoding.
        backend: Email backend to use.

    Example:
        ```python
        from fastapi_mailman import Mail
        from fastapi_mailman.config import ConnectionConfig

        config = ConnectionConfig(
            MAIL_USERNAME="user@example.com",
            MAIL_PASSWORD="secret",
            MAIL_SERVER="smtp.example.com",
            MAIL_PORT=587,
            MAIL_USE_TLS=True,
        )

        mail = Mail(config)

        # Send via helper method
        await mail.send_mail(
            subject="Hello",
            message="World",
            recipient_list=["recipient@example.com"],
        )

        # Or use EmailMessage directly
        msg = EmailMessage(subject="Hello", body="World", to=["recipient@example.com"])
        await msg.send()
        ```
    """

    def __init__(self, config: ConnectionConfig) -> None:
        """
        Initialize the Mail instance.

        Args:
            config: ConnectionConfig instance with email settings.
        """
        self.config = config
        self._init_from_config(config)
        set_mailman(self)

    def _init_from_config(self, config: ConnectionConfig) -> None:
        """Initialize attributes from configuration."""
        config_dict = config.model_dump()

        self.server: str = config_dict["MAIL_SERVER"]
        self.port: int = config_dict["MAIL_PORT"]
        self.username: str = config_dict["MAIL_USERNAME"]
        self.password: str = config_dict["MAIL_PASSWORD"]
        self.use_tls: bool = config_dict["MAIL_USE_TLS"]
        self.use_ssl: bool = config_dict["MAIL_USE_SSL"]
        self.default_sender: str | None = config_dict["MAIL_DEFAULT_SENDER"]
        self.timeout: int | None = config_dict["MAIL_TIMEOUT"]
        self.ssl_keyfile: str | None = config_dict["MAIL_SSL_KEYFILE"]
        self.ssl_certfile: str | None = config_dict["MAIL_SSL_CERTFILE"]
        self.use_localtime: bool = config_dict["MAIL_USE_LOCALTIME"]
        self.file_path: str | None = config_dict["MAIL_FILE_PATH"]
        self.default_charset: str = config_dict["MAIL_DEFAULT_CHARSET"]
        self.backend: str = config_dict["MAIL_BACKEND"]

    def __repr__(self) -> str:
        return f"<Mail server={self.server!r} port={self.port}>"
