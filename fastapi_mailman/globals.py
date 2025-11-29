"""Global state management for FastAPI-Mailman using contextvars."""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi_mailman import Mail

# Thread-safe context variable for the current Mail instance
_current_mailman: ContextVar[Mail | None] = ContextVar("current_mailman", default=None)


def get_mailman() -> Mail | None:
    """
    Get the current Mail instance from context.

    Returns:
        The current Mail instance or None if not set.
    """
    return _current_mailman.get()


def set_mailman(mailman: Mail | None) -> None:
    """
    Set the current Mail instance in context.

    Args:
        mailman: The Mail instance to set, or None to clear.
    """
    _current_mailman.set(mailman)


# Legacy alias for backward compatibility
# Will be deprecated in future versions
MAILMAN: Mail | None = None


def _get_global_mailman() -> Mail | None:
    """Get mailman from context or legacy global."""
    return get_mailman() or MAILMAN
