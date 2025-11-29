"""
Email backends for FastAPI-Mailman.

Available backends:
- smtp: Send emails via SMTP server (default)
- console: Print emails to stdout (development)
- file: Write emails to files (development/testing)
- locmem: Store emails in memory (testing)
- dummy: Discard emails (testing)
"""

from fastapi_mailman.backends.base import BaseEmailBackend
from fastapi_mailman.backends.console import EmailBackend as ConsoleEmailBackend
from fastapi_mailman.backends.dummy import EmailBackend as DummyEmailBackend
from fastapi_mailman.backends.file import EmailBackend as FileEmailBackend
from fastapi_mailman.backends.locmem import EmailBackend as LocMemEmailBackend
from fastapi_mailman.backends.smtp import EmailBackend as SMTPEmailBackend

__all__ = [
    "BaseEmailBackend",
    "ConsoleEmailBackend",
    "DummyEmailBackend",
    "FileEmailBackend",
    "LocMemEmailBackend",
    "SMTPEmailBackend",
]
