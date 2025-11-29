"""Console email backend - writes messages to stdout."""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING, Any, TextIO

from fastapi_mailman.backends.base import BaseEmailBackend

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi_mailman.message import EmailMessage


class EmailBackend(BaseEmailBackend):
    """
    Email backend that writes messages to a stream (stdout by default).

    Useful for development and debugging purposes.

    Attributes:
        stream: The output stream to write messages to.

    Example:
        ```python
        mail = Mail(config)
        mail.backend = "console"

        # Messages will be printed to stdout
        await mail.send_mail("Test", "Hello", to=["test@example.com"])
        ```
    """

    def __init__(
        self,
        *args: Any,
        stream: TextIO | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the console backend.

        Args:
            *args: Arguments for BaseEmailBackend.
            stream: Output stream (defaults to sys.stdout).
            **kwargs: Keyword arguments for BaseEmailBackend.
        """
        self.stream: TextIO = stream or sys.stdout
        self._lock = asyncio.Lock()
        super().__init__(*args, **kwargs)

    def write_message(self, message: EmailMessage) -> None:
        """
        Write a single message to the stream.

        Args:
            message: The EmailMessage to write.
        """
        msg = message.message()
        msg_data = msg.as_bytes()
        charset = msg.get_charset()
        output_charset = charset.get_output_charset() if charset and hasattr(charset, "get_output_charset") else "utf-8"
        msg_str = msg_data.decode(output_charset or "utf-8")

        self.stream.write(f"{msg_str}\n")
        self.stream.write("-" * 79)
        self.stream.write("\n")

    async def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """
        Write all messages to the stream.

        Args:
            email_messages: Sequence of EmailMessage instances.

        Returns:
            The number of messages written.
        """
        if not email_messages:
            return 0

        msg_count = 0

        async with self._lock:
            try:
                stream_created = await self.open()

                for message in email_messages:
                    self.write_message(message)
                    self.stream.flush()
                    msg_count += 1

                if stream_created:
                    await self.close()

            except Exception:
                if not self.fail_silently:
                    raise

        return msg_count
