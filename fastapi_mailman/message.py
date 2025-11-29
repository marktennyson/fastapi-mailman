"""Email message classes for FastAPI-Mailman."""

from __future__ import annotations

import mimetypes
from email import charset as Charset, encoders as Encoders, generator, message_from_string
from email.errors import HeaderParseError
from email.header import Header
from email.headerregistry import Address
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.message import MIMEMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, getaddresses, make_msgid
from io import BytesIO, StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi_mailman.errors import BadHeaderError, MailmanNotInitializedError
from fastapi_mailman.globals import _get_global_mailman
from fastapi_mailman.utils import DNS_NAME, force_str, punycode

if TYPE_CHECKING:
    from fastapi_mailman import Mail
    from fastapi_mailman.backends.base import BaseEmailBackend

__all__ = [
    "ADDRESS_HEADERS",
    "DEFAULT_ATTACHMENT_MIME_TYPE",
    "RFC5322_EMAIL_LINE_LENGTH_LIMIT",
    "BadHeaderError",
    "EmailMessage",
    "EmailMultiAlternatives",
    "SafeMIMEMessage",
    "SafeMIMEMultipart",
    "SafeMIMEText",
    "forbid_multi_line_headers",
    "make_msgid",
    "sanitize_address",
]

# Import parser for RFC 5322 address parsing
try:
    from email._header_value_parser import get_mailbox as _get_mailbox
except ImportError:
    # Fallback for older Python versions
    try:
        from email.headerregistry import parser  # type: ignore[attr-defined]

        _get_mailbox = parser.get_mailbox  # type: ignore[attr-defined]
    except (ImportError, AttributeError):
        _get_mailbox = None  # type: ignore[assignment]

# Configure UTF-8 charset encoding
# Don't BASE64-encode UTF-8 messages to avoid spam filter issues
utf8_charset = Charset.Charset("utf-8")
utf8_charset.body_encoding = None  # type: ignore[assignment]  # Python defaults to BASE64
utf8_charset_qp = Charset.Charset("utf-8")
utf8_charset_qp.body_encoding = Charset.QP

# Default MIME type for attachments when type cannot be determined
DEFAULT_ATTACHMENT_MIME_TYPE = "application/octet-stream"

# RFC 5322 email line length limit
RFC5322_EMAIL_LINE_LENGTH_LIMIT = 998

# Header names that contain structured address data (RFC 5322)
ADDRESS_HEADERS = frozenset(
    {
        "from",
        "sender",
        "reply-to",
        "to",
        "cc",
        "bcc",
        "resent-from",
        "resent-sender",
        "resent-to",
        "resent-cc",
        "resent-bcc",
    }
)


def forbid_multi_line_headers(name: str, val: Any, encoding: str) -> tuple[str, str]:
    """
    Forbid multi-line headers to prevent header injection attacks.

    Args:
        name: The header name.
        val: The header value.
        encoding: The character encoding to use.

    Returns:
        A tuple of (name, encoded_value).

    Raises:
        BadHeaderError: If the header value contains newlines.
    """
    val = str(val)
    if "\n" in val or "\r" in val:
        raise BadHeaderError(f"Header values can't contain newlines (got {val!r} for header {name!r})")

    try:
        val.encode("ascii")
    except UnicodeEncodeError:
        if name.lower() in ADDRESS_HEADERS:
            val = ", ".join(sanitize_address(addr, encoding) for addr in getaddresses((val,)))
        else:
            val = Header(val, encoding).encode()
    else:
        if name.lower() == "subject":
            val = Header(val).encode()

    return name, val


def sanitize_address(addr: str | tuple[str, str], encoding: str) -> str:
    """
    Format and sanitize an email address.

    Args:
        addr: Either a string email address or a (name, address) tuple.
        encoding: The character encoding to use.

    Returns:
        A properly formatted email address string.

    Raises:
        ValueError: If the address is invalid.
    """
    if not isinstance(addr, tuple):
        addr = force_str(addr)
        try:
            token, rest = _get_mailbox(addr)  # type: ignore[misc]
        except (HeaderParseError, ValueError, IndexError) as exc:
            raise ValueError(f'Invalid address "{addr}"') from exc
        else:
            if rest:
                raise ValueError(f'Invalid address; only {token} could be parsed from "{addr}"')
            nm = token.display_name or ""
            localpart = token.local_part
            domain = token.domain or ""
    else:
        nm, address = addr
        localpart, domain = address.rsplit("@", 1)

    address_parts = nm + localpart + domain
    if "\n" in address_parts or "\r" in address_parts:
        raise ValueError("Invalid address; address parts cannot contain newlines.")

    # Avoid UTF-8 encode if possible
    try:
        nm.encode("ascii")
        nm = Header(nm).encode()
    except UnicodeEncodeError:
        nm = Header(nm, encoding).encode()

    try:
        localpart.encode("ascii")
    except UnicodeEncodeError:
        localpart = Header(localpart, encoding).encode()

    domain = punycode(domain)
    parsed_address = Address(username=localpart, domain=domain)
    return formataddr((nm, parsed_address.addr_spec))


class MIMEMixin:
    """Mixin class providing enhanced MIME message serialization."""

    def as_string(self, unixfrom: bool = False, linesep: str = "\n") -> str:
        """
        Return the entire formatted message as a string.

        This overrides the default implementation to not mangle lines
        that begin with 'From '.

        Args:
            unixfrom: Include Unix From_ envelope header if True.
            linesep: Line separator to use.

        Returns:
            The formatted message string.
        """
        fp = StringIO()
        g = generator.Generator(fp, mangle_from_=False)
        g.flatten(self, unixfrom=unixfrom, linesep=linesep)  # type: ignore[arg-type]
        return fp.getvalue()

    def as_bytes(self, unixfrom: bool = False, linesep: str = "\n") -> bytes:
        """
        Return the entire formatted message as bytes.

        This overrides the default implementation to not mangle lines
        that begin with 'From '.

        Args:
            unixfrom: Include Unix From_ envelope header if True.
            linesep: Line separator to use.

        Returns:
            The formatted message bytes.
        """
        fp = BytesIO()
        g = generator.BytesGenerator(fp, mangle_from_=False)
        g.flatten(self, unixfrom=unixfrom, linesep=linesep)  # type: ignore[arg-type]
        return fp.getvalue()


class SafeMIMEMessage(MIMEMixin, MIMEMessage):  # type: ignore[misc]
    """MIME message class with header injection protection."""

    def __setitem__(self, name: str, val: Any) -> None:
        # message/rfc822 attachments must be ASCII
        name, val = forbid_multi_line_headers(name, val, "ascii")
        MIMEMessage.__setitem__(self, name, val)


class SafeMIMEText(MIMEMixin, MIMEText):  # type: ignore[misc]
    """MIME text class with header injection protection."""

    def __init__(self, _text: str, _subtype: str = "plain", _charset: str | None = None) -> None:
        self.encoding = _charset
        MIMEText.__init__(self, _text, _subtype=_subtype, _charset=_charset)

    def __setitem__(self, name: str, val: Any) -> None:
        name, val = forbid_multi_line_headers(name, val, self.encoding or "utf-8")
        MIMEText.__setitem__(self, name, val)

    def set_payload(self, payload: Any, charset: Any = None) -> None:
        if charset == "utf-8" and not isinstance(charset, Charset.Charset):
            has_long_lines = any(len(line.encode()) > RFC5322_EMAIL_LINE_LENGTH_LIMIT for line in payload.splitlines())
            # Quoted-Printable encoding shortens long lines
            charset = utf8_charset_qp if has_long_lines else utf8_charset
        MIMEText.set_payload(self, payload, charset=charset)


class SafeMIMEMultipart(MIMEMixin, MIMEMultipart):  # type: ignore[misc]
    """MIME multipart class with header injection protection."""

    def __init__(
        self,
        _subtype: str = "mixed",
        boundary: str | None = None,
        _subparts: Any = None,
        encoding: str | None = None,
        **_params: Any,
    ) -> None:
        self.encoding = encoding
        MIMEMultipart.__init__(self, _subtype, boundary, _subparts, **_params)

    def __setitem__(self, name: str, val: Any) -> None:
        name, val = forbid_multi_line_headers(name, val, self.encoding or "utf-8")
        MIMEMultipart.__setitem__(self, name, val)


class EmailMessage:
    """
    A container for email information.

    This class represents an email message with all its components including
    subject, body, recipients, attachments, and headers.

    Attributes:
        content_subtype: The MIME subtype for the body (default: 'plain').
        mixed_subtype: The MIME subtype for mixed content (default: 'mixed').
        encoding: Character encoding for the message.

    Example:
        ```python
        msg = EmailMessage(
            subject="Hello",
            body="This is the message body",
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )
        await msg.send()
        ```
    """

    content_subtype: str = "plain"
    mixed_subtype: str = "mixed"
    encoding: str | None = None

    def __init__(
        self,
        subject: str = "",
        body: str = "",
        from_email: str | None = None,
        to: list[str] | tuple[str, ...] | None = None,
        cc: list[str] | tuple[str, ...] | None = None,
        bcc: list[str] | tuple[str, ...] | None = None,
        reply_to: list[str] | tuple[str, ...] | None = None,
        attachments: list[tuple[str, Any, str] | MIMEBase] | None = None,
        headers: dict[str, Any] | None = None,
        connection: BaseEmailBackend | None = None,
        mailman: Mail | None = None,
    ) -> None:
        """
        Initialize a single email message.

        Args:
            subject: The email subject line.
            body: The email body text.
            from_email: Sender's email address.
            to: List of recipient email addresses.
            cc: List of CC email addresses.
            bcc: List of BCC email addresses.
            reply_to: List of Reply-To email addresses.
            attachments: List of attachments.
            headers: Additional email headers.
            connection: Email backend connection.
            mailman: Mail instance to use.

        Raises:
            MailmanNotInitializedError: If no Mail instance is available.
            TypeError: If recipient arguments are not lists or tuples.
        """
        self.mailman = mailman or _get_global_mailman()

        if self.mailman is None:
            raise MailmanNotInitializedError()

        # Validate and set recipients
        self.to = self._validate_recipient_list(to, "to")
        self.cc = self._validate_recipient_list(cc, "cc")
        self.bcc = self._validate_recipient_list(bcc, "bcc")
        self.reply_to = self._validate_recipient_list(reply_to, "reply_to")

        self.from_email = from_email or self.mailman.default_sender
        self.subject = subject
        self.body = body or ""
        self.attachments: list[tuple[str, Any, str] | MIMEBase] = []

        if attachments:
            for attachment in attachments:
                if isinstance(attachment, MIMEBase):
                    self.attach(attachment)
                else:
                    self.attach(*attachment)

        self.extra_headers = headers or {}
        self.connection = connection

    @staticmethod
    def _validate_recipient_list(
        recipients: list[str] | tuple[str, ...] | None,
        arg_name: str,
    ) -> list[str]:
        """Validate and convert recipient list."""
        if recipients is None:
            return []
        if not isinstance(recipients, (list, tuple)):
            raise TypeError(f'"{arg_name}" argument must be a list or tuple')
        return list(recipients)

    def get_connection(self, fail_silently: bool = False) -> BaseEmailBackend:
        """
        Get or create an email backend connection.

        Args:
            fail_silently: Whether to suppress connection errors.

        Returns:
            An email backend connection.

        Raises:
            RuntimeError: If the application is not configured with Fastapi-Mailman.
        """
        if not self.connection:
            if not self.mailman:
                raise RuntimeError("The current application was not configured with Fastapi-Mailman")
            self.connection = self.mailman.get_connection(fail_silently=fail_silently)
        return self.connection

    def message(self) -> SafeMIMEText | SafeMIMEMultipart:
        """
        Build and return the MIME message.

        Returns:
            The constructed MIME message object.
        """
        encoding = self.encoding or self.mailman.default_charset  # type: ignore[union-attr]
        msg: SafeMIMEText | SafeMIMEMultipart = SafeMIMEText(self.body, self.content_subtype, encoding)
        msg = self._create_message(msg)
        msg["Subject"] = self.subject
        msg["From"] = self.extra_headers.get("From", self.from_email)

        self._set_list_header_if_not_empty(msg, "To", self.to)
        self._set_list_header_if_not_empty(msg, "Cc", self.cc)
        self._set_list_header_if_not_empty(msg, "Reply-To", self.reply_to)

        # Handle case-insensitive header names (RFC 2045)
        header_names = {key.lower() for key in self.extra_headers}

        if "date" not in header_names:
            msg["Date"] = formatdate(localtime=self.mailman.use_localtime)  # type: ignore[union-attr]

        if "message-id" not in header_names:
            msg["Message-ID"] = make_msgid(domain=DNS_NAME.get_fqdn())

        for name, value in self.extra_headers.items():
            if name.lower() != "from":  # From is already handled
                msg[name] = value

        return msg

    def recipients(self) -> list[str]:
        """
        Return a list of all recipients.

        Includes direct addressees, CC, and BCC entries.

        Returns:
            List of all recipient email addresses.
        """
        return [email for email in (self.to + self.cc + self.bcc) if email]

    async def send(self, fail_silently: bool = False) -> int:
        """
        Send the email message.

        Args:
            fail_silently: Whether to suppress sending errors.

        Returns:
            Number of messages sent (0 or 1).
        """
        if not self.recipients():
            return 0

        async with self.get_connection(fail_silently) as conn:
            return await conn.send_messages([self])

    def attach(
        self,
        filename: str | MIMEBase | None = None,
        content: Any = None,
        mimetype: str | None = None,
    ) -> None:
        """
        Attach a file to the email.

        Args:
            filename: The filename or a MIMEBase instance.
            content: The file content.
            mimetype: The MIME type of the attachment.

        Raises:
            ValueError: If invalid arguments are provided.
        """
        if isinstance(filename, MIMEBase):
            if content is not None or mimetype is not None:
                raise ValueError("content and mimetype must not be given when a MIMEBase instance is provided.")
            self.attachments.append(filename)
        elif content is None:
            raise ValueError("content must be provided.")
        else:
            mimetype = mimetype or mimetypes.guess_type(filename or "")[0] or DEFAULT_ATTACHMENT_MIME_TYPE
            basetype, _ = mimetype.split("/", 1)

            if basetype == "text" and isinstance(content, bytes):
                try:
                    content = content.decode()
                except UnicodeDecodeError:
                    mimetype = DEFAULT_ATTACHMENT_MIME_TYPE

            self.attachments.append((filename or "", content, mimetype))

    def attach_file(self, path: str | Path, mimetype: str | None = None) -> None:
        """
        Attach a file from the filesystem.

        Args:
            path: Path to the file.
            mimetype: The MIME type (optional, will be guessed if not provided).
        """
        path = Path(path)
        content = path.read_bytes()
        self.attach(path.name, content, mimetype)

    def _create_message(self, msg: SafeMIMEText | SafeMIMEMultipart) -> SafeMIMEText | SafeMIMEMultipart:
        """Create the message with attachments."""
        return self._create_attachments(msg)

    def _create_attachments(self, msg: SafeMIMEText | SafeMIMEMultipart) -> SafeMIMEText | SafeMIMEMultipart:
        """Add attachments to the message."""
        if self.attachments:
            encoding = self.encoding or self.mailman.default_charset  # type: ignore[union-attr]
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.mixed_subtype, encoding=encoding)  # type: ignore[assignment]
            if self.body or body_msg.is_multipart():
                msg.attach(body_msg)
            for attachment in self.attachments:
                if isinstance(attachment, MIMEBase):
                    msg.attach(attachment)
                else:
                    msg.attach(self._create_attachment(*attachment))
        return msg

    def _create_mime_attachment(self, content: Any, mimetype: str) -> MIMEBase:
        """
        Convert content and mimetype into a MIME attachment.

        Args:
            content: The attachment content.
            mimetype: The MIME type.

        Returns:
            A MIME attachment object.
        """
        basetype, subtype = mimetype.split("/", 1)

        attachment: MIMEBase
        if basetype == "text":
            encoding = self.encoding or self.mailman.default_charset  # type: ignore[union-attr]
            attachment = SafeMIMEText(content, subtype, encoding)
        elif basetype == "message" and subtype == "rfc822":
            # Per RFC2046 s5.2.1, message/rfc822 must not be base64 encoded
            if isinstance(content, EmailMessage):
                content = content.message()
            elif not isinstance(content, Message):
                content = message_from_string(force_str(content))
            attachment = SafeMIMEMessage(content, subtype)
        else:
            # Encode non-text attachments with base64
            attachment = MIMEBase(basetype, subtype)
            attachment.set_payload(content)
            Encoders.encode_base64(attachment)

        return attachment

    def _create_attachment(
        self,
        filename: str,
        content: Any,
        mimetype: str | None = None,
    ) -> MIMEBase:
        """Create a MIME attachment from filename, content, and mimetype."""
        attachment = self._create_mime_attachment(content, mimetype or DEFAULT_ATTACHMENT_MIME_TYPE)

        if filename:
            try:
                filename.encode("ascii")
            except UnicodeEncodeError:
                filename = ("utf-8", "", filename)  # type: ignore[assignment]
            attachment.add_header("Content-Disposition", "attachment", filename=filename)

        return attachment

    def _set_list_header_if_not_empty(
        self,
        msg: SafeMIMEText | SafeMIMEMultipart,
        header: str,
        values: list[str],
    ) -> None:
        """Set a header from the extra_headers or from the values list."""
        if values:
            try:
                value = self.extra_headers[header]
            except KeyError:
                value = ", ".join(str(v) for v in values)
            msg[header] = value


class EmailMultiAlternatives(EmailMessage):
    """
    Email message with support for alternative content types.

    Makes it easy to send multipart/alternative messages, such as
    including both text and HTML versions of the content.

    Example:
        ```python
        msg = EmailMultiAlternatives(
            subject="Hello",
            body="Plain text content",
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )
        msg.attach_alternative("<h1>HTML content</h1>", "text/html")
        await msg.send()
        ```
    """

    alternative_subtype: str = "alternative"

    def __init__(
        self,
        subject: str = "",
        body: str = "",
        from_email: str | None = None,
        to: list[str] | tuple[str, ...] | None = None,
        cc: list[str] | tuple[str, ...] | None = None,
        bcc: list[str] | tuple[str, ...] | None = None,
        reply_to: list[str] | tuple[str, ...] | None = None,
        attachments: list[tuple[str, Any, str] | MIMEBase] | None = None,
        headers: dict[str, Any] | None = None,
        alternatives: list[tuple[str, str]] | None = None,
        connection: BaseEmailBackend | None = None,
        mailman: Mail | None = None,
    ) -> None:
        """
        Initialize an email with alternative content types.

        Args:
            subject: The email subject line.
            body: The email body text (plain text version).
            from_email: Sender's email address.
            to: List of recipient email addresses.
            cc: List of CC email addresses.
            bcc: List of BCC email addresses.
            reply_to: List of Reply-To email addresses.
            attachments: List of attachments.
            headers: Additional email headers.
            alternatives: List of (content, mimetype) tuples.
            connection: Email backend connection.
            mailman: Mail instance to use.
        """
        super().__init__(
            subject,
            body,
            from_email,
            to,
            cc,
            bcc,
            reply_to,
            attachments,
            headers,
            connection,
            mailman,
        )
        self.alternatives: list[tuple[str, str]] = alternatives or []

    def attach_alternative(self, content: str, mimetype: str) -> None:
        """
        Attach an alternative content representation.

        Args:
            content: The alternative content.
            mimetype: The MIME type of the content.

        Raises:
            ValueError: If content or mimetype is None.
        """
        if content is None or mimetype is None:
            raise ValueError("Both content and mimetype must be provided.")
        self.alternatives.append((content, mimetype))

    def _create_message(self, msg: SafeMIMEText | SafeMIMEMultipart) -> SafeMIMEText | SafeMIMEMultipart:
        """Create message with alternatives and attachments."""
        return self._create_attachments(self._create_alternatives(msg))

    def _create_alternatives(self, msg: SafeMIMEText | SafeMIMEMultipart) -> SafeMIMEText | SafeMIMEMultipart:
        """Create the alternatives structure."""
        encoding = self.encoding or self.mailman.default_charset  # type: ignore[union-attr]

        if self.alternatives:
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.alternative_subtype, encoding=encoding)  # type: ignore[assignment]
            if self.body:
                msg.attach(body_msg)
            for alternative in self.alternatives:
                msg.attach(self._create_mime_attachment(*alternative))

        return msg
