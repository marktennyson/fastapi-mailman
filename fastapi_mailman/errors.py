"""Custom exceptions for FastAPI-Mailman."""

from __future__ import annotations


class MailmanError(Exception):
    """Base exception for all FastAPI-Mailman errors."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


class ConnectionError(MailmanError):
    """Raised when there's an issue with the email server connection."""

    pass


class ConfigurationError(MailmanError):
    """Raised when the configuration is invalid or incomplete."""

    pass


class MailmanNotInitializedError(MailmanError):
    """Raised when trying to send email before Mail is initialized."""

    def __init__(self, message: str = "Mail instance has not been initialized yet.") -> None:
        super().__init__(message)


class InvalidFileError(MailmanError):
    """Raised when an invalid file is provided as an attachment."""

    pass


class TemplateFolderNotFoundError(MailmanError):
    """Raised when the template folder does not exist or is inaccessible."""

    pass


class BadHeaderError(ValueError):
    """Raised when email headers contain invalid characters (e.g., newlines)."""

    pass


class ImproperlyConfiguredError(MailmanError):
    """Raised when the application is improperly configured."""

    pass


# Legacy aliases for backward compatibility
ConnectionErrors = ConnectionError
WrongFile = InvalidFileError
PydanticClassRequired = ConfigurationError
TemplateFolderDoesNotExist = TemplateFolderNotFoundError
