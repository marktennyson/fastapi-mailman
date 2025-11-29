"""In-memory email backend for testing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi_mailman.backends.base import BaseEmailBackend

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fastapi_mailman.message import EmailMessage


class EmailBackend(BaseEmailBackend):
    """
    Email backend that stores messages in memory.

    Messages are stored in the mailman.outbox attribute, making it easy
    to inspect sent messages in tests.

    Attributes:
        mailman.outbox: List of sent EmailMessage instances.

    Example:
        ```python
        mail = Mail(config)
        mail.backend = "locmem"

        await mail.send_mail("Test", "Hello", to=["test@example.com"])

        # Inspect sent messages
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Test"
        ```
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the in-memory backend.

        Creates an outbox list on the mailman instance if it doesn't exist.
        """
        super().__init__(*args, **kwargs)

        if not hasattr(self.mailman, "outbox"):
            self.mailman.outbox = []  # type: ignore[attr-defined]

    async def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """
        Store messages in the outbox.

        Also triggers message() to validate headers.

        Args:
            email_messages: Sequence of EmailMessage instances.

        Returns:
            The number of messages stored.
        """
        msg_count = 0

        for message in email_messages:
            # Trigger header validation
            message.message()
            self.mailman.outbox.append(message)  # type: ignore[attr-defined]
            msg_count += 1

        return msg_count
