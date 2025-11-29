"""Email message and email sending related helper functions."""

from __future__ import annotations

import socket
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any


class CachedDnsName:
    """
    Lazy-loading cached DNS name for email headers.

    The hostname is cached on first access to avoid the performance
    penalty of repeated socket.getfqdn() calls.
    """

    _fqdn: str | None = None

    def __str__(self) -> str:
        """Return the fully qualified domain name."""
        return self.get_fqdn()

    def __repr__(self) -> str:
        """Return a representation of the cached DNS name."""
        return f"CachedDnsName(fqdn={self.get_fqdn()!r})"

    def get_fqdn(self) -> str:
        """
        Get the fully qualified domain name.

        Returns:
            The cached FQDN string.
        """
        if self._fqdn is None:
            self._fqdn = socket.getfqdn()
        return self._fqdn


# Global cached DNS name instance
DNS_NAME = CachedDnsName()


class FastapiUnicodeDecodeError(UnicodeDecodeError):
    """Enhanced UnicodeDecodeError with better error messages."""

    def __init__(self, obj: Any, *args: Any) -> None:
        self.obj = obj
        super().__init__(*args)

    def __str__(self) -> str:
        return f"{super().__str__()}. You passed in {self.obj!r} ({type(self.obj)})"


# Types that should not be converted to strings
_PROTECTED_TYPES: tuple[type, ...] = (
    type(None),
    int,
    float,
    Decimal,
    datetime,
    date,
    time,
)


def is_protected_type(obj: Any) -> bool:
    """
    Determine if the object instance is of a protected type.

    Objects of protected types are preserved as-is when passed to
    force_str(strings_only=True).

    Args:
        obj: The object to check.

    Returns:
        True if the object is a protected type, False otherwise.
    """
    return isinstance(obj, _PROTECTED_TYPES)


def force_str(
    s: Any,
    encoding: str = "utf-8",
    strings_only: bool = False,
    errors: str = "strict",
) -> str:
    """
    Convert a value to a string.

    Similar to smart_str(), except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    Args:
        s: The value to convert.
        encoding: The encoding to use for bytes objects.
        strings_only: If True, don't convert protected types.
        errors: Error handling scheme for decoding.

    Returns:
        The string representation of the value.

    Raises:
        FastapiUnicodeDecodeError: If decoding fails.
    """
    # Handle the common case first for performance
    if isinstance(s, str):
        return s

    if strings_only and is_protected_type(s):
        return s  # type: ignore[return-value, no-any-return]

    try:
        if isinstance(s, bytes):
            return s.decode(encoding, errors)
        # str() always returns str, regardless of input type
        result: str = str(s)
        return result
    except UnicodeDecodeError as e:
        raise FastapiUnicodeDecodeError(s, *e.args) from e


def punycode(domain: str) -> str:
    """
    Return the Punycode representation of a domain if it contains non-ASCII characters.

    Args:
        domain: The domain name to encode.

    Returns:
        The Punycode-encoded domain string.

    Example:
        >>> punycode("münchen.de")
        "xn--mnchen-3ya.de"
        >>> punycode("example.com")
        "example.com"
    """
    return domain.encode("idna").decode("ascii")
