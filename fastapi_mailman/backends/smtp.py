"""SMTP email backend using aiosmtplib."""

from __future__ import annotations

import asyncio
import ssl
from typing import TYPE_CHECKING, Any

import aiosmtplib

from fastapi_mailman.backends.base import BaseEmailBackend
from fastapi_mailman.message import sanitize_address

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi_mailman.message import EmailMessage


class EmailBackend(BaseEmailBackend):
    """
    SMTP email backend using aiosmtplib for async email sending.

    This backend manages connections to an SMTP server and handles
    authentication, TLS/SSL encryption, and message sending.

    Attributes:
        host: SMTP server hostname.
        port: SMTP server port.
        username: Authentication username.
        password: Authentication password.
        use_tls: Whether to use STARTTLS.
        use_ssl: Whether to use SSL/TLS.
        timeout: Connection timeout in seconds.
        ssl_keyfile: Path to SSL key file.
        ssl_certfile: Path to SSL certificate file.

    Example:
        ```python
        async with mail.get_connection() as conn:
            await conn.send_messages([message])
        ```
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool | None = None,
        fail_silently: bool = False,
        use_ssl: bool | None = None,
        timeout: int | None = None,
        ssl_keyfile: str | None = None,
        ssl_certfile: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the SMTP backend.

        Args:
            host: SMTP server hostname.
            port: SMTP server port.
            username: Authentication username.
            password: Authentication password.
            use_tls: Enable STARTTLS.
            fail_silently: Whether to suppress exceptions.
            use_ssl: Enable SSL/TLS.
            timeout: Connection timeout in seconds.
            ssl_keyfile: Path to SSL key file.
            ssl_certfile: Path to SSL certificate file.
            **kwargs: Additional arguments for BaseEmailBackend.

        Raises:
            ValueError: If both use_tls and use_ssl are True.
        """
        super().__init__(fail_silently=fail_silently, **kwargs)

        self.host = host or self.mailman.server
        self.port = port or self.mailman.port
        self.username = username if username is not None else self.mailman.username
        self.password = password if password is not None else self.mailman.password
        self.use_tls = use_tls if use_tls is not None else self.mailman.use_tls
        self.use_ssl = use_ssl if use_ssl is not None else self.mailman.use_ssl
        self.timeout = timeout if timeout is not None else self.mailman.timeout
        self.ssl_keyfile = ssl_keyfile if ssl_keyfile is not None else self.mailman.ssl_keyfile
        self.ssl_certfile = ssl_certfile if ssl_certfile is not None else self.mailman.ssl_certfile

        if self.use_ssl and self.use_tls:
            raise ValueError("MAIL_USE_TLS and MAIL_USE_SSL are mutually exclusive. Set only one of them to True.")

        self.connection: aiosmtplib.SMTP | None = None
        self._lock = asyncio.Lock()

    @property
    def connection_class(self) -> type[aiosmtplib.SMTP]:
        """Return the SMTP connection class."""
        return aiosmtplib.SMTP

    async def open(self) -> bool | None:
        """
        Open a connection to the SMTP server.

        Returns:
            True if a new connection was created, False if already connected,
            None if connection failed silently.
        """
        if self.connection:
            return False

        connection_params: dict[str, Any] = {}

        if self.timeout is not None:
            connection_params["timeout"] = self.timeout

        if self.use_ssl:
            connection_params.update(
                {
                    "tls_context": self._create_ssl_context(),
                    "use_tls": True,
                }
            )

        try:
            self.connection = self.connection_class(
                hostname=self.host,
                port=self.port,
                **connection_params,
            )

            await self.connection.connect()

            # STARTTLS over non-secure connection
            if not self.use_ssl and self.use_tls:
                await self.connection.starttls(tls_context=self._create_ssl_context())

            if self.username and self.password:
                await self.connection.login(self.username, self.password)

            return True

        except OSError:
            if not self.fail_silently:
                raise
            return None

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create an SSL context for TLS connections."""
        context = ssl.create_default_context()
        if self.ssl_certfile:
            context.load_cert_chain(
                certfile=self.ssl_certfile,
                keyfile=self.ssl_keyfile,
            )
        return context

    async def close(self) -> None:
        """Close the connection to the SMTP server."""
        if self.connection is None:
            return

        try:
            try:
                await self.connection.quit()
            except (ssl.SSLError, aiosmtplib.SMTPServerDisconnected):
                # Connection already closed by server or SSL issue
                self.connection.close()
            except aiosmtplib.SMTPException:
                if not self.fail_silently:
                    raise
        finally:
            self.connection = None

    async def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """
        Send one or more EmailMessage objects.

        Args:
            email_messages: Sequence of EmailMessage instances to send.

        Returns:
            The number of email messages successfully sent.
        """
        if not email_messages:
            return 0

        async with self._lock:
            new_conn_created = await self.open()

            if not self.connection or new_conn_created is None:
                # Failed silently on open()
                return 0

            num_sent = 0
            for message in email_messages:
                sent = await self._send(message)
                if sent:
                    num_sent += 1

            if new_conn_created:
                await self.close()

        return num_sent

    async def _send(self, email_message: EmailMessage) -> bool:
        """
        Send a single email message.

        Args:
            email_message: The EmailMessage to send.

        Returns:
            True if sent successfully, False otherwise.
        """
        if not email_message.recipients():
            return False

        encoding = email_message.encoding or self.mailman.default_charset
        from_email = sanitize_address(email_message.from_email or "", encoding)
        recipients = [sanitize_address(addr, encoding) for addr in email_message.recipients()]
        message = email_message.message()

        try:
            await self.connection.sendmail(  # type: ignore[union-attr]
                from_email,
                recipients,
                message.as_bytes(linesep="\r\n"),
            )
        except aiosmtplib.SMTPException:
            if not self.fail_silently:
                raise
            return False

        return True
