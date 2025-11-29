"""File email backend - writes messages to files."""

from __future__ import annotations

import os
import random
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi_mailman.backends.console import EmailBackend as ConsoleEmailBackend
from fastapi_mailman.errors import ImproperlyConfiguredError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from io import BufferedWriter

    from fastapi_mailman.message import EmailMessage


class EmailBackend(ConsoleEmailBackend):
    """
    Email backend that writes messages to files.

    Each email session creates a new file with a unique timestamp-based name.
    Useful for development and testing when you want to inspect sent emails.

    Attributes:
        file_path: Directory where email files are stored.

    Example:
        ```python
        mail = Mail(config)
        mail.backend = "file"
        mail.file_path = "/tmp/emails"

        # Messages will be written to /tmp/emails/
        await mail.send_mail("Test", "Hello", to=["test@example.com"])
        ```
    """

    def __init__(
        self,
        *args: Any,
        file_path: str | Path | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the file backend.

        Args:
            *args: Arguments for parent class.
            file_path: Directory to store email files.
            **kwargs: Keyword arguments for parent class.

        Raises:
            ImproperlyConfiguredError: If the directory cannot be created or accessed.
        """
        # Force stream to None since we'll use files
        kwargs["stream"] = None
        super().__init__(*args, **kwargs)

        self._fname: str | None = None
        self._file_stream: BufferedWriter | None = None

        # Get file path from argument or mailman config
        self.file_path = Path(file_path if file_path is not None else self.mailman.file_path or "")
        self.file_path = self.file_path.resolve()

        try:
            self.file_path.mkdir(parents=True, exist_ok=True)
        except FileExistsError as err:
            raise ImproperlyConfiguredError(
                f"Path for saving email messages exists but is not a directory: {self.file_path}"
            ) from err
        except OSError as err:
            raise ImproperlyConfiguredError(
                f"Could not create directory for saving email messages: {self.file_path} ({err})"
            ) from err

        if not os.access(self.file_path, os.W_OK):
            raise ImproperlyConfiguredError(f"Could not write to directory: {self.file_path}")

    def write_message(self, message: EmailMessage) -> None:
        """
        Write a single message to the file.

        Args:
            message: The EmailMessage to write.
        """
        if self._file_stream:
            self._file_stream.write(message.message().as_bytes() + b"\n")
            self._file_stream.write(b"-" * 79)
            self._file_stream.write(b"\n")

    def _get_filename(self) -> str:
        """
        Generate a unique filename for the current email session.

        Returns:
            The full path to the email file.
        """
        if self._fname is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            random_suffix = random.randrange(10**15)
            fname = f"{timestamp}-{random_suffix}.log"
            self._fname = str(self.file_path / fname)
        return self._fname

    async def open(self) -> bool:
        """
        Open the file for writing.

        Returns:
            True if a new file was opened, False if already open.
        """
        if self._file_stream is None:
            self._file_stream = Path(self._get_filename()).open("ab")  # noqa: SIM115
            return True
        return False

    async def close(self) -> None:
        """Close the file if open."""
        try:
            if self._file_stream is not None:
                self._file_stream.close()
        finally:
            self._file_stream = None

    async def send_messages(self, email_messages: Sequence[EmailMessage]) -> int:
        """
        Write all messages to a file.

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
                    if self._file_stream:
                        self._file_stream.flush()
                    msg_count += 1

                if stream_created:
                    await self.close()

            except Exception:
                if not self.fail_silently:
                    raise

        return msg_count
