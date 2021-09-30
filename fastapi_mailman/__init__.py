"""
Tools for sending email.
"""
from importlib import import_module

from fastapi_mailman.utils import DNS_NAME, CachedDnsName

from .message import (
    DEFAULT_ATTACHMENT_MIME_TYPE,
    BadHeaderError,
    EmailMessage,
    EmailMultiAlternatives,
    SafeMIMEMultipart,
    SafeMIMEText,
    forbid_multi_line_headers,
    make_msgid,
)
import types as ty
import typing as t

if t.TYPE_CHECKING:
    from fastapi_mailman.backends.base import BaseEmailBackend
    from .config import ConnectionConfig
    Mailman =t.TypeVar("Mailman", bound="Mail")

MAILMAN:t.Optional["Mailman"] = None

__all__ = [
    'CachedDnsName',
    'DNS_NAME',
    'EmailMessage',
    'EmailMultiAlternatives',
    'SafeMIMEText',
    'SafeMIMEMultipart',
    'DEFAULT_ATTACHMENT_MIME_TYPE',
    'make_msgid',
    'BadHeaderError',
    'forbid_multi_line_headers',
    'Mail',
]


available_backends = ['console', 'dummy', 'file', 'smtp', 'locmem']


class _MailMixin(object):
    
    def _get_backend_from_module(self, backend_module_name: str, backend_class_name: str) -> "BaseEmailBackend":
        """
        import the backend module and return the backend class.

        :param backend_module_name:
            the string based module name from where the backend class will be imported.

        :param backend_class_name:
            the string based backend class name.
        """
        backend_module: ty.ModuleType = import_module(backend_module_name)
        backend: "BaseEmailBackend" = getattr(backend_module, backend_class_name)
        return backend

    def import_backend(self, backend_name: t.Any) -> "BaseEmailBackend":
        """
        This is the base method to import the backend service.
        This method will implement the feature for fastapi_mailman to take custom backends.

        Now you can create your own backend class and implement with flask mailman.

        :for example::

            from flask import Flask

            app = Flask(__name__)
            app.config['MAIL_BACKEND'] = 'locmem'
            #or
            app.config['MAIL_BACKEND'] = 'smtp'
            #or
            app.config['MAIL_BACKEND'] = 'fastapi_mailman.backends.locmem'
            #or
            app.config['MAIL_BACKEND'] = 'fastapi_mailman.backends.locmem.EmailBackend'
            #or
            app.config['MAIL_BACKEND'] = 'your_project.mail.backends.custom.EmailBackend'
        """
        backend: t.Optional["BaseEmailBackend"] = None

        if not isinstance(backend_name, str):
            backend = backend_name

        else:
            default_backend_loc: str = "fastapi_mailman.backends"
            default_backend_class: str = "EmailBackend"

            if "." not in backend_name:
                backend_module_name: str = default_backend_loc + "." + backend_name
                backend: "BaseEmailBackend" = self._get_backend_from_module(backend_module_name, default_backend_class)

            else:
                if backend_name.endswith(default_backend_class):
                    backend_module_name, backend_class_name = backend_name.rsplit('.', 1)
                    backend: "BaseEmailBackend" = self._get_backend_from_module(backend_module_name, backend_class_name)

                else:
                    backend: "BaseEmailBackend" = self._get_backend_from_module(backend_name, default_backend_class)

        return backend

    def get_connection(self, backend=None, fail_silently=False, **kwds):
        """Load an email backend and return an instance of it.

        If backend is None (default), use app.config.MAIL_BACKEND.

        Both fail_silently and other keyword arguments are used in the
        constructor of the backend.
        """
        try:
            backend = backend or MAILMAN.backend

            klass = self.import_backend(backend)

        except ImportError:
            err_msg = (
                f"Unable to import backend: {backend}. "
                f"The available built-in mail backends are: {', '.join(available_backends)}"
            )
            raise RuntimeError(err_msg)

        return klass(mailman=MAILMAN, fail_silently=fail_silently, **kwds)

    async def send_mail(
        self,
        subject,
        message,
        from_email=None,
        recipient_list=None,
        fail_silently=False,
        auth_user=None,
        auth_password=None,
        connection=None,
        html_message=None,
    ):
        """
        Easy wrapper for sending a single message to a recipient list. All members
        of the recipient list will see the other recipients in the 'To' field.

        If auth_user is None, use the MAIL_USERNAME setting.
        If auth_password is None, use the MAIL_PASSWORD setting.
        """
        connection = connection or self.get_connection(
            username=auth_user,
            password=auth_password,
            fail_silently=fail_silently,
        )
        mail = EmailMultiAlternatives(MAILMAN, subject, message, from_email, recipient_list, connection=connection)
        if html_message:
            mail.attach_alternative(html_message, 'text/html')

        return await mail.send()

    async def send_mass_mail(self, datatuple, fail_silently=False, auth_user=None, auth_password=None, connection=None):
        """
        Given a datatuple of (subject, message, from_email, recipient_list), send
        each message to each recipient list. Return the number of emails sent.

        If from_email is None, use the MAIL_DEFAULT_SENDER setting.
        If auth_user and auth_password are set, use them to log in.
        If auth_user is None, use the MAIL_USERNAME setting.
        If auth_password is None, use the MAIL_PASSWORD setting.

        Note: The API for this method is frozen. New code wanting to extend the
        functionality should use the EmailMessage class directly.
        """
        connection = connection or await self.get_connection(
            username=auth_user,
            password=auth_password,
            fail_silently=fail_silently,
        )
        messages = [
            EmailMessage(MAILMAN, subject, message, sender, recipient, connection=connection)
            for subject, message, sender, recipient in datatuple
        ]
        return await connection.send_messages(messages)


class _Mail(_MailMixin):
    """Initialize a state instance with all configs and methods"""

    def __init__(
        self,
        server,
        port,
        username,
        password,
        use_tls,
        use_ssl,
        default_sender,
        timeout,
        ssl_keyfile,
        ssl_certfile,
        use_localtime,
        file_path,
        default_charset,
        backend,
    ):
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.default_sender = default_sender
        self.timeout = timeout
        self.ssl_keyfile = ssl_keyfile
        self.ssl_certfile = ssl_certfile
        self.use_localtime = use_localtime
        self.file_path = file_path
        self.default_charset = default_charset
        self.backend = backend


class Mail(_MailMixin):
    """Manages email messaging

    :param config: Default ConnectionConfig pydantic instance
    """

    def __init__(self, config:"ConnectionConfig"):
        self.config:"ConnectionConfig" = config
        self.state = self.initIns()


    def init_mail(self, config:"ConnectionConfig"):
        config_dict = config.dict()

        return _Mail(
            config_dict.get('MAIL_SERVER'),
            config_dict.get('MAIL_PORT'),
            config_dict.get('MAIL_USERNAME'),
            config_dict.get('MAIL_PASSWORD'),
            config_dict.get('MAIL_USE_TLS'),
            config_dict.get('MAIL_USE_SSL'),
            config_dict.get('MAIL_DEFAULT_SENDER'),
            config_dict.get('MAIL_TIMEOUT'),
            config_dict.get('MAIL_SSL_KEYFILE'),
            config_dict.get('MAIL_SSL_CERTFILE'),
            config_dict.get('MAIL_USE_LOCALTIME'),
            config_dict.get('MAIL_FILE_PATH'),
            config_dict.get('MAIL_DEFAULT_CHARSET'),
            config_dict.get('MAIL_BACKEND'),
        )

    def initIns(self):
        state = self.init_mail(self.config)
        global MAILMAN
        MAILMAN = state
        return state

    def __getattr__(self, name):
        return getattr(self.state, name)