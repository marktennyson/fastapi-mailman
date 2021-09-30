"""Base email backend class."""


class BaseEmailBackend:
    """
    Base class for email backend implementations.

    Subclasses must at least overwrite send_messages().

    open() and close() can be called indirectly by using a backend object as a
    context manager:

       with backend as connection:
           # do something with connection
           pass
    """

    def __init__(self, mailman=None, fail_silently=False, **kwargs):
        self.fail_silently = fail_silently
        try:
            self.mailman = mailman
        except KeyError:
            raise RuntimeError("The current application was not configured with Fastapi-Mailman")

    async def open(self):
        """
        Open a network connection.

        This method can be overwritten by backend implementations to
        open a network connection.

        It's up to the backend implementation to track the status of
        a network connection if it's needed by the backend.

        This method can be called by applications to force a single
        network connection to be used when sending mails. See the
        send_messages() method of the SMTP backend for a reference
        implementation.

        The default implementation does nothing.
        """
        pass

    async def close(self):
        """Close a network connection."""
        pass

    async def __aenter__(self):
        try:
            await self.open()
        except Exception:
            await self.close()
            raise
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        raise NotImplementedError('subclasses of BaseEmailBackend must override send_messages() method')
