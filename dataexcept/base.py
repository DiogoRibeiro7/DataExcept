"""The root of the DataExcept exception hierarchy.

Every exception this package raises derives from :class:`DataExceptError`, so a
caller can catch everything the library can raise with a single clause while
still catching narrowly where it matters::

    try:
        run_pipeline()
    except ValidationError:
        ...              # exactly this failure
    except DataExceptError:
        ...              # anything else DataExcept raised

The base also gives the whole hierarchy a working serialization contract. Many
of these exceptions take several constructor arguments while ``Exception.args``
holds only the rendered message, so the default pickling protocol -- which
replays ``args`` through ``__init__`` -- could not rebuild them. That made them
unusable across a process boundary, which is where a data pipeline most needs
them.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple, Type

__all__ = ["DataExceptError"]

#: Attribute names used across the package to hold the exception that caused
#: this one. Checked in order; the first that holds an exception wins.
_CAUSE_ATTRIBUTES = ("original", "original_exception", "cause")


def _rebuild(
    cls: Type["DataExceptError"], args: Tuple[Any, ...], state: Dict[str, Any]
) -> "DataExceptError":
    """Recreate *cls* without replaying its ``__init__``.

    Constructors here validate and render a message from their arguments;
    replaying them would need the original arguments, which ``args`` does not
    carry. Restoring ``args`` and ``__dict__` directly reproduces the exception
    exactly, including its message and every attribute it recorded.
    """
    exc = cls.__new__(cls)
    Exception.__init__(exc, *args)
    exc.__dict__.update(state)
    return exc


class DataExceptError(Exception):
    """Base class for every exception DataExcept raises."""

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        # Constructors that wrap another exception record it on an attribute.
        # Mirroring it into __cause__ is what makes a traceback print the
        # underlying failure, exactly as `raise ... from exc` would; assigning
        # __cause__ also sets __suppress_context__, as `raise from` does.
        for attribute in _CAUSE_ATTRIBUTES:
            candidate = getattr(self, attribute, None)
            if isinstance(candidate, BaseException):
                self.__cause__ = candidate
                break

    def __reduce__(
        self,
    ) -> Tuple[Any, Tuple[Type["DataExceptError"], Tuple[Any, ...], Dict[str, Any]]]:
        return (_rebuild, (type(self), self.args, self.__dict__.copy()))
