"""Base email backend class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi_mailman import Mail
    from fastapi_mailman.message import EmailMessage


class BaseEmailBackend(ABC):
    """
    Abstract base class for email backend implementations.

    Subclasses must implement the send_messages() method.
    Optionally, open() and close() can be overridden for connection management.

    The backend can be used as an async context manager:

        async with backend as connection:
            await connection.send_messages(messages)

    Attributes:
        fail_silently: Whether to suppress exceptions during sending.
        mailman: The Mail instance this backend is associated with.

    Example:
        ```python
        class CustomBackend(BaseEmailBackend):
            async def send_messages(self, email_messages):
                for message in email_messages:
                    # Custom sending logic here
                    pass
                return len(email_messages)
        ```
    """

    def __init__(
        self,
        mailman: Mail | None = None,
        fail_silently: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the email backend.

        Args:
            mailman: The Mail instance to use.
            fail_silently: Whether to suppress exceptions.
            **kwargs: Additional backend-specific arguments.

        Raises:
            RuntimeError: If mailman is not provided and not found in globals.
        """
        self.fail_silently = fail_silently
        if mailman is None:
            raise RuntimeError("The current application was not configured with Fastapi-Mailman")
        self.mailman = mailman

    async def open(self) -> bool | None:
        """
        Open a network connection.

        This method can be overridden by backend implementations to
        open a network connection. The default implementation does nothing.

        Returns:
            True if a new connection was opened, False if using existing,
            None if failed silently.
        """
        return None

    async def close(self) -> None:  # noqa: B027
        """
        Close the network connection.

        This method can be overridden by backend implementations.
        The default implementation does nothing (no-op).
        """

    async def __aenter__(self) -> BaseEmailBackend:
        """Async context manager entry."""
        try:
            await self.open()
        except Exception:
            await self.close()
            raise
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    @abstractmethod
    async def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """
        Send one or more EmailMessage objects.

        Args:
            email_messages: Sequence of EmailMessage instances to send.

        Returns:
            The number of email messages sent.

        Raises:
            NotImplementedError: If not overridden by subclass.
        """
        raise NotImplementedError("Subclasses of BaseEmailBackend must override send_messages()")
