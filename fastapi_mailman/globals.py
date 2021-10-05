import typing as t

if t.TYPE_CHECKING:
    from . import Mail

    Mailman = t.TypeVar("Mailman", bound=Mail)

MAILMAN: t.Optional["Mailman"] = None
