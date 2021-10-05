"""SMTP email backend class."""
import ssl
import threading
import typing as t

import aiosmtplib

from fastapi_mailman.backends.base import BaseEmailBackend
from fastapi_mailman.message import sanitize_address


class EmailBackend(BaseEmailBackend):
    """
    A wrapper that manages the SMTP network connection.
    """

    def __init__(
        self,
        host=None,
        port=None,
        username=None,
        password=None,
        use_tls=None,
        fail_silently=False,
        use_ssl=None,
        timeout=None,
        ssl_keyfile=None,
        ssl_certfile=None,
        **kwargs,
    ):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.host = host or self.mailman.server
        self.port = port or self.mailman.port
        self.username = self.mailman.username if username is None else username
        self.password = self.mailman.password if password is None else password
        self.use_tls = self.mailman.use_tls if use_tls is None else use_tls
        self.use_ssl = self.mailman.use_ssl if use_ssl is None else use_ssl
        self.timeout = self.mailman.timeout if timeout is None else timeout
        self.ssl_keyfile = self.mailman.ssl_keyfile if ssl_keyfile is None else ssl_keyfile
        self.ssl_certfile = self.mailman.ssl_certfile if ssl_certfile is None else ssl_certfile
        if self.use_ssl and self.use_tls:
            raise ValueError(
                "EMAIL_USE_TLS/EMAIL_USE_SSL are mutually exclusive, so only set " "one of those settings to True."
            )
        self.connection = None
        self._lock = threading.RLock()

    @property
    def connection_class(self) -> t.Type["aiosmtplib.SMTP"]:
        return aiosmtplib.SMTP

    async def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a
        new connection was required (True or False) or None if an exception
        passed silently.
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False

        # If local_hostname is not specified, socket.getfqdn() gets used.
        # For performance, we use the cached FQDN for local_hostname.
        # connection_params = {'local_hostname': DNS_NAME.get_fqdn()}
        connection_params = dict()
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        if self.use_ssl:
            connection_params.update(
                {
                    'client_key': self.ssl_keyfile,
                    'client_cert': self.ssl_certfile,
                }
            )
        try:
            self.connection = self.connection_class(self.host, self.port, **connection_params)
            # TLS/SSL are mutually exclusive, so only attempt TLS over
            # non-secure connections.
            await self.connection.connect()

            if not self.use_ssl and self.use_tls:
                await self.connection.starttls(client_key=self.ssl_keyfile, client_cert=self.ssl_certfile)

            if self.username and self.password:
                await self.connection.login(self.username, self.password)

            return True

        except OSError:
            if not self.fail_silently:
                raise

    async def close(self):
        """Close the connection to the email server."""
        if self.connection is None:
            return
        try:
            try:
                await self.connection.quit()
            except (ssl.SSLError, aiosmtplib.SMTPServerDisconnected):
                # This happens when calling quit() on a TLS connection
                # sometimes, or when the connection was already disconnected
                # by the server.
                self.connection.close()
            except aiosmtplib.SMTPException:
                if self.fail_silently:
                    return
                raise
        finally:
            self.connection = None

    async def send_messages(self, email_messages) -> int:
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages:
            return 0
        with self._lock:
            new_conn_created = await self.open()
            if not self.connection or new_conn_created is None:
                # We failed silently on open().
                # Trying to send would be pointless.
                return 0
            num_sent = 0
            for message in email_messages:
                sent = await self._send(message)
                if sent:
                    num_sent += 1
            if new_conn_created:
                await self.close()
        return num_sent

    async def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or self.mailman.default_charset
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = [sanitize_address(addr, encoding) for addr in email_message.recipients()]
        message = email_message.message()
        try:
            await self.connection.sendmail(from_email, recipients, message.as_bytes(linesep='\r\n'))
        except aiosmtplib.SMTPException:
            if not self.fail_silently:
                raise
            return False
        return True
