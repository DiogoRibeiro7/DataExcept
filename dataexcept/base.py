"""The root of the DataExcept exception hierarchy.

Every operational exception this package defines derives from
:class:`DataExceptError`, so a caller can catch the whole library with one
clause while still catching narrowly where it matters::

    try:
        run_pipeline()
    except ValidationError:
        ...              # exactly this failure
    except DataExceptError:
        ...              # anything else DataExcept raised

(Constructors also raise plain ``TypeError`` when given invalid arguments.
Those are programming errors, not operational ones, and are deliberately not
part of this hierarchy.)

The base also carries the serialization contract for the hierarchy. Two
problems make that necessary:

* Most constructors take several arguments while ``Exception.args`` holds only
  the rendered message, so the default protocol -- which replays ``args``
  through ``__init__`` -- cannot rebuild them.
* Several exceptions accept arbitrary caller state (``DataValidationError``
  takes any ``value``), and that state may not be pickleable at all.

An exception that cannot cross a process boundary is useless exactly where a
data pipeline needs it most, so rather than fail, unpickleable state is
replaced by a description of what was there.
"""

from __future__ import annotations

import pickle
from typing import Any, Dict, Optional, Tuple, Type

from .redaction import redact_urls_in_text

__all__ = ["DataExceptError", "UnpicklableCause", "UnpicklableValue"]

#: Attribute names used across the package to hold the exception that caused
#: this one. Checked in order; the first that holds an exception wins.
_CAUSE_ATTRIBUTES = ("original", "original_exception", "cause")


class UnpicklableValue:
    """Stands in for state that could not survive serialization.

    An exception carrying a lambda, an open file or a lock would otherwise be
    unraisable across a process boundary. Keeping a description preserves what
    the value was for debugging, which is the reason it was attached.
    """

    __slots__ = ("description",)

    def __init__(self, description: str) -> None:
        self.description = description

    def __repr__(self) -> str:
        return f"<unpicklable: {self.description}>"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, UnpicklableValue)
            and other.description == self.description
        )

    def __hash__(self) -> int:
        return hash(self.description)


def _safe(value: Any) -> Any:
    """Return *value*, or a placeholder if it cannot be pickled."""
    try:
        pickle.dumps(value)
    except Exception:
        try:
            description = f"{type(value).__name__}: {value!r}"
        except Exception:  # pragma: no cover - a repr that itself raises
            description = type(value).__name__
        return UnpicklableValue(description[:200])
    return value


def _safe_exception(exc: Optional[BaseException]) -> Optional[BaseException]:
    """Return *exc*, or an exception describing it if it cannot be pickled."""
    if exc is None:
        return None
    try:
        pickle.dumps(exc)
    except Exception:
        return UnpicklableCause(f"{type(exc).__name__}: {exc}")
    return exc


def _rebuild(
    cls: Type["DataExceptError"],
    args: Tuple[Any, ...],
    state: Dict[str, Any],
    cause: Optional[BaseException] = None,
    context: Optional[BaseException] = None,
    suppress_context: bool = False,
) -> "DataExceptError":
    """Recreate *cls* without replaying its ``__init__``.

    Constructors validate and render a message from their arguments; replaying
    them would need those arguments, which ``args`` does not carry. Restoring
    ``args`` and ``__dict__`` directly reproduces the exception exactly.

    The three chain arguments carry defaults so that a payload pickled by an
    earlier version -- which passed only ``cls``, ``args`` and ``state`` --
    still loads. An exception can outlive an upgrade: it may sit in a task
    queue, or be sent by a worker running the previous release.

    ``__cause__``, ``__context__`` and ``__suppress_context__`` live outside
    ``__dict__`` -- they are special exception state -- so they are restored
    explicitly. Without this the chain is silently lost, and a traceback
    rebuilt in another process no longer shows what actually failed.
    """
    exc = cls.__new__(cls)
    Exception.__init__(exc, *args)
    exc.__dict__.update(state)
    exc.__cause__ = cause
    exc.__context__ = context
    exc.__suppress_context__ = suppress_context
    return exc


class DataExceptError(Exception):
    """Base class for every operational exception DataExcept raises."""

    #: Passed to redact_urls_in_text when scrubbing this class's message.
    #: WebhookError sets it False, because a webhook URL's path *is* the
    #: credential.
    _keep_url_path = True

    def __init__(self, *args: Any) -> None:
        # One boundary for the whole hierarchy: whatever built the message --
        # a constructor, a caller-supplied `message`, or the text of a wrapped
        # exception quoting the original URL -- it is scrubbed here. Redacting
        # only the structured argument leaves all three of those routes open.
        keep_path = type(self)._keep_url_path
        if args and isinstance(args[0], str):
            args = (redact_urls_in_text(args[0], keep_path=keep_path),) + args[1:]
        # Many classes also store the message on self.message and render *that*
        # in __str__, so scrubbing args alone would leave the rendered form
        # untouched. Subclasses set it before calling up, so it is here to fix.
        stored = self.__dict__.get("message")
        if isinstance(stored, str):
            # Written straight into __dict__, symmetric with the read above:
            # this rewrites state a subclass already stored, rather than the
            # base declaring an attribute of its own.
            self.__dict__["message"] = redact_urls_in_text(stored, keep_path=keep_path)
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

    def __reduce__(self) -> Tuple[Any, Tuple[Any, ...]]:
        args = tuple(_safe(arg) for arg in self.args)
        state = {key: _safe(value) for key, value in self.__dict__.items()}
        return (
            _rebuild,
            (
                type(self),
                args,
                state,
                _safe_exception(self.__cause__),
                _safe_exception(self.__context__),
                self.__suppress_context__,
            ),
        )


class UnpicklableCause(DataExceptError):
    """Stands in for a cause that could not be serialized.

    ``__cause__`` and ``__context__`` must be exceptions, so the placeholder
    used for ordinary attributes will not do here. Dropping the chain instead
    would silently lose the reason for the failure.
    """
