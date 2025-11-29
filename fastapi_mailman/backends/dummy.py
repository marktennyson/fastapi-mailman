"""Dummy email backend - discards all messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi_mailman.backends.base import BaseEmailBackend

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi_mailman.message import EmailMessage


class EmailBackend(BaseEmailBackend):
    """
    Dummy email backend that discards all messages.

    Useful for testing when you don't want to actually send emails
    but still want the sending code to execute.

    Example:
        ```python
        mail = Mail(config)
        mail.backend = "dummy"

        # Messages will be discarded
        await mail.send_mail("Test", "Hello", to=["test@example.com"])
        ```
    """

    async def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """
        Pretend to send messages (actually discards them).

        Args:
            email_messages: Sequence of EmailMessage instances.

        Returns:
            The number of messages that would have been sent.
        """
        return len(list(email_messages))
